"""
State controlling the credits screen of the game.
"""

import random
import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, NeonButton
from ..components.flair_pieces import Spinner, Roller, Fadeout, ChipCurtain, SlotReelTitle


SCREEN_WIDTH = prepare.RENDER_SIZE[0]

#Names of all developers to include in the credits.
DEVELOPERS = ["camarce1", "Mekire", "iminurnamez", "macaframa", "metulburr",
              "jellyberg", "PaulPaterson", "trijazzguy", "menatwrk",
              "bar777foo", "bitcraft", "net_nomad", "andarms"]
ARTISTS = ["unnamed hero/heroine"]
ASSETS_NAMES = ["opengameart.org", "freesound.org", "jazz-on-line.com", "freemusicarchive.org",
              "U.S. Army Blues", "dafont.com", "Grand Chaos Productions", "Byron Knoll", "TheCorruptor", 
              "Kenney (www.kenney.nl)"] 
SOFTWARE = ["Python", "Pygame", "Pymunk"]
              
COLORS = ["black", "blue", "green", "red", "white"]

#Default keyword arguments for the ZipperBlock class.
ZIPPER_DEFAULTS = {"off"        : 100,
                   "stagger"    : 100,
                   "speed"      : 0.3,
                   "vert_space" : 150,
                   "chip_space" : 25,
                   "font_size"  : 80}


class ZipperBlock(tools._KwargMixin):
    """
    A block of up to five label+rollers that scroll across the screen
    in alternating directions. Used for the credits screen.
    """
    def __init__(self, font, text_list, midtop, **kwargs):
        """
        Arguments are a font object; a list of strings to make labels from;
        and the midtop point of the topmost label.  A number of keyword
        arguments are accepted to further customize the appearance.
        See ZIPPER_DEFAULTS for the accepted keywords.
        """
        self.process_kwargs("ZipperBlock", ZIPPER_DEFAULTS, kwargs)
        self.stop_x, y = midtop
        self.labels, self.rollers = self.make_labels_rolls(font, text_list, y)
        top = self.labels[0].rect.top
        fade_rect = pg.Rect(300, top, 800, prepare.RENDER_SIZE[1]-top)
        self.fader = Fadeout(fade_rect, prepare.BACKGROUND_BASE)
        self.state = "Zipping"
        self.done = False

    def make_labels_rolls(self, font, text_list, y):
        """
        Create each text label and a corresponding roller.  Arguments are
        a font object; a list of strings to make labels from; and the y
        coordinate that the top label starts from.
        """
        labels = []
        rollers = pg.sprite.Group()
        for i, text in enumerate(text_list):
            if not i%2:
                pos = (-self.off, y)
                roll = Roller(pos, random.choice(COLORS), "right", self.speed)
                r = roll.rect
                label = Label(font, self.font_size, text, "goldenrod3",
                              {"midright": (r.left-self.chip_space,r.centery)})
                label.speed = self.speed
            else:
                pos = (SCREEN_WIDTH+self.off, y)
                roll = Roller(pos, random.choice(COLORS), "left", self.speed)
                r = roll.rect
                label = Label(font, self.font_size, text, "goldenrod3",
                              {"midleft": (r.right+self.chip_space,r.centery)})
                label.speed = -self.speed
            label.true_centerx = label.rect.centerx
            label.moving = True
            labels.append(label)
            rollers.add(roll)
            y += self.vert_space
        return labels, rollers

    def update_label(self, label, dt):
        """
        Update the position of a label and set label.moving to False if the
        label passes the center of the screen.
        """
        centerx = label.rect.centerx
        frame_speed = self.speed*dt
        if label.moving:
            label.true_centerx += label.speed*dt
            label.rect.centerx = label.true_centerx
        if self.stop_x-frame_speed < centerx < self.stop_x+frame_speed:
            if label.moving:
                label.rect.centerx = self.stop_x
                label.moving = False

    def update(self, dt):
        """
        Update rollers and labels.  Once the state changes to "Fading", update
        the fader.
        """
        self.rollers.update(dt)
        if self.state == "Zipping":
            for label in self.labels:
                self.update_label(label, dt)
            if not any(label.moving for label in self.labels):
                self.state = "Fading"
        elif self.state == "Fading":
            self.fader.update(dt)
            if self.fader.done:
                self.done = True

    def draw(self, surface):
        """
        Draw all labels; the fader if ready; and any rollers to the target
        surface.
        """
        for label in self.labels:
            label.draw(surface)
        if self.state == "Fading":
            self.fader.draw(surface)
        self.rollers.draw(surface)


