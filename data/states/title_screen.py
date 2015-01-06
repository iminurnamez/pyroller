import os
import json
import pygame as pg

from .. import tools, prepare
from ..components import spotlight
from ..components.labels import ButtonGroup
from ..components.labels import Label, Blinker, MarqueeFrame, NeonButton
from ..components.casino_player import CasinoPlayer
from ..components.cards import Deck
from ..components.music_handler import MusicHandler


class TitleScreen(tools._State):
    """
    Initial state of the game. Introduces the game and lets user load a
    saved game if there's one present.
    """
    def __init__(self):
        super(TitleScreen, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.marquees = []
        self.make_titles()
        self.buttons = ButtonGroup()
        self.new_game, self.load_game = self.make_buttons()
        self.prepare_stats()
        self.lights = self.make_spotlights()
        self.check_straight_arg()

    def make_spotlights(self):
        lights = pg.sprite.LayeredDirty()
        y = self.screen_rect.bottom+20
        for i in range(1,5):
            start = 0 if i%2 else 0.5
            pos = (i*self.screen_rect.w/5, y)
            spotlight.SpotLight(pos, 4, 140, start, lights)
        return lights

    def check_straight_arg(self):
        """
        Check options to go straight to a particular game
        rather than showing the lobby - good for debugging.
        """
        if prepare.ARGS['straight']:
            self.persist["casino_player"] = CasinoPlayer(self.stats)
            self.next = prepare.ARGS['straight']
            self.done = True
        else:
            self.next = "LOBBYSCREEN"

    def prepare_stats(self):
        try:
            path = os.path.join("resources", "save_game.json")
            with open(path) as saved_file:
                stats = json.load(saved_file)
        except IOError:
            stats = None
        self.stats = stats

    def make_titles(self):
        font = prepare.FONTS["Saniretro"]
        self.title = Blinker(font, 128, "Py Rollers", "darkred",
                             {"midtop": (self.screen_rect.centerx,
                                         self.screen_rect.top + 50)}, 600,
                             image=prepare.GFX["pyrollers_shiny"])
        self.title2 = Blinker(font, 128, "Casino", "darkred",
                              {"midtop": (self.screen_rect.centerx,
                                          self.title.rect.bottom + 120)}, 600,
                              image=prepare.GFX["casino_shiny"])
        self.title.rect.left -= 1200
        self.title.true_x = self.title.rect.x
        self.title2.rect.left += 1600
        self.title2.true_x = self.title2.rect.x
        self.title.blinking = False
        self.title2.blinking = False
        self.title.on = True
        self.title2.on = True

    def make_buttons(self):
        x = self.screen_rect.centerx-(NeonButton.width//2)
        y = self.title2.rect.bottom+150
        new_game = NeonButton((x,y), "New", self.load_or_new,
                              None, self.buttons, visible=False)
        y = new_game.rect.bottom+50
        load_game = NeonButton((x,y), "Load", self.load_or_new,
                               True, self.buttons, visible=False)
        return new_game, load_game

    def load_or_new(self, payload):
        stats = self.stats if payload else None
        self.persist["casino_player"] = CasinoPlayer(stats)
        self.done = True

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.done = True
            self.quit = True
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            self.title.rect.centerx = self.screen_rect.centerx
            self.title2.rect.centerx = self.screen_rect.centerx
        self.buttons.get_event(event)

    def cleanup(self):
        spotlight.SpotLight.clear_cache() # Clear cache to reclaim memory.
        return super(TitleScreen, self).cleanup()

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        if self.title.rect.centerx < self.screen_rect.centerx:
            self.title.true_x += 0.6*dt
            self.title.rect.x = self.title.true_x
        else:
            self.title.rect.centerx = self.screen_rect.centerx
        if self.title2.rect.centerx > self.screen_rect.centerx:
            self.title2.true_x -= 0.6*dt
            self.title2.rect.x = self.title2.true_x
        else:
            self.title2.rect.centerx = self.screen_rect.centerx
            if not self.marquees:
                for title in (self.title, self.title2):
                    self.marquees.append(MarqueeFrame(title))
                    title.blinking = True
                self.new_game.visible = True
                if self.stats is not None:
                    self.load_game.visible = True
        for marquee in self.marquees:
            marquee.update(dt)
        self.lights.update(dt)
        self.draw(surface, dt)

    def draw(self, surface, dt):
        surface.fill(prepare.BACKGROUND_BASE)
        self.title.draw(surface, dt)
        self.title2.draw(surface, dt)
        for marquee in self.marquees:
            marquee.draw(surface)
        self.lights.draw(surface)
        self.buttons.draw(surface)
