from dataclasses import dataclass
from typing import Dict

from . import world

@dataclass
class BlockInfo:
    """Metadata for a block type."""
    group: str
    mining_time: int  # number of steps required to mine the block

# Default stats for each block type
BLOCK_STATS: Dict[int, BlockInfo] = {
    world.DIRT: BlockInfo(group="soil", mining_time=20),
    world.STONE: BlockInfo(group="rock", mining_time=60),
    world.COPPER_ORE: BlockInfo(group="ore", mining_time=90),
    world.IRON_ORE: BlockInfo(group="ore", mining_time=100),
    world.GOLD_ORE: BlockInfo(group="ore", mining_time=110),
    world.WOOD: BlockInfo(group="wood", mining_time=30),
    world.LEAVES: BlockInfo(group="leaf", mining_time=10),
    world.WATER: BlockInfo(group="liquid", mining_time=0),
}

