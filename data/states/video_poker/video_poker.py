import pygame as pg
from ... import tools, prepare
from ...components.labels import NeonButton
from .video_poker_machine import Machine


class VideoPoker(tools._State):
    """Class to represent a casino game."""
    def __init__(self):
        super(VideoPoker, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.machine = Machine((0,0), prepare.RENDER_SIZE)

        # self.loby_button = NeonButton('lobby')

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]

    def get_event(self, event, scale=(1,1)):
        """This method will be called for each event in the event queue
        while the state is active.
        """
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            #Use tools.scaled_mouse_pos(scale, event.pos) for correct mouse
            #position relative to the pygame window size.
            event_pos = tools.scaled_mouse_pos(scale, event.pos)
            self.persist["music_handler"].get_event(event, scale)


    def update(self, surface, keys, current_time, dt, scale):
        """
        This method will be called once each frame while the state is active.
        Surface is a reference to the rendering surface which will be scaled
        to pygame's display surface, keys is the return value of the last call
        to pygame.key.get_pressed. current_time is the number of milliseconds
        since pygame was initialized. dt is the number of milliseconds since
        the last frame.
        """
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.persist["music_handler"].update(scale)
        self.draw(surface, dt)


    def draw(self, surface, dt):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(prepare.FELT_GREEN)
        self.machine.draw(surface)
