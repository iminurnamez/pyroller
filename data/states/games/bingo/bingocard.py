"""Classes that manage and display bingo cards"""

import pygame as pg
import random

from data.prepare import BROADCASTER as B
from data.components import common
from .settings import SETTINGS as S
from . import events

# Highlight states
S_NONE = 0
S_GOOD = 1
S_BAD = 2

# States for the card itself
S_OFF = 0
S_WON = 1
S_LOST = 2

# Types of card
T_UNKNOWN = 'unknown'
T_PLAYER = 'player'
T_DEALER = 'dealer'


class BingoLabel(common.Clickable):
    """A label on a bingo card"""

    style_name = 'square-number'
    highlight_names = [None, 'bingo-label-highlight', 'bingo-label-bad-highlight']
    show_label = True
    show_mouse_over = True

    def __init__(self, name, card, offset, text):
        """Initialise the label"""
        self.name = name
        self.offset = offset
        self.text = text
        self.highlighted_state = S_NONE
        self.card = card
        self.is_active = True
        #
        self.x, self.y = card.x + offset[0], card.y + offset[1]
        self.label = common.getLabel(self.style_name, (self.x, self.y), text, S)
        self.highlighters = [
            self.get_highlighter(highlighter_name)
            for highlighter_name in self.highlight_names

        ]
        self.mouse_highlight = common.NamedSprite(
            'bingo-mouse-highlight', (self.x, self.y), scale=self.get_scale())
        #
        super(BingoLabel, self).__init__(name, self.label.rect)

    def get_highlighter(self, name):
        """Return a highlighter sprite"""
        return common.NamedSprite(name, (self.x, self.y), scale=self.get_scale()) if name else None

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
        elif self.highlighters[self.highlighted_state]:
            self.highlighters[self.highlighted_state].draw(surface)
        if self.show_label:
            self.label.draw(surface)

    def reset(self):
        """Reset the label"""
        self.highlighted_state = S_NONE

    def handle_mouse_enter(self):
        """Handle when the mouse enters"""
        if self.show_mouse_over:
            self.card.set_dirty()

    def handle_mouse_leave(self):
        """Handle when the mouse enters"""
        if self.show_mouse_over:
            self.card.set_dirty()


class BingoSquare(BingoLabel):
    """A square on a bingo card"""

    style_name = 'square-label'
    highlight_names = [None, 'bingo-highlight', 'bingo-bad-highlight']

    def __init__(self, name, card, offset, number):
        """Initialise the square"""
        super(BingoSquare, self).__init__(name, card, offset, number)
        #
        self.is_called = False
        self.marker = common.NamedSprite(
            'bingo-marker', (self.x, self.y), scale=self.get_scale())
        #
        self.is_focused = False
        self.focus_marker = common.NamedSprite(
            'bingo-close-highlight', (self.x, self.y), scale=self.get_scale()
        )

    def draw(self, surface):
        """Draw the square"""
        if self.is_called:
            self.marker.draw(surface)
        super(BingoSquare, self).draw(surface)
        if self.is_active and self.is_focused:
            self.focus_marker.draw(surface)

    def handle_click(self):
        """The number was clicked on"""
        if not self.is_active:
            return
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


