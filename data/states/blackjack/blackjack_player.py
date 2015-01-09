import pygame as pg
from collections import OrderedDict, defaultdict
from ... import prepare
from ...components.chips import Chip, ChipStack, ChipPile
from .blackjack_hand import Hand


class Player(object):
    def __init__(self, chip_size, cash=0, chips=None):
        self.chip_pile = ChipPile((5, 1000), chip_size, cash=cash, chips=chips)
        self.cash = 0
        self.hand_tls = [(350, 550)]
        self.hands = [Hand(tl) for tl in self.hand_tls]
        for hand in self.hands:
            hand.slots = [pg.Rect(hand.tl, prepare.CARD_SIZE)]
        
    def add_slot(self, hand):
        w, h = prepare.CARD_SIZE
        hand.slots.append(hand.slots[-1].move(w // 3, 0))
    
    def draw_hands(self, surface):
        for hand in self.hands:
            for card in hand.cards:
                card.draw(surface)
            hand.bet.draw(surface)
            
    def move_hands(self, offset):
        for hand in self.hands:
            self.move_hand(hand, offset)
         
    def move_hand(self, hand, offset):
        for slot in hand.slots:
            slot.move_ip(offset)
        for stack in hand.bet.stacks:
            stack.bottomleft = (stack.bottomleft[0] + offset[0],
                                         stack.bottomleft[1] + offset[1])
        for card in hand.cards:
            card.rect.move_ip(offset)
            card.pos = card.rect.center
        hand.tl = (hand.tl[0] + offset[0],
                        hand.tl[1] + offset[1])
        
    def draw(self, surface):
        self.draw_hands(surface)
        self.chip_pile.draw(surface)
