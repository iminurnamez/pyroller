from random import choice
import pygame as pg
from .. import tools, prepare
from ..components.labels import Label


class MusicHandler(object):
    def __init__(self):
        songs = [("main_stem", "Main Stem - U.S. Army Blues", .2),
                      ("gospel_truth", "The Gospel Truth - U.S. Army Blues", .2),
                      ("betcha_nickel", "Betcha' Nickel - Ella Fitzgerald and Her Famous Orchestra", .2),
                      ("buckin_the_dice", "Buckin' The Dice - Fats Waller and His Rhythm", .2),
                      ("money_burns_a_hole_in_my_pocket", "Money Burns A Hole In My Pocket - Dean Martin", .2),
                      ("ace_in_the_hole", "Ace In The Hole - Ella Fitzgerald", .25),
                      ("on_the_street_where_you_live", "On The Street Where You Live - Shelly Manne & Andre Previn", .5),
                      ("world_on_a_string", "I've Got The World On A String - Frank Sinatra", .3),
                      ("im_shooting_high", "I'm Shooting High - Chris Connor", .4),
                      ("caravan", "Caravan - Thelonious Monk", .3),
                      ("anything_for_you", "Anything For You - Kay Starr with Van Alexander's Orchestra", .35)
                ]
        self.current_song = "main_stem"
        self.songs = {song[0]: (prepare.MUSIC[song[0]], song[1], song[2]) for song in songs}
        self.volume_mod = 1.0
        
        #GUI icons
        self.rect = pg.Rect(0, 1, 300, 70)
        self.rect.right = prepare.RENDER_SIZE[0]
        self.skip_icon, self.mute_icon, self.play_icon = tools.strip_from_sheet(prepare.GFX["audio_icon_strip"],
                                                                                                              (0, 0), (64, 64), 3)
        self.music_icon_rect = self.play_icon.get_rect(bottomleft=(self.rect.left + 5, self.rect.bottom))
        self.skip_rect = self.skip_icon.get_rect(bottomright=(self.rect.right - 5, self.rect.bottom))
        sheet = prepare.GFX["volumeicons"]
        self.gray_icon = prepare.GFX["volumeiconsgray"]
        self.gray_rect = self.gray_icon.get_rect(midbottom=(self.rect.centerx, self.rect.bottom))
        icons = tools.strip_from_sheet(sheet, (0, 0), (24, 27), 5)
        vol_levels = [.3, .7, 1.0, 1.5, 2.0]
        left = self.gray_rect.left
        x_space = 24
        top = self.gray_rect.top
        self.volume_icons = []
        for i, icon_level in enumerate(zip(icons, vol_levels)):
            vol_icon = VolumeIcon((left + (i * x_space), top), icon_level[0], icon_level[1])
            self.volume_icons.append(vol_icon)
        font = prepare.FONTS["Saniretro"]
        self.volume_label = Label(font, 32, "Volume", "goldenrod3",
                                              {"midtop": (self.rect.centerx, self.rect.top + 3)})
        if not prepare.ARGS['music_off']:
            self.music_on = True
        else:
            self.music_on = False

    def change_song(self, song_name=None):
        song_name = song_name if song_name else choice([s for s in self.songs])
        self.current_song = song_name
        song_info = self.songs[song_name]
        pg.mixer.music.load(song_info[0])
        pg.mixer.music.set_volume(song_info[2] * self.volume_mod)
        pg.mixer.music.play()
        pg.display.set_caption("Now Playing: {}".format(song_info[1]))
        
    def change_volume(self, volume_level):
        self.volume_mod = volume_level
        song_volume = self.songs[self.current_song][2]
        pg.mixer.music.set_volume(self.volume_mod * song_volume)
        
    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(event.pos, scale)
            
            if self.music_icon_rect.collidepoint(pos):
                self.music_on = not self.music_on
                if self.music_on:
                    pg.mixer.music.play()
                else:
                    pg.mixer.music.stop()
            if self.music_on:
                if self.skip_rect.collidepoint(pos):
                    self.change_song()
                for icon in self.volume_icons:
                    if icon.rect.collidepoint(pos):
                        self.change_volume(icon.value)                   
                    
    def update(self):
        if self.music_on:
            if not pg.mixer.music.get_busy():
                self.change_song()
                
    def draw(self, surface):
        pg.draw.rect(surface, pg.Color("gray10"), self.rect)
        pg.draw.rect(surface, pg.Color("gold3"), self.rect, 4)
        self.volume_label.draw(surface)
        if self.music_on:
            surface.blit(self.mute_icon, self.music_icon_rect)
        else:
            surface.blit(self.play_icon, self.music_icon_rect)
        surface.blit(self.skip_icon, self.skip_rect)
        surface.blit(self.gray_icon, self.gray_rect)
        
        for icon in self.volume_icons:
            if icon.value <= self.volume_mod:
                icon.draw(surface)
        
        
class VolumeIcon(object):
    def __init__(self, topleft, image, value):
        self.value = value
        self.image = image
        self.rect = self.image.get_rect(topleft=topleft)
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)