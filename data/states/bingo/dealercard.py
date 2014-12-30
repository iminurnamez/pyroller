"""Implementation of the dealer cards

These work like the player cards but show less detail.

"""

from . import bingocard
from .settings import SETTINGS as S


class DealerSquare(bingocard.BingoSquare):
    """A square on a dealer card"""

    show_label = False
    show_mouse_over = False
    style_name = 'dealer-square-label'


class DealerCard(bingocard.BingoCard):
    """The dealer card"""

    square_class = DealerSquare
    label_class = None
    style_name = 'dealer-card-square'


class DealerCardCollection(bingocard.CardCollection):
    """A collection of dealer cards"""

    card_class = DealerCard