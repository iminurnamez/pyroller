"""Classes that manage and display bingo cards"""

import random

from ... import prepare
from .settings import SETTINGS as S
from . import utils


class BingoLabel(utils.Clickable):
    """A label on a bingo card"""

    style_name = 'square-label'

    def __init__(self, name, card, offset, text):
        """Initialise the label"""
        self.name = name
        self.offset = offset
        self.text = text
        self.is_highlighted = False
        #
        self.x, self.y = card.x + offset[0], card.y + offset[1]
        self.label = utils.getLabel(self.style_name, (self.x, self.y), text)
        self.highlighter = utils.NamedSprite('bingo-highlight', (self.x, self.y))
        self.mouse_highlight = utils.NamedSprite('bingo-mouse-highlight', (self.x, self.y))
        #
        super(BingoLabel, self).__init__(name, self.label.rect)

    def handle_click(self):
        """Respond to being clicked on"""
        pass

    def draw(self, surface):
        """Draw the square"""
        if self.mouse_over:
            self.mouse_highlight.draw(surface)
        elif self.is_highlighted:
            self.highlighter.draw(surface)
        self.label.draw(surface)


class BingoSquare(BingoLabel):
    """A square on a bingo card"""

    style_name = 'square-number'

    def __init__(self, name, card, offset, number):
        """Initialise the square"""
        super(BingoSquare, self).__init__(name, card, offset, number)
        #
        self.is_called = False
        self.marker = utils.NamedSprite('bingo-marker', (self.x, self.y))

    def draw(self, surface):
        """Draw the square"""
        super(BingoSquare, self).draw(surface)
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
        self.squares = utils.KeyedDrawableGroup()
        square_offset = S['card-square-offset']
        chosen_numbers = set()
        #
        # Create the numbered squares
        for x, y in S['card-square-scaled-offsets']:
            #
            # Get a number for this column
            number = self.get_random_number(x, chosen_numbers)
            chosen_numbers.add(number)
            #
            # Place on the card
            self.squares[(x, y)] = BingoSquare(
                '{0} [{1}, {2}]'.format(self.name, x, y),
                self, (square_offset * x, square_offset * y), number
            )
        #
        # Create the labels
        self.labels = utils.KeyedDrawableGroup()
        y_offset = min(S['card-square-rows']) - 1
        for x, letter in zip(S['card-square-cols'], 'BINGO'):
            self.labels[x] = BingoLabel(
                '{0} {1} label'.format(self.name, letter),
                self, (square_offset * x, square_offset * y_offset), letter
            )
        #
        self.clickables = utils.ClickableGroup(self.squares.values())

    def get_random_number(self, column, chosen):
        """Return a random number for the column, making sure not to duplicate"""
        while True:
            number = random.choice(S['card-numbers'][column])
            if number not in chosen:
                return number

    def draw(self, surface):
        """Draw the square"""
        self.squares.draw(surface)
        self.labels.draw(surface)

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