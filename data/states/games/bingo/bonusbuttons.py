"""UI for a button bar of bonus buttons"""

from ....components import common
from ....components import loggable
from .settings import SETTINGS as S
from .... import events
from . import events as event_types


S_OFF = 0
S_ON = 1
S_ACTIVE = 2


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
            button_name, duration, action = item
            button = common.MultiStateButton(
                'bonus-button-{0}'.format(button_name), (x + i * dx, y + i * dy),
                ['bingo-bonus-off', 'bingo-bonus-on', 'bingo-bonus-active'],
                'bonus-button-text',
                button_name, S_OFF, S,
            )
            button.linkEvent(common.E_MOUSE_CLICK, self.button_click)
            button.action = action
            button.duration = duration
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
                speed_up=S['bonus-randomize-button-speed-up'],
                states=(S_OFF, S_ON)
            )
        )

    def button_click(self, button, arg):
        """A button was clicked"""
        if button.state:
            self.log.info('Clicked on button {0}'.format(button.name))
            if button.action:
                button.action(self.state)
            self.state.add_generator(
                'flash-bonus-button',
                self.flash_bonus_button(button, button.duration)
            )

    def flash_bonus_button(self, button, duration):
        """Flash the bonus button"""
        flash_on, flash_off = S['bonus-active-flash-on'], S['bonus-active-flash-off']
        for i in range(int(duration / (flash_on + flash_off))):
            button.state = S_ACTIVE
            yield flash_on * 1000
            button.state = S_ON
            yield flash_off * 1000
        button.state = S_OFF
