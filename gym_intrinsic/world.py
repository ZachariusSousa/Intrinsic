import numpy as np
import pygame
import random
from .items import Block, ORE_TYPES


EMPTY = 0

# === List of available biomes ===
BIOMES = ["forest", "plains", "desert", "ocean", "mountains"]

# === Global terrain parameters ===
BIOME_SEGMENT   = 64     # Width of a biome in tiles
COARSE_STEP     = 128    # Distance between elevation anchor points
SEA_LEVEL_FRACT = 0.30   # Sea level as a fraction of total world height
BLEND_WIDTH     = 16     # Width of the biome blend zone
BLEND_NOISE     = 0.35   # Randomness in biome blending

# === Cave generation settings (2D value noise) ===
CAVE_FREQ   = 6          # Grid cell size for noise interpolation (lower = tighter variation)
CAVE_THRESH = 0.45       # Noise threshold under which tiles become empty (caves)

# === Value noise for caves ===================================================
def _valrand(ix: int, iy: int) -> float:
    """Repeatable pseudo-random value for grid point (ix, iy)."""
    return _rand_unit(ix * 374761393 + iy * 668265263)

def _value_noise(x: int, y: int, freq: int = CAVE_FREQ) -> float:
    """
    2D bilinear-interpolated value noise.
    Produces smooth pseudo-random values from a coarse grid.
    """
    gx, gy = x // freq, y // freq
    fx, fy = (x % freq) / freq, (y % freq) / freq

    v00 = _valrand(gx,     gy    )
    v10 = _valrand(gx + 1, gy    )
    v01 = _valrand(gx,     gy + 1)
    v11 = _valrand(gx + 1, gy + 1)

    vx0 = _lerp(v00, v10, fx)
    vx1 = _lerp(v01, v11, fx)
    return _lerp(vx0, vx1, fy)

# === Hash-based utilities for deterministic generation =======================
def _hash32(x: int) -> int:
    """Cheap 32-bit hash (Thomas Wang's integer hash)."""
    x = (x ^ 61) ^ (x >> 16)
    x = x + (x << 3)
    x = x ^ (x >> 4)
    x = x * 0x27d4eb2d
    x = x ^ (x >> 15)
    return x & 0xFFFFFFFF

def _rand_unit(n: int) -> float:
    """Convert hashed int to float in [0, 1)."""
    return _hash32(n + WORLD_SEED) / 0xFFFFFFFF

def _anchor_elevation(anchor_idx: int, h_min: int, h_max: int) -> int:
    """Return base elevation for a terrain anchor point."""
    return int(h_min + _rand_unit(anchor_idx * 17) * (h_max - h_min))

def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + t * (b - a)

# === Biome selection and blending ============================================
def _biome_for_x(global_x: int) -> str:
    """Choose a biome based on tile's global X coordinate."""
    segment = global_x // BIOME_SEGMENT
    return BIOMES[_hash32(segment * 97 + WORLD_SEED) % len(BIOMES)]

def _biome_blend(global_x: int) -> tuple[str, str, float]:
    """
    Returns (left_biome, right_biome, blend_t)
    where blend_t ∈ [0, 1] indicates position within blend zone.
    """
    seg  = global_x // BIOME_SEGMENT
    pos  = global_x % BIOME_SEGMENT
    b_left  = _biome_for_x((seg - 1) * BIOME_SEGMENT)
    b_mid   = _biome_for_x(seg * BIOME_SEGMENT)
    b_right = _biome_for_x((seg + 1) * BIOME_SEGMENT)

    if pos >= BIOME_SEGMENT - BLEND_WIDTH:
        t = (pos - (BIOME_SEGMENT - BLEND_WIDTH)) / (2 * BLEND_WIDTH)
        return b_mid, b_right, t
    if pos < BLEND_WIDTH:
        t = (pos + BLEND_WIDTH) / (2 * BLEND_WIDTH)
        return b_left, b_mid, t

    return b_mid, b_mid, 0.0

# === Set the world seed ======================================================
def set_world_seed(seed: int | None = None):
    """Set global WORLD_SEED. If none, generate a new random one."""
    global WORLD_SEED
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    WORLD_SEED = seed & 0xFFFFFFFF
    random.seed(seed)
    np.random.seed(seed)
set_world_seed()

