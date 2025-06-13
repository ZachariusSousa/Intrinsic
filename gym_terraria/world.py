import numpy as np

# Block type constants
EMPTY = 0
DIRT = 1
STONE = 2
ORE = 3

COLOR_MAP = {
    DIRT: (139, 69, 19),
    STONE: (100, 100, 100),
    ORE: (255, 215, 0),
}

def generate_world(width, height, dirt_layers=3, stone_layers=20, ore_chance=0.02):
    """Generate a simple world grid with dirt, stone and ore layers."""
    grid = np.zeros((height, width), dtype=np.int8)
    for y in range(height):
        if y >= height - stone_layers:
            grid[y, :] = STONE
            for x in range(width):
                if np.random.random() < ore_chance:
                    grid[y, x] = ORE
        elif y >= height - stone_layers - dirt_layers:
            grid[y, :] = DIRT
    # add a bedrock layer at the bottom to stand on
    grid[-1, :] = STONE
    return grid

def blocks_from_grid(grid, tile_size):
    """Create pygame.Rects from grid cells for rendering and collision."""
    import pygame

    height, width = grid.shape
    blocks = []
    for y in range(height):
        for x in range(width):
            block = grid[y, x]
            if block != EMPTY:
                rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                blocks.append((rect, block))
    return blocks
