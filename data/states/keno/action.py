import pygame as pg

class Action(object):
    def __init__(self, rect, label, callback):
        self.rect = rect
        self.label = label
        self.label.rect.center = self.rect.center
        self.color = '#181818'
        self.callback = callback
        
    def execute(self, mouse_pos):
        if self.callback:
            if self.rect.collidepoint(mouse_pos):
                self.callback()
            
    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)
        self.label.draw(surface)
