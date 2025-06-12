from gym.envs.registration import register

register(
    id="Terraria-v0",
    entry_point="gym_terraria.terraria_env:TerrariaEnv",
)

from .terraria_env import TerrariaEnv

__all__ = ["TerrariaEnv"]
