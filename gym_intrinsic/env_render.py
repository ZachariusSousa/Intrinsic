import pygame
from . import world
from .inventory_ui import InventoryUI
from . import items
from .items import Block, ORE_TYPES
from .env_logic import update_camera



def render_environment(env):
    if env.screen is None:
        pygame.init()
        env.screen = pygame.display.set_mode((1280, 960), pygame.RESIZABLE)
        env.clock = pygame.time.Clock()
        env.font = pygame.font.SysFont(None, 24)
        if env.inventory_ui is None:
            env.inventory_ui = InventoryUI(env.player, env.font)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            env.close()
            return
        elif event.type == pygame.VIDEORESIZE:
            env.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            if env.inventory_ui:
                env.inventory_ui.reposition(env.screen.get_width(), env.screen.get_height())
        update_camera(env)
            

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
        if screen_rect.bottom < 0 or screen_rect.top > env.screen.get_height():
            continue
        color = items.COLOR_MAP.get(block, (255, 255, 255))
        color = tuple(int(c * light) for c in color)
        pygame.draw.rect(env.screen, color, screen_rect)


def draw_water(env, light):
    for rect in env.water_blocks:
        screen_rect = rect.move(-env.camera_x, -env.camera_y)
        if screen_rect.bottom < 0 or screen_rect.top > env.screen.get_height():
            continue
        water_color = tuple(int(c * light) for c in items.COLOR_MAP[Block.WATER])
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
    # Lazy-load player sprites
    if not hasattr(env, "player_sprites"):
        import os
        TEXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "textures")
        env.player_sprites = {
            dir: pygame.image.load(os.path.join(TEXTURE_PATH, f"player_{dir}.png")).convert_alpha()
            for dir in ["up", "down", "left", "right"]
        }

    direction = (
    "right" if env.player.facing == [1, 0]
    else "left" if env.player.facing == [-1, 0]
    else "up" if env.player.facing == [0, -1]
    else "down"
    )
    
    for ai in env.ai_players:
        screen_rect = ai.rect.move(-env.camera_x, -env.camera_y)
        pygame.draw.rect(env.screen, (0, 255, 0), screen_rect, 2)

    sprite = env.player_sprites[direction]

    # Get bounding box of visible pixels
    bbox = sprite.get_bounding_rect()  # only non-transparent region
    cropped = sprite.subsurface(bbox)

    # Scale up so cropped area becomes tile_size
    scale_factor = env.tile_size / max(bbox.width, bbox.height)
    new_size = (int(cropped.get_width() * scale_factor), int(cropped.get_height() * scale_factor))
    scaled_sprite = pygame.transform.scale(cropped, new_size)

    # Compute position so it sits on the ground and is horizontally centered
    screen_x = env.player.rect.centerx - new_size[0] // 2 - env.camera_x
    screen_y = env.player.rect.bottom - new_size[1] - env.camera_y
    env.screen.blit(scaled_sprite, (screen_x, screen_y))


    
    # Draw mobs
    for entity in env.enemies + env.passive_mobs:
        screen_rect = entity.rect.move(-env.camera_x, -env.camera_y)
        color = tuple(int(c * light) for c in entity.color)
        pygame.draw.rect(env.screen, color, screen_rect)

    # Draw projectiles
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

    def draw_bar(value, max_value, color, y_frac):
        screen_w = env.screen.get_width()
        screen_h = env.screen.get_height()

        scale = min(screen_w / 1280, screen_h / 960)
        bar_width = int(300 * scale)
        bar_height = int(20 * scale)
        y = int(screen_h * y_frac)

        ratio = value / max_value
        filled_width = int(bar_width * ratio)

        pygame.draw.rect(env.screen, color, pygame.Rect(10, y, filled_width, bar_height))
        pygame.draw.rect(env.screen, (0, 0, 0), pygame.Rect(10, y, bar_width, bar_height), 2)

    draw_bar(env.player.health, env.player.max_health, (255, 0, 0), 0.03)
    draw_bar(env.player.food, env.player.max_food, (0, 128, 0), 0.06)
    draw_bar(env.player.oxygen, env.player.max_oxygen, (0, 0, 255), 0.09)

    # Draw FPS counter
    screen_w = env.screen.get_width()
    screen_h = env.screen.get_height()
    scale = min(screen_w / 1280, screen_h / 960)

    font_size = max(20, int(30 * scale))
    font = pygame.font.SysFont(None, font_size)

    fps = int(env.clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))

    # Place below the last bar (adjust spacing based on scaled height)
    fps_x = 10
    fps_y = int(screen_h * 0.12)

    env.screen.blit(fps_text, (fps_x, fps_y))

