import numpy as np

# Block type constants
EMPTY = 0
DIRT = 1
STONE = 2
COPPER_ORE = 3
IRON_ORE = 4
GOLD_ORE = 5
WOOD = 6
LEAVES = 7
WATER = 8

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
}

def generate_world(
    width,
    height,
    dirt_layers=3,
    stone_layers=20,
    ore_chance=0.02,
    tree_chance=0.05,
    water_chance=0.1,
):
    """Generate a simple world grid with dirt, stone, ore layers and trees."""
    grid = np.zeros((height, width), dtype=np.int8)

    for y in range(height):
        if y >= height - stone_layers:
            grid[y, :] = STONE
            for x in range(width):
                if np.random.random() < ore_chance:
                    grid[y, x] = np.random.choice(ORE_TYPES)
        elif y >= height - stone_layers - dirt_layers:
            grid[y, :] = DIRT

    # add a bedrock layer at the bottom to stand on
    grid[-1, :] = STONE

    # generate trees on the surface
    surface_y = height - stone_layers - dirt_layers - 1
    for x in range(width):
        if (
            np.random.random() < tree_chance
            and grid[surface_y, x] == EMPTY
            and grid[surface_y + 1, x] == DIRT
        ):
            trunk_height = np.random.randint(3, 6)
            for h in range(trunk_height):
                y_pos = surface_y - h
                if y_pos >= 0:
                    grid[y_pos, x] = WOOD
            top_y = surface_y - trunk_height + 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx = x + dx
                    ny = top_y + dy
                    if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == EMPTY:
                        grid[ny, nx] = LEAVES

    # generate simple water pools on the surface
    for x in range(width):
        if np.random.random() < water_chance and grid[surface_y, x] == EMPTY:
            grid[surface_y, x] = WATER
            if surface_y + 1 < height and grid[surface_y + 1, x] == EMPTY:
                grid[surface_y + 1, x] = WATER

    return grid

def blocks_from_grid(grid, tile_size):
    """Create pygame.Rects from grid cells for rendering and collision."""
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
