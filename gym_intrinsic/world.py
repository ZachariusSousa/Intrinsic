import numpy as np
import pygame
import random

# === Block types ============================================================
EMPTY, DIRT, STONE, COPPER_ORE, IRON_ORE, GOLD_ORE, WOOD, LEAVES, WATER, SAND, CACTUS, GRASS, SNOW, ICE = range(14)
ORE_TYPES = [COPPER_ORE, IRON_ORE, GOLD_ORE]

COLOR_MAP = {
    DIRT: (139, 69, 19),         STONE: (100, 100, 100),
    COPPER_ORE: (184, 115, 51),  IRON_ORE: (197, 197, 197),
    GOLD_ORE: (255, 215, 0),     WOOD: (160, 82, 45),
    LEAVES: (34, 139, 34),       WATER: (0, 0, 255),
    SAND: (237, 201, 175),       CACTUS: (0, 155, 0),
    GRASS: (124, 252,   0),      SNOW:  (255, 250, 250),
    ICE:   (173, 216, 230),
}

BIOMES = ["forest", "plains", "desert", "ocean", "mountains"]

# === Global noise settings ===================================================
BIOME_SEGMENT   = 64           # columns per biome (~10 screens at 32-px tiles)
COARSE_STEP     = 128           # columns between elevation anchor points
SEA_LEVEL_FRACT = 0.30          # % of world-height where water surface sits
BLEND_WIDTH   = 12          # try 16-48; larger = softer transitions
BLEND_NOISE   = 0.35        # 0–1 → roughness of patchy blocks in the band

# ---------------------------------------------------------------------------
# – helper noise utilities (no external libs, fully deterministic) –
# ---------------------------------------------------------------------------
def _hash32(x: int) -> int:
    """Cheap 32-bit integer hash (Thomas Wang)."""
    x = (x ^ 61) ^ (x >> 16)
    x = x + (x << 3)
    x = x ^ (x >> 4)
    x = x * 0x27d4eb2d
    x = x ^ (x >> 15)
    return x & 0xFFFFFFFF

def _rand_unit(n: int) -> float:
    """Deterministic pseudorandom float in [0,1)."""
    return _hash32(n + WORLD_SEED) / 0xFFFFFFFF

def _anchor_elevation(anchor_idx: int, h_min: int, h_max: int) -> int:
    """Deterministic elevation at an anchor column."""
    return int(h_min + _rand_unit(anchor_idx * 17) * (h_max - h_min))

def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)

def _biome_for_x(global_x: int) -> str:
    """Biome chosen per BIOME_SEGMENT; now depends on WORLD_SEED too."""
    segment = global_x // BIOME_SEGMENT
    # OLD: return BIOMES[_hash32(segment * 97) % len(BIOMES)]
    return BIOMES[_hash32(segment * 97 + WORLD_SEED) % len(BIOMES)]

def _biome_blend(global_x: int) -> tuple[str, str, float]:
    """
    Returns (primary_biome, neighbour_biome, t)  where  t∈[0,1].
    When t≈0  you are in the heart of the primary biome.
    When t≈1  you are inside the neighbour biome.
    """
    segment      = global_x // BIOME_SEGMENT
    pos_in_seg   = global_x %  BIOME_SEGMENT

    if pos_in_seg < BLEND_WIDTH:                       # left edge → blend with previous segment
        neighbour_seg = segment - 1
        t             = 1.0 - pos_in_seg / BLEND_WIDTH
    elif pos_in_seg > BIOME_SEGMENT - BLEND_WIDTH:     # right edge → blend with next segment
        neighbour_seg = segment + 1
        t             = (pos_in_seg - (BIOME_SEGMENT - BLEND_WIDTH)) / BLEND_WIDTH
    else:                                              # deep inside the segment
        return _biome_for_x(global_x), _biome_for_x(global_x), 0.0

    primary   = _biome_for_x(global_x)
    neighbour = _biome_for_x((neighbour_seg) * BIOME_SEGMENT)
    return primary, neighbour, t


def set_world_seed(seed: int | None = None):
    """
    Change the global WORLD_SEED used by every biome/terrain hash.
    Call once at start-up.  If you pass no argument, we pick a new
    pseudo-random seed so each program run is unique.
    """
    global WORLD_SEED
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    WORLD_SEED = seed & 0xFFFFFFFF       # keep it 32-bit for the hash
    random.seed(seed)                    # for np.random.rand() calls
    np.random.seed(seed)
set_world_seed()

