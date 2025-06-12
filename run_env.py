"""Simple script to play the Terraria gym environment."""

import argparse
import pygame
import gym
import gym_terraria
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Run the Terraria gym environment")
    parser.add_argument(
        "--control",
        choices=["ai", "manual"],
        default="ai",
        help="Choose control mode: 'ai' uses random actions, 'manual' uses the keyboard",
    )
    args = parser.parse_args()

    pygame.init()
    env = gym.make("Terraria-v0")
    obs, info = env.reset()
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        if args.control == "manual":
            keys = pygame.key.get_pressed()
            action = np.array([
                keys[pygame.K_LEFT] or keys[pygame.K_a],   # left
                keys[pygame.K_RIGHT] or keys[pygame.K_d],  # right
                keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]  # jump
            ], dtype=np.int8)
        else:
            action = env.action_space.sample()
            
        obs, reward, done, truncated, info = env.step(action)
        env.render()
    env.close()
    pygame.quit()

if __name__ == "__main__":
    main()
