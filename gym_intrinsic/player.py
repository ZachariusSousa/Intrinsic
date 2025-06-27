import pygame
from typing import Dict
from . import world

class Player:
    """Simple player container."""

    def __init__(self, screen_height: int, tile_size: int):
        self.tile_size = tile_size
        self.rect = pygame.Rect(
            50,
            screen_height - tile_size * 2,
            int(tile_size * 0.875),
            int(tile_size * 0.875),
        )
        self.velocity = [0.0, 0.0]
        self.facing = [1, 0]
        self.max_health = 100
        self.health = self.max_health
        self.max_food = 100
        self.food = self.max_food
        self.max_oxygen = 100
        self.oxygen = self.max_oxygen
        self.inventory: Dict[str, int] = {
            "dirt": 10,
            "stone": 0,
            "copper": 0,
            "iron": 0,
            "gold": 0,
            "wood": 0,
            "food": 0,
        }
        # basic 10 slot hotbar with the first slot containing dirt by default
        self.hotbar = [
            "dirt",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
        self.selected_slot = 0

    def eat_food(self) -> None:
        """Consume one food item to refill the food bar."""
        if self.inventory.get("food", 0) > 0 and self.food < self.max_food:
            self.inventory["food"] -= 1
            self.food = self.max_food

    def reset(self, screen_height: int) -> None:
        """Reset player position and state."""
        self.rect.x = 50
        self.rect.y = screen_height - self.tile_size * 2
        self.velocity = [0.0, 0.0]
        self.facing = [1, 0]
        self.health = self.max_health
        self.food = self.max_food
        self.oxygen = self.max_oxygen
        for key in self.inventory:
            self.inventory[key] = 10 if key == "dirt" else 0
        self.hotbar = [
            "dirt",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
        self.selected_slot = 0

    def on_ground(self, grid, grid_height: int, vel_y: float) -> bool:
        """Return True if standing on a solid block."""
        below_y = self.rect.bottom // self.tile_size
        left_x = self.rect.left // self.tile_size
        right_x = (self.rect.right - 1) // self.tile_size
        if below_y >= grid_height:
            return True
        return (
            grid[below_y, left_x] != world.EMPTY
            or grid[below_y, right_x] != world.EMPTY
        ) and vel_y >= 0

    @property
    def selected_item(self):
        """Return the item currently selected in the hotbar."""
        return self.hotbar[self.selected_slot]
