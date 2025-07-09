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
