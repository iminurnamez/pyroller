import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, NeonButton, ButtonGroup


class StatsMenu(tools._State):
    """
    This state allows the player to choose which game's stats they
    want to view or return to the lobby.
    """
    def __init__(self):
        super(StatsMenu, self).__init__()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.title = Label(self.font, 64, "Statistics", "darkred",
                          {"midtop":(screen_rect.centerx, screen_rect.top+10)})
        self.games = ["Blackjack", "Bingo", "Craps", "Keno", "Video Poker",
                      "Pachinko"]
        self.buttons = self.make_buttons(screen_rect)
        self.use_music_handler = False

    def make_buttons(self, screen_rect):
        top = self.title.rect.bottom+50
        buttons = ButtonGroup()
        for game in self.games:
            pos = (screen_rect.centerx-(NeonButton.width//2), top)
            button = NeonButton(pos, game, self.view_game_stats, game, buttons)
            top += button.rect.height+20
        pos = (screen_rect.centerx-(NeonButton.width//2),
               screen_rect.bottom-(NeonButton.height+10))
        NeonButton(pos, "Lobby", self.back_to_lobby, None, buttons)
        return buttons

    def back_to_lobby(self, *args):
        self.done = True
        self.next = "LOBBYSCREEN"

    def view_game_stats(self, game):
        self.persist["current_game_stats"] = game
        self.next = "STATSSCREEN"
        self.done = True

    def startup(self, current_time, persistent):
        self.start_time = current_time
        self.persist = persistent
        self.player = self.persist["casino_player"]

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"
        self.buttons.get_event(event)

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        self.title.draw(surface)
        self.buttons.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.draw(surface)
