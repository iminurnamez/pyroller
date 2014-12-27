"""Classes that manage and display bingo cards"""

import random

from ...prepare import BROADCASTER as B
from .settings import SETTINGS as S
from . import utils
from . import events


class BingoLabel(utils.Clickable):
    """A label on a bingo card"""

    style_name = 'square-number'
    highlight_name = 'bingo-label-highlight'
    show_label = True
    show_mouse_over = True

    def __init__(self, name, card, offset, text):
        """Initialise the label"""
        self.name = name
        self.offset = offset
        self.text = text
        self.is_highlighted = False
        self.card = card
        self.is_active = True
        #
        self.x, self.y = card.x + offset[0], card.y + offset[1]
        self.label = utils.getLabel(self.style_name, (self.x, self.y), text)
        self.highlighter = utils.NamedSprite(
            self.highlight_name, (self.x, self.y), scale=self.get_scale())
        self.mouse_highlight = utils.NamedSprite(
            'bingo-mouse-highlight', (self.x, self.y), scale=self.get_scale())
        #
        super(BingoLabel, self).__init__(name, self.label.rect)

    def get_scale(self):
        """Return the scale to use for graphics"""
        return S['{0}-scale'.format(self.style_name)]

    def handle_click(self):
        """Respond to being clicked on"""
        pass

    def draw(self, surface):
        """Draw the square"""
        if self.is_active and self.show_mouse_over and self.mouse_over:
            self.mouse_highlight.draw(surface)
        elif self.is_highlighted:
            self.highlighter.draw(surface)
        if self.show_label:
            self.label.draw(surface)

    def reset(self):
        """Reset the label"""
        self.is_highlighted = False


class BingoSquare(BingoLabel):
    """A square on a bingo card"""

    style_name = 'square-label'
    highlight_name = 'bingo-highlight'

    def __init__(self, name, card, offset, number):
        """Initialise the square"""
        super(BingoSquare, self).__init__(name, card, offset, number)
        #
        self.is_called = False
        self.marker = utils.NamedSprite(
            'bingo-marker', (self.x, self.y), scale=self.get_scale())
        #
        self.is_focused = False
        self.focus_marker = utils.NamedSprite(
            'bingo-close-highlight', (self.x, self.y), scale=self.get_scale()
        )

    def draw(self, surface):
        """Draw the square"""
        super(BingoSquare, self).draw(surface)
        if self.is_called:
            self.marker.draw(surface)
        if self.is_active and self.is_focused:
            self.focus_marker.draw(surface)

    def handle_click(self):
        """The number was clicked on"""
        if not self.is_active:
            return
        self.marker.rotate_to(random.randrange(0, 360))
        self.is_called = not self.is_called
        if self.is_called:
            self.card.call_square(self.text)
            B.processEvent((events.E_PLAYER_PICKED, self))
        else:
            self.card.reset_square(self.text)
            B.processEvent((events.E_PLAYER_UNPICKED, self))

    def reset(self):
        """Reset the square"""
        super(BingoSquare, self).reset()
        self.is_called = False
        self.is_focused = False

    def set_number(self, number):
        """Set the number to use"""
        self.text = number
        self.label.set_text(str(number))


