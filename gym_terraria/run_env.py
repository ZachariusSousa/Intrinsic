import gym
from terraria_env import TerrariaEnv

env = gym.make("Terraria-v0")
obs, info = env.reset()

for _ in range(1000):
    action = env.action_space.sample()
    obs, reward, done, truncated, info = env.step(action)
    env.render()
    if done:
        break

env.close()
