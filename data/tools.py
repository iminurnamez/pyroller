"""
This module contains the fundamental Control class and a prototype class
for States.  Also contained here are resource loading functions.
"""

import os
import copy
import argparse
import pygame as pg


class Control(object):
    """
    Control class for entire project. Contains the game loop, and contains
    the event_loop which passes events to States as needed. Logic for flipping
    states is also found here.
    """
    def __init__(self, caption, render_size, resolutions):
        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.render_size = render_size
        self.render_surf = pg.Surface(self.render_size).convert()
        self.resolutions = resolutions
        self.set_scale()
        self.caption = caption
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = 60.0
        self.show_fps = False
        self.now = 0.0
        self.keys = pg.key.get_pressed()
        self.state_dict = {}
        self.state_name = None
        self.state = None
        self.music_handler = None

    def setup_states(self, state_dict, start_state):
        """
        Given a dictionary of States and a State to start in,
        builds the self.state_dict.
        """
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]

    def update(self, dt):
        """
        Checks if a state is done or has called for a game quit.
        State is flipped if neccessary and State.update is called.
        """
        self.screen = pg.display.get_surface()
        self.now = pg.time.get_ticks()
        if self.state.quit:
            self.done = True
        elif self.state.done:
            self.flip_state()
        self.state.update(self.render_surf,self.keys,self.now,dt,self.scale)
        if self.music_handler and self.state.use_music_handler:
            self.music_handler.update(self.scale)
            self.music_handler.draw(self.render_surf)
        if self.render_size != self.screen_rect.size:
            scale_args = (self.render_surf, self.screen_rect.size)
            scaled_surf = pg.transform.smoothscale(*scale_args)
            self.screen.blit(scaled_surf, (0, 0))
        else:
            self.screen.blit(self.render_surf, (0, 0))


    def flip_state(self):
        """
        When a State changes to done necessary startup and cleanup functions
        are called and the current State is changed.
        """
        previous,self.state_name = self.state_name, self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.now, persist)
        self.state.previous = previous

    def event_loop(self):
        """
        Process all events and pass them down to current State.
        The f5 key globally turns on/off the display of FPS in the caption
        """
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
                self.toggle_show_fps(event.key)
                if event.key == pg.K_PRINT:
                    #Print screen for full render-sized screencaps.
                    pg.image.save(self.render_surf, "screenshot.png")
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.VIDEORESIZE:
                self.on_resize(event.size)
                pg.event.clear(pg.VIDEORESIZE)
            self.state.get_event(event, self.scale)
            if self.music_handler and self.state.use_music_handler:
                self.music_handler.get_event(event, self.scale)

    def on_resize(self, size):
        """
        If the user resized the window, change to the next available
        resolution depending on if scaled up or scaled down.
        """
        res_index = self.resolutions.index(self.screen_rect.size)
        adjust = 1 if size > self.screen_rect.size else -1
        if 0 <= res_index+adjust < len(self.resolutions):
            new_size = self.resolutions[res_index+adjust]
        else:
            new_size = self.screen_rect.size
        self.screen = pg.display.set_mode(new_size, pg.RESIZABLE)
        self.screen_rect.size = new_size
        self.set_scale()

    def set_scale(self):
        """
        Reset the ratio of render size to window size.
        Used to make sure that mouse clicks are accurate on all resolutions.
        """
        w_ratio = self.render_size[0]/float(self.screen_rect.w)
        h_ratio = self.render_size[1]/float(self.screen_rect.h)
        self.scale = (w_ratio, h_ratio)

    def toggle_show_fps(self, key):
        """Press f5 to turn on/off displaying the framerate in the caption."""
        if key == pg.K_F5:
            self.show_fps = not self.show_fps
            if not self.show_fps:
                pg.display.set_caption(self.caption)

    def main(self):
        """Main loop for entire program."""
        while not self.done:
            time_delta = self.clock.tick(self.fps)
            self.event_loop()
            self.update(time_delta)
            pg.display.update()
            if self.show_fps:
                fps = self.clock.get_fps()
                with_fps = "{} - {:.2f} FPS".format(self.caption, fps)
                pg.display.set_caption(with_fps)


class _State(object):
    """
    This is a prototype class for States.  All states should inherit from it.
    No direct instances of this class should be created. get_event and update
    must be overloaded in the childclass.  startup and cleanup need to be
    overloaded when there is data that must persist between States.
    """
    def __init__(self, persistant={}):
        self.start_time = 0.0
        self.now = 0.0
        self.done = False
        self.quit = False
        self.next = None
        self.previous = None
        self.persist = persistant
        self.use_music_handler = True

    def get_event(self, event, scale=(1,1)):
        """
        Processes events that were passed from the main event loop.
        Must be overloaded in children.
        """
        pass

    def startup(self, now, persistent):
        """
        Add variables passed in persistent to the proper attributes and
        set the start time of the State to the current time.
        """
        self.persist = persistent
        self.start_time = now

    def cleanup(self):
        """
        Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        """
        self.done = False
        return self.persist

    def update(self, surface, keys, now, dt, scale):
        """Update function for state.  Must be overloaded in children."""
        pass

    def render_font(self, font, msg, color, center):
        """Return the rendered font surface and its rect centered on center."""
        msg = font.render(msg, 1, color)
        rect = msg.get_rect(center=center)
        return msg, rect


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
