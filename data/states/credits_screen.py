import random
import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, NeonButton
from ..components.flair_pieces import Spinner, Roller, Fadeout, ChipCurtain



SCREEN_WIDTH = prepare.RENDER_SIZE[0]

DEVELOPERS = ["camarce1", "Mekire", "iminurnamez", "macaframa", "metulburr",
              "jellyberg", "PaulPaterson", "trijazzguy", "menatwrk",
              "bar777foo", "bitcraft", "net_nomad"]

COLORS = ["black", "blue", "green", "red", "white"]

ZIPPER_DEFAULTS = {"off"        : 100,
                   "stagger"    : 100,
                   "speed"      : 5,
                   "vert_space" : 150,
                   "chip_space" : 25,
                   "font_size"  : 80}


class ZipperBlock(tools._KwargMixin):
    def __init__(self, font, text_list, midtop, **kwargs):
        self.process_kwargs("ZipperBlock", ZIPPER_DEFAULTS, kwargs)
        self.stop_x, y = midtop
        self.labels, self.rollers = self.make_labels_rolls(font, text_list, y)
        top = self.labels[0].rect.top
        fade_rect = pg.Rect(300, top, 800, prepare.RENDER_SIZE[1]-top)
        self.fader = Fadeout(fade_rect, prepare.BACKGROUND_BASE)
        self.state = "Zipping"
        self.done = False

    def make_labels_rolls(self, font, text_list, y):
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
            label.moving = True
            labels.append(label)
            rollers.add(roll)
            y += self.vert_space
        return labels, rollers

    def update(self):
        self.rollers.update()
        if self.state == "Zipping":
            for label in self.labels:
                centerx = label.rect.centerx
                if label.moving:
                    label.rect.centerx += label.speed
                if self.stop_x-self.speed < centerx < self.stop_x+self.speed:
                    if label.moving:
                        label.rect.centerx = self.stop_x
                        label.moving = False
            if not any(label.moving for label in self.labels):
                self.state = "Fading"
        elif self.state == "Fading":
            self.fader.update()
            if self.fader.done:
                self.done = True

    def draw(self, surface):
        for label in self.labels:
            label.draw(surface)
        if self.state == "Fading":
            self.fader.draw(surface)
        self.rollers.draw(surface)


class CreditsScreen(tools._State):
    def __init__(self):
        super(CreditsScreen, self).__init__()
        self.screen = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.next = "LOBBYSCREEN"
        self.font = prepare.FONTS["Saniretro"]
        self.names = DEVELOPERS
        self.labels = []
        self.rollers = []
        self.zipper_blocks =[]
        self.zipper_block = None
        self.chip_curtain = None
        b_width = 318
        b_height = 101
        pos = self.screen.centerx-(b_width//2), self.screen.bottom-b_height-10
        self.done_button = NeonButton(pos, "Lobby")

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.zipper_blocks = []
        names = self.names[:]
        random.shuffle(names)
        title = Label(self.font, 112, "Development Team", "darkred",
                      {"center": (self.screen.centerx, 100)})
        title.moving = False
        grouped = [names[i:i+5] for i in range(0, len(names), 5)]
        for group in grouped:
            block = ZipperBlock(self.font, group, (700,title.rect.bottom+100))
            self.zipper_blocks.append(block)
        self.zipper_blocks = iter(self.zipper_blocks)
        self.zipper_block = next(self.zipper_blocks)
        self.titles = (title for _ in grouped)
        self.title = next(self.titles)
        spots = [(self.title.rect.left-100, self.title.rect.centery),
                 (self.title.rect.right+100, self.title.rect.centery)]
        self.spinners = pg.sprite.Group()
        Spinner(spots[0], "black", self.spinners)
        Spinner(spots[1], "black", self.spinners, reverse=True)
        self.chip_curtain = None

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.QUIT:
            self.done = True
        elif event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
            self.done = True
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.done_button.rect.collidepoint(pos):
                self.done = True

    def switch_blocks(self):
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
        except StopIteration:
            self.zipper_block = None
            self.title = None
            self.spinners.empty()
            self.chip_curtain = ChipCurtain("chipcurtain_python")

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.done_button.update(mouse_pos)
        if self.zipper_block:
            self.zipper_block.update()
            if self.zipper_block.done:
                self.switch_blocks()
        if self.chip_curtain:
            self.chip_curtain.update(dt)
            if self.chip_curtain.done:
                self.done = True
        self.spinners.update(dt)
        self.draw(surface)

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        if self.title:
            self.title.draw(surface)
        if self.zipper_block:
            self.zipper_block.draw(surface)
        self.spinners.draw(surface)
        if self.chip_curtain:
            self.chip_curtain.draw(surface)
        self.done_button.draw(surface)
