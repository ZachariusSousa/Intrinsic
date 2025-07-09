import pygame
from . import world, items
from .items import Block

def place_block(player, grid, target_x, target_y, update_blocks):
    selected = player.current_item()
    if (
        selected in items.ITEM_STATS
        and player.inventory.get(selected, 0) > 0
    ):
        info = items.ITEM_STATS[selected]
        if info.category == "block" and grid[target_y, target_x] == Block.EMPTY:
            grid[target_y, target_x] = info.block_id
            player.inventory[selected] -= 1
            update_blocks()
        elif info.category == "food" and player.food < player.max_food:
            player.inventory[selected] -= 1
            player.food = player.max_food
        elif info.category == "weapon":
            return info.damage
    return None

def attack_entities(attack_rect, enemies, passive_mobs, player, damage):
    for enemy in list(enemies):
        if enemy.rect.colliderect(attack_rect):
            enemy.health -= damage
            if enemy.health <= 0:
                enemies.remove(enemy)

    for mob in list(passive_mobs):
        if mob.rect.colliderect(attack_rect):
            mob.health -= damage
            if mob.health <= 0:
                player.inventory.add_item("food", mob.food_drop)
                passive_mobs.remove(mob)

def mine_block(grid, target, mining_progress, player, update_blocks):
    target_x, target_y = target
    block = grid[target_y, target_x]
    info = items.BLOCK_STATS.get(block)
    required = info.mining_time if info else 1
    mining_progress += 1
    if mining_progress >= required:
        grid[target_y, target_x] = Block.EMPTY
        item_name = items.BLOCK_TO_ITEM.get(block)
        if item_name:
            player.inventory.add_item(item_name)
        update_blocks()
        return None, 0
    return target, mining_progress

def handle_actions(env, action):
    _, _, _, use, destroy = action

    px = env.player.rect.centerx // env.tile_size
    py = env.player.rect.centery // env.tile_size
    dx, dy = env.player.facing

    tiles_in_sight = []
    for step in range(1, env.player.reach + 1):
        tx, ty = px + dx * step, py + dy * step
        if not (0 <= tx < env.grid_width and 0 <= ty < env.grid_height):
            break                     # went out of bounds
        tiles_in_sight.append((tx, ty))
    if not tiles_in_sight:
        return

    if use:
        tx, ty = tiles_in_sight[0]
        for cand in tiles_in_sight:
            if env.grid[cand[1], cand[0]] == Block.EMPTY:
                tx, ty = cand
                break
        dmg = place_block(env.player, env.grid, tx, ty, env._update_blocks)
        if dmg:
            attack_rect = pygame.Rect(
                tx * env.tile_size,
                ty * env.tile_size,
                env.tile_size,
                env.tile_size,
            )
            attack_entities(attack_rect, env.enemies, env.passive_mobs, env.player, dmg)

    if destroy:
        # Try to find a block to mine
        block_target = None
        for tx, ty in tiles_in_sight:
            if env.grid[ty, tx] != Block.EMPTY:
                block_target = (tx, ty)
                break

        if block_target is not None:
            target_x, target_y = block_target
            if (target_x, target_y) != env._mining_target:
                env._mining_target = (target_x, target_y)
                env._mining_progress = 0
            env._mining_target, env._mining_progress = mine_block(
                env.grid, (target_x, target_y),
                env._mining_progress, env.player, env._update_blocks
            )
        else:
            # No block found → reset mining
            env._mining_target = None
            env._mining_progress = 0

            # But still attack entities at nearest tile in reach
            for tx, ty in tiles_in_sight:
                attack_rect = pygame.Rect(
                    tx * env.tile_size,
                    ty * env.tile_size,
                    env.tile_size,
                    env.tile_size,
                )
                attack_entities(
                    attack_rect, env.enemies, env.passive_mobs, env.player, 10
                )

    else:
        env._mining_target = None
        env._mining_progress = 0