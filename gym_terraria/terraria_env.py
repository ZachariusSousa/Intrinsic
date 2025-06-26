import pygame
import numpy as np
import gym
from gym import spaces

from . import world
from . import blocks
from .player import Player
from .enemy_mobs import Enemy, Projectile, spawn_random_enemies, update_enemies, update_projectiles
from .passive_mobs import PassiveMob, spawn_random_passive_mobs, update_passive_mobs
from .weather import WeatherSystem


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

        self.player = Player(self.screen_height, self.tile_size)
        self.facing = [1, 0]  # initially facing right

        # World dimensions may extend beyond the screen
        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = (self.screen_height // self.tile_size) * 2

        self.grid = world.generate_world(self.grid_width, self.grid_height)
        self._update_blocks()
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
        # advance the day/night and season cycle
        self.weather.step()

        left, right, jump, place, destroy = action

        keys = pygame.key.get_pressed()

        if keys[pygame.K_e]:
            self.player.eat_food()

        self.in_water = any(self.player.rect.colliderect(r) for r in self.water_blocks)

        if (left or right or jump) and self.player.food > 0:
            self.player.food = max(0, self.player.food - 0.05)
        if self.player.food <= 0:
            self.player.health -= 0.1

        # update movement
        if left and not right:
            self.player.velocity[0] = -self.speed
        elif right and not left:
            self.player.velocity[0] = self.speed
        else:
            self.player.velocity[0] = 0

        # update facing based on keys (arrow keys or WASD)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.facing = [-1, 0]
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.facing = [1, 0]
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.facing = [0, -1]
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.facing = [0, 1]

        # jump (allow swimming upwards)
        if jump and (self._on_ground() or self.in_water):
            self.player.velocity[1] = self.jump_velocity if not self.in_water else -5

        # apply gravity (reduced in water)
        gravity = 0.2 if self.in_water else self.gravity
        self.player.velocity[1] += gravity

        # update position and handle collisions with blocks
        self.player.rect.x += int(self.player.velocity[0])
        for rect, _ in self.blocks:
            if self.player.rect.colliderect(rect):
                if self.player.velocity[0] > 0:
                    self.player.rect.right = rect.left
                elif self.player.velocity[0] < 0:
                    self.player.rect.left = rect.right
                self.player.velocity[0] = 0

        self.player.rect.y += int(self.player.velocity[1])
        for rect, _ in self.blocks:
            if self.player.rect.colliderect(rect):
                if self.player.velocity[1] > 0:
                    self.player.rect.bottom = rect.top
                elif self.player.velocity[1] < 0:
                    self.player.rect.top = rect.bottom
                self.player.velocity[1] = 0

        # world boundaries
        world_w = self.grid_width * self.tile_size
        world_h = self.grid_height * self.tile_size
        self.player.rect.x = max(0, min(self.player.rect.x, world_w - self.player.rect.width))
        self.player.rect.y = max(0, min(self.player.rect.y, world_h - self.player.rect.height))

        # update water status after movement
        self.in_water = any(self.player.rect.colliderect(r) for r in self.water_blocks)
        if self.in_water:
            self.player.oxygen = max(0, self.player.oxygen - 1)
            if self.player.oxygen == 0:
                self.player.health -= 0.5
        else:
            self.player.oxygen = min(self.player.max_oxygen, self.player.oxygen + 2)

        # update camera to follow player
        self.camera_y = int(self.player.rect.centery - self.screen_height // 2)
        self.camera_y = max(0, min(self.camera_y, world_h - self.screen_height))

        # block placement and destruction
        px = self.player.rect.centerx // self.tile_size
        py = self.player.rect.centery // self.tile_size
        dx, dy = self.facing
        target_x = px + dx
        target_y = py + dy

        if 0 <= target_x < self.grid_width and 0 <= target_y < self.grid_height:
            if place and self.player.inventory.get("dirt", 0) > 0 and self.grid[target_y, target_x] == world.EMPTY:
                self.grid[target_y, target_x] = world.DIRT
                self.player.inventory["dirt"] -= 1
                self._update_blocks()

            if destroy:
                block = self.grid[target_y, target_x]
                target = (target_x, target_y)
                if block != world.EMPTY:
                    if target != self._mining_target:
                        self._mining_target = target
                        self._mining_progress = 0
                    info = blocks.BLOCK_STATS.get(block)
                    required = info.mining_time if info else 1
                    self._mining_progress += 1
                    if self._mining_progress >= required:
                        self.grid[target_y, target_x] = world.EMPTY
                        if block == world.DIRT:
                            self.player.inventory["dirt"] += 1
                        elif block == world.STONE:
                            self.player.inventory["stone"] += 1
                        elif block == world.COPPER_ORE:
                            self.player.inventory["copper"] += 1
                        elif block == world.IRON_ORE:
                            self.player.inventory["iron"] += 1
                        elif block == world.GOLD_ORE:
                            self.player.inventory["gold"] += 1
                        elif block == world.WOOD:
                            self.player.inventory["wood"] += 1
                        self._update_blocks()
                        self._mining_target = None
                        self._mining_progress = 0
                else:
                    self._mining_target = None
                    self._mining_progress = 0
                    # attempt to attack enemy in front of player
                    attack_rect = pygame.Rect(
                        target_x * self.tile_size,
                        target_y * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                    for enemy in list(self.enemies):
                        if enemy.rect.colliderect(attack_rect):
                            enemy.health -= 10
                            if enemy.health <= 0:
                                self.enemies.remove(enemy)
                    for mob in list(self.passive_mobs):
                        if mob.rect.colliderect(attack_rect):
                            mob.health -= 10
                            if mob.health <= 0:
                                self.player.inventory["food"] = self.player.inventory.get("food", 0) + mob.food_drop
                                self.passive_mobs.remove(mob)
            else:
                self._mining_target = None
                self._mining_progress = 0

        # extend world horizontally when approaching edges
        threshold = self.tile_size * 5
        if self.player.rect.right > self.grid_width * self.tile_size - threshold:
            self._extend_world_right(self.grid_width // 2)
        if self.player.rect.left < threshold:
            self._extend_world_left(self.grid_width // 2)

        # update camera to follow player horizontally
        world_w = self.grid_width * self.tile_size
        world_h = self.grid_height * self.tile_size
        self.camera_x = int(self.player.rect.centerx - self.screen_width // 2)
        self.camera_x = max(0, min(self.camera_x, world_w - self.screen_width))
        # occasionally spawn new mobs
        self._spawn_mobs_randomly()
        # update mobs, enemies and projectiles
        update_passive_mobs(self.passive_mobs, self)
        update_enemies(self.enemies, self.player, self.projectiles)
        update_projectiles(self.projectiles, self.player, world_w)

        done = False
        if self.player.health <= 0:
            done = True
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
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 24)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return
        # sky color depends on day/night cycle and season
        self.screen.fill(self.weather.get_sky_color())
        light = self.weather.get_light_intensity()
        for rect, block in self.blocks:
            screen_rect = rect.move(-self.camera_x, -self.camera_y)
            if screen_rect.bottom < 0 or screen_rect.top > self.screen_height:
                continue
            color = world.COLOR_MAP.get(block, (255, 255, 255))
            color = tuple(int(c * light) for c in color)
            pygame.draw.rect(self.screen, color, screen_rect)
        for rect in self.water_blocks:
            screen_rect = rect.move(-self.camera_x, -self.camera_y)
            if screen_rect.bottom < 0 or screen_rect.top > self.screen_height:
                continue
            water_color = tuple(int(c * light) for c in world.COLOR_MAP[world.WATER])
            pygame.draw.rect(self.screen, water_color, screen_rect)

        # draw mining progress indicator
        if self._mining_target is not None and self._mining_progress > 0:
            tx, ty = self._mining_target
            block = self.grid[ty, tx]
            info = blocks.BLOCK_STATS.get(block)
            required = info.mining_time if info else 1
            ratio = min(1.0, self._mining_progress / required)
            size = int(self.tile_size * ratio)
            if size > 0:
                offset = (self.tile_size - size) // 2
                sx = tx * self.tile_size - self.camera_x + offset
                sy = ty * self.tile_size - self.camera_y + offset
                overlay = pygame.Surface((size, size), pygame.SRCALPHA)
                overlay.fill((255, 255, 255, 120))
                self.screen.blit(overlay, (sx, sy))
        player_color = tuple(int(c * light) for c in (255, 0, 0))
        pygame.draw.rect(self.screen, player_color, self.player.rect.move(-self.camera_x, -self.camera_y))

        # draw enemies
        for enemy in self.enemies:
            screen_rect = enemy.rect.move(-self.camera_x, -self.camera_y)
            color = tuple(int(c * light) for c in enemy.color)
            pygame.draw.rect(self.screen, color, screen_rect)

        # draw passive mobs
        for mob in self.passive_mobs:
            screen_rect = mob.rect.move(-self.camera_x, -self.camera_y)
            color = tuple(int(c * light) for c in mob.color)
            pygame.draw.rect(self.screen, color, screen_rect)

        # draw projectiles
        for proj in self.projectiles:
            screen_rect = proj.rect.move(-self.camera_x, -self.camera_y)
            proj_color = tuple(int(c * light) for c in (0, 0, 0))
            pygame.draw.rect(self.screen, proj_color, screen_rect)

        # draw facing indicator
        fx = self.player.rect.centerx + self.facing[0] * self.tile_size // 2
        fy = self.player.rect.centery + self.facing[1] * self.tile_size // 2
        pygame.draw.rect(
            self.screen,
            tuple(int(c * light) for c in (255, 255, 0)),
            pygame.Rect(fx - 4 - self.camera_x, fy - self.camera_y - 4, 8, 8),
        )

        # draw inventory UI
        if self.font:
            inv_text = " | ".join(f"{k}: {v}" for k, v in self.player.inventory.items())
            text_surf = self.font.render(inv_text, True, (0, 0, 0))
            self.screen.blit(text_surf, (10, 10))
            # health bar
            health_ratio = self.player.health / self.player.max_health
            pygame.draw.rect(self.screen, (255, 0, 0), pygame.Rect(10, 30, 100 * health_ratio, 10))
            pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(10, 30, 100, 10), 2)
            food_ratio = self.player.food / self.player.max_food
            pygame.draw.rect(self.screen, (0, 128, 0), pygame.Rect(10, 45, 100 * food_ratio, 10))
            pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(10, 45, 100, 10), 2)
            oxygen_ratio = self.player.oxygen / self.player.max_oxygen
            pygame.draw.rect(self.screen, (0, 0, 255), pygame.Rect(10, 60, 100 * oxygen_ratio, 10))
            pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(10, 60, 100, 10), 2)

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
        self.player.rect.x += extra_cols * self.tile_size
        # Shift all enemies to the right
        for enemy in self.enemies:
            enemy.rect.x += extra_cols * self.tile_size
        # Shift all passive mobs to the right
        for mob in self.passive_mobs:
            mob.rect.x += extra_cols * self.tile_size
        # Shift all projectiles to the right
        for proj in self.projectiles:
            proj.rect.x += extra_cols * self.tile_size
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
