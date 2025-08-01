import pygame
from gym_intrinsic.inventory import Inventory
from gym_intrinsic.items import Block

class Actor:
    def __init__(self, x, y, tile_size):
        self.tile_size = tile_size
        width = int(tile_size * 0.6)
        height = int(tile_size * 0.875)
        self.rect = pygame.Rect(x, y, width, height)

        self.velocity = [0.0, 0.0]
        self.facing = [1, 0]
        self.reach = 3

        self.max_health = 100
        self.health = self.max_health

        self.max_food = 100
        self.food = self.max_food

        self.max_oxygen = 100
        self.oxygen = self.max_oxygen

        self.hotbar = [None] * 10
        self.selected_slot = 0

        self.inventory = Inventory(40)
        self.inventory.player = self

    def current_item(self):
        if 0 <= self.selected_slot < len(self.hotbar):
            return self.hotbar[self.selected_slot]
        return None

    def eat_food(self):
        if self.inventory.get("food", 0) > 0 and self.food < self.max_food:
            self.inventory["food"] -= 1
            self.food = self.max_food

    def apply_gravity(self, gravity):
        self.velocity[1] += gravity

    def move_and_collide(self, blocks):
        self.rect.x += int(self.velocity[0])
        for rect, _ in blocks:
            if self.rect.colliderect(rect):
                if self.velocity[0] > 0:
                    self.rect.right = rect.left
                elif self.velocity[0] < 0:
                    self.rect.left = rect.right
                self.velocity[0] = 0

        self.rect.y += int(self.velocity[1])
        for rect, _ in blocks:
            if self.rect.colliderect(rect):
                if self.velocity[1] > 0:
                    self.rect.bottom = rect.top
                elif self.velocity[1] < 0:
                    self.rect.top = rect.bottom
                self.velocity[1] = 0

    def handle_oxygen(self, in_water):
        if in_water:
            self.oxygen = max(0, self.oxygen - 1)
            if self.oxygen == 0:
                self.health -= 0.5
        else:
            self.oxygen = min(self.max_oxygen, self.oxygen + 2)

    def consume_food(self):
        if self.food > 0:
            self.food = max(0, self.food - 0.05)
        if self.food <= 0:
            self.health -= 0.1

    def adjust_facing_from_keys(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.facing = [-1, 0]
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.facing = [1, 0]
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.facing = [0, -1]
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.facing = [0, 1]
        return self.facing

    def in_reach(self, tile_x, tile_y):
        tx = self.rect.centerx // self.tile_size
        ty = self.rect.centery // self.tile_size
        return ((tile_x - tx)**2 + (tile_y - ty)**2)**0.5 <= self.reach

    def on_ground(self, grid, grid_height, vel_y):
        below_y = self.rect.bottom // self.tile_size
        left_x = self.rect.left // self.tile_size
        right_x = (self.rect.right - 1) // self.tile_size
        if below_y >= grid_height:
            return True
        return (
            grid[below_y, left_x] != Block.EMPTY
            or grid[below_y, right_x] != Block.EMPTY
        ) and vel_y >= 0

    def reset(self, screen_height):
        self.rect.x = 50
        self.rect.y = screen_height - self.tile_size * 2
        self.velocity = [0.0, 0.0]
        self.facing = [1, 0]
        self.reach = 3
        self.health = self.max_health
        self.food = self.max_food
        self.oxygen = self.max_oxygen
        self.inventory.clear()
        self.inventory.add_item("dirt", 10)
        self.hotbar = ["dirt"] + [None] * 9
        self.selected_slot = 0
