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

The agent moves left, right, jumps, or stays idle with discrete actions. The world now generates endlessly to the left and right, with the camera following the player.
Trees can appear on the surface and multiple ore types are buried in the stone layers. Blocks you mine are added to a simple inventory displayed at the top left of the screen.
Mining progress is visible thanks to a translucent square that grows from the centre of the targeted block until it breaks.
Enemies and passive creatures now spawn randomly over time rather than only at the start of the game.

## Quick Start

Run the environment with the included script from the repository root. The
environment is registered automatically when ``gym_terraria`` is imported:

```bash
python run_env.py              # AI-controlled random actions
python run_env.py --control manual  # Play manually with the keyboard
```
When playing manually use the arrow keys (or ``A``/``D``) to move and ``Space`` to jump.
