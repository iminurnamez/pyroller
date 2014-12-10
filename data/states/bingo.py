import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, Button


class Bingo(tools._State):
    """State to represent a bing game"""

    def __init__(self):
        """Initialise the bingo game"""
        super(Bingo, self).__init__()
        #
        self.font = prepare.FONTS["Saniretro"]
        font_size = 64
        b_width = 360
        b_height = 90
        #
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.music_icon = prepare.GFX["speaker"]
        topright = (self.screen_rect.right - 10, self.screen_rect.top + 10)
        self.music_icon_rect = self.music_icon.get_rect(topright=topright)
        self.mute_icon = prepare.GFX["mute"]
        self.play_music = True
        #
        lobby_label = Label(self.font, font_size, "Lobby", "gold3", {"center": (0, 0)})
        self.lobby_button = Button(20, self.screen_rect.bottom - (b_height + 15),
                                                 b_width, b_height, lobby_label)

    def get_event(self, event, scale=(1,1)):
        """Check for events"""
        super(Bingo, self).get_event(event, scale)
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.music_icon_rect.collidepoint(pos):
                self.play_music = not self.play_music
                if self.play_music:
                    pg.mixer.music.play(-1)
                else:
                    pg.mixer.music.stop()
            elif self.lobby_button.rect.collidepoint(pos):
                self.game_started = False
                self.done = True
                self.next = "LOBBYSCREEN"
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.done = True
                self.next = "LOBBYSCREEN"

    def update(self, surface, keys, now, dt, scale):
        """Update the main surface once per frame"""
        surface.fill((0, 255, 0))
        #
        self.lobby_button.draw(surface)
        if self.play_music:
            surface.blit(self.mute_icon, self.music_icon_rect)
        else:
            surface.blit(self.music_icon, self.music_icon_rect)