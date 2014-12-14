"""Classes to help with matching patterns of squares on the cards"""

from . import loggable
from .settings import SETTINGS as S


class Pattern(loggable.Loggable):
    """A pattern of squares that would win the game"""

    name = 'Pattern'
    lx, rx = S['card-square-cols'][0], S['card-square-cols'][-1]
    by, ty = S['card-square-rows'][0], S['card-square-rows'][-1]

    def __init__(self):
        """Initialise the pattern"""
        self.addLogger()

    def get_matches(self, card):
        """Return a sequence of matching squares"""
        for offsets in self.get_square_offsets():
            yield [
                card.squares[offset] for offset in offsets
            ]

    def get_square_offsets(self):
        """Return a sequence of matching square offsets"""
        raise NotImplementedError('Must implement the get_square_offsets method')

    def get_number_to_go(self, card, called_balls):
        """Return the number of squares needed to win"""
        number_to_go = []
        for squares in self.get_matches(card):
            number_to_go.append(self.get_number_to_go_for_squares(card, squares, called_balls))
        #
        return min(number_to_go)

    def get_number_to_go_for_squares(self, card, squares, called_balls):
        """Return the number of squares needed to win from a particular set of squares"""
        number = 0
        for square in squares:
            if square.text not in called_balls:
                number += 1
        return number

    def get_winning_squares(self, card, called_balls):
        """Return the winning squares"""
        for squares in self.get_matches(card):
            if self.get_number_to_go_for_squares(card, squares, called_balls) == 0:
                yield squares


class CornersPattern(Pattern):
    """All the corners of the card"""

    name = 'Corners'

    def get_square_offsets(self):
        """Return a sequence of matching square offsets"""
        return [
            [(self.lx, self.by), (self.lx, self.ty), (self.rx, self.by), (self.rx, self.ty)],
        ]


class LinesPattern(Pattern):
    """Straight lines"""

    name = 'Lines'

    def get_square_offsets(self):
        """Return a sequence of matching square offsets"""
        for row in S['card-square-rows']:
            yield [(row, col) for col in S['card-square-cols']]
        for col in S['card-square-cols']:
            yield [(row, col) for row in S['card-square-rows']]
        yield [(row, row) for row in S['card-square-rows']]
        yield [(-row, row) for row in S['card-square-rows']]


class CoverallPattern(Pattern):
    """A blackout of the entire card"""

    name = 'Coverall'

    def get_square_offsets(self):
        """Return a sequence of matching square offsets"""
        yield [
            (row, col) for row in S['card-square-rows'] for col in S['card-square-cols']
        ]


class CenterPattern(Pattern):
    """All the center squares"""

    name = 'Center'

    def get_square_offsets(self):
        """Return a sequence of matching square offsets"""
        yield [
            (row, col) for row in S['card-square-rows'][1:-1] for col in S['card-square-cols'][1:-1]
        ]


class StampPattern(Pattern):
    """A stamp in one corner"""

    name = 'Stamp'

    def get_square_offsets(self):
        """Return a sequence of matching square offsets"""
        yield [
            (row, col) for row in S['card-square-rows'][:-3] for col in S['card-square-cols'][:-3]
        ]
        yield [
            (row, col) for row in S['card-square-rows'][3:] for col in S['card-square-cols'][3:]
        ]
        yield [
            (row, col) for row in S['card-square-rows'][:-3] for col in S['card-square-cols'][3:]
        ]
        yield [
            (row, col) for row in S['card-square-rows'][3:] for col in S['card-square-cols'][:-3]
        ]


PATTERNS = [
    LinesPattern(),
    StampPattern(),
    CornersPattern(),
    CenterPattern(),
    CoverallPattern(),
]