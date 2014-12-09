import os
import json
import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, Button, PayloadButton


class LobbyScreen(tools._State):
    """This state represents the casino lobby where the player can choose
    which game they want to play or view their game statistics. This is also
    the exit point for the game."""
    def __init__(self):
        super(LobbyScreen, self).__init__()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.games = [("Blackjack", "BLACKJACK"), ("Craps", "CRAPS")]
        b_width = 180
        b_height = 80
        left = screen_rect.centerx - (b_width / 2)
        top = screen_rect.top + 50
        self.game_buttons = []
        for game in self.games:
            label = Label(self.font, 48, game[0], "gold3", {"center": (0, 0)})
            button = PayloadButton(left, top, b_width, b_height, label, game[1])
            self.game_buttons.append(button)
            top += button.rect.height + 20

        stats_label = Label(self.font, 48, "Stats", "gold3", {"center": (0, 0)})
        self.stats_button = Button(left,
                                                screen_rect.bottom - ((b_height + 25) * 2),
                                                b_width, b_height, stats_label)
        done_label = Label(self.font, 48, "EXIT", "gold3", {"center": (0, 0)})
        self.done_button = Button(left, screen_rect.bottom - (b_height + 20),
                                                b_width, b_height, done_label)

    def startup(self, current_time, persistent):
        self.persist = persistent

    def exit_game(self):
        with open(os.path.join("resources", "save_game.json"), "w") as f:
            json.dump(self.persist["casino_player"].stats, f)
        self.done = True
        self.quit = True

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.exit_game()
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.done_button.rect.collidepoint(pos):
                self.exit_game()
            elif self.stats_button.rect.collidepoint(pos):
                self.done = True
                self.next = "STATSMENU"
            for button in self.game_buttons:
                if button.rect.collidepoint(pos):
                    self.done = True
                    self.next = button.payload

    def update(self, surface, keys, current_time, dt, scale):
        self.draw(surface)

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        for button in self.game_buttons:
            button.draw(surface)
        self.stats_button.draw(surface)
        self.done_button.draw(surface)