class CreditsScreen(tools._State):
    """
    This is the main state governing the credits screen.
    """
    def __init__(self):
        super(CreditsScreen, self).__init__()
        self.screen = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.next = "LOBBYSCREEN"
        self.font = prepare.FONTS["Saniretro"]
        self.dev_names = DEVELOPERS
        self.artist_names = ARTISTS
        self.assets_names = ASSETS_NAMES
        self.software_names = SOFTWARE
        self.zipper_blocks =[]
        self.zipper_block = None
        self.chip_curtain = None
        pos = (self.screen.centerx-(NeonButton.width//2),
               self.screen.bottom-NeonButton.height-10)
        self.done_button = NeonButton(pos, "Lobby", self.back_to_lobby)
        self.use_music_handler = False

    def back_to_lobby(self, *args):
        self.done = True
        pg.mixer.stop()

    def make_groups(self, names, group_size=5):
        return [names[i:i+group_size] for i in range(0, len(names), group_size)]
        
    def make_titles_blocks(self, title_name_pairs):
        titles = []
        zipper_blocks = []
        for pair in title_name_pairs:
            title_text, names = pair
            title = SlotReelTitle((self.screen.centerx, 20), title_text, initial_move=(0, -120))
            grouped = self.make_groups(names)
            for group in grouped:
                block = ZipperBlock(self.font, group, (700, 230))
                zipper_blocks.append(block)
                titles.append(title)
        return iter(titles), iter(zipper_blocks)    
    
    def startup(self, current_time, persistent):
        """
        Prepare title, spinners, and zipper blocks.  Names are randomized each
        time so that no single dev is always first in the credits.
        """
        self.persist = persistent
        self.zipper_blocks = []
        dev_names = self.dev_names[:]
        artist_names = self.artist_names[:]
        assets_names = self.assets_names[:]
        software_names = self.software_names[:]
        for names in (dev_names, artist_names, assets_names):
            random.shuffle(names)        
        self.titles, self.zipper_blocks = self.make_titles_blocks(
                                                [("Developers", dev_names),
                                                ("Artists", artist_names),
                                                ("Assets", assets_names),
                                                ("Software", software_names)])
        self.title = next(self.titles)
        self.zipper_block = next(self.zipper_blocks)
        spots = [(self.title.rect.left-100, self.title.rect.centery),
                 (self.title.rect.right+100, self.title.rect.centery)]
        self.spinners = pg.sprite.Group()
        Spinner(spots[0], "black", self.spinners)
        Spinner(spots[1], "black", self.spinners, reverse=True)
        self.chip_curtain = None
        self.title.startup()

    def get_event(self, event, scale=(1, 1)):
        """
        Set the state to done on Xing; pressing escape; or clicking the
        lobby button.
        """
        if event.type == pg.QUIT:
            self.back_to_lobby()
        elif event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
            self.back_to_lobby()
        self.done_button.get_event(event)

    def switch_blocks(self):
        """
        Switch to the next zipper block and title.  If all blocks have been
        used, initialize the chip_curtain.
        """
        try:
            rect = self.title.rect
            self.zipper_block = next(self.zipper_blocks)
            self.title = next(self.titles)
            if self.title.rect != rect:
                rect = self.title.rect
                spots = [(rect.x-100, rect.centery),
                         (rect.right+100, rect.centery)]
                self.spinners.empty()
                Spinner(spots[0], "blue", self.spinners)
                Spinner(spots[1], "blue", self.spinners, reverse=True)
                self.title.startup()
        except StopIteration:
            self.end_titles = []
            
            
            self.zipper_block = None
            self.title = None
            self.spinners.empty()
            self.chip_curtain = ChipCurtain("chipcurtain_python",
                                    spinner_settings={"frequency" : 45,
                                                      "variable"  : False})

    def update(self, surface, keys, current_time, dt, scale):
        """Update all elements and then draw the state."""
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.done_button.update(mouse_pos)
        if self.title:
            if self.title.moving:
                for spinner in self.spinners:
                    spinner.rect.move_ip(self.title.move_speed)
            self.title.update()
            
        if self.zipper_block and self.title.spun_out:
            self.zipper_block.update(dt)
            if self.zipper_block.done:
                self.switch_blocks()
        if self.chip_curtain:
            self.chip_curtain.update(dt)
            if self.chip_curtain.done:
                self.done = True
        self.spinners.update(dt)
        self.draw(surface)

    def draw(self, surface):
        """Render all currently active elements to the target surface."""
        surface.fill(prepare.BACKGROUND_BASE)
        if self.title:
            self.title.draw(surface)
        self.spinners.draw(surface)    
        if self.zipper_block:
            self.zipper_block.draw(surface)
        if self.chip_curtain:
            self.chip_curtain.draw(surface)
        self.done_button.draw(surface)
