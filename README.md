# Intrinsic Gym Environment

This repository provides a minimal 2D platformer environment similar to Terraria, built with `pygame` and `gym`. The environment can be used for simple reinforcement learning experiments or as a template for more advanced AI training.

## Installation

Make sure you have Python 3 installed. Then install the required packages:

```bash
pip install -r requirements.txt
```

## Quick Start

Run the environment with the included script from the repository root.

```bash
python run_env.py              # AI-controlled random actions
python run_env.py --control manual  # Play manually with the keyboard
```
## Controls

WASD - Movement
E - Open inventory (drag)
Left Click - Attack/Mine
Right Cick - Use/Place
1-0 - Hotbar selection