# ---------------------------------------------------------------------------
# – public API : generate_world() –
# ---------------------------------------------------------------------------
def generate_world(
    width: int,
    height: int,
    world_x_offset: int = 0,
    *,
    dirt_depth: int = 4,
    stone_depth: int = 30,
    ore_chance: float = 0.03,
    tree_chance: float = 0.05,
):
    """
    Produce a slice of the infinite world starting at `world_x_offset`
    (in tiles) and spanning `width` columns by `height` rows.
    """
    grid = np.zeros((height, width), dtype=np.int8)
    sea_level = int(height * SEA_LEVEL_FRACT)

    # Pre-compute anchor elevations for the whole slice
    min_elev, max_elev = int(height * 0.35), int(height * 0.55)

    # Generate every column
    for local_x in range(width):
        global_x      = world_x_offset + local_x
        biome, biome2, blend_t = _biome_blend(global_x)

        # --- inside the for-column loop, just after you compute `biome, biome2, blend_t`
        # PRECOMPUTE elevation anchors for *all* biomes  ────────────────
        anchor_idx0 = global_x // COARSE_STEP
        anchor_idx1 = anchor_idx0 + 1
        anchor_x0   = anchor_idx0 * COARSE_STEP
        t_elev      = (global_x - anchor_x0) / COARSE_STEP

        elev0 = _anchor_elevation(anchor_idx0, min_elev, max_elev)
        elev1 = _anchor_elevation(anchor_idx1, min_elev, max_elev)
        # ───────────────────────────────────────────────────────────────

        # ----- Elevation ------------------------------------------------
        if biome == "ocean":
            surface_y = sea_level                       # perfectly flat water-line
        else:
            surface_y = int(_lerp(elev0, elev1, t_elev))

            # biome-specific tweaks …
            if biome == "plains":
                surface_y = int(_lerp(surface_y, sea_level, 0.4))
            elif biome == "mountains":
                surface_y -= 8
                                            # raise terrain (smaller y → higher)
                
        if blend_t > 0.0:
        # Compute neighbour biome’s “ideal” surface_y the same way
            neighbour_surface = sea_level if biome2 == "ocean" else surface_y  # start with something
            if biome2 != "ocean":
                elev0_n = _anchor_elevation(anchor_idx0, min_elev, max_elev)
                elev1_n = _anchor_elevation(anchor_idx1, min_elev, max_elev)
                neighbour_surface = int(_lerp(elev0_n, elev1_n, t_elev))
                if biome2 == "plains":
                    neighbour_surface = int(_lerp(neighbour_surface, sea_level, 0.4))
                elif biome2 == "mountains":
                    neighbour_surface -= 8

            # Blend the two heights
            surface_y = int(_lerp(surface_y, neighbour_surface, blend_t))


        surface_y = max(0, min(height - 2, surface_y))               # clamp

        # ----- Column filling ----------------------------------------------
        water_depth = 6  # tiles
        for y in range(surface_y, height):
            depth = y - surface_y

            # === WATER (only oceans; keep first several blocks)
            if biome == "ocean" and depth < water_depth:
                grid[y, local_x] = WATER
                continue

            # === Surface block ===
            if depth == 0:
                # decide surface material for primary & neighbour
                def _top(b: str):
                    return {
                        "desert": SAND,
                        "plains": GRASS,
                        "mountains": SNOW,
                        "ocean": SAND,
                    }.get(b, DIRT)

                if blend_t == 0:
                    grid[y, local_x] = _top(biome)
                else:
                    # probabilistic mix so patches look noisy
                    prob = blend_t + (np.random.rand() - 0.5) * BLEND_NOISE
                    grid[y, local_x] = _top(biome2) if prob > 0.5 else _top(biome)


            # === Sub-surface dirt/sand ===
            elif depth < dirt_depth:
                grid[y, local_x] = SAND if biome == "desert" else DIRT

            # === Stone & ores ===
            elif depth < stone_depth:
                if np.random.rand() < ore_chance:
                    grid[y, local_x] = np.random.choice(ORE_TYPES)
                else:
                    grid[y, local_x] = STONE
            else:
                grid[y, local_x] = STONE

        # ----- Decorations ---------------------------------------------------
        if biome == "forest" and grid[surface_y, local_x] == DIRT and np.random.rand() < tree_chance:
            trunk_h = np.random.randint(3, 6)
            for h in range(trunk_h):
                y = surface_y - h
                if y >= 0:
                    grid[y, local_x] = WOOD
            top_y = surface_y - trunk_h + 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = local_x + dx, top_y + dy
                    if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == EMPTY:
                        grid[ny, nx] = LEAVES

        elif biome == "desert" and grid[surface_y, local_x] == SAND and np.random.rand() < 0.03:
            c_h = np.random.randint(2, 4)
            for h in range(c_h):
                y = surface_y - h
                if y >= 0:
                    grid[y, local_x] = CACTUS

    # Bedrock layer (last row)
    grid[-1, :] = STONE
    return grid

# ---------------------------------------------------------------------------
# – unchanged: blocks_from_grid –
# ---------------------------------------------------------------------------
def blocks_from_grid(grid: np.ndarray, tile_size: int):
    """Return solid-block rects (for collisions) and water rects (for swimming)."""
    height, width = grid.shape
    solid, water = [], []

    for y in range(height):
        for x in range(width):
            block = grid[y, x]
            if block == EMPTY:
                continue
            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            (water if block == WATER else solid).append((rect, block) if block != WATER else rect)

    return solid, water
