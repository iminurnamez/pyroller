"""Component that allows the player to select how many cards to play"""

from ...events import EventAware
from . import utils
from . import loggable
from .settings import SETTINGS as S
from . import events


class CardSelector(utils.DrawableGroup, loggable.Loggable, EventAware):
    """Component to allow the player to select how many cards to play"""
    
    def __init__(self, name, state):
        """Initialise the component"""
        self.addLogger()
        self.initEvents()
        #
        self.name = name
        self.state = state
        #
        self.ui = self.create_ui()
        self.number_of_cards = S['card-selection-default']

    def create_ui(self):
        """Create the UI for the component"""
        ui = utils.ClickableGroup()
        #
        x, y = S['card-selection-position']
        dx, dy = S['card-selection-offsets']
        #
        # Create buttons
        for idx, (text, number) in enumerate(S['card-selection']):
            button = utils.ImageOnOffButton(
                text, (x + idx * dx, y + idx * dy),
                'bingo-blue-button', 'bingo-blue-off-button', 'tiny-button',
                text,
                number == S['card-selection-default'],
                self.select_card_number, (idx, number),
                scale=S['tiny-button-scale']
            )
            self.append(button)
            ui.append(button)
        #
        return ui

    def select_card_number(self, arg):
        """A card selection button was pressed"""
        clicked_idx, number = arg
        self.number_of_cards = number
        self.log.info('Pressed card selection button {0}, number cards {1}'.format(clicked_idx, number))
        for idx, button in enumerate(self):
            button.state = idx == clicked_idx
        #
        self.processEvent((events.E_NUM_CARDS_CHANGED, number))