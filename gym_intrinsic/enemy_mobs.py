import pygame
import numpy as np
from dataclasses import dataclass
from typing import List
from .player import Player
from . import env_utils

@dataclass
class Enemy:
    rect: pygame.Rect
    type: str
    health: int
    color: tuple
    cooldown: int = 0

@dataclass
class Projectile:
    rect: pygame.Rect
    vel: int


def spawn_random_enemies(num: int, env) -> List[Enemy]:
    """Helper used by IntrinsicEnv.reset to populate enemies."""
    enemies: List[Enemy] = []
    for _ in range(num):
        etype = np.random.choice(["melee", "ranged"])
        ex = np.random.randint(0, env.grid_width)
        ey = env_utils.find_spawn_y(env, ex)
        rect = pygame.Rect(ex * env.tile_size, ey, env.tile_size, env.tile_size)
        health = 30 if etype == "melee" else 20
        color = (200, 0, 0) if etype == "melee" else (0, 0, 200)
        enemies.append(Enemy(rect=rect, type=etype, health=health, color=color))
    return enemies


def update_enemies(enemies: List[Enemy], player: Player, projectiles: List[Projectile]):
    """Update enemy movement and attacks."""
    for enemy in list(enemies):
        if enemy.type == "melee":
            speed = 2
            if enemy.rect.centerx < player.rect.centerx:
                enemy.rect.x += speed
                if enemy.rect.colliderect(player.rect):
                    enemy.rect.right = player.rect.left
                    player.health -= 1
            elif enemy.rect.centerx > player.rect.centerx:
                enemy.rect.x -= speed
                if enemy.rect.colliderect(player.rect):
                    enemy.rect.left = player.rect.right
                    player.health -= 1
            else:
                if enemy.rect.colliderect(player.rect):
                    player.health -= 1
        else:
            if enemy.cooldown > 0:
                enemy.cooldown -= 1
            if abs(enemy.rect.centerx - player.rect.centerx) < 200 and enemy.cooldown == 0:
                direction = 1 if player.rect.centerx > enemy.rect.centerx else -1
                proj = Projectile(pygame.Rect(enemy.rect.centerx, enemy.rect.centery, 8, 8), 5 * direction)
                projectiles.append(proj)
                enemy.cooldown = 60


def update_projectiles(projectiles: List[Projectile], player: Player, world_w: int):
    """Update projectile positions and handle collisions."""
    for proj in list(projectiles):
        proj.rect.x += proj.vel
        if proj.rect.colliderect(player.rect):
            player.health -= 5
            projectiles.remove(proj)
            continue
        if proj.rect.right < 0 or proj.rect.left > world_w:
            projectiles.remove(proj)
