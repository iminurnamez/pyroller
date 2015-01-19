"""UI for a button bar of bonus buttons"""

from ...components import common
from ...components import loggable
from .settings import SETTINGS as S
from ... import events
from . import events as event_types


class BonusButtonsDisplay(common.ClickableGroup, loggable.Loggable, events.EventAware):
    """UI to display a series of bonus buttons"""

    def __init__(self, name, position, state):
        """Initialise the display"""
        super(BonusButtonsDisplay, self).__init__()
        self.name = name
        self.state = state
        self.addLogger()
        self.initEvents()
        #
        self.buttons = common.DrawableGroup()
        x, y = S['bonus-buttons-position']
        dx, dy = S['bonus-buttons-offsets']
        for i, item in enumerate(S['bonus-buttons']):
            button_name, action = item
            button = common.ImageOnOffButton(
                'bonus-button-{0}'.format(button_name), (x + i * dx, y + i * dy),
                'bingo-bonus-on', 'bingo-bonus-off', 'bonus-button-text',
                button_name, False, S,
            )
            button.linkEvent(common.E_MOUSE_CLICK, self.button_click)
            button.action = action
            self.buttons.append(button)
            self.append(button)

    def draw(self, surface):
        """Draw the buttons"""
        self.buttons.draw(surface)

    def button_chosen(self, button):
        """A button was chosen"""
        self.log.info('Button {0} chosen'.format(button.name))

    def pick_new_button(self):
        """Pick a new button"""
        self.state.add_generator(
            'select-bonus-button',
            self.state.randomly_highlight_buttons(
                None, self.buttons,
                S['bonus-randomize-button-number'], S['bonus-randomize-button-delay'],
                self.button_chosen,
                speed_up=S['bonus-randomize-button-speed-up']
            )
        )

    def button_click(self, button, arg):
        """A button was clicked"""
        if button.state:
            self.log.info('Clicked on button {0}'.format(button.name))
            if button.action:
                button.action(self.state)