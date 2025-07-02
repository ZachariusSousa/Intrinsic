import pygame
import numpy as np
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PassiveMob:
    rect: pygame.Rect
    type: str
    health: int
    color: tuple
    food_drop: int
    direction: int = 0
    move_timer: int = 0
    vel_y: float = 0.0  # for gravity


PASSIVE_TYPES: Dict[str, Dict] = {
    "bunny": {"color": (255, 200, 200), "health": 10, "food": 1},
    "chicken": {"color": (255, 255, 0), "health": 15, "food": 2},
}


def spawn_random_passive_mobs(num: int, env) -> List[PassiveMob]:
    mobs: List[PassiveMob] = []
    types = list(PASSIVE_TYPES.keys())
    for _ in range(num):
        mtype = np.random.choice(types)
        ex = np.random.randint(0, env.grid_width)
        ey = env._find_spawn_y(ex)
        info = PASSIVE_TYPES[mtype]
        rect = pygame.Rect(ex * env.tile_size, ey, env.tile_size, env.tile_size)
        mobs.append(
            PassiveMob(
                rect=rect,
                type=mtype,
                health=info["health"],
                color=info["color"],
                food_drop=info["food"],
            )
        )
    return mobs


def update_passive_mobs(mobs: List[PassiveMob], env) -> None:
    gravity = 0.8
    max_fall_speed = 10
    tile_size = env.tile_size
    world_w = env.grid_width * tile_size
    world_h = env.grid_height * tile_size

    def is_solid(x: int, y: int) -> bool:
        if 0 <= x < env.grid_width and 0 <= y < env.grid_height:
            block = env.grid[y, x]
            return block not in (0, 8)  # not EMPTY or WATER
        return False

    for mob in mobs:
        # Horizontal movement
        if mob.move_timer <= 0:
            mob.direction = int(np.random.choice([-1, 0, 1]))
            mob.move_timer = int(np.random.randint(30, 90))
        mob.move_timer -= 1
        mob.rect.x += mob.direction

        # Clamp X
        mob.rect.x = max(0, min(mob.rect.x, world_w - tile_size))

        # Collision check X
        tile_left = mob.rect.left // tile_size
        tile_right = (mob.rect.right - 1) // tile_size
        tile_top = mob.rect.top // tile_size
        tile_bottom = (mob.rect.bottom - 1) // tile_size

        for ty in range(tile_top, tile_bottom + 1):
            if mob.direction > 0 and is_solid(tile_right, ty):
                mob.rect.right = tile_right * tile_size
                break
            elif mob.direction < 0 and is_solid(tile_left, ty):
                mob.rect.left = (tile_left + 1) * tile_size
                break

        # Apply gravity
        mob.vel_y = min(mob.vel_y + gravity, max_fall_speed)
        mob.rect.y += int(mob.vel_y)

        # Clamp Y
        mob.rect.y = max(0, min(mob.rect.y, world_h - tile_size))

        # Collision check Y
        tile_left = mob.rect.left // tile_size
        tile_right = (mob.rect.right - 1) // tile_size
        tile_top = mob.rect.top // tile_size
        tile_bottom = (mob.rect.bottom - 1) // tile_size

        if mob.vel_y > 0:  # falling
            for tx in range(tile_left, tile_right + 1):
                if is_solid(tx, tile_bottom):
                    mob.rect.bottom = tile_bottom * tile_size
                    mob.vel_y = 0
                    break
        elif mob.vel_y < 0:  # jumping or upward motion
            for tx in range(tile_left, tile_right + 1):
                if is_solid(tx, tile_top):
                    mob.rect.top = (tile_top + 1) * tile_size
                    mob.vel_y = 0
                    break
