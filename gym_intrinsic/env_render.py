import pygame
from . import world
from .inventory_ui import InventoryUI
from . import items


def render_environment(env):
    if env.screen is None:
        pygame.init()
        env.screen = pygame.display.set_mode((env.screen_width, env.screen_height))
        env.clock = pygame.time.Clock()
        env.font = pygame.font.SysFont(None, 24)
        if env.inventory_ui is None:
            env.inventory_ui = InventoryUI(env.player, env.font)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            env.close()
            return

    env.screen.fill(env.weather.get_sky_color())
    light = env.weather.get_light_intensity()

    draw_blocks(env, light)
    draw_water(env, light)
    draw_mining_indicator(env)
    draw_entities(env, light)
    draw_facing_indicator(env, light)
    draw_ui(env)
    pygame.display.flip()
    env.clock.tick(60)


def draw_blocks(env, light):
    for rect, block in env.blocks:
        screen_rect = rect.move(-env.camera_x, -env.camera_y)
        if screen_rect.bottom < 0 or screen_rect.top > env.screen_height:
            continue
        color = world.COLOR_MAP.get(block, (255, 255, 255))
        color = tuple(int(c * light) for c in color)
        pygame.draw.rect(env.screen, color, screen_rect)


def draw_water(env, light):
    for rect in env.water_blocks:
        screen_rect = rect.move(-env.camera_x, -env.camera_y)
        if screen_rect.bottom < 0 or screen_rect.top > env.screen_height:
            continue
        water_color = tuple(int(c * light) for c in world.COLOR_MAP[world.WATER])
        pygame.draw.rect(env.screen, water_color, screen_rect)


def draw_mining_indicator(env):
    if env._mining_target is not None and env._mining_progress > 0:
        tx, ty = env._mining_target
        block = env.grid[ty, tx]
        info = items.BLOCK_STATS.get(block)
        required = info.mining_time if info else 1
        ratio = min(1.0, env._mining_progress / required)
        size = int(env.tile_size * ratio)
        if size > 0:
            offset = (env.tile_size - size) // 2
            sx = tx * env.tile_size - env.camera_x + offset
            sy = ty * env.tile_size - env.camera_y + offset
            overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 120))
            env.screen.blit(overlay, (sx, sy))


def draw_entities(env, light):
    player_color = tuple(int(c * light) for c in (255, 0, 0))
    pygame.draw.rect(env.screen, player_color, env.player.rect.move(-env.camera_x, -env.camera_y))

    for entity in env.enemies + env.passive_mobs:
        screen_rect = entity.rect.move(-env.camera_x, -env.camera_y)
        color = tuple(int(c * light) for c in entity.color)
        pygame.draw.rect(env.screen, color, screen_rect)

    for proj in env.projectiles:
        screen_rect = proj.rect.move(-env.camera_x, -env.camera_y)
        proj_color = tuple(int(c * light) for c in (0, 0, 0))
        pygame.draw.rect(env.screen, proj_color, screen_rect)


def draw_facing_indicator(env, light):
    fx = env.player.rect.centerx + env.player.facing[0] * env.tile_size // 2
    fy = env.player.rect.centery + env.player.facing[1] * env.tile_size // 2
    pygame.draw.rect(
        env.screen,
        tuple(int(c * light) for c in (255, 255, 0)),
        pygame.Rect(fx - 4 - env.camera_x, fy - env.camera_y - 4, 8, 8),
    )


def draw_ui(env):
    if not env.font or not env.inventory_ui:
        return

    env.inventory_ui.draw(env.screen)

    def draw_bar(value, max_value, color, y):
        ratio = value / max_value
        pygame.draw.rect(env.screen, color, pygame.Rect(10, y, 100 * ratio, 10))
        pygame.draw.rect(env.screen, (0, 0, 0), pygame.Rect(10, y, 100, 10), 2)

    draw_bar(env.player.health, env.player.max_health, (255, 0, 0), 30)
    draw_bar(env.player.food, env.player.max_food, (0, 128, 0), 45)
    draw_bar(env.player.oxygen, env.player.max_oxygen, (0, 0, 255), 60)
