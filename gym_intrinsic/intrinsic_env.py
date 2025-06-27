import pygame
import numpy as np
import gym
from gym import spaces

from . import world
from . import blocks
from .player import Player
from .enemy_mobs import update_enemies, update_projectiles
from .passive_mobs import update_passive_mobs
from .weather import WeatherSystem
from .constants import HOTBAR_ITEM_TO_BLOCK
from . import env_step, env_render, env_utils



class IntrinsicEnv(gym.Env):
    """Simple 2D platformer environment using pygame."""

    metadata = {"render.modes": ["human"]}

    def __init__(self):
        super().__init__()
        self.screen_width = 640
        self.screen_height = 480
        self.tile_size = 32

        # Actions: left, right, jump, place block, destroy block
        self.action_space = spaces.MultiBinary(5)

        high = np.array(
            [self.screen_width, self.screen_height, np.finfo(np.float32).max, np.finfo(np.float32).max],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low=np.zeros(4, dtype=np.float32), high=high, dtype=np.float32)

        self.gravity = 0.8
        self.speed = 5
        self.jump_velocity = -15

        self.player = Player(self.screen_height, self.tile_size)
        self.facing = [1, 0]  # initially facing right

        # World dimensions may extend beyond the screen
        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = (self.screen_height // self.tile_size) * 2

        self.grid = world.generate_world(self.grid_width, self.grid_height)
        env_utils.update_blocks(self)
        self.in_water = False

        # Camera offset for rendering larger worlds
        self.camera_x = 0
        self.camera_y = 0



        # Font for UI rendering
        self.font = None

        self.screen = None
        self.clock = None
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
        self.passive_spawn_chance = 0.005

        # hotbar / inventory view state
        self.show_inventory = False
        self._prev_e = False
        self._inventory_item_rects = []
        self._hotbar_rects = []
        self._last_hotbar_click = [0] * 10

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
        self.show_inventory = False
        self._prev_e = False
        self._inventory_item_rects = []
        self._hotbar_rects = []
        self._last_hotbar_click = [0] * 10
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([self.player.rect.x, self.player.rect.y, self.player.velocity[0], self.player.velocity[1]], dtype=np.float32)

    def step(self, action):
        return env_step.step(self, action)

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
        env_render.render(self)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None

