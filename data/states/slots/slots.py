import random
import pygame as pg
from ... import tools, prepare
from ...components.labels import NeonButton, ButtonGroup


class Slots(tools._State):
    def __init__(self):
        super(Slots, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.font_size = 64
        self.buttons = self.make_buttons(self.screen_rect)

    def make_buttons(self, screen_rect):
        buttons = ButtonGroup()
        y = screen_rect.bottom-NeonButton.height-10
        lobby = NeonButton((20,y), "Lobby", self.back_to_lobby, None, buttons)
        return buttons

    def back_to_lobby(self, *args):
        self.next = "LOBBYSCREEN"
        self.done = True

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = "Slots"

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.buttons.get_event(event)

    def cash_out_player(self):
        self.casino_player.stats["cash"] = self.player.get_chip_total()

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        self.buttons.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.draw(surface)