class BingoCard(utils.Clickable):
    """A bingo card comprising a number of squares"""

    square_class = BingoSquare
    show_col_labels = True
    style_name = 'card-square'

    def __init__(self, name, position, state):
        """Initialise the bingo card"""
        super(BingoCard, self).__init__(name)
        #
        self.state = state
        self.x, self.y = position
        self.squares = utils.KeyedDrawableGroup()
        square_offset = S['{0}-offset'.format(self.style_name)]
        chosen_numbers = set()
        self.called_squares = []
        #
        # Create the numbered squares
        numbers = self.get_random_number_set()
        for x, y in S['card-square-scaled-offsets']:
            self.squares[(x, y)] = self.square_class(
                '{0} [{1}, {2}]'.format(self.name, x, y),
                self, (square_offset * x, square_offset * y),
                numbers[(x, y)]
            )
        #
        # Create the labels
        self.labels = utils.KeyedDrawableGroup()
        if self.show_col_labels:
            y_offset = min(S['card-square-rows']) - 1
            for x, letter in zip(S['card-square-cols'], 'BINGO'):
                self.labels[letter] = BingoLabel(
                    '{0} {1} label'.format(self.name, letter),
                    self, (square_offset * x, square_offset * y_offset), letter
                )
        #
        # The label for display of the remaining squares on the card
        label_offset = S['{0}-remaining-label-offset'.format(self.style_name)]
        self.remaining_label = utils.getLabel(
            'card-remaining-label',
            (self.x + label_offset[0], self.y + label_offset[1]),
            'Player card'
        )
        #
        self.clickables = utils.ClickableGroup(self.squares.values())
        self.drawables = utils.DrawableGroup([
            self.squares, self.labels, self.remaining_label,
        ])
        #
        self.potential_winning_squares = []
        self.is_active = True

    def set_new_numbers(self, numbers=None):
        """Draw new numbers for this card"""
        if numbers is None:
            numbers = self.get_random_number_set()
        for x, y in numbers:
            self.squares[(x, y)].set_number(numbers[(x, y)])

    def get_numbers(self):
        """Return the numbers on this card"""
        numbers = {}
        for x, y in self.squares:
            numbers['{0}:{1}'.format(x, y)] = self.squares[(x, y)].text
        return numbers

    def get_random_number_set(self):
        """Return a set of random numbers to use for this card"""
        numbers = {}
        chosen_numbers = set()
        for x, y in S['card-square-scaled-offsets']:
            number = self.get_random_number(x, chosen_numbers)
            chosen_numbers.add(number)
            numbers[(x, y)] = number
        return numbers

    def get_random_number(self, column, chosen):
        """Return a random number for the column, making sure not to duplicate"""
        while True:
            number = random.choice(S['card-numbers'][column])
            if number not in chosen:
                return number

    def draw(self, surface):
        """Draw the square"""
        self.drawables.draw(surface)

    def process_events(self, event, scale=(1, 1)):
        """Process clicking events"""
        self.clickables.process_events(event, scale)

    def set_label(self, text):
        """Set the card label text"""
        self.remaining_label.set_text(str(text))

    def call_square(self, number):
        """Call a particular square"""
        if not self.active:
            return
        for square in self.squares.values():
            if square.text == number:
                square.is_called = True
        self.called_squares.append(number)
        self.update_squares_to_go()

    def reset_square(self, number):
        """Reset a particular square"""
        if not self.active:
            return
        for square in self.squares.values():
            if square.text == number:
                square.is_called = False
        self.called_squares.remove(number)
        self.update_squares_to_go()

    def reset(self):
        """Reset the card"""
        for square in self.squares.values():
            square.reset()
        for label in self.labels.values():
            label.reset()
        self.called_squares = []
        self.update_squares_to_go()
        self.active = True

    def update_squares_to_go(self):
        """Update a card with the number of squares to go"""
        number_to_go, self.potential_winning_squares = self.state.winning_pattern.get_number_to_go_and_winners(self, self.called_squares)
        #
        self.set_label(
            '{0} to go'.format(number_to_go))
        #
        # Check if a line completed
        if self.active and number_to_go == 0:
            for squares in self.state.winning_pattern.get_winning_squares(self, self.called_squares):
                missing_squares = self.state.get_missing_squares(squares)
                if not missing_squares:
                    self.state.add_generator('flash-squares', self.flash_squares(squares, True))
                    self.state.play_sound('bingo-card-success')
                else:
                    self.state.add_generator('flash-squares', self.flash_squares(missing_squares, False))
                    self.state.play_sound('bingo-card-failure')
            #
            self.active = False

    def highlight_column(self, column):
        """Highlight a particular column"""
        if self.show_col_labels:
            for letter, label in self.labels.items():
                label.is_highlighted = letter == column

    def flash_squares(self, squares, end_state):
        """Flash a set of squares"""
        for state, delay in S['card-winning-flash-timing']:
            for square in squares:
                square.is_highlighted = state
                square.is_focused = False
            yield delay * 1000
        #
        for square in squares:
            square.is_highlighted = end_state

    @property
    def active(self):
        """Whether the card is active"""
        return self.is_active

    @active.setter
    def active(self, value):
        """Set whether the card is active"""
        self.is_active = value
        for square in self.squares.values():
            square.is_active = value


class CardCollection(utils.ClickableGroup, utils.DrawableGroup):
    """A set of bingo cards"""

    card_class = NotImplementedError

    def __init__(self, name, position, offsets, state):
        """Initialise the collection"""
        self.name = name
        self.x, self.y = position
        self.state = state
        #
        utils.ClickableGroup.__init__(self)
        utils.DrawableGroup.__init__(self, [self.card_class(
            '%s(%d)' % (self.name, i + 1),
            (self.x + x, self.y + y),
            state) for i, (x, y) in enumerate(offsets)]
        )

    def reset(self):
        """Reset all the cards"""
        for card in self:
            card.reset()

    def draw_new_numbers(self):
        """Draw new numbers for all cards"""
        for card in self:
            card.set_new_numbers()

    def get_card_numbers(self):
        """Return the numbers on all the cards for recreating later"""
        numbers = []
        for card in self:
            numbers.append(card.get_numbers())
        return numbers

    def set_card_numbers(self, numbers):
        """Set the numbers on all the cards"""
        for card in self:
            if not numbers:
                break
            #
            # Recreate the right form of the dictionary
            new_numbers = numbers.pop(0)
            new_numbers_dict = {}
            for text, number in new_numbers.items():
                x, y = map(int, text.split(':'))
                new_numbers_dict[(x, y)] = number
            #
            # Now set numbers in the card
            card.set_new_numbers(new_numbers_dict)