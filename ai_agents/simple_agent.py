import numpy as np

class SimpleAgent:
    def __init__(self, env):
        self.env = env

    def act(self, actor, env):
        player = env.player
        ax, ay = actor.rect.center
        px, py = player.rect.center

        move_left = ax > px + 10  # Add margin so it doesn't flicker
        move_right = ax < px - 10
        jump = py < ay - 20 and actor.on_ground(env.grid, env.grid_height, actor.velocity[1])

        return np.array([
            int(move_left),
            int(move_right),
            int(jump),
            0,  # use item
            0   # destroy block
        ], dtype=np.int8)


from actors.actor import Actor

class AIPlayer(Actor):
    def __init__(self, x, y, tile_size, agent_logic):
        super().__init__(x, y, tile_size)
        self.agent_logic = agent_logic

    def get_action(self, env):
        return self.agent_logic.act(self, env)
