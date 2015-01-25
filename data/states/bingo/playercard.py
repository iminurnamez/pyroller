"""Represents the player's bingo card"""

import pygame as pg

from ...components import common
from ... import prepare
from . import bingocard
from .settings import SETTINGS as S
from . import events


class PlayerLabel(bingocard.BingoLabel):
    """A label for the players square"""

    style_name = 'square-number'
    highlight_names = ['bingo-headers-off', 'bingo-headers-on', None]
    show_label = False

    def get_highlighter(self, name):
        """Return the highlighter sprite"""
        if not name:
            return None
        else:
            idx = 'BINGO'.index(self.text)
            main_sprite = common.NamedSprite.from_sprite_sheet(
                name, (5, 1), (idx, 0), (self.x, self.y),
            )
            return main_sprite


class PlayerSquare(bingocard.BingoSquare):
    """A square on a player card"""

    style_name = 'player-square-label'
    highlight_names = ['bingo-highlight-grid', 'bingo-highlight', 'bingo-bad-highlight']


class PlayerCard(bingocard.BingoCard):
    """The player card"""

    card_owner = bingocard.T_PLAYER
    square_class = PlayerSquare
    label_class = PlayerLabel
    style_name = 'player-card-square'
    state_names = ['bingo-value-off', 'bingo-value-win', 'bingo-value-lose']
    card_success_sound = 'bingo-card-success'
    card_back = 'bingo-card-back'
    use_cache = True

    def __init__(self, name, position, state, index):
        """Initialise the card"""
        super(PlayerCard, self).__init__(name, position, state, index)
        #
        self.initial_value = self.value = S['card-initial-value']
        #
        # The button to double down the bet
        label_offset = S['card-double-down-button-offset']
        self.double_down_button = common.ImageOnOffButton(
            'double-down',
            (self.x + label_offset[0], self.y + label_offset[1]),
            'bingo-double-on', 'bingo-double-off',
            'card-double-down-button',
            'Double', True,
            S,
        )
        self.double_down_button.linkEvent(common.E_MOUSE_CLICK, self.double_down)
        #
        # The label for display of the card value
        label_offset = S['card-value-label-offset']
        label_position = (self.x + label_offset[0], self.y + label_offset[1])
        self.value_label = common.getLabel(
            'card-value-label',
            label_position,
            '*PLACEHOLDER*', S
        )
        self.update_value(self.initial_value)
        #
        # Button states
        self.states = [common.NamedSprite(state_name, label_position) for state_name in self.state_names]
        #
        self.drawables.extend([
            self.double_down_button, self.value_label,
        ])
        self.clickables.append(self.double_down_button)

    def update_value(self, value):
        """Update the value of the card"""
        self.value = value
        self.value_label.set_text('${0}'.format(value))

    def double_down(self, obj=None, arg=None):
        """Double down the card"""
        if self.double_down_button.state:
            self.log.info('Doubling down on the card')
            self.update_value(self.value * 2)
            self.double_down_button.state = False
            self.state.add_generator('re-enable-double-down', self.enable_double_down_button(
                S['card-double-down-delay'] * 1000
            ))
            self.state.play_sound('bingo-double-up')
            self.state.add_generator('flash-card-state', self.flash_card_state(bingocard.S_WON, bingocard.S_NONE))

    def enable_double_down_button(self, delay):
        """Re-enable the double down button"""
        yield delay
        self.double_down_button.state = True
        self.set_dirty()

    def reset(self):
        """Reset the card"""
        super(PlayerCard, self).reset()
        self.update_value(self.initial_value)
        self.double_down_button.state = True

    def draw(self, surface):
        """Draw the square"""
        self.states[self.card_state].draw(surface)
        super(PlayerCard, self).draw(surface)

    def set_card_state(self, state):
        """Set the card state and flash it a bit"""
        super(PlayerCard, self).set_card_state(state)
        self.state.add_generator('flash-card-state', self.flash_card_state(self.card_state, state))
        self.double_down_button.state = False
        self.set_dirty()

    def flash_card_state(self, old_state, new_state):
        """Flash the card state"""
        for state, delay in S['card-winning-flash-timing']:
            self.card_state = new_state if state else old_state
            self.set_dirty()
            yield delay * 1000
        #
        super(PlayerCard, self).set_card_state(new_state)
        #
        # Win money if we won
        multiplier = [0, 1, -1][new_state]
        prepare.BROADCASTER.processEvent((events.E_SPEND_MONEY, multiplier * self.value))


class PlayerCardCollection(bingocard.CardCollection):
    """A collection of player cards"""

    card_class = PlayerCard