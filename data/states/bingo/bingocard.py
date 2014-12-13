"""Classes that manage and display bingo cards"""

import random

from ... import prepare
from .settings import SETTINGS as S
from . import utils


class BingoSquare(utils.Clickable):
    """A square on a bingo card"""

    def __init__(self, name, card, offset, number):
        """Initialise the square"""
        self.name = name
        self.offset = offset
        self.number = number
        self.is_highlighted = False
        self.is_called = False
        #
        x, y = card.x + offset[0], card.y + offset[1]
        self.label = utils.getLabel('square-number', (x, y), number)
        self.marker = utils.NamedSprite('bingo-marker', (x, y))
        self.highlighter = utils.NamedSprite('bingo-highlight', (x, y))
        #
        super(BingoSquare, self).__init__(name, self.label.rect)

    def draw(self, surface):
        """Draw the square"""
        if self.is_highlighted:
            self.highlighter.draw(surface)
        self.label.draw(surface)
        if self.is_called:
            self.marker.draw(surface)

    def handle_click(self):
        """The number was clicked on"""
        self.marker.rotate_to(random.randrange(0, 360))
        self.is_called = not self.is_called


class BingoCard(utils.Clickable):
    """A bingo card comprising a number of squares"""

    def __init__(self, name, position):
        """Initialise the bingo card"""
        super(BingoCard, self).__init__(name)
        #
        self.x, self.y = position
        self.squares = utils.DrawableGroup()
        square_offset = S['card-square-offset']
        for x, y in S['card-square-scaled-offsets']:
            self.squares.append(BingoSquare(
                '%s [%d,%d]' % (self.name, x, y),
                self, (square_offset * x, square_offset * y), 10
            ))
        #
        self.clickables = utils.ClickableGroup(self.squares)

    def draw(self, surface):
        """Draw the square"""
        self.squares.draw(surface)

    def process_events(self, event, scale=(1, 1)):
        """Process clicking events"""
        self.clickables.process_events(event, scale)


class CardCollection(utils.Drawable, utils.ClickableGroup):
    """A set of bingo cards"""

    def __init__(self, name, position, offsets):
        """Initialise the collection"""
        self.name = name
        self.x, self.y = position
        self.cards = utils.DrawableGroup([BingoCard(
            '%s(%d)' % (self.name, i + 1),
            (self.x + x, self.y + y)) for i, (x, y) in enumerate(offsets)]
        )
        #
        super(CardCollection, self).__init__(self.cards)

    def draw(self, surface):
        """Draw the cards"""
        self.cards.draw(surface)