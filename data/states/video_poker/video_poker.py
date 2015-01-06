import pygame as pg
from ... import tools, prepare
from ...components.labels import NeonButton
from .video_poker_machine import Machine


class VideoPoker(tools._State):
    """Class to represent a Video poker game."""
    def __init__(self):
        super(VideoPoker, self).__init__()
        w, h = prepare.RENDER_SIZE
        self.screen_rect = pg.Rect((0, 0), (w, h))
        self.font = prepare.FONTS["Saniretro"]
        self.machine = Machine((0,0), (w - 300, h))

        self.lobby_button = NeonButton((self.screen_rect.right - 330, 
                                    self.screen_rect.bottom - 120), "lobby")

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]
        self.machine.startup()

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"

        elif event.type == pg.MOUSEBUTTONDOWN:
            self.persist["music_handler"].get_event(event, scale)
            pos = tools.scaled_mouse_pos(scale, event.pos)
            event_pos = tools.scaled_mouse_pos(scale, event.pos)
            self.machine.get_event(pos)
            if self.lobby_button.rect.collidepoint(pos):
                self.done = True
                self.next = "LOBBYSCREEN"


    def update(self, surface, keys, current_time, dt, scale):
        self.machine.update(dt)
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.lobby_button.update(mouse_pos)
        self.persist["music_handler"].update(scale)
        self.draw(surface, dt)


    def draw(self, surface, dt):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(prepare.FELT_GREEN)
        self.machine.draw(surface, dt)
        self.persist["music_handler"].draw(surface)
        self.lobby_button.draw(surface)
