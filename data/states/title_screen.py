import os
import json
import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, Blinker, MarqueeFrame, Button
from ..components.casino_player import CasinoPlayer
from ..components.cards import Deck
from ..components.music_handler import MusicHandler


class TitleScreen(tools._State):
    """Initial state of the game. Introduces the game and lets user load a
    saved game if there's one present."""

    def __init__(self):
        super(TitleScreen, self).__init__()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        font = prepare.FONTS["Saniretro"]
        self.title = Blinker(font, 128, "Py Rollers", "darkred",
                             {"midtop": (screen_rect.centerx,
                                         screen_rect.top + 50)}, 600,
                             image=prepare.GFX["pyrollers_shiny"])
        self.title2 = Blinker(font, 128, "Casino", "darkred",
                              {"midtop": (screen_rect.centerx,
                                          self.title.rect.bottom + 120)}, 600,
                              image=prepare.GFX["casino_shiny"])
        self.title.rect.left -= 1200
        self.title2.rect.left += 1600
        self.title.blinking = False
        self.title2.blinking = False
        self.title.on = True
        self.title2.on = True

        b_width = 180
        b_height = 80
        left = screen_rect.centerx - (b_width / 2)
        top = self.title2.rect.bottom + 100
        new_game = Label(font, 32, "New Game", "goldenrod3",
                                     {"center": (0, 0)})
        self.new_game_button = Button(left, top, b_width, b_height, new_game)
        self.new_game_button.active = False
        top = self.new_game_button.rect.bottom + 50
        load_game = Label(font, 32, "Load Game", "goldenrod3",
                                         {"center": (0, 0)})
        self.load_game_button = Button(left, top, b_width, b_height, load_game)
        self.load_game_button.active = False
        self.buttons = [self.new_game_button, self.load_game_button]

        try:
            with open(os.path.join("resources", "save_game.json")) as saved_file:
                stats = json.load(saved_file)
        except:
            stats = None
        self.stats = stats
        self.screen_rect = screen_rect
        self.marquees = []
        #
        # Check options to go straight to a particular game rather than showing the lobby - good for debugging
        if prepare.ARGS['straight']:
            self.persist["casino_player"] = CasinoPlayer(self.stats)
            self.next = prepare.ARGS['straight']
            self.done = True
        else:
            self.next = "LOBBYSCREEN"

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.done = True
            self.quit = True
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            self.title.rect.centerx = self.title2.rect.centerx = self.screen_rect.centerx
            if self.new_game_button.rect.collidepoint(pos):
                if self.new_game_button.active:
                    self.persist["casino_player"] = CasinoPlayer()
                    self.done = True
            elif self.load_game_button.rect.collidepoint(pos):
                if self.load_game_button.active:
                    self.persist["casino_player"] = CasinoPlayer(self.stats)
                    self.done = True

    def update(self, surface, keys, current_time, dt, scale):
        if self.title.rect.centerx < self.screen_rect.centerx:
            self.title.rect.left += 10
        if self.title2.rect.centerx > self.screen_rect.centerx:
            self.title2.rect.left -= 10
        else:
            if not self.marquees:
                for title in (self.title, self.title2):
                    self.marquees.append(MarqueeFrame(title))
                    title.blinking = True
                self.new_game_button.active = True
                if self.stats is not None:
                    self.load_game_button.active = True
        for marquee in self.marquees:
            marquee.update(dt)
        self.draw(surface, dt)

    def draw(self, surface, dt):
        surface.fill(pg.Color("gray1"))
        self.title.draw(surface, dt)
        self.title2.draw(surface, dt)
        for marquee in self.marquees:
            marquee.draw(surface)
        for button in self.buttons:
            if button.active:
                button.draw(surface)