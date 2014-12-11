import pygame as pg
from .. import prepare
from ..components.blackjack_hand import Hand

class Dealer(object):
    def __init__(self, cards=None):
        self.hand_tl = (350, 30)
        if cards is not None:
            self.hand = Hand(self.hand_tl, cards)
        else:
            self.hand = Hand(self.hand_tl)
        self.hand.slots = [pg.Rect(self.hand_tl, prepare.CARD_SIZE)]
               
    def add_slot(self):
        w = prepare.CARD_SIZE[0]
        if len(self.hand.slots) < 2:
            move_dist = self.hand.slots[-1].width + 20
        else:
            move_dist = w // 2
        self.hand.slots.append(self.hand.slots[-1].move(move_dist, 0))

    def draw_hand(self, surface):
        for card in self.hand.cards:
            card.draw(surface)