
import pygame
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from .player import Player
from . import pathfinding


@dataclass
class Enemy:
    rect: pygame.Rect
    health: int
    color: Tuple[int, int, int]
    speed: int
    path: Optional[List[Tuple[int, int]]] = None
    path_index: int = 0
    vel_y: float = 0.0
    last_path_time: int = 0
    last_player_tile: Optional[Tuple[int, int]] = None

    def is_melee(self) -> bool:
        return False

    def is_ranged(self) -> bool:
        return False


@dataclass
class MeleeEnemy(Enemy):
    def __post_init__(self):
        self.color = (200, 0, 0)
        self.health = 30
        self.speed = 2

    def is_melee(self) -> bool:
        return True


@dataclass
class RangedEnemy(Enemy):
    cooldown: int = 0

    def __post_init__(self):
        self.color = (0, 0, 200)
        self.health = 20
        self.speed = 1

    def is_ranged(self) -> bool:
        return True


@dataclass
class Projectile:
    rect: pygame.Rect
    vel: Tuple[int, int]


def spawn_random_enemies(num: int, env) -> List[Enemy]:
    enemies: List[Enemy] = []
    for _ in range(num):
        etype = np.random.choice(["melee", "ranged"])
        ex = np.random.randint(0, env.grid_width)
        ey = env._find_spawn_y(ex)
        rect = pygame.Rect(ex * env.tile_size, ey, env.tile_size, env.tile_size)
        if etype == "melee":
            enemies.append(MeleeEnemy(rect=rect, health=0, color=(0, 0, 0), speed=0))  # values set in __post_init__
        else:
            enemies.append(RangedEnemy(rect=rect, health=0, color=(0, 0, 0), speed=0))
    return enemies



def update_enemies(enemies: List[Enemy], player: Player, projectiles: List[Projectile], env):
    tile_size = env.tile_size
    gravity = 0.8
    max_fall_speed = 10

    def is_solid(x, y):
        return 0 <= x < env.grid_width and 0 <= y < env.grid_height and env.grid[y, x] not in (0, 8)

    current_time = pygame.time.get_ticks()
    player_tile = (player.rect.centerx // tile_size, player.rect.bottom // tile_size)

    for enemy in enemies:
        enemy_tile = (enemy.rect.centerx // tile_size, enemy.rect.bottom // tile_size)

        should_repath = (
            enemy.path is None or
            enemy.path_index >= len(enemy.path) or
            current_time - enemy.last_path_time > 1500 or
            enemy.last_player_tile != player_tile
        )

        if should_repath:
            path = pathfinding.astar(env, enemy_tile, player_tile)
            if path:
                enemy.path = path
                enemy.path_index = 0
                enemy.last_path_time = current_time
                enemy.last_player_tile = player_tile

        if enemy.path and enemy.path_index < len(enemy.path):
            target = enemy.path[enemy.path_index]
            target_px = target[0] * tile_size + tile_size // 2
            target_py = target[1] * tile_size

            if abs(enemy.rect.centerx - target_px) <= enemy.speed:
                enemy.path_index += 1
            elif enemy.rect.centerx < target_px:
                enemy.rect.x += enemy.speed
            else:
                enemy.rect.x -= enemy.speed

            # Check grounded
            grounded = False
            left = enemy.rect.left // tile_size
            right = (enemy.rect.right - 1) // tile_size
            bottom = enemy.rect.bottom // tile_size
            for tx in range(left, right + 1):
                if is_solid(tx, bottom):
                    grounded = True
                    break

            # Jump if needed
            if (
                target_py + tile_size < enemy.rect.bottom and
                abs(enemy.rect.centerx - target_px) <= tile_size and
                grounded and abs(enemy.vel_y) < 1e-3
            ):
                enemy.vel_y = -6

        # Gravity
        enemy.vel_y = min(enemy.vel_y + gravity, max_fall_speed)
        enemy.rect.y += int(enemy.vel_y)

        # Vertical collisions
        left = enemy.rect.left // tile_size
        right = (enemy.rect.right - 1) // tile_size
        top = enemy.rect.top // tile_size
        bottom = (enemy.rect.bottom - 1) // tile_size

        if enemy.vel_y > 0:
            for tx in range(left, right + 1):
                if is_solid(tx, bottom):
                    enemy.rect.bottom = bottom * tile_size
                    enemy.vel_y = 0
                    break
        elif enemy.vel_y < 0:
            for tx in range(left, right + 1):
                if is_solid(tx, top):
                    enemy.rect.top = (top + 1) * tile_size
                    enemy.vel_y = 0
                    break

        # Attacks
        if enemy.is_melee() and enemy.rect.colliderect(player.rect):
            player.health -= 1

        elif enemy.is_ranged():
            if enemy.cooldown > 0:
                enemy.cooldown -= 1
            dx = player.rect.centerx - enemy.rect.centerx
            dy = player.rect.centery - enemy.rect.centery
            if abs(dx) < 300 and abs(dy) < 100 and enemy.cooldown == 0:
                vx = 5 if dx > 0 else -5
                vy = int(dy / max(abs(dx), 1) * abs(vx))
                proj = Projectile(
                    rect=pygame.Rect(enemy.rect.centerx, enemy.rect.centery, 8, 8),
                    vel=(vx, vy)
                )
                projectiles.append(proj)
                enemy.cooldown = 90


def update_projectiles(projectiles: List[Projectile], player: Player, world_w: int, env):
    tile_size = env.tile_size

    def is_solid(x, y):
        return 0 <= x < env.grid_width and 0 <= y < env.grid_height and env.grid[y, x] not in (0, 8)

    for proj in list(projectiles):
        proj.rect.x += proj.vel[0]
        proj.rect.y += proj.vel[1]

        if proj.rect.right < 0 or proj.rect.left > world_w:
            projectiles.remove(proj)
            continue

        tile_x = proj.rect.centerx // tile_size
        tile_y = proj.rect.centery // tile_size
        if is_solid(tile_x, tile_y):
            projectiles.remove(proj)
            continue

        if proj.rect.colliderect(player.rect):
            player.health -= 5
            projectiles.remove(proj)
