import pygame as pg
from .. import tools, prepare


class GameName(tools._State):
    """Class to represent a casino game."""
    def __init__(self):
        super(GameName, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        
    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]
        
    def get_event(self, event):
        """This method will be called for each event in the event queue 
        while the state is active.
        """
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            #use tools.scaled_mouse_pos(event.pos) for correct mouse position
            #relative to the pygame window size
            event_pos = tools.scaled_mouse_pos(event.pos)
            
    def draw(self, surface):
        """This method handles drawing/blitting the state each frame."""
        pass    
        
    def update(self, surface, keys, current_time, dt):
        """This method will be called once each frame while the state is
        active. surface is a reference to the rendering surface which will be scaled
        to pygame's display surface, keys is the return value of the last call to 
        pygame.key.get_pressed. current_time is the number of milliseconds since
        pygame was initialized. dt is the number of milliseconds since the last frame."""
        
        mouse_pos = tools.scaled_mouse_pos()
        
        self.draw(surface)
        
        