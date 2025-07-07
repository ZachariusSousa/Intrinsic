import numpy as np
import pygame
import random
from .items import export_block_constants, ORE_TYPES

globals().update(export_block_constants())
EMPTY = 0

BIOMES = ["forest", "plains", "desert", "ocean", "mountains"]

# === Global noise settings ===================================================
BIOME_SEGMENT   = 64           # columns per biome (~10 screens at 32-px tiles)
COARSE_STEP     = 128           # columns between elevation anchor points
SEA_LEVEL_FRACT = 0.30          # % of world-height where water surface sits
BLEND_WIDTH   = 16         # larger = softer transitions
BLEND_NOISE   = 0.35        # 0–1 → roughness of patchy blocks in the blend zone

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
    return BIOMES[_hash32(segment * 97 + WORLD_SEED) % len(BIOMES)]


def _biome_blend(global_x: int) -> tuple[str, str, float]:
    """
    Returns (left_biome, right_biome, t) where
        • t ∈ [0,1] spans the *entire* 2·BLEND_WIDTH zone around a boundary
        • outside that zone: left == right and t == 0
    This eliminates the double-ramp “V” shape.
    """
    seg        = global_x // BIOME_SEGMENT      
    pos        = global_x %  BIOME_SEGMENT     
    b_left     = _biome_for_x((seg - 1) * BIOME_SEGMENT)
    b_mid      = _biome_for_x(seg       * BIOME_SEGMENT)
    b_right    = _biome_for_x((seg + 1) * BIOME_SEGMENT)

    if pos >= BIOME_SEGMENT - BLEND_WIDTH:
        t = (pos - (BIOME_SEGMENT - BLEND_WIDTH)) / (2 * BLEND_WIDTH)  
        return b_mid, b_right, t

    if pos < BLEND_WIDTH:
        t = (pos + BLEND_WIDTH) / (2 * BLEND_WIDTH)        
        return b_left, b_mid, t

    return b_mid, b_mid, 0.0




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

    min_elev, max_elev = int(height * 0.35), int(height * 0.55)

    # Generate every column
    for local_x in range(width):
        global_x      = world_x_offset + local_x
        biome, biome2, blend_t = _biome_blend(global_x)

        base_segment = None
        if biome == _biome_for_x(global_x):
            base_segment = global_x // BIOME_SEGMENT
        else:
            base_segment = (global_x // BIOME_SEGMENT) - 1

        base_origin_x = base_segment * BIOME_SEGMENT
        anchor_idx0   = (base_origin_x + (global_x - base_origin_x)) // COARSE_STEP
        anchor_idx1   = anchor_idx0 + 1
        anchor_x0     = anchor_idx0 * COARSE_STEP
        t_elev        = (global_x - anchor_x0) / COARSE_STEP


        elev0 = _anchor_elevation(anchor_idx0, min_elev, max_elev)
        elev1 = _anchor_elevation(anchor_idx1, min_elev, max_elev)
        base_y = _lerp(elev0, elev1, t_elev)


        def _bias(b: str, base: float) -> float:
            if b == "ocean":
                return sea_level - base
            if b == "plains":
                return _lerp(base, sea_level, 0.4) - base
            if b == "mountains":
                return -8.0
            return 0.0

        bias_left  = _bias(biome,  base_y)
        bias_right = _bias(biome2, base_y)

        w = (1 - np.cos(blend_t * np.pi)) * 0.5
        surface_y_f = base_y + (1 - w) * bias_left + w * bias_right

        surface_y = int(round(surface_y_f))   
        surface_y = max(0, min(height - 2, surface_y))


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
