import pygame
import numpy as np
import gym
from typing import Optional
from gym import spaces
import os

from . import world
from . import items
from .player import Player
from .enemy_mobs import Enemy, Projectile, spawn_random_enemies, update_enemies, update_projectiles
from .passive_mobs import PassiveMob, spawn_random_passive_mobs, update_passive_mobs
from .weather import WeatherSystem
from .inventory_ui import InventoryUI
from . import player_actions
from . import env_logic
from . import env_render


class IntrinsicEnv(gym.Env):
    """Simple 2D platformer environment using pygame."""

    metadata = {"render.modes": ["human"]}

    def __init__(self):
        super().__init__()
        self.screen_width = 1280
        self.screen_height = 960
        self.tile_size = 64

        # Actions: left, right, jump, use item, destroy block
        self.action_space = spaces.MultiBinary(5)

        high = np.array(
            [self.screen_width, self.screen_height, np.finfo(np.float32).max, np.finfo(np.float32).max],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low=np.zeros(4, dtype=np.float32), high=high, dtype=np.float32)

        self.gravity = 0.8
        self.speed = 10
        self.jump_velocity = -20

        self.player = Player(self.screen_height, self.tile_size)
        self.facing = [1, 0]  # initially facing right

        # World dimensions may extend beyond the screen
        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = (self.screen_height // self.tile_size) * 6

        self.world_x_offset = 0  # total tiles offset from world origin (left side)
        self.grid = world.generate_world(self.grid_width, self.grid_height, world_x_offset=self.world_x_offset)
        self._update_blocks()
        self.in_water = False

        # Camera offset for rendering larger worlds
        self.camera_x = 0
        self.camera_y = 0



        # Font for UI rendering
        self.font = None

        self.screen = None
        self.clock = None
        self.inventory_ui: Optional[InventoryUI] = None
        # Weather and time system
        self.weather = WeatherSystem()

        # Enemies, passive mobs and projectiles lists
        self.enemies = []
        self.passive_mobs = []
        self.projectiles = []

        # mining state
        self._mining_target = None  # (x, y) of block being mined
        self._mining_progress = 0

        # spawning configuration
        self.max_enemies = 5
        self.max_passive_mobs = 5
        self.enemy_spawn_chance = 0.001
        self.passive_spawn_chance = 0.01
        
        # pathfinding
        self.repathing_time = 1500

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.player.reset(self.screen_height)
        self.facing = [1, 0]
        self.weather = WeatherSystem()
        # Start with an empty world and spawn mobs dynamically during gameplay
        self.enemies = []
        self.passive_mobs = []
        self.projectiles = []
        self._mining_target = None
        self._mining_progress = 0
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([self.player.rect.x, self.player.rect.y, self.player.velocity[0], self.player.velocity[1]], dtype=np.float32)

    def step(self, action):
        self.weather.step()
        env_logic.handle_input(self, action)
        env_logic.handle_physics(self)
        env_logic.handle_actions(self, action)
        env_logic.update_camera(self)
        env_logic.maybe_extend_world(self)
        env_logic.spawn_and_update_mobs(self)

        done = self.player.health <= 0
        reward = 0.0
        return self._get_obs(), reward, done, False, {}


    def _on_ground(self):
        """Check if the player stands on any solid block."""
        below_y = self.player.rect.bottom // self.tile_size
        left_x = self.player.rect.left // self.tile_size
        right_x = (self.player.rect.right - 1) // self.tile_size
        if below_y >= self.grid_height:
            return True
        def solid(val):
            return val not in (world.EMPTY, world.WATER)
        return (
            solid(self.grid[below_y, left_x])
            or solid(self.grid[below_y, right_x])
        ) and self.player.velocity[1] >= 0

    def render(self):
        env_render.render_environment(self)

        
    def handle_events(self, events) -> None:
        """Forward pygame events to UI (e.g., inventory)."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.player.selected_slot = event.key - pygame.K_1
                elif event.key == pygame.K_0:
                    self.player.selected_slot = 9
                elif event.key == pygame.K_e and self.inventory_ui:
                    self.inventory_ui.toggle()
            if self.inventory_ui:
                self.inventory_ui.handle_event(event)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    def _extend_world_right(self, extra_cols):
        """Extend world to the right using proper x-offset for biome continuity."""
        new_offset = self.world_x_offset + self.grid_width
        new_grid = world.generate_world(extra_cols, self.grid_height, world_x_offset=new_offset)
        self.grid = np.concatenate([self.grid, new_grid], axis=1)
        self.grid_width += extra_cols
        self._update_blocks()


    def _extend_world_left(self, extra_cols):
        """Extend world to the left and adjust global offset."""
        new_offset = self.world_x_offset - extra_cols
        new_grid = world.generate_world(extra_cols, self.grid_height, world_x_offset=new_offset)
        self.grid = np.concatenate([new_grid, self.grid], axis=1)
        self.grid_width += extra_cols
        self.world_x_offset -= extra_cols  # shift global position left

        shift_px = extra_cols * self.tile_size
        self.player.rect.x += shift_px
        for enemy in self.enemies:
            enemy.rect.x += shift_px
        for mob in self.passive_mobs:
            mob.rect.x += shift_px
        for proj in self.projectiles:
            proj.rect.x += shift_px

        self._update_blocks()


    def _update_blocks(self):
        """Recreate block rectangles from the grid for collision and rendering."""
        self.blocks, self.water_blocks = world.blocks_from_grid(self.grid, self.tile_size)

    def _find_spawn_y(self, tile_x: int) -> int:
        """Return the surface y position (in pixels) for spawning an enemy."""
        for y in range(self.grid_height):
            block = self.grid[y, tile_x]
            if block != world.EMPTY and block not in (world.WOOD, world.LEAVES):
                return max(0, (y - 1) * self.tile_size)
        # default to ground level if nothing found
        return max(0, (self.grid_height - 2) * self.tile_size)

    def _spawn_mobs_randomly(self) -> None:
        """Occasionally add new mobs to the world."""
        if (
            len(self.enemies) < self.max_enemies
            and np.random.random() < self.enemy_spawn_chance
        ):
            self.enemies.extend(spawn_random_enemies(1, self))
        if (
            len(self.passive_mobs) < self.max_passive_mobs
            and np.random.random() < self.passive_spawn_chance
        ):
            self.passive_mobs.extend(spawn_random_passive_mobs(1, self))
