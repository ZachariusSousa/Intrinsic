import pygame

from . import world, blocks, env_utils
from .constants import HOTBAR_ITEM_TO_BLOCK


def render(env):
    """Draw the current game state using pygame."""
    if env.screen is None:
        pygame.init()
        env.screen = pygame.display.set_mode((env.screen_width, env.screen_height))
        env.clock = pygame.time.Clock()
        env.font = pygame.font.SysFont(None, 24)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            env.close()
            return
    env_utils.handle_ui_events(env, events)
    env.screen.fill(env.weather.get_sky_color())
    light = env.weather.get_light_intensity()
    for rect, block in env.blocks:
        screen_rect = rect.move(-env.camera_x, -env.camera_y)
        if screen_rect.bottom < 0 or screen_rect.top > env.screen_height:
            continue
        color = world.COLOR_MAP.get(block, (255, 255, 255))
        color = tuple(int(c * light) for c in color)
        pygame.draw.rect(env.screen, color, screen_rect)
    for rect in env.water_blocks:
        screen_rect = rect.move(-env.camera_x, -env.camera_y)
        if screen_rect.bottom < 0 or screen_rect.top > env.screen_height:
            continue
        water_color = tuple(int(c * light) for c in world.COLOR_MAP[world.WATER])
        pygame.draw.rect(env.screen, water_color, screen_rect)

    if env._mining_target is not None and env._mining_progress > 0:
        tx, ty = env._mining_target
        block = env.grid[ty, tx]
        info = blocks.BLOCK_STATS.get(block)
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
    player_color = tuple(int(c * light) for c in (255, 0, 0))
    pygame.draw.rect(env.screen, player_color, env.player.rect.move(-env.camera_x, -env.camera_y))

    for enemy in env.enemies:
        screen_rect = enemy.rect.move(-env.camera_x, -env.camera_y)
        color = tuple(int(c * light) for c in enemy.color)
        pygame.draw.rect(env.screen, color, screen_rect)

    for mob in env.passive_mobs:
        screen_rect = mob.rect.move(-env.camera_x, -env.camera_y)
        color = tuple(int(c * light) for c in mob.color)
        pygame.draw.rect(env.screen, color, screen_rect)

    for proj in env.projectiles:
        screen_rect = proj.rect.move(-env.camera_x, -env.camera_y)
        proj_color = tuple(int(c * light) for c in (0, 0, 0))
        pygame.draw.rect(env.screen, proj_color, screen_rect)

    fx = env.player.rect.centerx + env.facing[0] * env.tile_size // 2
    fy = env.player.rect.centery + env.facing[1] * env.tile_size // 2
    pygame.draw.rect(
        env.screen,
        tuple(int(c * light) for c in (255, 255, 0)),
        pygame.Rect(fx - 4 - env.camera_x, fy - env.camera_y - 4, 8, 8),
    )

    if env.font:
        inv_text = " | ".join(f"{k}: {v}" for k, v in env.player.inventory.items())
        text_surf = env.font.render(inv_text, True, (0, 0, 0))
        env.screen.blit(text_surf, (10, 10))
        health_ratio = env.player.health / env.player.max_health
        pygame.draw.rect(env.screen, (255, 0, 0), pygame.Rect(10, 30, 100 * health_ratio, 10))
        pygame.draw.rect(env.screen, (0, 0, 0), pygame.Rect(10, 30, 100, 10), 2)
        food_ratio = env.player.food / env.player.max_food
        pygame.draw.rect(env.screen, (0, 128, 0), pygame.Rect(10, 45, 100 * food_ratio, 10))
        pygame.draw.rect(env.screen, (0, 0, 0), pygame.Rect(10, 45, 100, 10), 2)
        oxygen_ratio = env.player.oxygen / env.player.max_oxygen
        pygame.draw.rect(env.screen, (0, 0, 255), pygame.Rect(10, 60, 100 * oxygen_ratio, 10))
        pygame.draw.rect(env.screen, (0, 0, 0), pygame.Rect(10, 60, 100, 10), 2)

        hotbar_y = env.screen_height - env.tile_size - 10
        new_hotbar = []
        for i, item in enumerate(env.player.inventory.hotbar):
            x = 10 + i * (env.tile_size + 4)
            rect = pygame.Rect(x, hotbar_y, env.tile_size, env.tile_size)
            pygame.draw.rect(env.screen, (200, 200, 200), rect, 0)
            border = 3 if i == env.player.inventory.selected_slot else 1
            pygame.draw.rect(
                env.screen,
                (255, 255, 0) if i == env.player.inventory.selected_slot else (0, 0, 0),
                rect,
                border,
            )
            if item:
                label = env.font.render(item[0].upper(), True, (0, 0, 0))
                env.screen.blit(label, (x + 4, hotbar_y + 2))
                count = env.player.inventory.get(item, 0)
                count_surf = env.font.render(str(count), True, (0, 0, 0))
                env.screen.blit(count_surf, (x + 2, hotbar_y + env.tile_size - 12))
            new_hotbar.append(rect)
        env._hotbar_rects = new_hotbar

        if env.show_inventory:
            items = list(env.player.inventory.items())
            cols = 5
            size = env.tile_size
            rows = (len(items) + cols - 1) // cols
            width = cols * (size + 4) + 20
            height = rows * (size + 20) + 20
            surf = pygame.Surface((width, height))
            surf.fill((220, 220, 220))
            new_rects = []
            for idx, (name, count) in enumerate(items):
                cx = idx % cols
                cy = idx // cols
                x = 10 + cx * (size + 4)
                y = 10 + cy * (size + 20)
                rect = pygame.Rect(x, y, size, size)
                color = world.COLOR_MAP.get(HOTBAR_ITEM_TO_BLOCK.get(name, 0), (180, 180, 180))
                pygame.draw.rect(surf, color, rect)
                label = env.font.render(name[0].upper(), True, (0, 0, 0))
                surf.blit(label, (x + 3, y + 2))
                cnt = env.font.render(str(count), True, (0, 0, 0))
                surf.blit(cnt, (x + 2, y + size - 12))
                screen_rect = pygame.Rect((env.screen_width - width) // 2 + x, (env.screen_height - height) // 2 + y, size, size)
                new_rects.append((name, screen_rect))
            pos = (
                (env.screen_width - width) // 2,
                (env.screen_height - height) // 2,
            )
            env.screen.blit(surf, pos)
            env._inventory_item_rects = new_rects
        else:
            env._inventory_item_rects = []

    pygame.display.flip()
    env.clock.tick(60)

