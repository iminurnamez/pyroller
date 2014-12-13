"""Classes that manage and display bingo cards"""

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
        self.label = utils.getLabel(
            'square-number', (card.x + offset[0], card.y + offset[1]), number)
        self.marker = prepare.GFX['bingo-marker']
        #
        super(BingoSquare, self).__init__(name, self.label.rect)

    def draw(self, surface):
        """Draw the square"""
        self.label.draw(surface)


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