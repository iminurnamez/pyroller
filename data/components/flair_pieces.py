import os
import copy
import random
import itertools
from math import degrees

import pygame as pg
from ..tools import strip_from_sheet
from .chips import Chip
from .. import prepare


COLORS = ["black", "blue","green", "red", "white"]

SPINNER_Y = {"blue"  : 0,
             "red"   : 80,
             "black" : 160,
             "green" : 240,
             "white" : 320}

SPINNER_DEFAULTS = {"frequency" : 17,
                    "reverse"   : False,
                    "variable"  : True,
                    "accel"     : 0.1,
                    "min_spin"  : 3,
                    "max_spin"  : 31}

CURTAIN_SPINNER_DEFAULTS = {"frequency" : 20,
                            "reverse"   : False,
                            "variable"  : True,
                            "accel"     : 0.5,
                            "min_spin"  : 15,
                            "max_spin"  : 25}

CURTAIN_DEFAULTS = {"start_y"              : 0,
                    "bg_color"             : "black",
                    "text_color"           : "red",
                    "single_color"         : False,
                    "cycle_colors"         : False,
                    "color_flip_frequency" : 3,
                    "scroll_speed"         : 4,
                    "spinner_settings"     : CURTAIN_SPINNER_DEFAULTS}


class _KwargMixin(object):
    def process_kwargs(self, name, defaults, kwargs):
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
        self.__dict__.update(settings)


class Fadeout(object):
    def __init__(self, rect, color="gray1", fade_increment=1.5):
        self.rect = rect
        self.surf = pg.Surface(rect.size)
        try:
            self.surf.fill(pg.Color(color))
        except ValueError:
            self.surf.fill(color)
        self.surf.convert_alpha()
        self.alpha = 0
        self.increment = fade_increment
        self.done = False

    def update(self):
        self.alpha += self.increment
        if self.alpha >= 255:
            self.done = True
        self.surf.set_alpha(int(self.alpha))

    def draw(self, surface):
        surface.blit(self.surf, self.rect)


class Spinner(_KwargMixin):
    def __init__(self, center, color, **kwargs):
        self.process_kwargs("Spinner", SPINNER_DEFAULTS, kwargs)
        self.elapsed = 0.0
        self.image, self.switch_image = self.prepare_images(color)
        self.rect = self.image.get_rect(center=center)
        self.flipped = False

    def prepare_images(self, color):
        sheet = prepare.GFX["spinners"]
        y = SPINNER_Y[color]
        images = strip_from_sheet(sheet, (0, y), (80, 80), 10)
        switch_image = images[-1]
        images.extend([pg.transform.flip(img,1,1) for img in images[-2:0:-1]])
        if self.reverse:
            images.reverse()
        self.images = itertools.cycle(images)
        return next(self.images), switch_image

    def update(self, dt):
        self.elapsed += dt
        self.flipped = False
        while self.elapsed >= self.frequency:
            if self.image is self.switch_image:
                self.flipped = True
            self.elapsed -= self.frequency
            self.image = next(self.images)
        if self.variable:
            self.frequency += self.accel
            slow = self.accel > 0 and self.frequency > self.max_spin
            fast = self.accel < 0 and self.frequency < self.min_spin
            if slow or fast:
                self.accel *= -1

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class ChipCurtain(_KwargMixin):
    def __init__(self, image_name, **kwargs):
        self.process_kwargs("ChipCurtain", CURTAIN_DEFAULTS, kwargs)
        self.prepare_rows(image_name)
        self.spinners = self.create_spinners()
        self.bottom = prepare.RENDER_SIZE[1]
        self.color_flip_count = 0
        self.done = False

    def prepare_rows(self, image_name):
        self.color_cycle = itertools.cycle(COLORS)
        if self.cycle_colors:
            self.bg_color = next(self.color_cycle)
        if self.single_color:
            rows = ["X" * 18 for _ in range(20)]
            self.single_color = self.bg_color
        else:
            rows = make_char_map(image_name)
        self.chips = []
        start_left = -20
        vert_space = 80
        horiz_space = 80
        top = self.start_y - (len(rows) * vert_space)
        self.wrap_y = top + (prepare.RENDER_SIZE[1] - self.start_y)
        for row in rows:
            left = start_left
            new_row = []
            for char in row:
                if self.bg_color == "random":
                    bg = random.choice(COLORS)
                else:
                    bg = self.bg_color
                color = bg if char=="X" else self.text_color
                new_row.append([[left, top], color])
                left += horiz_space
            self.chips.extend(new_row)
            top += vert_space

    def create_spinners(self):
        spinners = {}
        for color in COLORS:
            spinner = Spinner((0, 0), color, **self.spinner_settings)
            spinners[color] = spinner
        return spinners

    def update(self, dt):
        if self.cycle_colors:
            if self.spinners["black"].flipped:
                self.color_flip_count += 1
                if not self.color_flip_count % self.color_flip_frequency:
                    self.single_color = next(self.color_cycle)
        for color in self.spinners:
            self.spinners[color].update(dt)
        for chip in self.chips:
            chip[0][1] += self.scroll_speed
            if chip[0][1] > self.bottom:
                chip[0][1] = self.wrap_y

    def draw(self, surface):
        for chip in self.chips:
            color = self.single_color or chip[1]
            surface.blit(self.spinners[color].image, chip[0])


class Roller(object):
    def __init__(self, center, color, direction, speed):
        self.image = Chip.flat_images[(32,19)][color]
        self.rect = self.image.get_rect(center=center)
        self.pos = center
        self.rot_image = self.image
        self.angle = 0
        self.direction = direction
        self.multiplier = -1 if direction == "left" else 1
        self.rotation = .05 * self.multiplier * -1
        self.speed = speed
        self.done = False

    def update(self):
        self.pos = (self.pos[0]+(self.speed*self.multiplier), self.pos[1])
        self.angle += self.rotation
        self.rot_image = pg.transform.rotate(self.image, degrees(self.angle))
        self.rect = self.rot_image.get_rect(center=self.pos)
        if self.direction == "left":
            if self.pos[0] < -self.rect.width:
                self.done = True
        else:
            if self.pos[0] > prepare.RENDER_SIZE[0] + self.rect.width:
                self.done = True

    def draw(self, surface):
        surface.blit(self.rot_image, self.rect)


def make_char_map(img_name):
    chipmap = prepare.GFX[img_name]
    size = chipmap.get_size()
    rows = []

    for y in range(size[1]):
        rows.append([[[x, y], chipmap.get_at((x, y))] for x in range(size[0])])
    converted = []
    for row in rows:
        converted_row = []
        for cell in row:
            char = "O" if cell[1] == (0,0,0,255) else "X"
            converted_row.append(char)
        converted.append("".join(converted_row))
    return converted