import pygame
from . import player_actions, world
from .enemy_mobs import update_enemies, update_projectiles
from .passive_mobs import update_passive_mobs
from .items import Block, ORE_TYPES


def handle_input_single(env, actor, action):
    left, right, jump, *_ = action

    if (left or right or jump) and actor.food > 0:
        actor.consume_food()
    if actor.food <= 0:
        actor.health -= 0.1

    if left and not right:
        actor.velocity[0] = -env.speed
    elif right and not left:
        actor.velocity[0] = env.speed
    else:
        actor.velocity[0] = 0

    if actor is env.player:  # only update facing if it's the player
        keys = pygame.key.get_pressed()
        actor.adjust_facing_from_keys(keys)

    if jump and (env._on_ground() or env.in_water):
        actor.velocity[1] = env.jump_velocity if not env.in_water else -5

def handle_input(env, action):
    handle_input_single(env, env.player, action)

def handle_physics(env):
    # checks if the player is in water
    in_water = any(env.player.rect.colliderect(r) for r in env.water_blocks)
    env.in_water = in_water

    # uses reduced gravity if in water, otherwise uses normal gravity
    gravity = 0.2 if in_water else env.gravity

    env.player.apply_gravity(gravity)
    env.player.move_and_collide(env.blocks)

    # clamps the player's position within the world except upwards
    world_w = env.grid_width * env.tile_size
    world_h = env.grid_height * env.tile_size
    env.player.rect.x = max(0, min(env.player.rect.x, world_w - env.player.rect.width))
    env.player.rect.y = min(env.player.rect.y, world_h - env.player.rect.height)

    # decreases players oxygen if in water
    env.player.handle_oxygen(in_water)


def update_camera(env):
    # Fallback to default screen size if screen is not initialized yet
    if env.screen:
        screen_w = env.screen.get_width()
        screen_h = env.screen.get_height()
    else:
        screen_w = 1280
        screen_h = 960


    env.camera_x = env.player.rect.centerx - screen_w // 2
    env.camera_y = env.player.rect.centery - screen_h // 2

    # Clamp to world bounds
    max_x = env.grid_width * env.tile_size - screen_w
    max_y = env.grid_height * env.tile_size - screen_h
    env.camera_x = max(0, min(env.camera_x, max_x))
    env.camera_y = max(0, min(env.camera_y, max_y))


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
