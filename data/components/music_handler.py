from random import choice

import pygame as pg
from .. import tools, prepare
from ..components.labels import Label


SONGS = [
    ("main_stem", "Main Stem - U.S. Army Blues", 0.2),
    ("gospel_truth", "The Gospel Truth - U.S. Army Blues", 0.2),
    ("betcha_nickel",
        "Betcha' Nickel - Ella Fitzgerald and Her Famous Orchestra", 0.2),
    ("buckin_the_dice", "Buckin' The Dice - Fats Waller and His Rhythm", 0.2),
    ("money_burns_a_hole_in_my_pocket",
        "Money Burns A Hole In My Pocket - Dean Martin", 0.2),
    ("ace_in_the_hole", "Ace In The Hole - Ella Fitzgerald", 0.25),
    ("world_on_a_string",
        "I've Got The World On A String - Frank Sinatra", 0.3),
    ("im_shooting_high", "I'm Shooting High - Chris Connor", 0.5),
    ("anything_for_you", ("Anything For You - "
        "Kay Starr with Van Alexander's Orchestra"), 0.35)
    ]


class MusicHandler(object):
    def __init__(self):
        self.current_song = "main_stem"
        self.song_index = 0
        self.songs = {s[0]: (prepare.MUSIC[s[0]], s[1], s[2]) for s in SONGS}
        self.volume_mod = 1.0
        self.prep_icons()
        self.skip_hl_on = False
        self.mute_hl_on = False
        font = prepare.FONTS["Saniretro"]
        self.volume_label = Label(font, 32, "Volume", "goldenrod3",
                                 {"midtop": (self.rect.centerx,self.rect.y+3)})
        self.music_on = not prepare.ARGS['music_off']

    def prep_icons(self):
        """
        Strip needed icons off needed sheets and place them in data
        structures as needed.
        """
        icon_sheet = prepare.GFX["audio_icon_strip"]
        volume_sheet = prepare.GFX["volumeicons"]
        self.rect = pg.Rect(0, 1, 300, 70)
        self.rect.right = prepare.RENDER_SIZE[0]
        icons = tools.strip_from_sheet(icon_sheet, (0, 0), (64, 64), 3)
        self.skip_icon, self.mute_icon, self.play_icon = icons
        self.music_icon_rect = self.play_icon.get_rect()
        self.music_icon_rect.bottomleft = (self.rect.x+5, self.rect.bottom)
        hl_icons = tools.strip_from_sheet(icon_sheet, (0, 64), (64, 64), 3)
        self.skip_hl, self.mute_hl, self.play_hl = hl_icons
        self.skip_rect = self.skip_icon.get_rect()
        self.skip_rect.bottomright = (self.rect.right-5, self.rect.bottom)
        self.gray_icon = prepare.GFX["volumeiconsgray"]
        self.gray_rect = self.gray_icon.get_rect()
        self.gray_rect.midbottom=(self.rect.centerx, self.rect.bottom)
        volume_icons = tools.strip_from_sheet(volume_sheet, (0,0), (24,27), 5)
        vol_levels = [0.3, 0.7, 1.0, 1.5, 2.0]
        left = self.gray_rect.left
        x_space = 24
        top = self.gray_rect.top
        self.volume_icons = []
        for i, icon_level in enumerate(zip(volume_icons, vol_levels)):
            vol_icon = VolumeIcon((left+(i*x_space),top),
                                  icon_level[0], icon_level[1])
            self.volume_icons.append(vol_icon)

    def change_song(self, song_name=None):
        """
        Change to a song given by song_name or change to the next song
        if song_name is None.
        """
        if song_name:
            for i,song in enumerate(SONGS):
                if song_name == song[0]:
                    self.song_index = i
                    break
        else:
            self.song_index = (self.song_index+1)%len(SONGS)
        self.current_song = SONGS[self.song_index][0]
        song_info = self.songs[self.current_song]
        pg.mixer.music.load(song_info[0])
        pg.mixer.music.set_volume(song_info[2] * self.volume_mod)
        pg.mixer.music.play()
        caption = "{} - Now Playing: {}".format(prepare.CAPTION, song_info[1])
        pg.display.set_caption(caption)

    def change_volume(self, volume_level):
        self.volume_mod = volume_level
        song_volume = self.songs[self.current_song][2]
        pg.mixer.music.set_volume(self.volume_mod*song_volume)

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(event.pos, scale)
            if self.music_icon_rect.collidepoint(pos):
                self.mute_unmute_music()
            if self.music_on:
                if self.skip_rect.collidepoint(pos):
                    self.change_song()
                for icon in self.volume_icons:
                    if icon.rect.collidepoint(pos):
                        self.change_volume(icon.value)

    def mute_unmute_music(self):
        self.music_on = not self.music_on
        if self.music_on:
            pg.mixer.music.play()
        else:
            pg.mixer.music.stop()

    def update(self, scale):
        pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        self.mute_hl_on = self.music_icon_rect.collidepoint(pos)
        self.skip_hl_on = self.skip_rect.collidepoint(pos)
        if self.music_on:
            if not pg.mixer.music.get_busy():
                self.change_song()

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color("gray10"), self.rect)
        pg.draw.rect(surface, pg.Color("gold3"), self.rect, 4)
        self.volume_label.draw(surface)
        if self.music_on:
            if self.mute_hl_on:
                surface.blit(self.mute_hl, self.music_icon_rect)
            else:
                surface.blit(self.mute_icon, self.music_icon_rect)
        else:
            if self.mute_hl_on:
                surface.blit(self.play_hl, self.music_icon_rect)
            else:
                surface.blit(self.play_icon, self.music_icon_rect)
        if self.skip_hl_on:
            surface.blit(self.skip_hl, self.skip_rect)
        else:
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
