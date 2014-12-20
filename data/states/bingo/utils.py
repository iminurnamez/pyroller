"""Utility functions - some of these could go be refactored into the core eventually"""

import collections
import pygame as pg

from ...components import labels
from ... import prepare
from ... import tools

from .settings import SETTINGS as S
from . import loggable


def getLabel(name, position, text):
    """Return a label using named settings"""
    return labels.Label(
        font_path=S['%s-font' % name],
        text_color=S['%s-font-color' % name],
        font_size=S['%s-font-size' % name],
        text=str(text),
        rect_attributes={'center': position},
    )


class EventAware(object):
    """Base class for objects that can handle events"""

    def process_events(self, event, scale=(1, 1)):
        """Process pygame events"""


class Clickable(EventAware, loggable.Loggable):

    """Simple class to make an item clickable"""

    def __init__(self, name, rect=None):
        """Initialise the clickable"""
        self.name = name
        self.rect = rect
        self.mouse_over = False
        self.addLogger()

    def process_events(self, event, scale=(1, 1)):
        """Process pygame events"""
        pos = tools.scaled_mouse_pos(scale, event.pos)
        #
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pos):
                self.handle_click()
        elif event.type == pg.MOUSEMOTION:
            mouse_over = self.rect.collidepoint(pos)
            if mouse_over != self.mouse_over:
                if self.mouse_over:
                    self.handle_mouse_leave()
                else:
                    self.handle_mouse_enter()
            self.mouse_over = mouse_over

    def handle_click(self):
        """Do something when we are clicked on"""
        self.log.debug('Clicked on %s' % self.name)

    def handle_mouse_enter(self):
        """Do something when the mouse enters our rect"""
        self.log.debug('Mouse enter %s' % self.name)

    def handle_mouse_leave(self):
        """Do something when the mouse leaves our rect"""
        self.log.debug('Mouse leave %s' % self.name)


class ClickableGroup(list, EventAware):
    """A list of clickable items"""

    def process_events(self, event, scale=(1, 1)):
        """Process all the events"""
        for item in self:
            item.process_events(event, scale)


class Drawable(object):
    """Simple base class for all screen objects"""

    def draw(self, surface):
        """Draw this item onto the given surface"""
        raise NotImplementedError('Need to implement the draw method')


class DrawableGroup(list, Drawable):
    """A list of drawable items"""

    def draw(self, surface):
        """Draw all these items onto the given surface"""
        for item in self:
            item.draw(surface)


class KeyedDrawableGroup(collections.OrderedDict, Drawable):
    """A drawable group based on a dictionary so you can retrieve items"""

    def draw(self, surface):
        """Draw all the items to the given surface"""
        for item in self.values():
            item.draw(surface)


class NamedSprite(Drawable):
    """A sprite loaded from a named file"""

    def __init__(self, name, position, filename=None, scale=1.0):
        """Initialise the sprite"""
        super(NamedSprite, self).__init__()
        #
        self.name = name
        self.angle = 0
        self.sprite = prepare.GFX[filename if filename else name]
        w, h = self.sprite.get_size()
        #
        # Scale if needed
        if scale != 1.0:
            self.sprite = pg.transform.scale(self.sprite, (int(w * scale), int(h * scale)))
            w, h = w * scale, h * scale
        #
        self.rect = pg.Rect(position[0] - w / 2, position[1] - h / 2, w, h)

    def draw(self, surface):
        """Draw the sprite"""
        surface.blit(self.sprite, self.rect)

    def rotate_to(self, angle):
        """Rotate the sprite"""
        delta = angle - self.angle
        x, y = self.rect.x + self.rect.width / 2, self.rect.y + self.rect.height / 2
        self.sprite = pg.transform.rotate(self.sprite, delta)
        w, h = self.sprite.get_size()
        self.rect = pg.Rect(x - w / 2, y - h / 2, w, h)


class ImageButton(Clickable):
    """A button with an image and text"""

    def __init__(self, name, position, filename, text_properties, text, callback, arg):
        """Initialise the button"""
        self.callback = callback
        self.arg = arg
        #
        self.image = NamedSprite(name, position, filename)
        self.label = getLabel(text_properties, position, text)
        #
        super(ImageButton, self).__init__(name, self.image.rect)

    def draw(self, surface):
        """Draw the button"""
        self.image.draw(surface)
        self.label.draw(surface)

    def handle_click(self):
        """Handle the click event"""
        self.callback(self.arg)


class ImageOnOffButton(Clickable):
    """A button with an on and off image and text"""

    def __init__(self, name, position, on_filename, off_filename, text_properties, text, state, callback, arg, scale=1.0):
        """Initialise the button"""
        self.callback = callback
        self.arg = arg
        self.state = state
        #
        self.on_image = NamedSprite(name, position, on_filename, scale=scale)
        self.off_image = NamedSprite(name, position, off_filename, scale=scale)
        self.label = getLabel(text_properties, position, text)
        #
        super(ImageOnOffButton, self).__init__(name, self.on_image.rect)

    def draw(self, surface):
        """Draw the button"""
        if self.state:
            self.on_image.draw(surface)
        else:
            self.off_image.draw(surface)
        self.label.draw(surface)

    def handle_click(self):
        """Handle the click event"""
        self.callback(self.arg)