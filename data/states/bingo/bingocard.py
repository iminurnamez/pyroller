"""Classes that manage and display bingo cards"""

from ...components import labels
from settings import SETTINGS as S
import utils


class BingoSquare(object):
    """A square on a bingo card"""

    def __init__(self, card, offset, number):
        """Initialise the square"""
        self.offset = offset
        self.number = number
        self.is_highlighted = False
        self.is_called = False
        #
        self.label = utils.getLabel(
            'square-number', (card.x + offset[0], card.y + offset[1]), number)

    def draw(self, surface):
        """Draw the square"""
        self.label.draw(surface)


class BingoCard(object):
    """A bingo card comprising a number of squares"""

    def __init__(self, position):
        """Initialise the bingo card"""
        self.x, self.y = position
        self.squares = utils.DrawableGroup()
        square_offset = S['card-square-offset']
        for x, y in S['card-square-scaled-offsets']:
            self.squares.append(BingoSquare(self, (square_offset * x, square_offset * y), 10))

    def draw(self, surface):
        """Draw the square"""
        self.squares.draw(surface)


class CardCollection(utils.Drawable):
    """A set of bingo cards"""

    def __init__(self, position, offsets):
        """Initialise the collection"""
        self.x, self.y = position
        self.cards = utils.DrawableGroup([BingoCard((self.x+ x, self.y + y)) for x, y in offsets])

    def draw(self, surface):
        """Draw the cards"""
        self.cards.draw(surface)