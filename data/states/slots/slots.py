from collections import OrderedDict

import pygame as pg

from data import tools, prepare
from data.components import advisor
from data.components.labels import NeonButton, ButtonGroup
import data.state


class Slots(data.state.State):
    show_in_lobby = True
    name = 'Slots'

    def __init__(self):
        super(Slots, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.font_size = 64
        self.buttons = self.make_buttons(self.screen_rect)
        self.bar = prepare.GFX["baccarat-menu-back"].copy()
        self.hud = pg.sprite.Group()
        self.animations = pg.sprite.Group()
        self.messager = advisor.Advisor(self.hud, self.animations)

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([('spins', 0),
                            ('total winnings', 0),
                            ('jackpots', 0),
                            ])
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
        self.casino_player.current_game = self.name
        self.messager.queue_text("Welcome to PyRamid Slots!")
        self.messager.queue_text("Let's get these slots rollin'!")

    def cleanup(self):
        self.done = False
        self.messager.empty()
        self.hud.empty()
        return self.persist

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.buttons.get_event(event)

    def cash_out_player(self):
        self.casino_player.stats["cash"] = self.player.get_chip_total()

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        surface.blit(self.bar, (0, 0))
        self.hud.draw(surface)
        self.buttons.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.animations.update(dt)
        self.draw(surface)
