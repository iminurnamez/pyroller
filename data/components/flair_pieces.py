"""
This module includes graphical flairs to spice up menus and screens.
"""

import os
import random
import itertools
from math import degrees
import string

import pygame as pg
from .. import tools
from .chips import Chip
from .labels import Label
from .. import prepare

LETTERS = string.ascii_uppercase
COLORS = ["black", "blue", "green", "red", "white"]

#Y coordinates for each color of chip on the spinner spritesheet.
SPINNER_Y = {"blue"  : 0,
             "red"   : 80,
             "black" : 160,
             "green" : 240,
             "white" : 320}

#Default keyword arguments for Spinner.
SPINNER_DEFAULTS = {"frequency" : 17,
                    "reverse"   : False,
                    "variable"  : True,
                    "accel"     : 0.006,
                    "min_spin"  : 3,
                    "max_spin"  : 31}

#Default keyword arguments for the Spinner created in ChipCurtain.
CURTAIN_SPINNER_DEFAULTS = {"frequency" : 20,
                            "reverse"   : False,
                            "variable"  : True,
                            "accel"     : 0.03,
                            "min_spin"  : 15,
                            "max_spin"  : 40}

#Default keyword arguments for ChipCurtain.
CURTAIN_DEFAULTS = {"start_y"              : 0,
                    "bg_color"             : "black",
                    "text_color"           : "red",
                    "single_color"         : False,
                    "cycle_colors"         : False,
                    "color_flip_frequency" : 3,
                    "scroll_speed"         : 0.25,
                    "spinner_settings"     : CURTAIN_SPINNER_DEFAULTS}


class Fadeout(object):
    """
    Used for gradually fading a graphical element off the screen.
    Currently fades to a solid color but could be modified to optionally
    fade to a background image.
    """
    def __init__(self, rect, color="gray1", fade_increment=0.1):
        """
        Arguments are the rect of the target area; the color (either as a valid
        color string name or an rgb tuple); and a fade_increment giving the
        change in alpha per frame (integers and floats accepted).
        """
        self.rect = pg.Rect(rect)
        self.image = pg.Surface(rect.size).convert()
        try:
            self.image.fill(pg.Color(color))
        except ValueError:
            self.image.fill(color)
        self.image.convert_alpha()
        self.alpha = 0
        self.increment = fade_increment
        self.done = False

    def update(self, dt):
        """
        Increment and change the alpha value of the surface.
        If alpha reaches 255 set self.done to True.
        """
        self.alpha = min(self.alpha+self.increment*dt, 255)
        if self.alpha == 255:
            self.done = True
        self.image.set_alpha(int(self.alpha))

    def draw(self, surface):
        """Blit the fader image to the target surface."""
        surface.blit(self.image, self.rect)


class Spinner(pg.sprite.Sprite, tools._KwargMixin):
    """
    Class for the spinning chip sprites.
    """
    def __init__(self, center, color, *groups, **kwargs):
        """
        Arguments are the center of the sprite (x,y) and a color (must be a
        member of COLORS constant declared at the top of the module).
        This class also accepts a number of keyword arguments for
        customization.  Please see the SPINNER_DEFAULTS constant for all
        accepted keywords.
        """
        super(Spinner, self).__init__(*groups)
        self.process_kwargs("Spinner", SPINNER_DEFAULTS, kwargs)
        self.elapsed = 0.0
        self.image, self.switch_image = self.prepare_images(color)
        self.rect = self.image.get_rect(center=center)
        self.flipped = False

    def prepare_images(self, color):
        """
        Strip the images from the spinner sprite sheet and flip them to create
        a full cycle.  Return the first image in the cycle and the image on
        which to switch spinner to flipped.
        """
        sheet = prepare.GFX["spinners"]
        y = SPINNER_Y[color]
        images = tools.strip_from_sheet(sheet, (0, y), (80, 80), 10)
        switch_image = images[-1]
        images.extend([pg.transform.flip(img,1,1) for img in images[-2:0:-1]])
        if self.reverse:
            images.reverse()
        self.images = itertools.cycle(images)
        return next(self.images), switch_image

    def update(self, dt):
        """
        Change to next frame if frequency has elapsed.
        If the spinner has variable frequency, modify it based on self.accel.
        """
        self.elapsed += dt
        self.flipped = False
        while self.elapsed >= self.frequency:
            if self.image is self.switch_image:
                self.flipped = True
            self.elapsed -= self.frequency
            self.image = next(self.images)
        if self.variable:
            self.frequency += self.accel*dt
            slow = self.accel > 0 and self.frequency > self.max_spin
            fast = self.accel < 0 and self.frequency < self.min_spin
            if slow or fast:
                self.accel *= -1

    def draw(self, surface):
        """Blit the image to the target surface."""
        surface.blit(self.image, self.rect)


