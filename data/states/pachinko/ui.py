import pygame
from ... import prepare

__all__ = ['TextSprite', 'Button']


class TextSprite(pygame.sprite.DirtySprite):
    def __init__(self, text, font=None, fg=None, bg=None):
        super(TextSprite, self).__init__()
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.image = None
        self._fg = fg if fg is not None else (255, 255, 255)
        self._bg = bg if bg is not None else (0, 0, 0)
        self._text = text
        self._font = font
        self.dirty = 0
        self.update_image()

    def update_image(self):
        image = self._font.render(self._text, True, self._fg, self._bg)
        self.rect.size = image.get_size()
        self.image = image.convert_alpha()
        self.dirty = 1

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.update_image()


class Button(pygame.sprite.DirtySprite):
    """Button class that responds to mouse events"""

    def __init__(self, text, rect, callback, args=None, kwargs=None):
        super(Button, self).__init__()
        self._callback = callback, args, kwargs
        self.image = None
        self.rect = pygame.Rect(rect)
        self.dirty = 1
        self.update_image()

    def update_image(self):
        """This is functional equivalent to components.labels.Button.draw"""
        border_color = pygame.Color('gray10')
        other_color = pygame.Color('gold3')
        surface = pygame.Surface(self.rect.size)
        border = pygame.Rect((0, 0), self.rect.size)
        rect = border.inflate(-16, -18).move(0, -3)
        pygame.draw.rect(surface, border_color, rect)
        pygame.draw.rect(surface, border_color, border)
        pygame.draw.rect(surface, other_color, rect, 3)
        pygame.draw.rect(surface, other_color, border, 4)
        points = [(rect.topleft, border.topleft),
                      (rect.topright, border.topright),
                      (rect.bottomleft, border.bottomleft),
                      (rect.bottomright, border.bottomright)]
        for pair in points:
            pygame.draw.line(surface, other_color, pair[0], pair[1], 2)
        self.image = surface
        self.dirty = 1

    def on_click(self, pos):
        cb, args, kwargs = self._callback
        cb(*args, **kwargs)

    def on_mouse_enter(self, pos):
        pass

    def on_mouse_leave(self, pos):
        pass