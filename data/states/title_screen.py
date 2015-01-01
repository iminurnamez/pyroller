import os
import json
import pygame as pg

from .. import tools, prepare
from ..components import spotlight
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
        self.make_buttons()
        self.prepare_stats()
        self.make_spotlights()
        self.check_straight_arg()

    def make_spotlights(self):
        self.lights = []
        y = self.screen_rect.bottom+30
        fourths = [i*self.screen_rect.w/5 for i in range(1,5)]
        self.lights.append(spotlight.SpotLight((fourths[0],y), 4, 140))
        self.lights.append(spotlight.SpotLight((fourths[1],y), 4, 140, 0.5))
        self.lights.append(spotlight.SpotLight((fourths[2],y), 4, 140))
        self.lights.append(spotlight.SpotLight((fourths[3],y), 4, 140, 0.5))

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
        b_width = 318
        left = self.screen_rect.centerx-(b_width//2)
        top = self.title2.rect.bottom + 150
        self.new_game_button = NeonButton((left, top), "New")
        self.new_game_button.active = False
        top = self.new_game_button.rect.bottom + 50
        self.load_game_button = NeonButton((left, top), "Load")
        self.load_game_button.active = False
        self.buttons = [self.new_game_button, self.load_game_button]

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.done = True
            self.quit = True
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            self.title.rect.centerx = self.screen_rect.centerx
            self.title2.rect.centerx = self.screen_rect.centerx
            if self.new_game_button.rect.collidepoint(pos):
                if self.new_game_button.active:
                    self.persist["casino_player"] = CasinoPlayer()
                    self.done = True
            elif self.load_game_button.rect.collidepoint(pos):
                if self.load_game_button.active:
                    self.persist["casino_player"] = CasinoPlayer(self.stats)
                    self.done = True

    def cleanup(self):
        spotlight.SpotLight.clear_cache() # Clear cache to reclaim memory.
        return super(TitleScreen, self).cleanup()

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        for button in self.buttons:
            button.update(mouse_pos)
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
                self.new_game_button.active = True
                if self.stats is not None:
                    self.load_game_button.active = True
        for marquee in self.marquees:
            marquee.update(dt)
        for light in self.lights:
            light.update(dt)
        self.draw(surface, dt)

    def draw(self, surface, dt):
        surface.fill(prepare.BACKGROUND_BASE)
        self.title.draw(surface, dt)
        self.title2.draw(surface, dt)
        for marquee in self.marquees:
            marquee.draw(surface)
        for light in self.lights:
            light.draw(surface)
        for button in self.buttons:
            if button.active:
                button.draw(surface)
