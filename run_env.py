import pygame
import gym
from gym_terraria import TerrariaEnv

def main():
    pygame.init()  # Initialize pygame
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
    pygame.quit()  # Quit pygame

if __name__ == "__main__":
    main()