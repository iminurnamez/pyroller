import pygame as pg
from ... import tools, prepare
from ...components.labels import NeonButton
from .video_poker_machine import Machine


class VideoPoker(tools._State):
    """Class to represent the Video Poker game."""
    def __init__(self):
        super(VideoPoker, self).__init__()
        w, h = prepare.RENDER_SIZE
        self.screen_rect = pg.Rect((0, 0), (w, h))
        self.machine = Machine((0, 0), (w - 300, h))
        pos = (self.screen_rect.right-330, self.screen_rect.bottom-120)
        self.lobby_button = NeonButton(pos, "lobby", self.back_to_lobby)

    def back_to_lobby(self, *args):
        self.done = True
        self.next = "LOBBYSCREEN"

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.machine.startup(self.casino_player)

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.QUIT:
            self.back_to_lobby(None)

        self.lobby_button.get_event(event)
        self.machine.get_event(event, scale)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.lobby_button.update(mouse_pos)
        self.machine.update(mouse_pos, dt)
        self.draw(surface, dt)

    def draw(self, surface, dt):
        surface.fill(prepare.FELT_GREEN)
        self.machine.draw(surface)
        self.lobby_button.draw(surface)
