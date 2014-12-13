from __future__ import division
import pygame as pg
from .labels import Label
from .. import prepare


class Bet:
    def __init__(self, size, topleft, name, mult_dict):
        self.name = name
        self.multiplier_dict = mult_dict
        self.setup_highlighter(size, topleft)
        self.setup_label(name, mult_dict)
    
    def setup_label(self, text, mult_dict):
        self.font = prepare.FONTS["Saniretro"]
        font_size = 30
        spacer = 5
        text += '{}Payoff: {}'.format(' '*spacer, mult_dict)
        self.label_name = Label(self.font, font_size, text, "white", {"center": (560,22)})
        
    def setup_highlighter(self, size, topleft):
        self.highlighter = pg.Surface(size).convert()
        self.highlighter.set_alpha(128)  
        self.bettable_color = (0,180,0)
        self.unbettable_color = (180,0,0)
        self.highlighter.fill(self.bettable_color) 
        self.highlighter_rect = self.highlighter.get_rect(topleft=topleft)
        self.is_draw = False
        
    def update(self, mouse_pos):
        if self.highlighter_rect.collidepoint(mouse_pos):
            self.is_draw = True
        else:
            self.is_draw = False
            
    def draw(self, surface):
        if self.is_draw:
            surface.blit(self.highlighter, self.highlighter_rect)
            self.label_name.draw(surface)
