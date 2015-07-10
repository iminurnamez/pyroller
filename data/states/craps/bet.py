from __future__ import division

import pygame as pg

from data.components.labels import Label
from data import prepare


class Bet:
    def __init__(self, size, topleft, bettable, name, mult_dict, triangles=None, pos=None, size2=None):
        self.name = name
        self.multiplier_dict = mult_dict
        self.triangles = triangles
        self.alpha = 128
        self.bettable_color = (0,180,0)
        self.unbettable_color = (180,0,0)
        self.color = self.bettable_color
        self.extra_filler_pos = pos
        self.size2 = size2

        self.fillers = []
        if self.triangles:
            for triangle in self.triangles:
                self.fillers.append(self.setup_fillers(triangle))

        self.setup_highlighter(size, topleft)
        self.text = ''
        self.setup_label(name, mult_dict)
        self.bettable = bettable

    def setup_label(self, text, mult_dict):
        self.font = prepare.FONTS["Saniretro"]
        self.font_size = 30
        self.bettable_lbl_color = 'white'
        self.unbettable_lbl_color = 'red'
        self.lbl_color = self.bettable_lbl_color
        spacer = 5
        self.text += '{}Payoff: {}'.format(' '*spacer, mult_dict)
        self.update_label()

    def update_label(self):
        self.label_name = Label(self.font, self.font_size, self.text, self.lbl_color, {"bottomleft": (20, 918)})

    def setup_highlighter(self, size, topleft):
        self.highlighter = pg.Surface(size).convert()
        self.highlighter.set_alpha(self.alpha)
        self.highlighter.fill(self.color)
        self.highlighter_rect = self.highlighter.get_rect(topleft=topleft)
        self.is_draw = False

    def setup_fillers(self, points):
        image = pg.Surface(self.size2)
        if not prepare.DEBUG:
            image.set_colorkey((0,0,0))
        image.set_alpha(128)
        pg.draw.polygon(image, self.color, points,0)
        return image

    def update_highlight_color(self, point):
        if self.bettable == 'always':
            self.color = self.bettable_color
            self.lbl_color = self.bettable_lbl_color
        elif self.bettable == 'on_point':
            if point:
                self.color = self.bettable_color
                self.lbl_color = self.bettable_lbl_color
            else:
                self.color = self.unbettable_color
                self.lbl_color = self.unbettable_lbl_color
        elif self.bettable == 'off_point':
            if not point:
                self.color = self.bettable_color
                self.lbl_color = self.bettable_lbl_color
            else:
                self.color = self.unbettable_color
                self.lbl_color = self.unbettable_lbl_color
        self.highlighter.fill(self.color)
        self.update_label()

    def update(self, mouse_pos, point):
        if self.highlighter_rect.collidepoint(mouse_pos):
            self.is_draw = True
        else:
            self.is_draw = False
        self.update_highlight_color(point)


    def draw(self, surface):
        if self.is_draw:
            surface.blit(self.highlighter, self.highlighter_rect)
            self.label_name.draw(surface)
            if self.triangles and self.extra_filler_pos:
                for filler in self.fillers:
                    surface.blit(filler, self.extra_filler_pos)
