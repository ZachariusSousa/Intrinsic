import pygame
from . import player_actions, world
from .enemy_mobs import update_enemies, update_projectiles
from .passive_mobs import update_passive_mobs


def handle_input(env, action):
    left, right, jump, *_ = action
    keys = pygame.key.get_pressed()

    if (left or right or jump) and env.player.food > 0:
        env.player.consume_food()
    if env.player.food <= 0:
        env.player.health -= 0.1

    if left and not right:
        env.player.velocity[0] = -env.speed
    elif right and not left:
        env.player.velocity[0] = env.speed
    else:
        env.player.velocity[0] = 0

    env.player.adjust_facing_from_keys(keys)

    if jump and (env._on_ground() or env.in_water):
        env.player.velocity[1] = env.jump_velocity if not env.in_water else -5


def handle_physics(env):
    env.in_water = any(env.player.rect.colliderect(r) for r in env.water_blocks)
    gravity = 0.2 if env.in_water else env.gravity
    env.player.apply_gravity(gravity)
    env.player.move_and_collide(env.blocks)

    world_w = env.grid_width * env.tile_size
    world_h = env.grid_height * env.tile_size
    env.player.rect.x = max(0, min(env.player.rect.x, world_w - env.player.rect.width))
    env.player.rect.y = min(env.player.rect.y, world_h - env.player.rect.height)

    env.in_water = any(env.player.rect.colliderect(r) for r in env.water_blocks)
    env.player.handle_oxygen(env.in_water)


def handle_actions(env, action):
    _, _, _, use, destroy = action

    px = env.player.rect.centerx // env.tile_size
    py = env.player.rect.centery // env.tile_size
    dx, dy = env.player.facing
    target_x = px + dx
    target_y = py + dy

    if not (0 <= target_x < env.grid_width and 0 <= target_y < env.grid_height):
        return

    if use:
        dmg = player_actions.place_block(
            env.player, env.grid, target_x, target_y, env._update_blocks
        )
        if dmg:
            attack_rect = pygame.Rect(
                target_x * env.tile_size,
                target_y * env.tile_size,
                env.tile_size,
                env.tile_size,
            )
            player_actions.attack_entities(attack_rect, env.enemies, env.passive_mobs, env.player, dmg)

    if destroy:
        block = env.grid[target_y, target_x]
        target = (target_x, target_y)
        if block != world.EMPTY:
            if target != env._mining_target:
                env._mining_target = target
                env._mining_progress = 0
            env._mining_target, env._mining_progress = player_actions.mine_block(
                env.grid, target, env._mining_progress, env.player, env._update_blocks
            )
        else:
            env._mining_target = None
            env._mining_progress = 0
            attack_rect = pygame.Rect(
                target_x * env.tile_size,
                target_y * env.tile_size,
                env.tile_size,
                env.tile_size,
            )
            player_actions.attack_entities(attack_rect, env.enemies, env.passive_mobs, env.player, 10)
    else:
        env._mining_target = None
        env._mining_progress = 0


def update_camera(env):
    world_w = env.grid_width * env.tile_size
    world_h = env.grid_height * env.tile_size
    env.camera_y = min(int(env.player.rect.centery - env.screen_height // 2), world_h - env.screen_height)
    env.camera_x = max(0, min(int(env.player.rect.centerx - env.screen_width // 2), world_w - env.screen_width))


def maybe_extend_world(env):
    threshold = env.tile_size * 5
    if env.player.rect.right > env.grid_width * env.tile_size - threshold:
        env._extend_world_right(env.grid_width // 2)
    if env.player.rect.left < threshold:
        env._extend_world_left(env.grid_width // 2)


def spawn_and_update_mobs(env):
    env._spawn_mobs_randomly()
    update_passive_mobs(env.passive_mobs, env)
    update_enemies(env.enemies, env.player, env.projectiles, env)
    update_projectiles(env.projectiles, env.player, env.grid_width * env.tile_size, env)
