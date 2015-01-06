import pygame as pg
from ... import prepare
from ...tools import scaled_mouse_pos
from ...components.labels import Label, MultiLineLabel, Button

class AdvisorWindow(object):
    def __init__(self, center, text):
        self.font = prepare.FONTS["Saniretro"]
        self.window = pg.Rect(0, 0, 600, 600)
        self.window.center = center
        
        self.label = MultiLineLabel(self.font, 32, text, "gray20",
                                              {"center": self.window.center},
                                              char_limit=42)
        self.done_button = NeonButton((self.window.centerx - 159,
                                                        self.window.bottom - 80), "Done")
        self.done = False
        
    def update(self, mouse_pos):
        self.done_button.update(mouse_pos)
        
    def get_event(self, pos):
        if self.done_button.rect.collidepoint(pos):
            self.done = True
                
    def draw(self, surface):
        pg.draw.rect(surface, pg.Color("antiquewhite"), self.window)
        pg.draw.rect(surface, pg.Color("gray40"), self.window, 3)
        self.label.draw(surface)
        self.done_button.draw(surface)

