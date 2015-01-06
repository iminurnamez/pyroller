"""Classes to help with matching patterns of squares on the cards"""

from ...components import common
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

    def get_number_to_go_and_winners(self, card, called_balls):
        """Return the number of squares needed to win and the winning balls"""
        number_to_go = []
        one_winners = set()
        for squares in self.get_matches(card):
            numbers = self.get_numbers_to_go_for_squares(card, squares, called_balls)
            if len(numbers) == 1:
                one_winners.update(numbers)
            number_to_go.append(len(numbers))
        #
        return min(number_to_go), one_winners

    def get_numbers_to_go_for_squares(self, card, squares, called_balls):
        """Return the numbers of the squares needed to win from a particular set of squares"""
        numbers = set()
        for square in squares:
            if square.text not in called_balls:
                numbers.add(square)
        return numbers

    def get_winning_squares(self, card, called_balls):
        """Return the winning squares"""
        for squares in self.get_matches(card):
            if len(self.get_numbers_to_go_for_squares(card, squares, called_balls)) == 0:
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


class PatternButton(common.ImageOnOffButton):
    """A button to show the pattern"""

    def __init__(self, idx, position, on_filename, off_filename, text_properties, text, state,
                 settings, scale=1.0):
        super(PatternButton, self).__init__(PATTERNS[idx].name, position, on_filename, off_filename,
                                            text_properties,  text, state,  settings, scale)
        #
        # Label needs to be moved over because of the image
        self.label.rect.x += self.label.rect.w / 2 - settings['winning-pattern-label-width']
        #
        # Put the right logo image on there
        x, y = position
        self.logo_on_image = common.NamedSprite.from_sprite_sheet(
            'patterns', (6, 2), (idx, 0),
            (x - settings['winning-pattern-logo-offset'], y),
            scale=settings['winning-pattern-logo-scale']
        )
        self.logo_off_image = common.NamedSprite.from_sprite_sheet(
            'patterns', (6, 2), (idx, 1),
            (x - settings['winning-pattern-logo-offset'], y),
            scale=settings['winning-pattern-logo-scale']
        )

    def draw(self, surface):
        """Draw the button"""
        super(PatternButton, self).draw(surface)
        if self.state:
            self.logo_on_image.draw(surface)
        else:
            self.logo_off_image.draw(surface)

class RandomPattern(object):
    """Special pattern to indicate random pattern should be used"""

    name = "Random"


PATTERNS = [
    LinesPattern(),
    StampPattern(),
    CornersPattern(),
    CenterPattern(),
    CoverallPattern(),
    RandomPattern(),
]