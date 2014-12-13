"""Utility functions - some of these could go be refactored into the core eventually"""

from ...components import labels
from settings import SETTINGS as S


def getLabel(name, position, text):
    """Return a label using named settings"""
    return labels.Label(
        font_path=S['%s-font' % name],
        text_color=S['%s-font-color' % name],
        font_size=S['%s-font-size' % name],
        text=str(text),
        rect_attributes={'center': position},
    )


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