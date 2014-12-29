import os
import json
import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Button, PayloadButton, ImageButton
from ..components.flair_pieces import ChipCurtain
from ..components.music_handler import MusicHandler


class LobbyScreen(tools._State):
    """
    This state represents the casino lobby where the player can choose
    which game they want to play or view their game statistics. This is also
    the exit point for the game.
    """
    def __init__(self):
        super(LobbyScreen, self).__init__()
        self.music_handler = MusicHandler()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.games = [("Bingo", "BINGO"), ("Blackjack", "BLACKJACK"), ("Craps", "CRAPS"), ("Keno", "KENO")]
        num_columns = 3
        left = screen_rect.width // (num_columns + 1)
        top = screen_rect.top + 80
        self.game_buttons = []

        for game in self.games:
            icon = pg.transform.scale(prepare.GFX["screenshot_{}".format(game[0].lower())],
                                                  (280, 210))
            icon.set_colorkey(pg.Color("purple"))
            icon_rect = icon.get_rect(midtop=(left, top))
            label = Label(self.font, 48, game[0], "gold3", {"center": (0, 0)})
            button = ImageButton(icon, {"midtop": (left, top)}, label)
            button.payload = game[1]
            b = button.rect
            button.frame_rect = pg.Rect(b.topleft, (b.width, b.height + label.rect.height))
            self.game_buttons.append(button)
            left += screen_rect.width // (num_columns + 1)
            if left > screen_rect.width - 100:
                left = screen_rect.width // (num_columns + 1)
                top += label.rect.height + icon_rect.height + 50

        b_width = 300
        b_height = 80
        credits_label = Label(self.font, 48, "Credits", "gold3", {"center": (0, 0)})
        self.credits_button = Button(9, screen_rect.bottom - (b_height + 11), b_width,
                                                  b_height, credits_label)
        stats_label = Label(self.font, 48, "Stats", "gold3", {"center": (0, 0)})
        self.stats_button = Button(screen_rect.right - (b_width + 10),
                                                screen_rect.bottom - (b_height + 11),
                                                b_width, b_height, stats_label)
        done_label = Label(self.font, 48, "EXIT", "gold3", {"center": (0, 0)})
        self.done_button = Button(screen_rect.centerx - (b_width//2),
                                                screen_rect.bottom - (b_height + 11),
                                                b_width, b_height, done_label)

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.chip_curtain = ChipCurtain(None, single_color=True,
                                                      start_y=prepare.RENDER_SIZE[1] - 5,
                                                      variable_spin=False, spin_frequency=120,
                                                      scroll_speed=.8, cycle_colors=True)
        if "music_handler" not in self.persist:
            self.persist["music_handler"] = self.music_handler
        else:
            self.music_handler = self.persist["music_handler"]

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
            self.music_handler.get_event(event, scale)
            if self.done_button.rect.collidepoint(pos):
                self.exit_game()
            elif self.stats_button.rect.collidepoint(pos):
                self.done = True
                self.next = "STATSMENU"
            elif self.credits_button.rect.collidepoint(pos):
                self.done = True
                self.next = "CREDITSSCREEN"
            for button in self.game_buttons:
                if button.frame_rect.collidepoint(pos):
                    self.done = True
                    self.next = button.payload
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.exit_game()

    def update(self, surface, keys, current_time, dt, scale):
        self.chip_curtain.update(dt)
        self.music_handler.update(scale)
        self.draw(surface)

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        self.chip_curtain.draw(surface)
        for button in self.game_buttons:
            pg.draw.rect(surface, pg.Color("gray10"), button.frame_rect)
            button.draw(surface)
            pg.draw.rect(surface, pg.Color("gold3"), button.rect, 4)
            pg.draw.rect(surface, pg.Color("gold3"), button.frame_rect, 4)
        self.stats_button.draw(surface)
        self.done_button.draw(surface)
        self.credits_button.draw(surface)
        self.music_handler.draw(surface)
