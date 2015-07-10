import random
from collections import OrderedDict
import pygame as pg

from data import tools, prepare
from data.components.labels import NeonButton, ButtonGroup
import data.state


class Scene(data.state.State):
    name = "Template Scene"

    def __init__(self):
        super(Scene, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.buttons = self.make_buttons(self.screen_rect)

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([("games played", 0)])
        return stats

    def make_buttons(self, screen_rect):
        buttons = ButtonGroup()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        NeonButton(pos, "Lobby", self.back_to_lobby, None,
                   buttons, bindings=[pg.K_ESCAPE])
        return buttons

    def back_to_lobby(self, *args):
        self.next = "LOBBYSCREEN"
        self.done = True

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = "template"

    def cleanup(self):
        self.done = False
        return self.persist

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.buttons.get_event(event)

    def cash_out_player(self):
        self.casino_player.stats["cash"] = self.player.get_chip_total()

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.buttons.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.draw(surface)
