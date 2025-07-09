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

        # Automatically add to hotbar if there's space and it's not already there
        if hasattr(self, "player"):  # ensure player is bound
            if name not in self.player.hotbar:
                for i in range(len(self.player.hotbar)):
                    if self.player.hotbar[i] is None:
                        self.player.hotbar[i] = name
                        break

        return True


    def __setitem__(self, key: str, value: int) -> None:
        if value <= 0:
            if key in self:
                super().__delitem__(key)
        else:
            super().__setitem__(key, value)
