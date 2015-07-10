"""Implementation of the dealer cards

These work like the player cards but show less detail.

"""

from . import bingocard


class DealerSquare(bingocard.BingoSquare):
    """A square on a dealer card"""

    show_label = False
    show_mouse_over = False
    style_name = 'dealer-square-label'


class DealerCard(bingocard.BingoCard):
    """The dealer card"""

    card_owner = bingocard.T_DEALER
    square_class = DealerSquare
    label_class = None
    style_name = 'dealer-card-square'
    card_success_sound = 'bingo-card-lost'


class DealerCardCollection(bingocard.CardCollection):
    """A collection of dealer cards"""

    card_class = DealerCard
