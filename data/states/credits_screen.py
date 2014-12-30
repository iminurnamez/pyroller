from random import shuffle, choice
from itertools import cycle

import pygame as pg
from .. import tools, prepare
from ..components.labels import Label
from ..components.flair_pieces import Spinner, Roller, Fadeout, ChipCurtain


DEVELOPERS = ("camarce1 Mekire iminurnamez macaframa metulburr jellyberg "
              "PaulPaterson trijazzguy menatwrk bar777foo").split()


class ZipperBlock(object):
    def __init__(self, font, text_list, midtop, offscreen_distance=100,
                         stagger=100, speed=5, vert_space=150, chip_space = 25,
                         font_size=80):
        self.labels = []
        self.rollers = []
        colors = ["black", "blue", "green", "red", "white"]
        screen_width = prepare.RENDER_SIZE[0]
        self.stop_x, y = midtop
        self.speed = speed
        self.state = "Zipping"
        self.done = False

        for i, text in enumerate(text_list):
            if not i % 2:
                roller = Roller((-offscreen_distance, y), choice(colors), "right", speed)
                r = roller.rect
                label = Label(font, font_size, text, "goldenrod3",
                                   {"midright": (r.left - chip_space, r.centery)})
                label.speed = speed
                label.moving = True
            else:
                roller = Roller((screen_width + offscreen_distance, y),
                                     choice(colors), "left", speed)
                r = roller.rect
                label = Label(font, font_size, text, "goldenrod3",
                                   {"midleft": (r.right + chip_space, r.centery)})
                label.speed = -speed
                label.moving = True
            self.rollers.append(roller)
            self.labels.append(label)
            #offscreen_distance += stagger
            y += vert_space
        top = self.labels[0].rect.top
        fade_rect = pg.Rect(300, top, 800, prepare.RENDER_SIZE[1] - top)
        self.fader = Fadeout(fade_rect, prepare.BACKGROUND_BASE)

    def update(self):
        for roller in self.rollers:
            roller.update()
        if self.state == "Zipping":
            for label in self.labels:
                if label.moving:
                    label.rect.centerx += label.speed
                if self.stop_x - self.speed < label.rect.centerx < self.stop_x + self.speed:
                    if label.moving:
                        label.rect.centerx = self.stop_x
                        label.moving = False
            if not any([x.moving for x in self.labels]):
                self.state = "Fading"
        elif self.state == "Fading":
            self.fader.update()
            if self.fader.done:
                self.done = True
        self.rollers = [x for x in self.rollers if not x.done]

    def draw(self, surface):
        for label in self.labels:
            label.draw(surface)
        if self.state == "Fading":
            self.fader.draw(surface)
        for roller in self.rollers:
            roller.draw(surface)


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

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.zipper_blocks =[]
        self.zipper_block = None

        names = self.names[:]
        shuffle(names)
        title = Label(self.font, 112, "Development Team", "darkred",
                      {"center": (self.screen.centerx, 100)})
        title.moving = False
        grouped = [names[i: i + 5] for i in range(0, len(names), 5)]
        for group in grouped:
            block = ZipperBlock(self.font, group, (700,title.rect.bottom+100))
            self.zipper_blocks.append(block)
        self.zipper_blocks = iter(self.zipper_blocks)
        self.zipper_block = next(self.zipper_blocks)
        self.titles = [title] * len(grouped)
        self.titles = iter(self.titles)
        self.title = next(self.titles)
        spinner_spots = [(self.title.rect.left-100, self.title.rect.centery),
                         (self.title.rect.right+100, self.title.rect.centery)]
        self.spinners = [Spinner(spinner_spots[0], "black"),
                        Spinner(spinner_spots[1], "black", reverse=True)]
        self.chip_curtain = None

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.QUIT:
            self.done = True
        elif event.type == pg.KEYUP and event.key == pg.K_ESCAPE:
            self.done = True

    def update(self, surface, keys, current_time, dt, scale):
        if self.zipper_block:
            self.zipper_block.update()
            if self.zipper_block.done:
                try:
                    rect = self.title.rect
                    self.zipper_block = next(self.zipper_blocks)
                    self.title = next(self.titles)
                    if self.title.rect != rect:
                        spinner_spots = [(self.title.rect.left - 100, self.title.rect.centery),
                                                  (self.title.rect.right + 100, self.title.rect.centery)]
                        self.spinners = [Spinner(spinner_spots[0], "blue"),
                                                Spinner(spinner_spots[1], "blue", reverse=True)]
                except StopIteration:
                    self.zipper_block = None
                    self.title = None
                    self.spinners = None
                    self.chip_curtain = ChipCurtain("chipcurtain_python")
        if self.chip_curtain:
            self.chip_curtain.update(dt)
            if self.chip_curtain.done:
                self.done = True
        if self.spinners:
            for spinner in self.spinners:
                spinner.update(dt)
        self.draw(surface)

    def draw(self, surface):
        surface.fill(prepare.BACKGROUND_BASE)
        if self.title:
            self.title.draw(surface)
        if self.zipper_block:
            self.zipper_block.draw(surface)
        if self.spinners:
            for spinner in self.spinners:
                spinner.draw(surface)
        if self.chip_curtain:
            self.chip_curtain.draw(surface)