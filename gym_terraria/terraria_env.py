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

        self.action_space = spaces.Discrete(4)  # 0 left, 1 right, 2 jump, 3 idle

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
        self.ground = pygame.Rect(0, self.screen_height - self.tile_size, self.screen_width, self.tile_size)

        self.screen = None
        self.clock = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.player.x = 50
        self.player.y = self.screen_height - self.tile_size * 2
        self.velocity = [0.0, 0.0]
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([self.player.x, self.player.y, self.velocity[0], self.velocity[1]], dtype=np.float32)

    def step(self, action):
        left, right, jump = action

        # horizontal movement
        if left and not right:
            self.velocity[0] = -self.speed
        elif right and not left:
            self.velocity[0] = self.speed
        else:
            self.velocity[0] = 0

        # jump
        if jump and self._on_ground():
            self.velocity[1] = self.jump_velocity

        # apply gravity
        self.velocity[1] += self.gravity

        # update position
        self.player.x += int(self.velocity[0])
        self.player.y += int(self.velocity[1])

        # ground collision
        if self.player.colliderect(self.ground):
            self.player.bottom = self.ground.top
            self.velocity[1] = 0

        # world boundaries
        self.player.x = max(0, min(self.player.x, self.screen_width - self.player.width))

        done = False
        reward = 0.0
        if self.player.right >= self.screen_width:
            done = True
            reward = 1.0

        return self._get_obs(), reward, done, False, {}

    def _on_ground(self):
        return self.player.bottom >= self.ground.top and self.velocity[1] >= 0

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
        pygame.draw.rect(self.screen, (34, 139, 34), self.ground)
        pygame.draw.rect(self.screen, (255, 0, 0), self.player)
        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None
