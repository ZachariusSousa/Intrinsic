import pygame
import numpy as np

from . import world, blocks, env_utils
from .constants import HOTBAR_ITEM_TO_BLOCK
from .enemy_mobs import update_enemies, update_projectiles
from .passive_mobs import update_passive_mobs


def step(env, action):
    """Logic for a single environment step."""
    # advance the day/night and season cycle
    env.weather.step()

    left, right, jump, place, destroy = action

    keys = pygame.key.get_pressed()

    # toggle inventory view with 'e'
    if keys[pygame.K_e] and not env._prev_e:
        env.show_inventory = not env.show_inventory
    env._prev_e = keys[pygame.K_e]

    # hotbar selection with number keys 1-0
    number_keys = [
        pygame.K_1,
        pygame.K_2,
        pygame.K_3,
        pygame.K_4,
        pygame.K_5,
        pygame.K_6,
        pygame.K_7,
        pygame.K_8,
        pygame.K_9,
        pygame.K_0,
    ]
    for idx, k in enumerate(number_keys):
        if keys[k]:
            env.player.inventory.selected_slot = idx

    env.in_water = any(env.player.rect.colliderect(r) for r in env.water_blocks)

    if (left or right or jump) and env.player.food > 0:
        env.player.food = max(0, env.player.food - 0.05)
    if env.player.food <= 0:
        env.player.health -= 0.1

    # update movement
    if left and not right:
        env.player.velocity[0] = -env.speed
    elif right and not left:
        env.player.velocity[0] = env.speed
    else:
        env.player.velocity[0] = 0

    # update facing based on keys (arrow keys or WASD)
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        env.facing = [-1, 0]
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        env.facing = [1, 0]
    elif keys[pygame.K_UP] or keys[pygame.K_w]:
        env.facing = [0, -1]
    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        env.facing = [0, 1]

    # jump (allow swimming upwards)
    if jump and (env._on_ground() or env.in_water):
        env.player.velocity[1] = env.jump_velocity if not env.in_water else -5

    # apply gravity (reduced in water)
    gravity = 0.2 if env.in_water else env.gravity
    env.player.velocity[1] += gravity

    # update position and handle collisions with blocks
    env.player.rect.x += int(env.player.velocity[0])
    for rect, _ in env.blocks:
        if env.player.rect.colliderect(rect):
            if env.player.velocity[0] > 0:
                env.player.rect.right = rect.left
            elif env.player.velocity[0] < 0:
                env.player.rect.left = rect.right
            env.player.velocity[0] = 0

    env.player.rect.y += int(env.player.velocity[1])
    for rect, _ in env.blocks:
        if env.player.rect.colliderect(rect):
            if env.player.velocity[1] > 0:
                env.player.rect.bottom = rect.top
            elif env.player.velocity[1] < 0:
                env.player.rect.top = rect.bottom
            env.player.velocity[1] = 0

    # world boundaries
    world_w = env.grid_width * env.tile_size
    world_h = env.grid_height * env.tile_size
    env.player.rect.x = max(0, min(env.player.rect.x, world_w - env.player.rect.width))
    env.player.rect.y = max(0, min(env.player.rect.y, world_h - env.player.rect.height))

    # update water status after movement
    env.in_water = any(env.player.rect.colliderect(r) for r in env.water_blocks)
    if env.in_water:
        env.player.oxygen = max(0, env.player.oxygen - 1)
        if env.player.oxygen == 0:
            env.player.health -= 0.5
    else:
        env.player.oxygen = min(env.player.max_oxygen, env.player.oxygen + 2)

    # update camera to follow player
    env.camera_y = int(env.player.rect.centery - env.screen_height // 2)
    env.camera_y = max(0, min(env.camera_y, world_h - env.screen_height))

    # block placement and destruction
    px = env.player.rect.centerx // env.tile_size
    py = env.player.rect.centery // env.tile_size
    dx, dy = env.facing
    target_x = px + dx
    target_y = py + dy

    if 0 <= target_x < env.grid_width and 0 <= target_y < env.grid_height:
        selected = env.player.selected_item
        if (
            place
            and selected in HOTBAR_ITEM_TO_BLOCK
            and env.player.inventory.get(selected, 0) > 0
            and env.grid[target_y, target_x] == world.EMPTY
        ):
            env.grid[target_y, target_x] = HOTBAR_ITEM_TO_BLOCK[selected]
            env.player.inventory[selected] -= 1
            env_utils.update_blocks(env)

        if destroy:
            block = env.grid[target_y, target_x]
            target = (target_x, target_y)
            if block != world.EMPTY:
                if target != env._mining_target:
                    env._mining_target = target
                    env._mining_progress = 0
                info = blocks.BLOCK_STATS.get(block)
                required = info.mining_time if info else 1
                env._mining_progress += 1
                if env._mining_progress >= required:
                    env.grid[target_y, target_x] = world.EMPTY
                    if block == world.DIRT:
                        env.player.inventory["dirt"] += 1
                    elif block == world.STONE:
                        env.player.inventory["stone"] += 1
                    elif block == world.COPPER_ORE:
                        env.player.inventory["copper"] += 1
                    elif block == world.IRON_ORE:
                        env.player.inventory["iron"] += 1
                    elif block == world.GOLD_ORE:
                        env.player.inventory["gold"] += 1
                    elif block == world.WOOD:
                        env.player.inventory["wood"] += 1
                    env_utils.update_blocks(env)
                    env._mining_target = None
                    env._mining_progress = 0
            else:
                env._mining_target = None
                env._mining_progress = 0
                attack_rect = pygame.Rect(
                    target_x * env.tile_size,
                    target_y * env.tile_size,
                    env.tile_size,
                    env.tile_size,
                )
                for enemy in list(env.enemies):
                    if enemy.rect.colliderect(attack_rect):
                        enemy.health -= 10
                        if enemy.health <= 0:
                            env.enemies.remove(enemy)
                for mob in list(env.passive_mobs):
                    if mob.rect.colliderect(attack_rect):
                        mob.health -= 10
                        if mob.health <= 0:
                            env.player.inventory["food"] = env.player.inventory.get("food", 0) + mob.food_drop
                            env.passive_mobs.remove(mob)
        else:
            env._mining_target = None
            env._mining_progress = 0

    # extend world horizontally when approaching edges
    threshold = env.tile_size * 5
    if env.player.rect.right > env.grid_width * env.tile_size - threshold:
        env_utils.extend_world_right(env, env.grid_width // 2)
    if env.player.rect.left < threshold:
        env_utils.extend_world_left(env, env.grid_width // 2)

    # update camera to follow player horizontally
    world_w = env.grid_width * env.tile_size
    world_h = env.grid_height * env.tile_size
    env.camera_x = int(env.player.rect.centerx - env.screen_width // 2)
    env.camera_x = max(0, min(env.camera_x, world_w - env.screen_width))
    # occasionally spawn new mobs
    env_utils.spawn_mobs_randomly(env)
    # update mobs, enemies and projectiles
    update_passive_mobs(env.passive_mobs, env)
    update_enemies(env.enemies, env.player, env.projectiles)
    update_projectiles(env.projectiles, env.player, world_w)

    done = False
    if env.player.health <= 0:
        done = True
    reward = 0.0

    return env._get_obs(), reward, done, False, {}
