import pygame
from typing import List, Optional, Tuple

class InventoryUI:
    """Simple inventory and hotbar UI with drag-and-drop."""

    PADDING = 4
    INV_COLUMNS = 10
    MAX_SLOTS = 40

    def __init__(self, player, font):
        self.player = player
        self.font = font
        self.base_slot_size = 80
        self.slot_size = self.base_slot_size

        self.dragging: Optional[str] = None
        self.drag_from_hotbar: bool = False
        self.drag_index: int = -1
        self.offset = (0, 0)
        self.hotbar_rects: List[pygame.Rect] = []
        self.inv_rects: List[Tuple[str, pygame.Rect]] = []
        self.show_inventory = False

    def toggle(self) -> None:
        self.show_inventory = not self.show_inventory

    def reposition(self, width: int, height: int) -> None:
        scale = min(width / 1280, height / 960)
        self.slot_size = int(self.base_slot_size * scale)

        self.hotbar_rects = []
        hb_w = len(self.player.hotbar) * (self.slot_size + self.PADDING)
        start_x = (width - hb_w) // 2
        y = height - self.slot_size - 10
        for i in range(len(self.player.hotbar)):
            rect = pygame.Rect(start_x + i * (self.slot_size + self.PADDING), y, self.slot_size, self.slot_size)
            self.hotbar_rects.append(rect)

        self.inv_rects = []
        if self.show_inventory:
            inv_items = list(self.player.inventory.keys())
            rows = (len(inv_items) + self.INV_COLUMNS - 1) // self.INV_COLUMNS
            total_w = self.INV_COLUMNS * (self.slot_size + self.PADDING) - self.PADDING
            total_h = rows * (self.slot_size + self.PADDING) - self.PADDING
            start_x = (width - total_w) // 2
            start_y = (height - total_h) // 2

            for idx, name in enumerate(inv_items):
                col = idx % self.INV_COLUMNS
                row = idx // self.INV_COLUMNS
                x = start_x + col * (self.slot_size + self.PADDING)
                y = start_y + row * (self.slot_size + self.PADDING)
                rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                self.inv_rects.append((name, rect))

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

            # --- HOTBAR click ---
            for idx, rect in enumerate(self.hotbar_rects):
                if rect.collidepoint(pos):
                    item = self.player.hotbar[idx]
                    if item:
                        if shift_held:
                            # Move from hotbar → inventory
                            if self.player.inventory.add_item(item, 1):
                                self.player.hotbar[idx] = None
                        else:
                            self.dragging = item
                            self.drag_from_hotbar = True
                            self.drag_index = idx
                            self.offset = (pos[0] - rect.x, pos[1] - rect.y)
                            self.player.hotbar[idx] = None
                    return

            # --- INVENTORY click ---
            if self.show_inventory:
                for idx, (name, rect) in enumerate(self.inv_rects):
                    if rect.collidepoint(pos) and self.player.inventory.get(name, 0) > 0:
                        if shift_held:
                            # Move from inventory → hotbar
                            for i in range(len(self.player.hotbar)):
                                if self.player.hotbar[i] is None:
                                    self.player.hotbar[i] = name
                                    if self.player.inventory.get(name, 0) == 0:
                                        # Remove duplicates from other hotbar slots
                                        for j, slot in enumerate(self.player.hotbar):
                                            if slot == name and j != i:
                                                self.player.hotbar[j] = None
                                    return
                            # No space in hotbar
                        else:
                            self.dragging = name
                            self.drag_from_hotbar = False
                            self.drag_index = idx
                            self.offset = (pos[0] - rect.x, pos[1] - rect.y)
                        return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = event.pos
            if self.dragging:
                for idx, rect in enumerate(self.hotbar_rects):
                    if rect.collidepoint(pos):
                        self.player.hotbar[idx] = self.dragging
                        self.dragging = None
                        return
                self.dragging = None


    def draw(self, surface) -> None:
        self.reposition(surface.get_width(), surface.get_height())

        for name, rect in self.inv_rects:
            pygame.draw.rect(surface, (200, 200, 200), rect)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2)
            if self.player.inventory.get(name, 0) > 0 and name not in self.player.hotbar:
                text = self.font.render(name[:3], True, (0, 0, 0))
                surface.blit(text, (rect.x + 2, rect.y + 2))
                cnt = self.player.inventory.get(name, 0)
                cnt_surf = self.font.render(str(cnt), True, (0, 0, 0))
                surface.blit(cnt_surf, (rect.right - cnt_surf.get_width() - 2, rect.bottom - cnt_surf.get_height() - 2))

        for idx, rect in enumerate(self.hotbar_rects):
            pygame.draw.rect(surface, (180, 180, 180), rect)
            border_color = (255, 255, 0) if idx == self.player.selected_slot else (0, 0, 0)
            pygame.draw.rect(surface, border_color, rect, 2)
            item = self.player.hotbar[idx]
            if item:
                text = self.font.render(item[:3], True, (0, 0, 0))
                surface.blit(text, (rect.x + 2, rect.y + 2))
                cnt = self.player.inventory.get(item, 0)
                cnt_surf = self.font.render(str(cnt), True, (0, 0, 0))
                surface.blit(cnt_surf, (rect.right - cnt_surf.get_width() - 2, rect.bottom - cnt_surf.get_height() - 2))

        if self.dragging:
            pos = pygame.mouse.get_pos()
            rect = pygame.Rect(pos[0] - self.offset[0], pos[1] - self.offset[1], self.slot_size, self.slot_size)
            pygame.draw.rect(surface, (255, 255, 255), rect)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2)
            text = self.font.render(self.dragging[:3], True, (0, 0, 0))
            surface.blit(text, (rect.x + 2, rect.y + 2))

        if self.show_inventory:
            item_names = list(self.player.inventory.keys())
            for i in range(self.MAX_SLOTS):
                if i >= len(item_names):
                    col = i % self.INV_COLUMNS
                    row = i // self.INV_COLUMNS
                    x = (surface.get_width() - self.INV_COLUMNS * (self.slot_size + self.PADDING) + self.PADDING) // 2 + col * (self.slot_size + self.PADDING)
                    y = (surface.get_height() - ((len(item_names) + self.INV_COLUMNS - 1) // self.INV_COLUMNS) * (self.slot_size + self.PADDING) + self.PADDING) // 2 + row * (self.slot_size + self.PADDING)
                    rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                    pygame.draw.rect(surface, (200, 200, 200), rect)
                    pygame.draw.rect(surface, (0, 0, 0), rect, 2)
