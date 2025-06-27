import pygame
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
from . import env_utils

@dataclass
class PassiveMob:
    rect: pygame.Rect
    type: str
    health: int
    color: tuple
    food_drop: int
    direction: int = 0
    move_timer: int = 0

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
        ey = env_utils.find_spawn_y(env, ex)
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
    world_w = env.grid_width * env.tile_size
    for mob in mobs:
        if mob.move_timer <= 0:
            mob.direction = int(np.random.choice([-1, 0, 1]))
            mob.move_timer = int(np.random.randint(30, 90))
        mob.move_timer -= 1
        mob.rect.x += mob.direction
        mob.rect.x = max(0, min(mob.rect.x, world_w - env.tile_size))
        tile_x = mob.rect.centerx // env.tile_size
        ground_y = env_utils.find_spawn_y(env, tile_x)
        mob.rect.bottom = ground_y + env.tile_size