class BingoCard(common.Clickable):
    """A bingo card comprising a number of squares"""

    card_owner = T_UNKNOWN
    square_class = BingoSquare
    label_class = BingoLabel
    style_name = 'card-square'
    card_success_sound = 'unknown'
    card_back = None
    use_cache = False

    def __init__(self, name, position, state, index):
        """Initialise the bingo card"""
        super(BingoCard, self).__init__(name)
        #
        self.state = state
        self.x, self.y = position
        self.index = index
        #
        self.squares = common.KeyedDrawableGroup()
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
        self.labels = common.KeyedDrawableGroup()
        if self.label_class:
            y_offset = min(S['card-square-rows']) - 1
            for x, letter in zip(S['card-square-cols'], 'BINGO'):
                self.labels[letter] = self.label_class(
                    '{0} {1} label'.format(self.name, letter),
                    self, (square_offset * x, square_offset * y_offset + S['card-square-header-offset'][1]), letter
                )
        #
        self.clickables = common.ClickableGroup(self.squares.values())
        self.drawables = common.DrawableGroup([
            self.squares, self.labels,
        ])
        #
        # The back of the card
        if self.card_back:
            dx, dy = S['square-back-offset']
            self.card_back_image = common.NamedSprite(
                'bingo-card-back', (position[0] + dx, position[1] + dy), scale=S['square-back-scale']
            )
            self.drawables.append(self.card_back_image)
        #
        self.card_state = S_NONE
        #
        self.potential_winning_squares = []
        self.is_active = True
        #
        self.cache = None
        self.w, self.h = S['square-cache-size']
        self.cached_rect = pg.Rect(position[0] - self.w / 2, position[1] - self.h / 2, self.w, self.h)

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
        if not self.cache or not self.use_cache:
            self.drawables.draw(surface)
            self.cache = surface.subsurface(self.cached_rect).copy()
        else:
            surface.blit(self.cache, (self.x - self.w / 2, self.y - self.h / 2))

    def process_events(self, event, scale=(1, 1)):
        """Process clicking events"""
        self.clickables.process_events(event, scale)

    def call_square(self, number):
        """Call a particular square"""
        if not self.active:
            return
        for square in self.squares.values():
            if square.text == number:
                square.is_called = True
        self.called_squares.append(number)
        self.update_squares_to_go()
        self.set_dirty()

    def reset_square(self, number):
        """Reset a particular square"""
        if not self.active:
            return
        for square in self.squares.values():
            if square.text == number:
                square.is_called = False
        self.called_squares.remove(number)
        self.update_squares_to_go()
        self.set_dirty()

    def reset(self):
        """Reset the card"""
        for square in self.squares.values():
            square.reset()
        for label in self.labels.values():
            label.reset()
        self.called_squares = []
        self.update_squares_to_go()
        self.active = True
        self.card_state = S_NONE
        self.set_dirty()

    def update_squares_to_go(self):
        """Update a card with the number of squares to go"""
        number_to_go, self.potential_winning_squares = self.state.winning_pattern.get_number_to_go_and_winners(self, self.called_squares)
        #
        # Check if a line completed
        if self.active and number_to_go == 0:
            for squares in self.state.winning_pattern.get_winning_squares(self, self.called_squares):
                state = None
                missing_squares = self.state.get_missing_squares(squares)
                if not missing_squares:
                    self.state.add_generator('flash-squares', self.flash_squares(squares, S_GOOD, S_GOOD))
                    self.state.play_sound(self.card_success_sound)
                    self.set_card_state(S_WON)
                else:
                    self.state.add_generator('flash-squares', self.flash_squares(missing_squares, S_BAD, S_BAD))
                    self.state.play_sound('bingo-card-failure')
                    self.set_card_state(S_LOST)
                B.processEvent((events.E_CARD_COMPLETE, self))
            #
            self.active = False

    def highlight_column(self, column):
        """Highlight a particular column"""
        if self.label_class and (self.active or column is None):
            for letter, label in self.labels.items():
                label.highlighted_state = S_NONE if letter != column else S_GOOD
        self.set_dirty()

    def flash_squares(self, squares, on_state, end_state):
        """Flash a set of squares"""
        for state, delay in S['card-winning-flash-timing']:
            for square in squares:
                square.highlighted_state = on_state if state else S_NONE
                square.is_focused = False
            self.set_dirty()
            yield delay * 1000
        #
        for square in squares:
            square.highlighted_state = end_state
        self.set_dirty()

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

    def flash_labels(self):
        """Flash labels in a nice pattern"""
        on_time = S['label-flash-delay-on'] * 1000
        #
        # One at a time
        for letters in S['label-flash-states']:
            for letter in 'BINGO':
                self.labels[letter].highlighted_state = letter in letters
            self.set_dirty()
            yield on_time

    def set_card_state(self, state):
        """Set the card state"""
        self.log.info('Set card state {0} {1}'.format(self, state))
        self.card_state = state
        self.highlight_column(None)

    def set_dirty(self):
        """Mark the card as dirty"""
        self.cache = None


class CardCollection(common.ClickableGroup, common.DrawableGroup):
    """A set of bingo cards"""

    card_class = NotImplementedError

    def __init__(self, name, position, offsets, state):
        """Initialise the collection"""
        self.name = name
        self.x, self.y = position
        self.state = state
        #
        common.ClickableGroup.__init__(self)
        common.DrawableGroup.__init__(self, [self.card_class(
            '%s(%d)' % (self.name, i + 1),
            (self.x + x, self.y + y),
            state, i) for i, (x, y) in enumerate(offsets)]
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
