class Inventory:
    """Manage player inventory and hotbar."""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self._items = {
            "dirt": 10,
            "stone": 0,
            "copper": 0,
            "iron": 0,
            "gold": 0,
            "wood": 0,
            "food": 0,
        }
        self.hotbar = [
            "dirt",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
        self.selected_slot = 0

    # dictionary-like access
    def __getitem__(self, key):
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value

    def get(self, key, default=None):
        return self._items.get(key, default)

    def items(self):
        return self._items.items()

    def add(self, item: str, count: int = 1) -> None:
        self._items[item] = self._items.get(item, 0) + count

    def remove(self, item: str, count: int = 1) -> bool:
        if self._items.get(item, 0) < count:
            return False
        self._items[item] -= count
        return True

    @property
    def selected_item(self):
        return self.hotbar[self.selected_slot]

    def shift_to_hotbar(self, item: str) -> None:
        if self.get(item, 0) <= 0:
            return
        for i, slot in enumerate(self.hotbar):
            if slot is None:
                self.hotbar[i] = item
                return

    def remove_from_hotbar(self, index: int) -> None:
        """Clear the hotbar slot at the given index."""
        if 0 <= index < len(self.hotbar):
            self.hotbar[index] = None

    def swap_hotbar_slots(self, i: int, j: int) -> None:
        """Swap two hotbar slots."""
        if 0 <= i < len(self.hotbar) and 0 <= j < len(self.hotbar):
            self.hotbar[i], self.hotbar[j] = self.hotbar[j], self.hotbar[i]
