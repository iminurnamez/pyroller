import pygame as pg
from ...components.labels import Label, Button, PayloadButton, Blinker, MultiLineLabel, NeonButton
from ... import tools, prepare

class KenoSpot(object):
    COLORS = {
        'open': '#181818',
        'owned': '#9c8013',
        'hit': '#eedb1e',
        'miss': '#690808',
    }
    
    """A spot on a Keno card."""
    def __init__(self, left, top, width, height, label):
        self.rect = pg.Rect(left, top, width, height)
        label.rect.center = self.rect.center
        self.label = label
        self.color = self.COLORS['open']
        
        self.owned = False
        self.hit   = False

    def toggle_owned(self):
        self.owned = not self.owned
        self.update_color()
        
    def toggle_hit(self):
        self.hit = not self.hit
        self.update_color()
        
    def update_color(self):
        if self.owned:
            self.color = self.COLORS['owned']
        else:
            self.color = self.COLORS['open']
            
        if self.hit and self.owned:
            self.color = self.COLORS['hit']
        elif self.hit:
            self.color = self.COLORS['miss']

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)
        self.label.draw(surface)

class Keno(tools._State):
    """Class to represent a casino game."""
    def __init__(self):
        super(Keno, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.game_started = False
        self.font = prepare.FONTS["Saniretro"]

        self.mock_label = Label(self.font, 64, 'KENO [WIP]', 'gold3', {'center':(640,40)})

        b_width = 360
        b_height = 90
        side_margin = 10
        w = self.screen_rect.right - (b_width + side_margin)
        h = self.screen_rect.bottom - (b_height+15)
        self.lobby_button = NeonButton((w, h), "Lobby")
        
        self.buttons = []
        self.buttons.extend([self.lobby_button])
        
        self.spots = []
        font_size = 48
        text = "0"
        text_color = "white"
        rect_attrib = {'center':(0,0)}
        
        x_origin = 300
        x = x_origin
        y = 100
        for row in range(0,8):
            for col in range(1,11):
                text = str(col+(10*row))
                label = Label(self.font, font_size, text, text_color, rect_attrib)
                spot = KenoSpot(x, y, 64, 64, label)
                self.spots.extend([spot])
                x += 70
            y += 70
            x = x_origin
            
        #pretend picks
        self.spots[15].toggle_owned()
        self.spots[22].toggle_owned()
        self.spots[44].toggle_owned()
        self.spots[52].toggle_owned()
        self.spots[74].toggle_owned()
        self.spots[79].toggle_owned()
        
        #pretend draw
        self.spots[55].toggle_hit()
        self.spots[53].toggle_hit()
        self.spots[73].toggle_hit()
        self.spots[2].toggle_hit()
        self.spots[67].toggle_hit()
        self.spots[3].toggle_hit()
        self.spots[16].toggle_hit()
        self.spots[19].toggle_hit()
        self.spots[23].toggle_hit()
        self.spots[79].toggle_hit()
        self.spots[22].toggle_hit()
        self.spots[51].toggle_hit()
        self.spots[44].toggle_hit()
        self.spots[11].toggle_hit()
        self.spots[10].toggle_hit()
        self.spots[7].toggle_hit()
        self.spots[8].toggle_hit()
        self.spots[33].toggle_hit()
        self.spots[77].toggle_hit()
        self.spots[65].toggle_hit()

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]

        self.casino_player.stats["Keno"]["games played"] += 1

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

            if self.lobby_button.rect.collidepoint(event_pos):
                self.game_started = False
                self.done = True
                self.next = "LOBBYSCREEN"
            else:
                for spot in self.spots:
                    if spot.rect.collidepoint(event_pos):
                        spot.toggle_owned()

    def draw(self, surface):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(prepare.FELT_GREEN)
        
        self.mock_label.draw(surface)
        
        for button in self.buttons:
            button.draw(surface)
        
        for spot in self.spots:
            spot.draw(surface)
            
        self.persist["music_handler"].draw(surface)

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
        for button in self.buttons:
            button.update(mouse_pos)
        
        self.persist["music_handler"].update(scale)
        self.draw(surface)

