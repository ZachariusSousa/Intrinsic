from dataclasses import dataclass
from typing import Dict, Optional
import json
import os

from . import world

@dataclass
class ItemInfo:
    """Metadata for an item."""
    category: str
    group: str = ""
    mining_time: int = 0
    block_id: Optional[int] = None
    damage: int = 0
    color: Optional[list[int]] = None

# Load item definitions from items.json
_items_path = os.path.join(os.path.dirname(__file__), "items.json")
with open(_items_path, "r") as f:
    _RAW_ITEMS = json.load(f)

ITEM_STATS: Dict[str, ItemInfo] = {}
ITEM_TO_BLOCK: Dict[str, int] = {}
BLOCK_TO_ITEM: Dict[int, str] = {}
BLOCK_STATS: Dict[int, ItemInfo] = {}

def export_block_constants():
    return {name.upper(): block_id for name, block_id in ITEM_TO_BLOCK.items()}

for name, data in _RAW_ITEMS.items():
    info = ItemInfo(**data)
    ITEM_STATS[name] = info
    if info.block_id is not None:
        ITEM_TO_BLOCK[name] = info.block_id
        BLOCK_TO_ITEM[info.block_id] = name
        BLOCK_STATS[info.block_id] = info

COLOR_MAP: Dict[int, tuple[int, int, int]] = {
    info.block_id: tuple(info.color)
    for info in ITEM_STATS.values()
    if info.block_id is not None and info.color is not None
}

ORE_TYPES: list[int] = [
    info.block_id for info in ITEM_STATS.values()
    if info.group == "ore" and info.block_id is not None
]


