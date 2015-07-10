import pygame as pg

from data import tools, prepare
from data.components.labels import Label, NeonButton, ButtonGroup
import data.state


class StatsMenu(data.state.State):
    """
    This state allows the player to choose which game's stats they
    want to view or return to the lobby.
    """
    name = "stats_menu"

    def __init__(self):
        super(StatsMenu, self).__init__()
        self.font = prepare.FONTS["Saniretro"]
        self.title = None
        self.buttons = ButtonGroup()
        self.labels = []
        self.lines = []
        self.use_music_handler = False

    def collect_games_with_stats(self):
        for name, scene in self.controller.query_all_states().items():
            if hasattr(scene, 'initialize_stats'):
                yield name

    def make_labels(self):
        self.labels = []
        cash = self.player.cash
        balance = self.player.account_balance
        assets = cash + balance
        starting_cash = prepare.MONEY
        profit = assets - starting_cash
        label_info = [("Cash", cash, 110),
                      ("Account", balance, 150),
                      ("Assets", assets, 198),
                      ("Starting Cash", -starting_cash, 238),
                      ("Profit", profit, 283)]
        left = 500
        right = 900
        for name, value, topy in label_info:
            label1 = Label(self.font, 36, name, "white",
                                  {"topleft": (left, topy)})
            color = "darkgreen" if value >= 0 else "darkred"
            label2 = Label(self.font, 36, "{:.2f}".format(value),
                                  color, {"topright": (right, topy)})
            self.labels.extend([label1, label2])
        self.lines = [((left, 193), (right, 193)),
                          ((left, 280), (right, 280))]

    def make_buttons(self, games, screen_rect, col=2):
        spacer_x = 20
        spacer_y = 20
        start_y = 410
        start_x = (screen_rect.w-NeonButton.width*col-spacer_x*(col-1))//2
        buttons = ButtonGroup()
        for i,game in enumerate(games):
            y,x = divmod(i, col)
            pos = (start_x+x*(NeonButton.width+spacer_x),
                   start_y+y*(NeonButton.height+spacer_y))
            button = NeonButton(pos, game, self.view_game_stats, game, buttons)
        pos = (screen_rect.centerx-(NeonButton.width//2),
               screen_rect.bottom-(NeonButton.height+10))
        NeonButton(pos, "Lobby", self.back_to_lobby, None, buttons,
                   bindings=[pg.K_ESCAPE])
        return buttons

    def back_to_lobby(self, *args):
        self.done = True
        self.next = "lobby"

    def view_game_stats(self, game):
        self.persist["current_game_stats"] = game
        self.next = "stats_screen"
        self.done = True

    def startup(self, current_time, persistent):
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.title = Label(self.font, 64, "Statistics", "darkred",
                          {"midtop":(screen_rect.centerx, screen_rect.top+10)})
        self.start_time = current_time
        self.persist = persistent
        self.player = self.persist["casino_player"]
        games = self.collect_games_with_stats()
        self.buttons = self.make_buttons(games, screen_rect, 3)
        self.make_labels()

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.done = True
            self.next = "lobby"
        self.buttons.get_event(event)

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        self.title.draw(surface)
        self.buttons.draw(surface)
        for label in self.labels:
            label.draw(surface)
        for line in self.lines:
            pg.draw.line(surface, pg.Color("white"), *line)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.draw(surface)
