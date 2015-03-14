import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, GroupLabel, NeonButton, ButtonGroup


class StatsScreen(tools._State):
    """This state displays the player's statistics for a
    particular game."""
    def __init__(self):
        super(StatsScreen, self).__init__()
        self.font = prepare.FONTS["Saniretro"]
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.buttons = self.make_buttons(screen_rect)
        self.labels = []
        self.use_music_handler = False

    def make_buttons(self, screen_rect):
        buttons = ButtonGroup()
        x,y = (screen_rect.centerx-(NeonButton.width//2)-170,
               screen_rect.bottom-(NeonButton.height+10))
        NeonButton((x,y), "Lobby", self.back_to_x, "LOBBYSCREEN", buttons)
        x = screen_rect.centerx-(NeonButton.width//2)+170
        NeonButton((x,y), "Back", self.back_to_x, "STATSMENU", buttons, bindings=[pg.K_ESCAPE])
        return buttons

    def back_to_x(self, next_state):
        self.done = True
        self.next = next_state

    def startup(self, current_time, persistent):
        self.start_time = current_time
        self.persist = persistent
        screen = pg.Rect((0,0), prepare.RENDER_SIZE)
        game = self.persist["current_game_stats"]
        player_stats = self.persist["casino_player"]
        player_stats.current_game = game
        stats = player_stats.get_visible_stat_names()
        self.labels = []
        title = GroupLabel(self.labels, self.font, 64, game, "darkred",
                           {"midtop": (screen.centerx, screen.top + 10)})
        left = screen.left + 450
        right = screen.left + 950
        top = title.rect.bottom + 20
        for stat in stats:
            label = GroupLabel(self.labels, self.font, 36, stat.title(),
                               "gold3", {"topleft": (left, top)})
            label2 = GroupLabel(self.labels, self.font, 36,
                                "{}".format(player_stats.get(stat)), "gold3",
                                {"topright": (right, top)})
            top += label.rect.height + 10

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.back_to_x("LOBBYSCREEN")
        self.buttons.get_event(event)

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        for label in self.labels:
            label.draw(surface)
        self.buttons.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.draw(surface)