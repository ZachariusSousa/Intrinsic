class Button:
    """Simple clickable and draggable button."""

    def __init__(self, rect, data=None, draggable=False):
        import pygame
        self.rect = pygame.Rect(rect)
        self.data = data
        self.draggable = draggable
        self.dragging = False
        self._offset = (0, 0)

    def handle_event(self, event):
        import pygame
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    return "shift"
                if self.draggable:
                    self.dragging = True
                    self._offset = (self.rect.x - event.pos[0], self.rect.y - event.pos[1])
                return "click"
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.rect.topleft = (event.pos[0] + self._offset[0], event.pos[1] + self._offset[1])
            return "drag"
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return "drop"
        return None
