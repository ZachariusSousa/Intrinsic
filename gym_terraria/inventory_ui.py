import pygame
from typing import List, Optional, Tuple

class InventoryUI:
    """Simple inventory and hotbar UI with drag-and-drop."""

    SLOT_SIZE = 40
    PADDING = 4

    def __init__(self, player, font):
        self.player = player
        self.font = font
        self.dragging: Optional[str] = None
        self.drag_from_hotbar: bool = False
        self.drag_index: int = -1
        self.offset = (0, 0)
        self.hotbar_rects: List[pygame.Rect] = []
        self.inv_rects: List[Tuple[str, pygame.Rect]] = []
        self.show_inventory = False

    def toggle(self) -> None:
        """Toggle inventory visibility."""
        self.show_inventory = not self.show_inventory

    def reposition(self, width: int, height: int) -> None:
        """Compute slot rectangles based on screen size."""
        self.hotbar_rects = []
        hb_w = len(self.player.hotbar) * self.SLOT_SIZE
        start_x = (width - hb_w) // 2
        y = height - self.SLOT_SIZE - 10
        for i in range(len(self.player.hotbar)):
            rect = pygame.Rect(start_x + i * self.SLOT_SIZE, y, self.SLOT_SIZE, self.SLOT_SIZE)
            self.hotbar_rects.append(rect)

        self.inv_rects = []
        if self.show_inventory:
            x = (width - self.SLOT_SIZE) // 2
            y = height // 2 - (len(self.player.inventory) * self.SLOT_SIZE) // 2
            for idx, name in enumerate(self.player.inventory.keys()):
                rect = pygame.Rect(x, y + idx * self.SLOT_SIZE, self.SLOT_SIZE, self.SLOT_SIZE)
                self.inv_rects.append((name, rect))

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for idx, rect in enumerate(self.hotbar_rects):
                if rect.collidepoint(pos):
                    item = self.player.hotbar[idx]
                    if item:
                        self.dragging = item
                        self.drag_from_hotbar = True
                        self.drag_index = idx
                        self.offset = (pos[0] - rect.x, pos[1] - rect.y)
                        self.player.hotbar[idx] = None
                    return
            if self.show_inventory:
                for idx, (name, rect) in enumerate(self.inv_rects):
                    if rect.collidepoint(pos) and self.player.inventory.get(name, 0) > 0:
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
                # drop anywhere else returns item to inventory (no changes needed)
                self.dragging = None

    def draw(self, surface) -> None:
        self.reposition(surface.get_width(), surface.get_height())
        # draw inventory slots
        for name, rect in self.inv_rects:
            pygame.draw.rect(surface, (200, 200, 200), rect)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2)
            if self.player.inventory.get(name, 0) > 0:
                text = self.font.render(name[:3], True, (0, 0, 0))
                surface.blit(text, (rect.x + 2, rect.y + 2))
                cnt = self.player.inventory.get(name, 0)
                cnt_surf = self.font.render(str(cnt), True, (0, 0, 0))
                surface.blit(cnt_surf, (rect.right - cnt_surf.get_width() - 2, rect.bottom - cnt_surf.get_height() - 2))

        # draw hotbar
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
            rect = pygame.Rect(pos[0] - self.offset[0], pos[1] - self.offset[1], self.SLOT_SIZE, self.SLOT_SIZE)
            pygame.draw.rect(surface, (255, 255, 255), rect)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2)
            text = self.font.render(self.dragging[:3], True, (0, 0, 0))
            surface.blit(text, (rect.x + 2, rect.y + 2))


