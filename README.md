# Intrinsic Terraria Gym Environment

This repository provides a minimal 2D platformer environment similar to Terraria, built with `pygame` and `gym`. The environment can be used for simple reinforcement learning experiments or as a template for more advanced games.

## Installation

Make sure you have Python 3 installed. Then install the required packages:

```bash
pip install pygame gym numpy
```

Older versions of NumPy (<1.24) don't expose ``np.bool8`` which the Gym
wrappers expect. The package automatically provides a fallback so upgrading
NumPy is optional.

## Usage

Import and register the environment, then create it using `gym.make`:

```python
import gym
import gym_terraria

env = gym.make("Terraria-v0")
obs, info = env.reset()

for _ in range(1000):
    action = env.action_space.sample()
    obs, reward, done, truncated, info = env.step(action)
    env.render()
    if done:
        break

env.close()
```

The agent moves left, right, or jumps with discrete actions. Reaching the far right side of the screen ends the episode with a reward of `1.0`.

## Quick Start

Run the environment with the included script from the repository root. The
environment is registered automatically when ``gym_terraria`` is imported:

```bash
python run_env.py
```
