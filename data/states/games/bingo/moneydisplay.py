"""Classes to display the total amount of money that the player has"""

from ....components import common, loggable
from .settings import SETTINGS as S


class MoneyDisplay(common.DrawableGroup, loggable.Loggable):
    """Display for the amount of money the player owns"""

    def __init__(self, name, position, amount, state):
        """Initialise the display"""
        common.DrawableGroup.__init__([])
        self.addLogger()
        #
        self.state = state
        self.num_digits = S['money-num-digits']
        self.amount = amount
        x, y = position
        dx, dy = S['money-offsets']
        digits = self.get_desired_digits()
        #
        for i in range(self.num_digits + 1):
            self.append(MoneyDigit(
                'money-digit-{0}'.format(i + 1),
                (x + i * dx, y + i * dy),
                digits[i],
                state
            ))

    def get_desired_digits(self):
        """Return the digits to use"""
        return '${1:0{0}d}'.format(self.num_digits, self.amount)

    def add_money(self, amount):
        """Add or remove money from the display"""
        self.set_money(self.amount + amount)

    def set_money(self, amount):
        """Set the amount of money"""
        self.amount = amount
        for digit, item in zip(self.get_desired_digits(), self):
            item.set_digit(digit)


class MoneyDigit(common.DrawableGroup, loggable.Loggable):
    """Display for a single digit of a number"""

    def __init__(self, name, position, value, state):
        """Initialise the display"""
        common.DrawableGroup.__init__([])
        self.addLogger()
        #
        self.state = state
        self.ox, self.oy = self.x, self.y = position
        self.dx, self.dy = S['money-hide-offsets']
        self.background = common.NamedSprite(
            'digit-background', position, 'bingo-money-display',
        )
        self.text = common.getLabel(
            'money-digit', position, value, S
        )
        #
        self.append(self.background)
        self.append(self.text)
        #
        self.new_value = None
        self.hider = None

    def set_digit(self, digit):
        """Set the current digit"""
        self.hider = self.state.add_generator(
            'digit-hider', self.hide_and_show_new(digit)
        )

    def hide_and_show_new(self, digit):
        """Hide this display and then reshow with new digit"""
        # TODO: refactor the movement logic here - this should be built into the Drawable class
        if digit != self.text.text:
            self.new_value = digit
            for i in range(S['money-hide-repeats']):
                for item in self:
                    item.rect.x += self.dx
                    item.rect.y += self.dy
                yield 1
            #
            self.text.rect_attr = {'x': self.text.rect.x, 'y': self.text.rect.y}
            self.text.set_text(self.new_value)
            #
            for i in range(S['money-hide-repeats']):
                for item in self:
                    item.rect.x -= self.dx
                    item.rect.y -= self.dy
                yield 1
