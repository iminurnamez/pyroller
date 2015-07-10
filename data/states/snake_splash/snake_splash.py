from random import randint

import pygame as pg

from data import prepare
import data.state


class SnakeSplash(data.state.State):
    name = "snake_splash"

    def __init__(self):
        super(SnakeSplash, self).__init__()
        self.next = "title_screen"
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.image = prepare.GFX["snakesign"]
        self.on = False
        self.duration = 3000
        self.use_music_handler = False

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.done = True
            self.quit = True
        elif event.type == pg.KEYUP:
            self.done  = True
            if event.key == pg.K_ESCAPE:
                self.quit = True
        elif event.type == pg.MOUSEBUTTONUP:
            self.done = True

    def draw(self, surface):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(prepare.BACKGROUND_BASE)
        if self.on:
            surface.blit(self.image, (175, 0))

    def update(self, surface, keys, current_time, dt, scale):
        """
        This method will be called once each frame while the state is active.
        Surface is a reference to the rendering surface which will be scaled
        to pygame's display surface, keys is the return value of the last call
        to pygame.key.get_pressed. current_time is the number of milliseconds
        since pygame was initialized. dt is the number of milliseconds since
        the last frame.
        """
        self.duration -= dt
        if self.duration <= 0:
            self.done = True
        if randint(0, 100) < 20:
            self.on = not self.on
        self.draw(surface)

