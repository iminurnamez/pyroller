import pygame as pg
from ... import prepare
from ...components.labels import Blinker, Label
from ...components.cards import Deck
from .video_poker_data import *


class Dealer:
    def __init__(self, topleft, size):
        print("In Dealer init")
        self.rect = pg.Rect(topleft, size)

        self.deck = Deck((20, 20), card_size=(187, 271), infinite=True)

        self.hand = []
        self.hand_len = 0
        self.card_index = None
        self.max_cards = None
        self.revealing = False
        self.held_cards = []
        self.changing_cards = []
        self.waiting = False
        self.playing = False
        self.double_up = False

        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.big_text_size = 100
        self.line_height = 35
        self.text_color = "white"
        self.big_text_color = "red"
        self.text_bg_color = "darkblue"

        self.held_labels = []
        self.double_up_labels = []

        self.text = " insert coins "
        self.no_playing_label = Blinker(self.font, self.big_text_size, self.text, self.big_text_color,
                                        {"center": self.rect.center}, 700, self.text_bg_color)

        self.text = " play 1 to 5 coins "
        self.waiting_label = Blinker(self.font, self.big_text_size, self.text, self.big_text_color,
                                     {"center": self.rect.center}, 700, self.text_bg_color)

        self.card_spacing = 30

        self.animation_speed = 170.0
        self.elapsed = self.animation_speed

        self.deal_sound = prepare.SFX["cardplace2"]
        self.held_sound = prepare.SFX["bingo-ball-chosen"]

    def startup(self):
        print("In Dealer Startup")
        self.hand = self.deck.make_hand()
        self.hand_len = len(self.hand)
        self.build()
        self.card_index = 0
        self.max_cards = len(self.hand)
        self.revealing = False
        self.held_cards = []
        self.changing_cards = list(range(5))
        self.waiting = False
        self.playing = False
        self.double_up = False

    def start_double_up(self):
        for index in range(self.hand_len):
            self.hand[index] = self.deck.draw_card()
        self.held_cards = []
        self.changing_cards = list(range(5))
        # first card
        self.hand[0].face_up = True
        self.toggle_held(0)
        self.build()

    def draw_cards(self):
        for index in range(self.hand_len):
            if index not in self.held_cards:
                self.hand[index] = self.deck.draw_card()
        self.build()
        self.revealing = True

    def build(self):
        print("In Dealer Build")
        x = self.rect.left
        y = self.rect.top + self.line_height
        for index, card in enumerate(self.hand):
            card.rect.left = x
            card.rect.top = y
            label = Label(self.font, self.text_size, 'held', self.text_color,
                          {"bottom": card.rect.top, "centerx": card.rect.centerx})
            self.held_labels.append(label)

            if index == 0:
                label = Label(self.font, self.text_size, 'dealer', self.text_color,
                              {"bottom": card.rect.top, "centerx": card.rect.centerx})
            else:
                label = Label(self.font, self.text_size, 'player', self.text_color,
                              {"bottom": card.rect.top, "centerx": card.rect.centerx})
            self.double_up_labels.append(label)
            x += self.card_spacing + card.rect.w

    def toggle_held(self, index):
        if index in self.held_cards:
            self.held_cards.remove(index)
            self.changing_cards.append(index)
        else:
            self.held_cards.append(index)
            self.changing_cards.remove(index)
        self.held_sound.play()
        self.changing_cards.sort()

    def select_card(self, index):
        self.hand[index].face_up = True
        self.toggle_held(index)
        return self.compare_cards(index)

    def compare_cards(self, index):
        val1 = self.hand[0].value
        val2 = self.hand[index].value

        if val2 == 1:
            return True
        if val1 == 1:
            # if dealer card is an Ace and player isn't an Ace
            return False
        else:
            return not val1 > val2

    def evaluate_hand(self):
        values = []
        suits = []
        for card in self.hand:
            values.append(card.value)
            suits.append(card.suit)

        values.sort()
        suits.sort()

        # if don't match any rank
        rank = NO_HAND

        pairs = []
        are_three = False
        for val in values:
            matches = values.count(val)
            if matches == 2:
                if val not in pairs:
                    pairs.append(val)
            elif matches == 3:
                if not are_three:
                    are_three = True

        pairs_len = len(pairs)
        if pairs_len == 1 and are_three:
            """Full house"""
            rank = HAND_RANKS['FULL_HOUSE']

        elif pairs_len == 1:
            """ Jacks or betters"""
            if 1 in pairs or 11 in pairs or 12 in pairs or 13 in pairs:
                rank = HAND_RANKS['JACKS_OR_BETTER']

        elif pairs_len == 2:
            """Two pair"""
            rank = HAND_RANKS['TWO_PAIR']

        elif are_three:
            """Three of a kind"""
            rank = HAND_RANKS['THREE_OF_A_KIND']

        """Straight, if is an Ace in the hand, Check if other 4 cards are
            K, Q, J, 10 or  2, 3, 4, 5
            else Check if 5 cards are continuous in rank"""
        if 1 in values:
            a = values[1] == 2 and values[2] == 3 \
                and values[3] == 4 and values[4] == 5
            b = values[1] == 10 and values[2] == 11 \
                and values[3] == 12 and values[4] == 13
            is_straight = a or b
        else:
            test_value = values[0] + 1
            is_straight = True
            for i in range(1, 5):
                if values[i] != test_value:
                    is_straight = False
                test_value += 1

        highest = max(values)

        """Flush, previously we sort it, so the array must look like this:
        ['Clubs', 'Diamonds', 'Diamonds', 'Hearts', 'Hearts'],
        so if the first and the last element are the same means that all
        the suits are the same"""
        if suits[0] == suits[4]:
            if is_straight:
                if highest == 13 and 1 in values:
                    rank = HAND_RANKS['ROYAL_FLUSH']
                else:
                    rank = HAND_RANKS['STR_FLUSH']
            else:
                rank = HAND_RANKS['FLUSH']
        elif is_straight:
            rank = HAND_RANKS['STRAIGHT']
        else:
            """4 of a kind, Check for: 4 cards of the same value
            + higher value unmatched card, and Check for: lower ranked unmatched
            card + 4 cards of the same rank"""
            a = values[0] == values[1] == values[2] == values[3]
            b = values[1] == values[2] == values[3] == values[4]
            if a or b:
                rank = HAND_RANKS['4_OF_A_KIND']

        # and finally return the current rank
        return rank

    def get_event(self, mouse_pos):
        if self.playing:
            for index, card in enumerate(self.hand):
                if card.rect.collidepoint(mouse_pos):
                    return index

    def update(self, dt):
        if self.revealing:
            self.elapsed += dt
            while self.elapsed >= self.animation_speed:
                self.elapsed -= self.animation_speed
                if self.changing_cards:
                    index = self.changing_cards[self.card_index]
                    self.hand[index].face_up = True
                    self.deal_sound.play()
                    self.card_index += 1
                    if self.card_index >= len(self.changing_cards):
                        self.card_index = 0
                        self.revealing = False

        if not self.playing:
            self.no_playing_label.update(dt)

        if self.waiting:
            self.waiting_label.update(dt)

    def draw(self, surface):
        for card in self.hand:
            card.draw(surface)
        for index in self.held_cards:
            if self.double_up:
                self.double_up_labels[index].draw(surface)
            else:
                self.held_labels[index].draw(surface)
        if not self.playing:
            self.no_playing_label.draw(surface)
        elif self.waiting:
            self.waiting_label.draw(surface)