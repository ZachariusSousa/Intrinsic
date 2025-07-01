import numpy as np
import pygame

from . import world



def extend_world_right(env, extra_cols: int) -> None:
    """Extend the world grid to the right."""
    new_grid = world.generate_world(extra_cols, env.grid_height)
    env.grid = np.concatenate([env.grid, new_grid], axis=1)
    env.grid_width += extra_cols
    update_blocks(env)


def extend_world_left(env, extra_cols: int) -> None:
    """Extend the world grid to the left."""
    new_grid = world.generate_world(extra_cols, env.grid_height)
    env.grid = np.concatenate([new_grid, env.grid], axis=1)
    env.grid_width += extra_cols
    env.player.rect.x += extra_cols * env.tile_size
    for enemy in env.enemies:
        enemy.rect.x += extra_cols * env.tile_size
    for mob in env.passive_mobs:
        mob.rect.x += extra_cols * env.tile_size
    for proj in env.projectiles:
        proj.rect.x += extra_cols * env.tile_size
    update_blocks(env)


def update_blocks(env) -> None:
    """Recreate block rectangles from the grid."""
    env.blocks, env.water_blocks = world.blocks_from_grid(env.grid, env.tile_size)


def find_spawn_y(env, tile_x: int) -> int:
    """Return the surface y position for spawning an entity."""
    for y in range(env.grid_height):
        block = env.grid[y, tile_x]
        if block != world.EMPTY and block not in (world.WOOD, world.LEAVES):
            return max(0, (y - 1) * env.tile_size)
    return max(0, (env.grid_height - 2) * env.tile_size)


def spawn_mobs_randomly(env) -> None:
    from .enemy_mobs import spawn_random_enemies  # moved import here
    from .passive_mobs import spawn_random_passive_mobs  # moved import here

    """Occasionally add new mobs to the world."""
    if (
        len(env.enemies) < env.max_enemies
        and np.random.random() < env.enemy_spawn_chance
    ):
        env.enemies.extend(spawn_random_enemies(1, env))
    if (
        len(env.passive_mobs) < env.max_passive_mobs
        and np.random.random() < env.passive_spawn_chance
    ):
        env.passive_mobs.extend(spawn_random_passive_mobs(1, env))


def shift_to_hotbar(env, item: str) -> None:
    env.player.inventory.shift_to_hotbar(item)


def shift_from_hotbar(env, index: int) -> None:
    env.player.inventory.remove_from_hotbar(index)


def handle_ui_events(env, events) -> None:
    for event in events:
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            # handle inventory buttons when inventory is visible
            if env.show_inventory:
                for btn in env._inventory_buttons:
                    action = btn.handle_event(event)
                    if action == "shift":
                        shift_to_hotbar(env, btn.data["name"])
                    elif action == "click":
                        env._dragged_item = ("inventory", btn.data["name"])
                        env._drag_pos = event.pos
                    elif action == "drag":
                        env._drag_pos = event.pos
                    elif action == "drop":
                        env._dragged_item = None

            # hotbar buttons
            for btn in env._hotbar_buttons:
                action = btn.handle_event(event)
                index = btn.data["index"]
                item = env.player.inventory.hotbar[index]
                if action == "shift":
                    shift_from_hotbar(env, index)
                elif action == "click" and item:
                    env._dragged_item = ("hotbar", index)
                    env._drag_pos = event.pos
                elif action == "drag":
                    env._drag_pos = event.pos
                elif action == "drop":
                    if env._dragged_item is not None:
                        # handle drop onto another hotbar slot
                        if env._dragged_item[0] == "hotbar":
                            src = env._dragged_item[1]
                            if src != index:
                                env.player.inventory.swap_hotbar_slots(src, index)
                        elif env._dragged_item[0] == "inventory" and item is None:
                            env.player.inventory.hotbar[index] = env._dragged_item[1]
                    env._dragged_item = None

        if event.type == pygame.MOUSEBUTTONUP:
            env._dragged_item = None

