import os
import pygame as pg
from . import tools


"""
This module initializes the display and creates dictionaries of resources.
"""

import os
import pygame as pg

from . import tools

ORIGINAL_CAPTION = "Py Roller Casino"
SCREEN_SIZE = (800, 800) #(1366, 768)
CARD_SIZE = (64, 93)
CARD_SIZE = (int(CARD_SIZE[0] * 1.5),
                       int(CARD_SIZE[1] * 1.5))
CHIP_SIZE = (32, 32)

#Pre-initialize the mixer for less delay before a sound plays
pg.mixer.pre_init(44100, -16, 1, 512)


#Initialization
pg.init()
os.environ['SDL_VIDEO_CENTERED'] = "TRUE"
pg.display.set_caption(ORIGINAL_CAPTION)
SCREEN = pg.display.set_mode(SCREEN_SIZE)
SCREEN_RECT = SCREEN.get_rect()


#Resource loading (Fonts and music just contain path names).
FONTS = tools.load_all_fonts(os.path.join("resources", "fonts"))
MUSIC = tools.load_all_music(os.path.join("resources", "music"))
SFX   = tools.load_all_sfx(os.path.join("resources", "sound"))
GFX   = tools.load_all_gfx(os.path.join("resources", "graphics"))

#It's time to start the music, it's time to light the lights
pg.mixer.music.load(MUSIC["main_stem"])
pg.mixer.music.set_volume(.2)
pg.mixer.music.play(-1)