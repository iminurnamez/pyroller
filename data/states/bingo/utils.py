"""Utility functions - some of these could go be refactored into the core eventually"""

import pygame as pg

from ...components import labels
from ... import tools

from settings import SETTINGS as S
import loggable


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
        self.addLogger()

    def process_events(self, event, scale=(1, 1)):
        """Process pygame events"""
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.rect.collidepoint(pos):
                self.handle_click()

    def handle_click(self):
        """Do something when we are clicked on"""
        self.log.debug('Clicked on %s' % self.name)


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