# === Main world generation function ==========================================
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
    Generate a terrain slice of width × height starting at world_x_offset.
    Includes biome blending, surface materials, ores, and cave carving.
    """
    grid = np.zeros((height, width), dtype=np.int8)
    sea_level = int(height * SEA_LEVEL_FRACT)
    min_elev, max_elev = int(height * 0.35), int(height * 0.55)

    for local_x in range(width):
        global_x = world_x_offset + local_x
        biome, biome2, blend_t = _biome_blend(global_x)

        # Determine elevation anchors for smooth terrain
        base_segment = global_x // BIOME_SEGMENT if biome == _biome_for_x(global_x) else (global_x // BIOME_SEGMENT) - 1
        base_origin_x = base_segment * BIOME_SEGMENT
        anchor_idx0 = (base_origin_x + (global_x - base_origin_x)) // COARSE_STEP
        anchor_idx1 = anchor_idx0 + 1
        anchor_x0   = anchor_idx0 * COARSE_STEP
        t_elev      = (global_x - anchor_x0) / COARSE_STEP

        elev0 = _anchor_elevation(anchor_idx0, min_elev, max_elev)
        elev1 = _anchor_elevation(anchor_idx1, min_elev, max_elev)
        base_y = _lerp(elev0, elev1, t_elev)

        # Apply biome-specific elevation offsets
        def _bias(b: str, base: float) -> float:
            if b == "ocean": return sea_level - base
            if b == "plains": return _lerp(base, sea_level, 0.4) - base
            if b == "mountains": return -8.0
            return 0.0

        bias_left  = _bias(biome,  base_y)
        bias_right = _bias(biome2, base_y)
        w = (1 - np.cos(blend_t * np.pi)) * 0.5
        surface_y_f = base_y + (1 - w) * bias_left + w * bias_right
        surface_y = max(0, min(height - 2, int(round(surface_y_f))))

        # Fill column from surface downward
        water_depth = 6
        for y in range(surface_y, height):
            depth = y - surface_y

            # === Carve out caves using value noise ===
            if depth >= dirt_depth:
                n = _value_noise(global_x, y)
                if n < CAVE_THRESH:
                    continue  # leave cell empty and skip material placement

            # === Ocean water surface ===
            if biome == "ocean" and depth < water_depth:
                grid[y, local_x] = Block.WATER
                continue

            # === Surface block ===
            if depth == 0:
                def _top(b: str):
                    return {
                        "desert": Block.SAND,
                        "plains": Block.GRASS,
                        "mountains": Block.SNOW,
                        "ocean": Block.SAND,
                    }.get(b, Block.DIRT)

                if blend_t == 0:
                    grid[y, local_x] = _top(biome)
                else:
                    prob = blend_t + (np.random.rand() - 0.5) * BLEND_NOISE
                    grid[y, local_x] = _top(biome2) if prob > 0.5 else _top(biome)

            # === Subsurface layer ===
            elif depth < dirt_depth:
                grid[y, local_x] = Block.SAND if biome == "desert" else Block.DIRT

            # === Stone and ores ===
            elif depth < stone_depth:
                grid[y, local_x] = np.random.choice(ORE_TYPES) if np.random.rand() < ore_chance else Block.STONE
            else:
                grid[y, local_x] = Block.STONE

        # === Tree decoration (forest) ===
        if biome == "forest" and grid[surface_y, local_x] == Block.DIRT and np.random.rand() < tree_chance:
            trunk_h = np.random.randint(3, 6)
            for h in range(trunk_h):
                y = surface_y - h
                if y >= 0:
                    grid[y, local_x] = Block.WOOD
            top_y = surface_y - trunk_h + 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = local_x + dx, top_y + dy
                    if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == EMPTY:
                        grid[ny, nx] = Block.LEAVES

        # === Cactus decoration (desert) ===
        elif biome == "desert" and grid[surface_y, local_x] == Block.SAND and np.random.rand() < 0.03:
            c_h = np.random.randint(2, 4)
            for h in range(c_h):
                y = surface_y - h
                if y >= 0:
                    grid[y, local_x] = Block.CACTUS

    # Final bedrock row
    grid[-1, :] = Block.STONE
    return grid

# === Block rect conversion ===================================================
def blocks_from_grid(grid: np.ndarray, tile_size: int):
    """
    Converts grid to Pygame rects for collisions and rendering.
    Returns solid block rects and water rects separately.
    """
    height, width = grid.shape
    solid, water = [], []

    for y in range(height):
        for x in range(width):
            block = grid[y, x]
            if block == EMPTY:
                continue
            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            (water if block == Block.WATER else solid).append((rect, block) if block != Block.WATER else rect)

    return solid, water
