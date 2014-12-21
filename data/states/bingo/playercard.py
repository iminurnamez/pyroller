"""Represents the player's bingo card"""


from . import bingocard
from .settings import SETTINGS as S
from . import utils


class PlayerSquare(bingocard.BingoSquare):
    """A square on a player card"""

    style_name = 'player-square-label'


class PlayerCard(bingocard.BingoCard):
    """The player card"""

    square_class = PlayerSquare
    style_name = 'player-card-square'

    def __init__(self, name, position, state):
        """Initialise the card"""
        super(PlayerCard, self).__init__(name, position, state)
        #
        self.initial_value = self.value = S['card-initial-value']
        #
        # The button to double down the bet
        label_offset = S['card-double-down-button-offset']
        self.double_down_button = utils.ImageOnOffButton(
            'double-down',
            (self.x + label_offset[0], self.y + label_offset[1]),
            'bingo-red-button', 'bingo-red-off-button',
            'card-double-down-button',
            'Double', True, self.double_down, None,
            S['small-button-scale'],
        )
        #
        # The label for display of the card value
        label_offset = S['card-value-label-offset']
        self.value_label = utils.getLabel(
            'card-value-label',
            (self.x + label_offset[0], self.y + label_offset[1]),
            '*PLACEHOLDER*'
        )
        self.update_value(self.initial_value)
        #
        self.drawables.extend([
            self.double_down_button, self.value_label
        ])
        self.clickables.append(self.double_down_button)

    def update_value(self, value):
        """Update the value of the card"""
        self.value = value
        self.value_label.set_text('Card value ${0}'.format(value))

    def double_down(self, arg):
        """Double down the card"""
        if self.double_down_button.state:
            self.log.info('Doubling down on the card')
            self.update_value(self.value * 2)
            self.double_down_button.state = False
            self.state.add_generator('re-enable-double-down', self.enable_double_down_button(
                S['card-double-down-delay'] * 1000
            ))

    def enable_double_down_button(self, delay):
        """Re-enable the double down button"""
        yield delay
        self.double_down_button.state = True

    def reset(self):
        """Reset the card"""
        super(PlayerCard, self).reset()
        self.update_value(self.initial_value)


class PlayerCardCollection(bingocard.CardCollection):
    """A collection of player cards"""

    card_class = PlayerCard