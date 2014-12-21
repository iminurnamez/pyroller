"""Implementation of the dealer cards

These work like the player cards but show less detail.

"""

from . import bingocard
from .settings import SETTINGS as S
from . import utils


class DealerSquare(bingocard.BingoSquare):
    """A square on a dealer card"""

    show_label = False
    show_mouse_over = False


class DealerCard(bingocard.BingoCard):
    """The dealer card"""

    square_class = DealerSquare
    show_col_labels = False


class DealerCardCollection(bingocard.CardCollection):
    """A collection of dealer cards"""

    card_class = DealerCard