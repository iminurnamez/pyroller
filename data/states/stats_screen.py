import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, GroupLabel, Button, NeonButton


class StatsScreen(tools._State):
    """This state displays the player's statistics for a
    particular game."""
    def __init__(self):
        super(StatsScreen, self).__init__()
        self.font = prepare.FONTS["Saniretro"]
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        b_width = 318
        b_height = 101
        self.done_button = NeonButton((screen_rect.centerx-(b_width//2),
                                      screen_rect.bottom - (b_height + 10)),
                                      "Lobby")
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
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.done_button.rect.collidepoint(pos):
                self.done = True
                self.next = "LOBBYSCREEN"

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        for label in self.labels:
            label.draw(surface)
        self.done_button.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.done_button.update(mouse_pos)
        self.draw(surface)
