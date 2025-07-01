"""Inventory UI logic for IntrinsicEnv."""

from __future__ import annotations

import pygame
from typing import List, Tuple

from . import world

# map hotbar item names to world block IDs
HOTBAR_ITEM_TO_BLOCK = {
    "dirt": world.DIRT,
    "stone": world.STONE,
    "copper": world.COPPER_ORE,
    "iron": world.IRON_ORE,
    "gold": world.GOLD_ORE,
    "wood": world.WOOD,
}

# type alias for item name and rect pair
ItemRect = Tuple[str, pygame.Rect]


def init_state(env: "IntrinsicEnv") -> None:
    """Initialize inventory UI state on the environment."""
    env._inventory_item_rects: List[ItemRect] = []
    env._hotbar_rects: List[pygame.Rect] = []
    env._last_hotbar_click: List[int] = [0] * 10


def shift_to_hotbar(env: "IntrinsicEnv", item: str) -> None:
    """Move one item to the first empty hotbar slot."""
    if env.player.inventory.get(item, 0) <= 0:
        return
    for i, slot in enumerate(env.player.hotbar):
        if slot is None:
            env.player.hotbar[i] = item
            return


def handle_events(env: "IntrinsicEnv", events) -> None:
    """Handle mouse events related to the inventory UI."""
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and env.show_inventory:
            pos = event.pos
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                for name, rect in env._inventory_item_rects:
                    if rect.collidepoint(pos):
                        shift_to_hotbar(env, name)
                        break
            else:
                now = pygame.time.get_ticks()
                for idx, rect in enumerate(env._hotbar_rects):
                    if rect.collidepoint(pos):
                        if now - env._last_hotbar_click[idx] < 400:
                            item = env.player.hotbar[idx]
                            if item:
                                env.player.inventory[item] = env.player.inventory.get(item, 0)
                                env.player.hotbar[idx] = None
                        env._last_hotbar_click[idx] = now


def draw(env: "IntrinsicEnv") -> None:
    """Render the inventory and hotbar to ``env.screen``."""
    screen = env.screen
    font = env.font
    size = env.tile_size

    # render hotbar
    hotbar_y = env.screen_height - size - 10
    new_hotbar: List[pygame.Rect] = []
    for i, item in enumerate(env.player.hotbar):
        x = 10 + i * (size + 4)
        rect = pygame.Rect(x, hotbar_y, size, size)
        pygame.draw.rect(screen, (200, 200, 200), rect, 0)
        border = 3 if i == env.player.selected_slot else 1
        pygame.draw.rect(
            screen,
            (255, 255, 0) if i == env.player.selected_slot else (0, 0, 0),
            rect,
            border,
        )
        if item:
            color = world.COLOR_MAP.get(HOTBAR_ITEM_TO_BLOCK.get(item, 0), (180, 180, 180))
            inner = rect.inflate(-4, -4)
            pygame.draw.rect(screen, color, inner)
            count = env.player.inventory.get(item, 0)
            count_surf = font.render(str(count), True, (0, 0, 0))
            screen.blit(count_surf, (x + 2, hotbar_y + size - 12))
        new_hotbar.append(rect)
    env._hotbar_rects = new_hotbar

    # inventory window
    if env.show_inventory:
        items = list(env.player.inventory.items())
        cols = 5
        rows = (len(items) + cols - 1) // cols
        width = cols * (size + 4) + 20
        height = rows * (size + 20) + 20
        surf = pygame.Surface((width, height))
        surf.fill((220, 220, 220))
        new_rects: List[ItemRect] = []
        for idx, (name, count) in enumerate(items):
            cx = idx % cols
            cy = idx // cols
            x = 10 + cx * (size + 4)
            y = 10 + cy * (size + 20)
            rect = pygame.Rect(x, y, size, size)
            color = world.COLOR_MAP.get(HOTBAR_ITEM_TO_BLOCK.get(name, 0), (180, 180, 180))
            pygame.draw.rect(surf, color, rect)
            label = font.render(name[0].upper(), True, (0, 0, 0))
            surf.blit(label, (x + 3, y + 2))
            cnt = font.render(str(count), True, (0, 0, 0))
            surf.blit(cnt, (x + 2, y + size - 12))
            screen_rect = pygame.Rect(
                (env.screen_width - width) // 2 + x,
                (env.screen_height - height) // 2 + y,
                size,
                size,
            )
            new_rects.append((name, screen_rect))
        pos = (
            (env.screen_width - width) // 2,
            (env.screen_height - height) // 2,
        )
        screen.blit(surf, pos)
        env._inventory_item_rects = new_rects
    else:
        env._inventory_item_rects = []

