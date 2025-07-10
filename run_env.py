"""Simple script to play the gym environment."""

import argparse
import pygame
import gym
import gym_intrinsic
import numpy as np
from ai_agents.simple_agent import SimpleAgent
 
def main():
    parser = argparse.ArgumentParser(description="Run the gym environment")
    parser.add_argument(
        "--control",
        choices=["ai", "manual"],
        default="ai",
        help="Choose control mode: 'ai' uses random actions, 'manual' uses the keyboard",
    )
    args = parser.parse_args()

    pygame.init()
    env = gym.make("Intrinsic-v0")
    obs, info = env.reset()
    done = False
 
    while not done:
        events = pygame.event.get()          
        for event in events:
            if event.type == pygame.QUIT:
                done = True

        env.handle_events(events)         

        if args.control == "manual":
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            action = np.array([
                keys[pygame.K_LEFT] or keys[pygame.K_a],   # left
                keys[pygame.K_RIGHT] or keys[pygame.K_d],  # right
                keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w],  # jump
                mouse_buttons[2],  # use item (right mouse button)
                mouse_buttons[0],  # destroy block (left mouse button)
            ], dtype=np.int8)
        else:
            action = np.zeros(5, dtype=np.int8) 

        obs, reward, done, truncated, info = env.step(action)
        env.render()
    env.close()
    pygame.quit()

if __name__ == "__main__":
    main()

