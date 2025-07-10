from actors.actor import Actor
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class Player(Actor):
    def __init__(self, screen_height: int, tile_size: int):
        super().__init__(50, screen_height - tile_size * 2, tile_size)
