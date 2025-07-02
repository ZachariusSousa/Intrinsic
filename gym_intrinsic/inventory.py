from collections import OrderedDict

class Inventory(OrderedDict):
    """Dictionary-like inventory with a fixed number of slots."""

    def __init__(self, max_slots: int):
        super().__init__()
        self.max_slots = max_slots

    def add_item(self, name: str, amount: int = 1) -> bool:
        """Add an item if space permits. Returns True on success."""
        if name in self:
            super().__setitem__(name, self[name] + amount)
            return True
        if len(self) >= self.max_slots:
            return False
        super().__setitem__(name, amount)
        return True

    def __setitem__(self, key: str, value: int) -> None:
        if value <= 0:
            if key in self:
                super().__delitem__(key)
        else:
            super().__setitem__(key, value)
