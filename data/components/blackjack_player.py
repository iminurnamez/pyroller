import pygame as pg
from collections import OrderedDict, defaultdict
from .. import prepare
from ..components.chips import Chip, ChipStack, cash_to_chips
from ..components.blackjack_hand import Hand

class Player(object):
    def __init__(self, cash=0, chips=None):
        self.screen_width = pg.display.get_surface().get_width()
        self.cash = cash
        if chips is None:
            chips = cash_to_chips(self.cash)
            self.cash = 0            
        self.chips = OrderedDict()
        self.chips_bottomleft = (20, 700)
        left, bottom = self.chips_bottomleft
        for color in Chip.chip_values:
            self.chips[color] = ChipStack([x for x in chips if x.color == color], (left, bottom))
            left += 50
        self.chip_stacks_rect = pg.Rect(0, 0, left - self.chips_bottomleft[0], 100)
        self.chip_stacks_rect.bottomleft = self.chips_bottomleft
        self.cash = 0
        self.hand_tls = [(250, 450)]
        self.hands = [Hand(tl) for tl in self.hand_tls]
        for hand in self.hands:
            hand.slots = [pg.Rect(hand.tl, prepare.CARD_SIZE)]
        
    def add_slot(self, hand):
        w, h = prepare.CARD_SIZE
        hand.slots.append(hand.slots[-1].move(w // 3, 0))
        
    def get_chip_total(self):
        total = 0
        for color in self.chips:
            total += Chip.chip_values[color] * len(self.chips[color].chips)
        return total
    
    def withdraw_chips(self, amount):
        chips = cash_to_chips(self.get_chip_total() - amount)
        withdrawal = cash_to_chips(amount)
        left, bottom = self.chips_bottomleft
        for color in Chip.chip_values:
            self.chips[color] = ChipStack([x for x in chips if x.color == color], (left, bottom))
            left += 50
        return withdrawal

    def add_chips(self, chips):
        for chip in chips:
            self.chips[chip.color].chips.append(chip)
        for stack in self.chips.values():
            stack.align()
                    
    def update(self):
        pass
        
    def draw_chips(self, surface):
        for stack in self.chips.values():
            stack.draw(surface)
    
    def draw_hand(self, surface):
        for hand in self.hands:
            for card in hand.cards:
                card.draw(surface)
            self.draw_hand_bet(hand, surface)
            
    def move_hands(self, offset):
        for hand in self.hands:
            self.move_hand(hand, offset)
         
    def move_hand(self, hand, offset):
        for slot in hand.slots:
            slot.move_ip(offset)
        for card in hand.cards:
            card.rect.move_ip(offset)
            card.pos = card.rect.center
        hand.tl = (hand.tl[0] + offset[0],
                        hand.tl[1] + offset[1])
        
    def draw_hand_bet(self, hand, surface):
        left, bottom = hand.tl
        offsets = [(30, -20), (70, -20), (20, -60), (60, -60), (100, -60)]
        stack_spots = [(left + x, bottom + y) for x,y in offsets]
        chips = defaultdict(list)
        for chip in hand.bet:
            chips[chip.color].append(chip)
        stacks = [ChipStack(chips[color], (0, 0)) for color in chips]
        stacks = sorted(stacks, key=lambda x: len(x.chips))
        for stack, spot in zip(stacks, stack_spots):
            stack.bottomleft = spot
            stack.align()
        for stack in stacks[::-1]:
            stack.draw(surface)
            
            
    def draw(self, surface):
        self.draw_hand(surface)
        self.draw_chips(surface)
    
            
    
                
        
            