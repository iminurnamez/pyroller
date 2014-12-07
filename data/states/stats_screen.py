import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, GroupLabel, Button


class StatsScreen(tools._State):
    """This state displays the player's statistics for a
    particular game."""
    def __init__(self):
        super(StatsScreen, self).__init__()
        self.font = prepare.FONTS["Saniretro"]
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        b_width = 180
        b_height = 80
        left = screen_rect.centerx - (b_width / 2)
        done_label = Label(self.font, 48, "Lobby", "gold4", {"center": (0, 0)})
        self.done_button = Button(left, screen_rect.bottom - (b_height + 10),
                                                b_width, b_height, done_label)
        self.labels = []

    def startup(self, current_time, persistent):
        self.start_time = current_time
        self.persist = persistent
        screen = pg.display.get_surface().get_rect()
        game = self.persist["current_game_stats"]
        stats = self.persist["casino_player"].stats[game]
        self.labels = []
        title = GroupLabel(self.labels, self.font, 64, game, "darkred",
                                   {"midtop": (screen.centerx, screen.top + 10)})
        left1 = screen.left + 200
        left2 = screen.left + 500
        top = title.rect.bottom + 20
        for stat in stats:
            label = GroupLabel(self.labels, self.font, 32, stat.title(), "gold3",
                                         {"topleft": (left1, top)})
            label2 = GroupLabel(self.labels, self.font, 32, "{}".format(stats[stat]),
                                           "gold3", {"topleft": (left2, top)})
            top += label.rect.height + 10


    def get_event(self, event, scale=(1,1)):
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.done_button.rect.collidepoint(pos):
                self.done = True
                self.next = "LOBBYSCREEN"

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        for label in self.labels:
            label.draw(surface)
        self.done_button.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        self.draw(surface)
