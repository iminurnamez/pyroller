import os
from math import degrees
from random import choice
from itertools import cycle

import pygame as pg
from ..tools import strip_from_sheet
from .chips import Chip
from .. import prepare


SPINNER_Y = {"blue"  : 0,
             "red"   : 80,
             "black" : 160,
             "green" : 240,
             "white" : 320}


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


class Spinner(object):
    def __init__(self, center, color, spin_frequency=17, reverse=False,
                         variable_spin=True, acceleration=.2, min_spin=3,
                         max_spin=31):
        self.variable_spin = variable_spin
        self.acceleration = acceleration
        self.min_spin = min_spin
        self.max_spin =max_spin
        self.spin_frequency = spin_frequency
        self.elapsed = 0.0
        self.acceleration = .1
        sheet = prepare.GFX["spinners"]
        y = SPINNER_Y[color]
        self.images = strip_from_sheet(sheet, (0, y), (80, 80), 10, rows=1)
        self.switch_image = self.images[-1]
        flipped = [pg.transform.flip(img, True, True) for img in self.images[1:-1]]
        self.images.extend(flipped[::-1])
        if reverse:
            self.images = self.images[::-1]
        self.images = cycle(self.images)
        self.image = next(self.images)
        self.rect = self.image.get_rect(center=center)
        self.flipped = False

    def update(self, dt):
        self.elapsed += dt
        self.flipped = False
        while self.elapsed >= self.spin_frequency:
            if self.image == self.switch_image:
                self.flipped = True
            self.elapsed -= self.spin_frequency
            self.image = next(self.images)
        if self.variable_spin:
            self.spin_frequency += self.acceleration
            slow = self.acceleration > 0 and self.spin_frequency > self.max_spin
            fast = self.acceleration < 0 and self.spin_frequency < self.min_spin
            if slow or fast:
                self.acceleration *= -1

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class ChipCurtain(object):
    def __init__(self, image_name, start_y=0, bg_color="black",
                        text_color="red", single_color=False, cycle_colors=False,
                        color_flip_frequency=3, spin_frequency=20,
                        reverse=False, variable_spin=True, acceleration=.5,
                        min_spin=15, max_spin=25, scroll_speed=4):
        self.scroll_speed = scroll_speed
        colors = ["black", "blue","green", "red", "white"]
        self.color_cycle = cycle(colors)
        self.cycle_colors = cycle_colors
        if self.cycle_colors:
            bg_color = next(self.color_cycle)
        self.single_color = None
        self.color_flip_frequency = color_flip_frequency
        if single_color:
            rows = ["X" * 18 for _ in range(20)]
            self.single_color = bg_color
        else:
            rows = make_char_map(image_name)
        self.chips = []
        start_left = -20
        vert_space = 80
        horiz_space = 80
        top = start_y - (len(rows) * vert_space)
        self.wrap_y = top + (prepare.RENDER_SIZE[1] - start_y)
        for row in rows:
            left = start_left
            new_row = []
            for char in row:
                if bg_color == "random":
                    bg = choice(colors)
                else:
                    bg = bg_color
                color = bg if char == "X" else text_color
                new_row.append([[left, top], color])
                left += horiz_space
            self.chips.extend(new_row)
            top += vert_space
        self.spinners = {color: Spinner((0, 0), color, spin_frequency,
                                                      reverse, variable_spin, acceleration,
                                                      min_spin, max_spin)
                                for color in colors
                                }
        self.done = False
        self.bottom = prepare.RENDER_SIZE[1]
        self.color_flip_count = 0

    def update(self, dt):
        if self.cycle_colors:
            if self.spinners["black"].flipped:
                self.color_flip_count += 1
                if not self.color_flip_count % self.color_flip_frequency:
                    color = next(self.color_cycle)
                    self.single_color = color

        for color in self.spinners:
            self.spinners[color].update(dt)
        for chip in self.chips:
            chip[0][1] += self.scroll_speed
            if chip[0][1] > self.bottom:
                chip[0][1] = self.wrap_y

    def draw(self, surface):
        for chip in self.chips:
            if self.single_color:
                surface.blit(self.spinners[self.single_color].image, chip[0])
            else:
                surface.blit(self.spinners[chip[1]].image, chip[0])


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
        self.pos = (self.pos[0] + (self.speed * self.multiplier),
                         self.pos[1])
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