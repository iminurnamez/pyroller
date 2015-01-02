import pygame as pg
from ... import tools
from .playfield import Playfield


class Pachinko(tools._State):
    """Pachinko game."""

    def startup(self, now, persistent):
        self.playfield = Playfield()

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.playfield.depress_plunger()

        elif event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                self.playfield.release_plunger()

    def update(self, surface, keys, current_time, dt, scale):
        self.playfield.update(surface, dt)
