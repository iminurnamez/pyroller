import pygame as pg
from data import prepare
from data.components.advisor import Advisor
from data.components.labels import Button


class KenoAdvisor(object):

    def __init__(self):
        self.active = True
        self.group  = pg.sprite.Group()
        self.frames = pg.sprite.Group()
        self.advisor= Advisor(self.group, self.frames)
        self.advisor.active = True
        self.images = {
            'back'      : prepare.GFX["advisor_back"],
            'front'     : prepare.GFX["advisor_front"],
            'back_dim'  : prepare.GFX["advisor_back_dim"],
            'front_dim' : prepare.GFX["advisor_front_dim"],
        }
        
        self.rect   = self.get_rect()
        self.button = Button(self.rect, call=self.toggle_active)
        
        # Just testing to ensure it works...
        self.advisor.queue_text("Welcome to Keno!", dismiss_after=2500)
      
    def get_rect(self):
        return self.images['back'].get_rect().union(self.images['front'].get_rect())
        
    def toggle_active(self):
        self.active = not self.active
    
    def update(self, dt):
        if self.active:
            self.frames.update(dt)
        
    def draw(self, surface):
        if self.active:
            surface.blit(self.images['back'], (0,0))
            self.group.draw(surface)
            surface.blit(self.images['front'], (0,0))
        else:
            surface.blit(self.images['back_dim'], (0,0))
            surface.blit(self.images['front_dim'], (0,0))
