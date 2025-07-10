import numpy as np

class SimpleAgent:
    def __init__(self, env):
        self.env = env

    def act(self, observation):
        # Very basic: move right and jump occasionally
        move_right = 1
        move_left = 0
        jump = np.random.rand() < 0.1  # 10% chance
        use_item = 0
        destroy_block = 0
        return np.array([move_left, move_right, jump, use_item, destroy_block], dtype=np.int8)
