"""Classes to display the total amount of money that the player has"""

from ...components import common, loggable
from .settings import SETTINGS as S


class MoneyDisplay(common.DrawableGroup, loggable.Loggable):
    """Display for the amount of money the player owns"""

    def __init__(self, name, position):
        """Initialise the display"""
        common.DrawableGroup.__init__([])
        self.addLogger()
        #
        x, y = position
        dx, dy = S['money-offsets']
        #
        for i in range(S['money-num-digits']):
            self.append(MoneyDigit(
                'money-digit-{0}'.format(i + 1),
                (x + i * dx, y + i * dy),
                '$' if i == 0 else '0',
            ))


class MoneyDigit(common.DrawableGroup, loggable.Loggable):
    """Display for a single digit of a number"""

    def __init__(self, name, position, value):
        """Initialise the display"""
        common.DrawableGroup.__init__([])
        self.addLogger()
        #
        self.background = common.NamedSprite(
            'digit-background', position, 'bingo-money-display',
        )
        self.text = common.getLabel(
            'money-digit', position, value, S
        )
        #
        self.append(self.background)
        self.append(self.text)