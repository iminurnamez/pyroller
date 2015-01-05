import pygame as pg
from .. import prepare, tools
from .labels import MultiLineLabel, NeonButton


class WarningWindow(object):
    """A popup window to confirm a player's action. The callback function
    will be called if the user clicks on the "OK" button."""
    def __init__(self, center, text, callback):
        font = prepare.FONTS["Saniretro"]
        self.window = prepare.GFX["warning_window"]
        self.rect = self.window.get_rect(center=center)
        self.label = MultiLineLabel(font, 48, text, "gold3",
                                    {"midtop": (self.rect.centerx, self.rect.top + 50)},
                                    char_limit=36, align="center")
        x = 24                          
        self.ok = NeonButton((self.rect.left + x, self.rect.bottom - (101 + x)), "Exit")
        self.cancel = NeonButton((self.rect.right - (318 + x), self.rect.bottom - (101 + x)), "Back")
        self.done = False
        self.callback = callback
        
    def get_event(self, event, scale):
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(event.pos, scale)
            if self.ok.rect.collidepoint(pos):
                self.done = True
                self.callback()
            elif self.cancel.rect.collidepoint(pos):
                self.done = True
                
    def update(self, mouse_pos):
        self.ok.update(mouse_pos)
        self.cancel.update(mouse_pos)
            
    def draw(self, surface):
        surface.blit(self.window, self.rect)
        self.label.draw(surface)
        self.ok.draw(surface)
        self.cancel.draw(surface)