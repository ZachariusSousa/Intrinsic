import pygame
import numpy as np
import gym
from gym import spaces


class TerrariaEnv(gym.Env):
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

        self.player = pygame.Rect(50, self.screen_height - self.tile_size * 2, self.tile_size, self.tile_size)
        self.velocity = [0.0, 0.0]
        self.facing = 1  # 1 right, -1 left

        # Grid based world
        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = self.screen_height // self.tile_size
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
        self.grid[-1, :] = 1  # ground blocks
        self._update_blocks()

        # Simple inventory: only dirt blocks
        self.inventory = {"dirt": 0}

        self.screen = None
        self.clock = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.player.x = 50
        self.player.y = self.screen_height - self.tile_size * 2
        self.velocity = [0.0, 0.0]
        self.inventory = {"dirt": self.inventory.get("dirt", 0)}
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([self.player.x, self.player.y, self.velocity[0], self.velocity[1]], dtype=np.float32)

    def step(self, action):
        left, right, jump, place, destroy = action

        # horizontal movement
        if left and not right:
            self.velocity[0] = -self.speed
            self.facing = -1
        elif right and not left:
            self.velocity[0] = self.speed
            self.facing = 1
        else:
            self.velocity[0] = 0

        # jump
        if jump and self._on_ground():
            self.velocity[1] = self.jump_velocity

        # apply gravity
        self.velocity[1] += self.gravity

        # update position and handle collisions with blocks
        self.player.x += int(self.velocity[0])
        for rect in self.blocks:
            if self.player.colliderect(rect):
                if self.velocity[0] > 0:
                    self.player.right = rect.left
                elif self.velocity[0] < 0:
                    self.player.left = rect.right
                self.velocity[0] = 0

        self.player.y += int(self.velocity[1])
        for rect in self.blocks:
            if self.player.colliderect(rect):
                if self.velocity[1] > 0:
                    self.player.bottom = rect.top
                elif self.velocity[1] < 0:
                    self.player.top = rect.bottom
                self.velocity[1] = 0

        # world boundaries
        self.player.x = max(0, min(self.player.x, self.screen_width - self.player.width))
        self.player.y = max(0, min(self.player.y, self.screen_height - self.player.height))

        # block placement and destruction
        target_x = self.player.centerx // self.tile_size + self.facing
        target_y = self.player.centery // self.tile_size
        if 0 <= target_x < self.grid_width and 0 <= target_y < self.grid_height:
            if place and self.inventory.get("dirt", 0) > 0 and self.grid[target_y, target_x] == 0:
                self.grid[target_y, target_x] = 1
                self.inventory["dirt"] -= 1
                self._update_blocks()
            if destroy and self.grid[target_y, target_x] == 1:
                self.grid[target_y, target_x] = 0
                self.inventory["dirt"] = self.inventory.get("dirt", 0) + 1
                self._update_blocks()

        done = False
        reward = 0.0
        if self.player.right >= self.screen_width:
            done = True
            reward = 1.0

        return self._get_obs(), reward, done, False, {}

    def _on_ground(self):
        """Check if the player stands on any solid block."""
        below_y = (self.player.bottom) // self.tile_size
        left_x = self.player.left // self.tile_size
        right_x = (self.player.right - 1) // self.tile_size
        if below_y >= self.grid_height:
            return True
        return (
            self.grid[below_y, left_x] == 1 or self.grid[below_y, right_x] == 1
        ) and self.velocity[1] >= 0

    def render(self):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.clock = pygame.time.Clock()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return
        self.screen.fill((135, 206, 235))  # sky blue
        for rect in self.blocks:
            pygame.draw.rect(self.screen, (139, 69, 19), rect)
        pygame.draw.rect(self.screen, (255, 0, 0), self.player)
        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    def _update_blocks(self):
        """Recreate block rectangles from the grid for collision and rendering."""
        self.blocks = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y, x] == 1:
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                    self.blocks.append(rect)

