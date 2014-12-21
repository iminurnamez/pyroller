from itertools import cycle
import pygame as pg
from .. import prepare


LOADED_FONTS = {}

#Helper function for MultiLineLabel class
def wrap_text(text, char_limit, separator=" "):
    """Splits a string into a list of strings no longer than char_limit."""
    words = text.split(separator)
    lines = []
    current_line = []
    current_length = 0
    for word in words:

        if len(word) + current_length <= char_limit:
            current_length += len(word) + len(separator)
            current_line.append(word)
        else:
            lines.append(separator.join(current_line))
            current_line = [word]
            current_length = len(word) + len(separator)
    if current_line:
        lines.append(separator.join(current_line))
    return lines


class _Label(object):
    '''Parent class all labels inherit from. Color arguments can use color names
       or an RGB tuple. rect_attributes should be a dict with keys of
       pygame.Rect attribute names (strings) and the relevant position(s) as values.'''
    def __init__(self, font_path, font_size, text, text_color, rect_attributes,
                         bground_color=None):
        if (font_path, font_size) not in LOADED_FONTS:
            LOADED_FONTS[(font_path, font_size)] = pg.font.Font(font_path, font_size)
        self.f = LOADED_FONTS[(font_path, font_size)]
        self.background_color = bground_color
        self.text_color = text_color
        self.rect_attributes = rect_attributes
        #
        self.set_text(text)

    def set_text(self, text):
        '''Set the text to display'''
        self.displayed_text = text
        self.update_text()

    def update_text(self):
        '''Update the surface using the current properties and text'''
        if self.background_color is not None:
            self.text = self.f.render(self.displayed_text, True, pg.Color(self.text_color),
                                         pg.Color(self.background_color))
        else:
            self.text = self.f.render(self.displayed_text, True, pg.Color(self.text_color))
        self.rect = self.text.get_rect(**self.rect_attributes)

    def draw(self, surface):
        surface.blit(self.text, self.rect)


class Label(_Label):
    '''Creates a surface with text blitted to it (self.text) and an associated
       rectangle (self.rect). Label will have a transparent background if
       bground_color is not passed to __init__.'''
    def __init__(self, font_path, font_size, text, text_color, rect_attributes,
                         bground_color=None):
        super(Label, self).__init__(font_path, font_size, text, text_color,
                                                rect_attributes, bground_color)


class GroupLabel(Label):
    '''Creates a Label object which is then appended to group.'''
    def __init__(self, group, font_path, font_size, text, text_color,
                         rect_attributes, bground_color=None):
        super(GroupLabel, self).__init__(font_path, font_size, text, text_color,
                                                        rect_attributes, bground_color)
        group.append(self)


