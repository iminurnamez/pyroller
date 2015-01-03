import pygame

__all__ = ['TextSprite']


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