class ChipCurtain(tools._KwargMixin):
    """
    A descending curtain of Spinner chips.
    """
    def __init__(self, image_name, **kwargs):
        """
        The argument image_name is the name of an image which indicates a
        custom pattern of chips to draw (used in the credits screen).
        Pass None if not needed.
        This class accepts a large number of keyword arguments to customize
        behavior.  Please see the constant CURTAIN_DEFAULTS for details.
        """
        self.process_kwargs("ChipCurtain", CURTAIN_DEFAULTS, kwargs)
        self.prepare_rows(image_name)
        self.spinners = self.create_spinners()
        self.bottom = prepare.RENDER_SIZE[1]
        self.color_flip_count = 0
        self.done = False

    def prepare_rows(self, image_name):
        """
        Create a list containing all the information for each chip in the
        curtain.  The image_name will be used if curtain is not declared
        single_color.
        """
        self.color_cycle = itertools.cycle(COLORS)
        if self.cycle_colors:
            self.bg_color = next(self.color_cycle)
        if self.single_color:
            rows = ["X"*18 for _ in range(20)]
            self.single_color = self.bg_color
        else:
            rows = make_char_map(image_name)
        self.chips = []
        start_left = -20
        vert_space = 80
        horiz_space = 80
        top = self.start_y-(len(rows)*vert_space)
        self.wrap_y = top+(prepare.RENDER_SIZE[1]-self.start_y)
        for row in rows:
            left = start_left
            new_row = []
            for char in row:
                if self.bg_color == "random":
                    bg = random.choice(COLORS)
                else:
                    bg = self.bg_color
                color = bg if char=="X" else self.text_color
                new_row.append([[left,top], color])
                left += horiz_space
            self.chips.extend(new_row)
            top += vert_space

    def create_spinners(self):
        """
        Create a dictionary containing an instance of each color of Spinner.
        """
        spinners = {}
        for color in COLORS:
            spinner = Spinner((0, 0), color, **self.spinner_settings)
            spinners[color] = spinner
        return spinners

    def update(self, dt):
        """
        Change current color if needed; update all spinner instances;
        and increment each chips y location.
        """
        if self.cycle_colors:
            if self.spinners["black"].flipped:
                self.color_flip_count += 1
                if not self.color_flip_count % self.color_flip_frequency:
                    self.single_color = next(self.color_cycle)
        for color in self.spinners:
            self.spinners[color].update(dt)
        for chip in self.chips:
            chip[0][1] += self.scroll_speed*dt
            if chip[0][1] > self.bottom:
                chip[0][1] = self.wrap_y

    def draw(self, surface):
        """
        Blit the desired color of spinner instance to the display surface
        for each chip.  If self.single color is not set, use the chips
        individual color data.
        """
        for position,chip_color in self.chips:
            color = self.single_color or chip_color
            surface.blit(self.spinners[color].image, position)


class Roller(pg.sprite.Sprite):
    """
    A class for rolling chip sprites; notably used in the credits menu.
    """
    def __init__(self, center, color, direction, speed, *groups):
        """
        The argument center is the position of the center of the chip (x,y);
        color indicates the desired chip color (must be a member of COLORS);
        direction indicates which way the chip will roll ("left" or "right");
        speed is a float indicating how fast the chip rolls.
        """
        super(Roller, self).__init__(*groups)
        self.raw_image = Chip.flat_images[(32,19)][color]
        self.rect = self.raw_image.get_rect(center=center)
        self.pos = list(center)
        self.image = self.raw_image.copy()
        self.angle = 0
        self.direction = direction
        self.multiplier = -1 if direction == "left" else 1
        self.rotation = -0.003*self.multiplier
        self.speed = speed
        self.done = False

    def update(self, dt):
        """
        Update position and rotation of chip.  If the chip has rolled off the
        screen, set self.done to True.
        """
        self.pos[0] += self.speed*self.multiplier*dt
        self.angle += self.rotation*dt
        self.image = pg.transform.rotate(self.raw_image, degrees(self.angle))
        self.rect = self.image.get_rect(center=self.pos)
        if self.direction == "left":
            if self.pos[0] < -self.rect.width:
                self.kill()
        elif self.pos[0] > prepare.RENDER_SIZE[0]+self.rect.width:
            self.kill()

    def draw(self, surface):
        """Blit the image to the target surface."""
        surface.blit(self.image, self.rect)


def make_char_map(image_name, empty=(0,0,0,255)):
    """
    Parse a valid image into a format that ChipCurtain understands.
    The argument empty indicates the color on the image which is assigned to
    the bg_color.
    """
    chipmap = prepare.GFX[image_name]
    width, height = chipmap.get_size()
    converted = []
    for y in range(height):
        row = [chipmap.get_at((x,y)) for x in range(width)]
        converted.append("".join("O" if cell==empty else "X" for cell in row))
    return converted

    
