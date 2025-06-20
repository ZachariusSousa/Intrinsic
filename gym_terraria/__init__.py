from gym.envs.registration import register
import numpy as np

# Older NumPy versions (<1.24) don't provide ``np.bool8`` which Gym
# expects. Create an alias to maintain compatibility.
if not hasattr(np, "bool8"):
    np.bool8 = np.bool_

register(
    id="Terraria-v0",
    entry_point="gym_terraria.terraria_env:TerrariaEnv",
)

from .terraria_env import TerrariaEnv
from .player import Player
from .enemy_mobs import Enemy, Projectile
from .passive_mobs import PassiveMob

__all__ = ["TerrariaEnv", "Player", "Enemy", "Projectile", "PassiveMob"]
