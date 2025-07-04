import numpy as np
import scipy.interpolate

# === Block Types ===
EMPTY = 0
DIRT = 1
STONE = 2
COPPER_ORE = 3
IRON_ORE = 4
GOLD_ORE = 5
WOOD = 6
LEAVES = 7
WATER = 8
SAND = 9
CACTUS = 10
GRASS = 11
SNOW = 12
ICE = 13

ORE_TYPES = [COPPER_ORE, IRON_ORE, GOLD_ORE]

COLOR_MAP = {
    DIRT: (139, 69, 19),
    STONE: (100, 100, 100),
    COPPER_ORE: (184, 115, 51),
    IRON_ORE: (197, 197, 197),
    GOLD_ORE: (255, 215, 0),
    WOOD: (160, 82, 45),
    LEAVES: (34, 139, 34),
    WATER: (0, 0, 255),
    SAND: (237, 201, 175),
    CACTUS: (0, 155, 0),
    GRASS: (124, 252, 0),
    SNOW: (255, 250, 250),
    ICE: (173, 216, 230),
}

BIOMES = ["forest", "desert", "plains", "ocean", "mountains"]

def generate_noise(size, octaves=4, base_scale=40, seed=1):
    np.random.seed(seed)
    result = np.zeros(size)
    for i in range(octaves):
        scale = base_scale * (2 ** i)
        amp = 0.5 ** i
        anchors = np.linspace(0, size, scale)
        values = np.random.rand(scale)
        interp = scipy.interpolate.PchipInterpolator(anchors, values)
        result += interp(np.arange(size)) * amp
    return result

def assign_biomes_global(total_width, biome_segment=50, seed=1):
    np.random.seed(seed)
    biome_map = []
    while len(biome_map) < total_width:
        biome = np.random.choice(BIOMES)
        biome_map += [biome] * biome_segment
    return biome_map[:total_width]

    # Smooth final elevation transitions (limit max step change)
def smooth_elevation(elevations, window=5):
    padded = np.pad(elevations, (window // 2,), mode='edge')
    smoothed = np.convolve(padded, np.ones(window) / window, mode='valid')
    return smoothed.astype(int)



def generate_world(
    width,
    height,
    world_x_offset=0,
    dirt_depth=4,
    stone_depth=30,
    ore_chance=0.03,
    tree_chance=0.05,
):
    """Generate a 2D world chunk with elevation scaling and biome continuity."""
    grid = np.zeros((height, width), dtype=np.int8)

    # Elevation and biome generation
        # Always generate from absolute position 0 to end, then slice properly
    start_x = world_x_offset
    end_x = world_x_offset + width

    abs_start = min(start_x, 0)
    abs_end = max(end_x, 0)
    full_width = abs_end - abs_start  # total width needed
    
    elev_seed = np.random.randint(0, 10_000)
    raw_elevation = generate_noise(full_width, base_scale=40, seed=elev_seed)
    min_elev = int(height * 0.2)
    max_elev = int(height * 0.3)
    elevation_scaled = (raw_elevation * (max_elev - min_elev) + min_elev).astype(int)

    # Slice before smoothing
    slice_start = start_x - abs_start
    slice_end = slice_start + width
    elevation = smooth_elevation(elevation_scaled[slice_start:slice_end])

    biome_seed = np.random.randint(0, 10_000)
    biome_map_full = assign_biomes_global(full_width, biome_segment=50, seed=biome_seed)
    biome_map = biome_map_full[slice_start:slice_end]

    biome_map = biome_map_full[slice_start:slice_end]


    for x in range(width):
        surface_y = max(0, min(height - 1, elevation[x]))  # clamp to valid range
        biome = biome_map[x]

        # === Surface and subsurface ===
        for y in range(surface_y, height):
            depth = y - surface_y
            if depth == 0:
                if biome == "desert":
                    grid[y, x] = SAND
                elif biome == "plains":
                    grid[y, x] = GRASS
                elif biome == "ocean":
                    grid[y, x] = WATER
                elif biome == "mountains":
                    grid[y, x] = SNOW
                else:
                    grid[y, x] = DIRT
            elif depth < dirt_depth:
                grid[y, x] = SAND if biome == "desert" else DIRT
            elif depth < stone_depth:
                grid[y, x] = STONE
                if np.random.rand() < ore_chance:
                    grid[y, x] = np.random.choice(ORE_TYPES)
            else:
                grid[y, x] = STONE

        # === Decorations ===
        if biome == "forest" and grid[surface_y, x] == DIRT and np.random.rand() < tree_chance:
            trunk_height = np.random.randint(3, 6)
            for h in range(trunk_height):
                y_pos = surface_y - h
                if 0 <= y_pos < height:
                    grid[y_pos, x] = WOOD
            top_y = surface_y - trunk_height + 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx = x + dx
                    ny = top_y + dy
                    if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == EMPTY:
                        grid[ny, nx] = LEAVES

        elif biome == "desert" and grid[surface_y, x] == SAND and np.random.rand() < 0.03:
            cactus_height = np.random.randint(2, 4)
            for h in range(cactus_height):
                y_pos = surface_y - h
                if 0 <= y_pos < height:
                    grid[y_pos, x] = CACTUS

        elif biome == "mountains" and np.random.rand() < 0.1:
            for h in range(1, 3):
                y_pos = surface_y + h
                if 0 <= y_pos < height:
                    grid[y_pos, x] = STONE

    # Bedrock
    grid[-1, :] = STONE
    return grid

def blocks_from_grid(grid, tile_size):
    import pygame
    height, width = grid.shape
    solid = []
    water = []

    for y in range(height):
        for x in range(width):
            block = grid[y, x]
            if block == EMPTY:
                continue
            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            if block == WATER:
                water.append(rect)
            else:
                solid.append((rect, block))
    return solid, water
