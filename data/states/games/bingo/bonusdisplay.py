"""UI for a bonus counter - when it reaches a limit you get a bonus button"""


from data.components import common
from data.components import loggable
from .settings import SETTINGS as S
from data import events
from . import events as event_types


S_NONE = 0
S_CHARGING_DOWN = 1
S_CHARGING_UP = 2


class BonusDisplay(common.Drawable, loggable.Loggable, events.EventAware):
    """UI for a bonus counter"""

    def __init__(self, name, position, state):
        """Initialise the display"""
        super(BonusDisplay, self).__init__()
        self.addLogger()
        self.initEvents()
        self.name = name
        self.state = state
        #
        self.x, self.y = position
        #
        # Make all the individual lights
        self.off_light = common.NamedSprite.from_sprite_sheet(
            'bingo-bonus-light', (1, 3), (0, 0), position)
        self.on_light = common.NamedSprite.from_sprite_sheet(
            'bingo-bonus-light', (1, 3), (0, 1), position)
        self.charging_light = common.NamedSprite.from_sprite_sheet(
            'bingo-bonus-light', (1, 3), (0, 2), position)
        #
        self.dx, self.dy = S['bonus-light-offset']
        self.max_number = S['bonus-light-number']
        self.number = 0
        #
        self.flasher = None
        self.original_numbers = None
        self.charging = S_NONE

    def draw(self, surface):
        """Draw the lights"""
        for i in range(self.max_number):
            x, y = self.x + self.dx * i, self.y + self.dy * i
            if i < self.number:
                # Light is on
                light = self.off_light if self.charging == S_CHARGING_UP else self.on_light
            else:
                # Light is off
                light = self.charging_light if self.charging != S_NONE else self.off_light
            surface.blit(light.sprite, (x, y))

    def add_bonus(self, number=1):
        """Add a bonus"""
        #
        # If recharging then skip the bonus
        if self.charging != S_NONE:
            return
        #
        # Stop any flashing and restart it
        if self.flasher:
            self.flasher.stop()
            n1, n2 = self.original_numbers
            self.number, number = n1, (n2 - n1) + number
        self.flasher = self.state.add_generator('bonus-flasher', self.flash_bonus(self.number, self.number + number))

    def flash_bonus(self, n1, n2):
        """Flash the bonus"""
        self.original_numbers = n1, n2
        #
        # Flash the lights on and off
        for i in range(S['bonus-flash-repeat']):
            self.number = n2
            yield S['bonus-flash-on'] * 1000
            #
            if n2 >= self.max_number:
                break
            #
            self.number = n1
            yield S['bonus-flash-off'] * 1000

        #
        self.number = n2
        self.flasher = None
        #
        # When we get to the end then recharge the display
        if self.number >= self.max_number:
            self.processEvent((event_types.E_BONUS_REACHED, self))
            self.state.play_sound('bingo-tada')
            self.charging = S_CHARGING_DOWN
            for i in range(self.max_number, 0, -1):
                self.number = i
                yield S['bonus-charge-delay'] * 1000
            #
            self.charging = S_CHARGING_UP
            for i in range(self.max_number):
                self.number = i
                yield S['bonus-charge-delay'] * 1000
            #
            self.charging = S_NONE
            self.number = 0
