"""
Contained here are resource loading functions.
"""

import os
import copy
import argparse

import pygame as pg


class _KwargMixin(object):
    """
    Useful for classes that require a lot of keyword arguments for
    customization.
    """
    def process_kwargs(self, name, defaults, kwargs):
        """
        Arguments are a name string (displayed in case of invalid keyword);
        a dictionary of default values for all valid keywords;
        and the kwarg dict.
        """
        settings = copy.deepcopy(defaults)
        for kwarg in kwargs:
            if kwarg in settings:
                if isinstance(kwargs[kwarg], dict):
                    settings[kwarg].update(kwargs[kwarg])
                else:
                    settings[kwarg] = kwargs[kwarg]
            else:
                message = "{} has no keyword: {}"
                raise AttributeError(message.format(name, kwarg))
        for setting in settings:
            setattr(self, setting, settings[setting])


### Mouse position functions
def scaled_mouse_pos(scale, pos=None):
    """
    Return the mouse position adjusted for screen size if no pos argument is
    passed and returns pos adjusted for screen size if pos is passed.
    """
    x,y = pg.mouse.get_pos() if pos is None else pos
    return (int(x*scale[0]), int(y*scale[1]))


### Resource loading functions.
def load_all_gfx(directory,colorkey=(0,0,0),accept=(".png",".jpg",".bmp")):
    """
    Load all graphics with extensions in the accept argument.  If alpha
    transparency is found in the image the image will be converted using
    convert_alpha().  If no alpha transparency is detected image will be
    converted using convert() and colorkey will be set to colorkey.
    """
    graphics = {}
    for pic in os.listdir(directory):
        name,ext = os.path.splitext(pic)
        if ext.lower() in accept:
            img = pg.image.load(os.path.join(directory, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            graphics[name]=img
    return graphics


def load_all_music(directory, accept=(".wav", ".mp3", ".ogg", ".mdi")):
    """
    Create a dictionary of paths to music files in given directory
    if their extensions are in accept.
    """
    songs = {}
    for song in os.listdir(directory):
        name,ext = os.path.splitext(song)
        if ext.lower() in accept:
            songs[name] = os.path.join(directory, song)
    return songs


def load_all_fonts(directory, accept=(".ttf",)):
    """
    Create a dictionary of paths to font files in given directory
    if their extensions are in accept.
    """
    return load_all_music(directory, accept)


def load_all_movies(directory, accept=(".mpg",)):
    """
    Create a dictionary of paths to movie files in given directory
    if their extensions are in accept.
    """
    return load_all_music(directory, accept)


def load_all_sfx(directory, accept=(".wav", ".mp3", ".ogg", ".mdi")):
    """
    Load all sfx of extensions found in accept.  Unfortunately it is
    common to need to set sfx volume on a one-by-one basis.  This must be done
    manually if necessary in the setup module.
    """
    effects = {}
    for fx in os.listdir(directory):
        name,ext = os.path.splitext(fx)
        if ext.lower() in accept:
            effects[name] = pg.mixer.Sound(os.path.join(directory, fx))
    return effects


def strip_from_sheet(sheet, start, size, columns, rows=1):
    """
    Strips individual frames from a sprite sheet given a start location,
    sprite size, and number of columns and rows.
    """
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pg.Rect(location, size)))
    return frames


def strip_coords_from_sheet(sheet, coords, size):
    """Strip specific coordinates from a sprite sheet."""
    frames = []
    for coord in coords:
        location = (coord[0]*size[0], coord[1]*size[1])
        frames.append(sheet.subsurface(pg.Rect(location, size)))
    return frames


def get_cell_coordinates(rect, point, size):
    """Find the cell of size, within rect, that point occupies."""
    cell = [None, None]
    point = (point[0]-rect.x, point[1]-rect.y)
    cell[0] = (point[0]//size[0])*size[0]
    cell[1] = (point[1]//size[1])*size[1]
    return tuple(cell)


def cursor_from_image(image):
    """Take a valid image and create a mouse cursor."""
    colors = {(0,0,0,255) : "X",
              (255,255,255,255) : "."}
    rect = image.get_rect()
    icon_string = []
    for j in range(rect.height):
        this_row = []
        for i in range(rect.width):
            pixel = tuple(image.get_at((i,j)))
            this_row.append(colors.get(pixel, " "))
        icon_string.append("".join(this_row))
    return icon_string


def get_cli_args(caption, win_pos, start_size, money):
    """
    Modify prepare module globals based on command line arguments,
    quickly force settings for debugging.
    """
    parser = argparse.ArgumentParser(description='{} Arguments'.format(caption))
    parser.add_argument('-c','--center', action='store_false',
        help='position starting window at (0,0), sets SDL_VIDEO_CENTERED to false')
    parser.add_argument('-w','--winpos', nargs=2, default=win_pos, metavar=('X', 'Y'),
        help='position starting window at (X,Y), default is (0,0)')
    parser.add_argument('-s' , '--size', nargs=2, default=start_size, metavar=('WIDTH', 'HEIGHT'),
        help='set window size to WIDTH HEIGHT, defualt is {}'.format(start_size))
    parser.add_argument('-f' , '--fullscreen', action='store_true',
        help='start in fullscreen')
    parser.add_argument('-m' , '--music_off', action='store_true',
        help='start with no music')
    parser.add_argument('-S', '--straight', action='store', type=str,
        help='go straight to the named game')
    parser.add_argument('-M', '--money', default=money, metavar='VALUE',
        help='set money to value')
    parser.add_argument('-d', '--debug', action='store_true',
        help='run game in debug mode')
    parser.add_argument('-F', '--FPS', action='store_true',
        help='show FPS in title bar')
    parser.add_argument('-p', '--profile', action='store_true',
        help='run game with profiling')
    parser.add_argument('-B', '--bots', action='store_true',
        help='enable test bots')
    parser.add_argument('-N', '--iterations', action='store', type=int,
        help='maximum number of iterations to run for (useful with profiling option')
    args = vars(parser.parse_args())
    #check each condition
    if not args['center'] or (args['winpos'] != win_pos): #if -c or -w options
        args['center'] = False
    if args['size'] != start_size: # if screen size is different
        args['resizable'] = False
    if args['fullscreen']:
        args['center'] = False
        args['resizable'] = False
    return args
