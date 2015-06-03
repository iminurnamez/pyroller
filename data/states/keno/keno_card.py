import pygame as pg
from ...components.labels import Label
from ... import prepare
from .keno_spot import KenoSpot

class KenoCard(object):
    def __init__(self, sprite_sheet=None):
        self.font = prepare.FONTS["Saniretro"]
        self.sheet = sprite_sheet
        self.spots = []
        self.current_pick = []
        self.build()

    @property
    def spot_count(self):
        count = 0
        for spot in self.spots:
            if spot.owned:
                count+=1
        return count

    @property
    def hit_count(self):
        count = 0
        for spot in self.spots:
            if spot.hit and spot.owned:
                count+=1
        return count

    def build(self):
        font_size = 48
        text = "0"
        text_color = "white"
        rect_attrib = {'center':(0,0)}

        x_origin = 336
        x = x_origin
        y = 200
        for row in range(0,8):
            for col in range(1,11):
                text = str(col+(10*row))
                label = Label(self.font, font_size, text, text_color, rect_attrib)

                if self.sheet:
                    spot = KenoSpot(x, y, 64, 64, label, self.sheet[int(text)-1])
                else:
                    spot = KenoSpot(x, y, 64, 64, label)

                self.spots.extend([spot])
                x += 70
            y += 70
            x = x_origin

    def toggle_owned(self, number):
        self.spots[number].toggle_owned()

    def toggle_hit(self, number):
        self.spots[number].toggle_hit()

    def ready_play(self, clear_all=False):
        for spot in self.spots:
            spot.hit = False
            spot.update_color()

        if clear_all:
            for spot in self.spots:
                spot.owned = False
                spot.update_color()

    def reset(self):
        for spot in self.spots:
            spot.reset()

    def update(self, mouse_pos):
        for spot in self.spots:
            if spot.rect.collidepoint(mouse_pos):
                if (self.spot_count < 10 and not spot.owned) or spot.owned:
                    spot.toggle_owned()

    def draw(self, surface):
        x_pos = 64
        y_pos = 136
        size  = 64
        for ball in self.current_pick:
            img = self.spots[ball].img
            surface.blit(img, pg.Rect(x_pos, y_pos, size, size))
            x_pos += size


        for spot in self.spots:
            spot.draw(surface)
