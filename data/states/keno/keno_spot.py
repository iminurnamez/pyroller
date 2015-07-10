import pygame as pg

class KenoSpot(object):
    COLORS = {
        'open': '#181818',
        'owned': '#9c8013',
        'hit': '#eedb1e',
        'miss': '#690808',
    }

    """A spot on a Keno card."""
    def __init__(self, left, top, width, height, label, img=None):
        self.rect = pg.Rect(left, top, width, height)
        label.rect.center = self.rect.center
        self.label = label
        self.color = self.COLORS['open']
        self.img = img

        self.owned = False
        self.hit   = False

    def reset(self):
        self.owned = False
        self.hit   = False
        self.update_color()

    def toggle_owned(self):
        self.owned = not self.owned
        self.update_color()

    def toggle_hit(self):
        self.hit = not self.hit
        self.update_color()

    def update_color(self):
        if self.owned:
            self.color = self.COLORS['owned']
        else:
            self.color = self.COLORS['open']

        if self.hit and self.owned:
            self.color = self.COLORS['hit']
        elif self.hit:
            self.color = self.COLORS['miss']

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)

        if self.img:
            if self.hit:
                surface.blit(self.img, self.rect)
            else:
                self.label.draw(surface)
        else:
            self.label.draw(surface)
