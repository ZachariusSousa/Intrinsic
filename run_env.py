"""Simple script to play the Terraria gym environment."""

import pygame
import gym
import gym_terraria

def main():
    pygame.init()
    env = gym.make("Terraria-v0")
    obs, info = env.reset()
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        action = env.action_space.sample()
        obs, reward, done, truncated, info = env.step(action)
        env.render()
    env.close()
    pygame.quit()

if __name__ == "__main__":
    main()