class LetterReel(object):
    """
    A spinning reel of letters. After spinning num_spins times,
    the reel will stop on the first frame.
    """ 
    def __init__(self, topleft, letter, letter_size, spin_speed,
                         num_spins, num_letters=5):
        letters = [letter]
        self.letter = letter
        self.letter_size = w,h = letter_size
        for _ in range(num_letters - 1):
            letters.append(random.choice(LETTERS))
        self.letter_strip = pg.Surface((w, h * num_letters)).convert()
        self.letter_strip.fill(pg.Color("antiquewhite"))
        for num, letter in enumerate(letters):
            label = Label(prepare.FONTS["Saniretro"], 112, letter, "gray10", 
                               {"center": (w//2, h//2 + (h * num))})
            label.draw(self.letter_strip)
        self.viewport = pg.Rect((0, 0), letter_size)
        self.image = self.letter_strip.subsurface(pg.Rect((0, 0), letter_size))  
        self.image_rect = self.image.get_rect(topleft=topleft)
        self.spin_speed = spin_speed
        self.num_spins = num_spins
        self.spins = 0
        if self.spin_speed < 0:
            self.spins -= 1
        self.done = False
        self.clunk_sound = prepare.SFX["slot_reel_clunk"]
        
    def make_image(self):
        strip = self.letter_strip
        strip_w, strip_h = strip.get_size()
        img = pg.Surface(self.viewport.size).convert()
        if self.spin_speed > 0:
            if self.viewport.top > strip_h:
                self.viewport.top = self.viewport.top - strip_h
                self.spins += 1
            if self.viewport.bottom > strip_h:
                top_rect = pg.Rect(0, self.viewport.top, self.viewport.width,
                                             strip_h - self.viewport.top)
                top_strip = strip.subsurface(top_rect)
                bottom_rect = pg.Rect(0, 0, self.viewport.width,
                                                   self.viewport.height - top_rect.height)
                bottom_strip = strip.subsurface(bottom_rect)
                img.blit(top_strip, (0, 0))
                img.blit(bottom_strip, (0, top_rect.height))
            else:
                whole_strip = strip.subsurface(self.viewport)
                img.blit(whole_strip, (0, 0))
        else:
            if self.viewport.bottom < 0:
                self.viewport.bottom = strip_h + self.viewport.bottom
                self.spins += 1
            if self.viewport.top < 0:
                bottom_rect = pg.Rect(0, 0, self.viewport.width, 
                                                  self.viewport.height + self.viewport.top)
                bottom_strip = strip.subsurface(bottom_rect)
                top_rect = pg.Rect(0, strip_h + self.viewport.top, self.viewport.width,
                                             abs(self.viewport.top))
                top_strip = strip.subsurface(top_rect)
                img.blit(top_strip, (0, 0))
                img.blit(bottom_strip, (0, top_rect.height))
            else:
                whole_strip = strip.subsurface(self.viewport)
                img.blit(whole_strip, (0, 0))
        return img
        
    def update(self):
        if self.spins < self.num_spins:
            self.viewport.move_ip(0, self.spin_speed)
        else:
            if not self.done:
                self.done = True
                self.clunk_sound.play()
            self.viewport.topleft = (0, 0)    
        self.image = self.make_image()
        
    def draw(self, surface):
        surface.blit(self.image, self.image_rect)
        
        
class SlotReelTitle(object):
    """
    Converts text into a row of spinning reels like a slot machine.
    """
    def __init__(self, midtop, title_text, letter_size=(80, 120), spacer=3):
        letters = list(title_text)
        width = len(letters) * letter_size[0] + ((len(letters) - 1) * spacer)
        self.rect = pg.Rect(0, 0, width, letter_size[1])
        self.rect.midtop = midtop
        self.reels = []
        x = self.rect.left
        self.frame = self.rect.inflate(8, 8)
        toggle = 0
        speed = 33
        num_spins = 2
        for letter in letters:
            spin_speed = -1 * speed if  toggle % 2 else speed
            reel = LetterReel((x, midtop[1]), letter, letter_size,
                                   spin_speed, num_spins)
            self.reels.append(reel)
            x += letter_size[0] + spacer
            toggle += 1
            num_spins += 1
        self.spun_out = False
        self.spin_sound = prepare.SFX["slot_reel_short"]
        self.spin_sound.set_volume(.2)
        self.moving = True
        self.final_top = midtop[1]
        self.move((0, -120))
        self.move_speed = (0, 2)        

    def startup(self):
        self.spin_sound.play(-1)
        
    def move(self, move):
        self.rect.move_ip(move)
        self.frame.move_ip(move)
        for reel in self.reels:
            reel.image_rect.move_ip(move)
    
    def update(self):
        for reel in self.reels:
            reel.update()
        spun_out = [x for x in self.reels if x.spins >= x.num_spins]
        if len(spun_out) >= len(self.reels) // 2:
            self.spun_out = True
        if len(spun_out) >= len(self.reels):
            self.spin_sound.stop()        
        if self.moving:
            self.move(self.move_speed)
            if self.rect.top >= self.final_top:
                self.moving = False
                
    def draw(self, surface):
        for reel in self.reels:
            reel.draw(surface) 
        pg.draw.rect(surface, pg.Color("darkred"), self.frame, 4)    
            