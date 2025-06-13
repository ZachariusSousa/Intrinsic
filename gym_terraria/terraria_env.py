import pygame
import numpy as np
import gym
from gym import spaces

from . import world


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
        self.facing = [1, 0]  # initially facing right

        # World dimensions may extend beyond the screen
        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = (self.screen_height // self.tile_size) * 2

        self.grid = world.generate_world(self.grid_width, self.grid_height)
        self._update_blocks()

        # Camera offset for rendering larger worlds
        self.camera_x = 0
        self.camera_y = 0

        # Simple inventory for mined blocks
        self.inventory = {
            "dirt": 10,
            "stone": 0,
            "copper": 0,
            "iron": 0,
            "gold": 0,
            "wood": 0,
        }

        # Font for UI rendering
        self.font = None

        self.screen = None
        self.clock = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.player.x = 50
        self.player.y = self.screen_height - self.tile_size * 2
        self.velocity = [0.0, 0.0]
        self.inventory = {
            "dirt": 10,
            "stone": 0,
            "copper": 0,
            "iron": 0,
            "gold": 0,
            "wood": 0,
        }
        self.facing = [1, 0]
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([self.player.x, self.player.y, self.velocity[0], self.velocity[1]], dtype=np.float32)

    def step(self, action):
        left, right, jump, place, destroy = action

        keys = pygame.key.get_pressed()

        # update movement
        if left and not right:
            self.velocity[0] = -self.speed
        elif right and not left:
            self.velocity[0] = self.speed
        else:
            self.velocity[0] = 0

        # update facing based on keys (arrow keys or WASD)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.facing = [-1, 0]
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.facing = [1, 0]
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.facing = [0, -1]
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.facing = [0, 1]

        # jump
        if jump and self._on_ground():
            self.velocity[1] = self.jump_velocity

        # apply gravity
        self.velocity[1] += self.gravity

        # update position and handle collisions with blocks
        self.player.x += int(self.velocity[0])
        for rect, _ in self.blocks:
            if self.player.colliderect(rect):
                if self.velocity[0] > 0:
                    self.player.right = rect.left
                elif self.velocity[0] < 0:
                    self.player.left = rect.right
                self.velocity[0] = 0

        self.player.y += int(self.velocity[1])
        for rect, _ in self.blocks:
            if self.player.colliderect(rect):
                if self.velocity[1] > 0:
                    self.player.bottom = rect.top
                elif self.velocity[1] < 0:
                    self.player.top = rect.bottom
                self.velocity[1] = 0

        # world boundaries
        world_w = self.grid_width * self.tile_size
        world_h = self.grid_height * self.tile_size
        self.player.x = max(0, min(self.player.x, world_w - self.player.width))
        self.player.y = max(0, min(self.player.y, world_h - self.player.height))

        # update camera to follow player
        self.camera_y = int(self.player.centery - self.screen_height // 2)
        self.camera_y = max(0, min(self.camera_y, world_h - self.screen_height))

        # block placement and destruction
        px = self.player.centerx // self.tile_size
        py = self.player.centery // self.tile_size
        dx, dy = self.facing
        target_x = px + dx
        target_y = py + dy

        if 0 <= target_x < self.grid_width and 0 <= target_y < self.grid_height:
            if place and self.inventory.get("dirt", 0) > 0 and self.grid[target_y, target_x] == world.EMPTY:
                self.grid[target_y, target_x] = world.DIRT
                self.inventory["dirt"] -= 1
                self._update_blocks()
            if destroy and self.grid[target_y, target_x] != world.EMPTY:
                block = self.grid[target_y, target_x]
                self.grid[target_y, target_x] = world.EMPTY
                if block == world.DIRT:
                    self.inventory["dirt"] += 1
                elif block == world.STONE:
                    self.inventory["stone"] += 1
                elif block == world.COPPER_ORE:
                    self.inventory["copper"] += 1
                elif block == world.IRON_ORE:
                    self.inventory["iron"] += 1
                elif block == world.GOLD_ORE:
                    self.inventory["gold"] += 1
                elif block == world.WOOD:
                    self.inventory["wood"] += 1
                self._update_blocks()

        # extend world horizontally when approaching edges
        threshold = self.tile_size * 5
        if self.player.right > self.grid_width * self.tile_size - threshold:
            self._extend_world_right(self.grid_width // 2)
        if self.player.left < threshold:
            self._extend_world_left(self.grid_width // 2)

        # update camera to follow player horizontally
        world_w = self.grid_width * self.tile_size
        world_h = self.grid_height * self.tile_size
        self.camera_x = int(self.player.centerx - self.screen_width // 2)
        self.camera_x = max(0, min(self.camera_x, world_w - self.screen_width))

        done = False
        reward = 0.0

        return self._get_obs(), reward, done, False, {}

    def _on_ground(self):
        """Check if the player stands on any solid block."""
        below_y = (self.player.bottom) // self.tile_size
        left_x = self.player.left // self.tile_size
        right_x = (self.player.right - 1) // self.tile_size
        if below_y >= self.grid_height:
            return True
        return (
            self.grid[below_y, left_x] != world.EMPTY
            or self.grid[below_y, right_x] != world.EMPTY
        ) and self.velocity[1] >= 0

    def render(self):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 24)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return
        self.screen.fill((135, 206, 235))  # sky blue
        for rect, block in self.blocks:
            screen_rect = rect.move(-self.camera_x, -self.camera_y)
            if screen_rect.bottom < 0 or screen_rect.top > self.screen_height:
                continue
            color = world.COLOR_MAP.get(block, (255, 255, 255))
            pygame.draw.rect(self.screen, color, screen_rect)
        pygame.draw.rect(self.screen, (255, 0, 0), self.player.move(-self.camera_x, -self.camera_y))

        # draw facing indicator
        fx = self.player.centerx + self.facing[0] * self.tile_size // 2
        fy = self.player.centery + self.facing[1] * self.tile_size // 2
        pygame.draw.rect(
            self.screen,
            (255, 255, 0),
            pygame.Rect(fx - 4 - self.camera_x, fy - self.camera_y - 4, 8, 8),
        )

        # draw inventory UI
        if self.font:
            inv_text = " | ".join(f"{k}: {v}" for k, v in self.inventory.items())
            text_surf = self.font.render(inv_text, True, (0, 0, 0))
            self.screen.blit(text_surf, (10, 10))

        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    def _extend_world_right(self, extra_cols):
        """Extend the world grid to the right by generating additional columns."""
        new_grid = world.generate_world(extra_cols, self.grid_height)
        self.grid = np.concatenate([self.grid, new_grid], axis=1)
        self.grid_width += extra_cols
        self._update_blocks()

    def _extend_world_left(self, extra_cols):
        """Extend the world grid to the left by generating additional columns."""
        new_grid = world.generate_world(extra_cols, self.grid_height)
        self.grid = np.concatenate([new_grid, self.grid], axis=1)
        self.grid_width += extra_cols
        self.player.x += extra_cols * self.tile_size
        self._update_blocks()

    def _update_blocks(self):
        """Recreate block rectangles from the grid for collision and rendering."""
        self.blocks = world.blocks_from_grid(self.grid, self.tile_size)