class MultiLineLabel(object):
    """Creates a single surface with multiple labels blitted to it."""
    def __init__(self, font_path, font_size, text, text_color, rect_attributes,
                         bground_color=None, char_limit=42, align="left", vert_space=0):
        lines = wrap_text(text, char_limit)
        labels = [Label(font_path, font_size, line, text_color, {"center": (0, 0)}, bground_color)
                      for line in lines]
        width = max([x.rect.width for x in labels])
        height = sum([x.rect.height for x in labels]) + (vert_space * (len(lines) - 1))
        self.surf = pg.Surface((width, height)).convert()
        self.surf.set_colorkey(pg.Color("black"))
        self.surf.fill(pg.Color("black"))
        self.rect = self.surf.get_rect(**rect_attributes)
        aligns = {"left": {"left": 0},
                      "center": {"centerx": self.rect.width // 2},
                      "right": {"right": self.rect.width}
                      }
        y = 0
        for label in labels:
            label.rect = label.text.get_rect(**aligns[align])
            label.rect.top = y
            label.draw(self.surf)
            y += label.rect.height + vert_space

    def draw(self, surface):
        surface.blit(self.surf, self.rect)


class Blinker(Label):
    """A label that blinks. blink_frequency is the number of milliseconds
    between blinks."""
    def __init__(self, font_path, font_size, text, text_color, rect_attributes,
                         blink_frequency, bground_color=None):
        super(Blinker, self).__init__(font_path, font_size, text, text_color,
                                                  rect_attributes, bground_color)
        self.frequency = blink_frequency
        self.elapsed = 0.0
        self.on = True
        self.blinking = True

    def draw(self, surface, dt):
        self.elapsed += dt
        if self.elapsed >= self.frequency:
            self.elapsed -= self.frequency
            if self.blinking:
                self.on = not self.on
        if self.on:
            surface.blit(self.text, self.rect)


#Label Enhancements
class Bulb(object):
    """Class to represent an individual light bulb for
    MarqueeFrame objects."""
    def __init__(self, center_point):
        self.image = prepare.GFX["bulb"]
        self.rect = self.image.get_rect(center=center_point)
        self.on = False

    def draw(self, surface):
        """Draw bulb to surface."""
        surface.blit(self.image, self.rect)


class MarqueeFrame(object):
    """A MarqueeFrame draws a ring of blinking lights around a label."""
    def __init__(self, label, bulb_radius=20, bulb_color="goldenrod3",
                        frequency=120):
        diam = bulb_radius * 2
        width = ((label.rect.width // diam) + 1) * diam
        height = ((label.rect.height // diam) + 1) * diam
        self.rect = pg.Rect((0, 0), (width, height))
        self.rect.center = label.rect.center
        self.bulbs = []
        bottom_bulbs = []
        left_bulbs = []
        for i in range(-diam, self.rect.width + diam, diam):
            x = self.rect.left + i + bulb_radius
            y = self.rect.top - bulb_radius
            y2 = self.rect.bottom + bulb_radius
            self.bulbs.append(Bulb((x, y)))
            bottom_bulbs.append(Bulb((x, y2)))
        for j in range(0, self.rect.height + diam, diam):
            x1 = self.rect.left - bulb_radius
            x2 = self.rect.right + bulb_radius
            y = self.rect.top + j + bulb_radius
            left_bulbs.append(Bulb((x1, y)))
            self.bulbs.append(Bulb((x2, y)))
        self.bulbs.extend(bottom_bulbs[1:-1][::-1])
        self.bulbs.extend(left_bulbs[::-1])
        self.bulb_cycle = cycle(self.bulbs)
        self.bulb = next(self.bulb_cycle)
        self.elapsed = 0.0
        self.frequency = frequency
        for i, bulb in enumerate(self.bulbs):
            if not i % 2:
                bulb.on = True

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed > self.frequency:
            self.elapsed -= self.frequency
            for bulb in self.bulbs:
                bulb.on = not bulb.on

    def draw(self, surface):
        for bulb in self.bulbs:
            if bulb.on:
                bulb.draw(surface)


class Button(object):
    """A simple button class."""
    def __init__(self, left, top, width, height, label):
        self.rect = pg.Rect(left, top, width, height)
        label.rect.center = self.rect.center
        self.label = label

    def draw(self, surface):
        """Draw button to surface."""
        pg.draw.rect(surface, pg.Color("gray10"), self.rect)
        border = self.rect.inflate(16, 18)
        border.top = self.rect.top - 6
        pg.draw.rect(surface, pg.Color("gray10"), border)
        color = "gold3"
        pg.draw.rect(surface, pg.Color(color), self.rect, 3)
        pg.draw.rect(surface, pg.Color(color), border, 4)
        points = [(self.rect.topleft, border.topleft),
                      (self.rect.topright, border.topright),
                      (self.rect.bottomleft, border.bottomleft),
                      (self.rect.bottomright, border.bottomright)]
        for pair in points:
            pg.draw.line(surface, pg.Color(color), pair[0], pair[1], 2)
        self.label.draw(surface)


class ImageButton(object):
    def __init__(self, image, rect_attributes, label):
        self.image = image
        self.rect = self.image.get_rect(**rect_attributes)
        self.label = label
        self.label.rect.midtop = self.rect.midbottom

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.label.draw(surface)

class PayloadButton(Button):
    """A button that holds a "payload" value."""
    def __init__(self, left, top, width, height, label, payload):
        super(PayloadButton, self).__init__(left, top, width, height, label)
        self.payload = payload


class FunctionButton(Button):
    """A button that calls a function when clicked."""
    def __init__(self, left, top, width, height, label, function, function_args):
        super(FunctionButton, self).__init__(left, top, width, height, label)
        self.function = function
        self.function_args = function_args

    def click(self, dynamic_args=None):
        """If the button's function requires arguments that need to be
        calculated at the time the button is clicked they can be passed
        as this method's dynamic_args."""
        function_args = list(self.function_args)
        if dynamic_args:
            function_args.extend(list(dynamic_args))
        self.function(*function_args)
