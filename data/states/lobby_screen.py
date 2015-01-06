import os
import json
import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, ImageButton, NeonButton, ButtonGroup
from ..components.flair_pieces import ChipCurtain
from ..components.music_handler import MusicHandler


CURTAIN_SETTINGS = {"single_color" : True,
                    "start_y" : prepare.RENDER_SIZE[1]-5,
                    "scroll_speed" : 0.05,
                    "cycle_colors" : True,
                    "spinner_settings" : {"variable" : False,
                                          "frequency" : 120}}


class LobbyScreen(tools._State):
    """
    This state represents the casino lobby where the player can choose
    which game they want to play or view their game statistics. This is also
    the exit point for the game.
    """
    def __init__(self):
        super(LobbyScreen, self).__init__()
        self.persist["music_handler"] = MusicHandler()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.games = [("Bingo", "BINGO"), ("Blackjack", "BLACKJACK"),
                      ("Craps", "CRAPS"), ("Keno", "KENO"),
                      ("video_poker", "VIDEOPOKER"), ("Pachinko", "PACHINKO")]
        self.game_buttons = self.make_game_buttons(screen_rect)
        self.navigation_buttons = self.make_navigation_buttons(screen_rect)
        self.chip_curtain = None #Created on startup.

    def make_game_buttons(self, screen_rect):
        num_columns = 3
        left = screen_rect.width // (num_columns + 1)
        top = screen_rect.top + 80
        game_buttons = []
        for game in self.games:
            icon_raw = prepare.GFX["screenshot_{}".format(game[0].lower())]
            icon = pg.transform.scale(icon_raw, (280, 210)).convert_alpha()
            icon_rect = icon.get_rect(midtop=(left, top))
            label = Label(self.font, 48, game[0], "gold3", {"center": (0, 0)})
            button = ImageButton(icon, {"midtop": (left, top)}, label)
            button.payload = game[1]
            b = button.rect
            button.frame_rect = pg.Rect(b.topleft,
                                       (b.width,b.height+label.rect.height))
            game_buttons.append(button)
            left += screen_rect.width // (num_columns + 1)
            if left > screen_rect.width - 100:
                left = screen_rect.width // (num_columns + 1)
                top += label.rect.height + icon_rect.height + 50
        return game_buttons

    def make_navigation_buttons(self, screen_rect):
        buttons = ButtonGroup()
        pos = (9, screen_rect.bottom-(NeonButton.height+11))
        NeonButton(pos, "Credits", self.change_state, "CREDITSSCREEN", buttons)
        pos = (screen_rect.right-(NeonButton.width+10),
               screen_rect.bottom-(NeonButton.height+11))
        NeonButton(pos, "Stats", self.change_state, "STATSMENU", buttons)
        pos = (screen_rect.centerx-(NeonButton.width//2),
               screen_rect.bottom-(NeonButton.height+11))
        NeonButton(pos, "Exit", self.exit_game, None, buttons)
        return buttons

    def startup(self, current_time, persistent):
        self.persist = persistent
        if not self.chip_curtain:
            self.chip_curtain = ChipCurtain(None, **CURTAIN_SETTINGS)

    def exit_game(self, *args):
        with open(os.path.join("resources", "save_game.json"), "w") as f:
            json.dump(self.persist["casino_player"].stats, f)
        self.done = True
        self.quit = True

    def change_state(self, next_state):
        self.done = True
        self.next = next_state

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.exit_game()
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            self.persist["music_handler"].get_event(event, scale)
            for button in self.game_buttons:
                if button.frame_rect.collidepoint(pos):
                    self.done = True
                    self.next = button.payload
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.exit_game()
        self.navigation_buttons.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.chip_curtain.update(dt)
        self.persist["music_handler"].update(scale)
        self.navigation_buttons.update(mouse_pos)
        self.draw(surface)

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        self.chip_curtain.draw(surface)
        for button in self.game_buttons:
            pg.draw.rect(surface, pg.Color("gray10"), button.frame_rect)
            button.draw(surface)
            pg.draw.rect(surface, pg.Color("gold3"), button.rect, 4)
            pg.draw.rect(surface, pg.Color("gold3"), button.frame_rect, 4)
        self.navigation_buttons.draw(surface)
        self.persist["music_handler"].draw(surface)
