import heapq
import numpy as np

def is_solid(env, x, y):
    if 0 <= x < env.grid_width and 0 <= y < env.grid_height:
        block = env.grid[y, x]
        return block not in (0, 8)  # not EMPTY or WATER
    return False

def is_walkable(env, x, y):
    """Tile is air and has solid ground underneath."""
    return (
        0 <= x < env.grid_width and 0 <= y < env.grid_height - 1
        and env.grid[y, x] == 0
        and is_solid(env, x, y + 1)
    )
    
def is_step_up_tile(env, x, y):
    """Can step onto this tile from below if it's air and tile below is solid."""
    if 0 <= x < env.grid_width and 1 <= y < env.grid_height:
        return (
            env.grid[y, x] == 0 and  # air
            is_solid(env, x, y + 1) and  # solid underfoot
            is_solid(env, x, y + 1)  # support below
        )
    return False

def get_neighbors(env, x, y):
    neighbors = []

    # Walk left/right
    for dx in [-1, 1]:
        nx = x + dx
        ny = y

        if is_walkable(env, nx, ny):
            neighbors.append((nx, ny))

        # Step up 1 tile
        elif is_step_up_tile(env, nx, ny - 1):
            neighbors.append((nx, ny - 1))

        # Drop down 1–2 tiles
        for drop in [1, 2]:
            if 0 <= ny + drop < env.grid_height and is_walkable(env, nx, ny + drop):
                neighbors.append((nx, ny + drop))
                break  # only take the shallowest fall

    return neighbors

def find_random_air_target(env, max_attempts=100):
    for _ in range(max_attempts):
        x = np.random.randint(0, env.grid_width)
        for y in range(env.grid_height):
            if is_walkable(env, x, y):
                return (x, y)
    return None

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(env, start, goal):
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, cost, current = heapq.heappop(open_set)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]

        for neighbor in get_neighbors(env, current[0], current[1]):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, tentative_g, neighbor))
                came_from[neighbor] = current

    return None  # No path found
