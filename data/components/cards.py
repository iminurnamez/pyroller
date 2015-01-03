import os
from random import shuffle
import pygame as pg
from .. import prepare
from ..components.angles import get_angle, project


class Card(object):
    """Class to represent a single playing card."""
    card_names = {1: "Ace",
                           2: "Two",
                           3: "Three",
                           4: "Four",
                           5: "Five",
                           6: "Six",
                           7: "Seven",
                           8: "Eight",
                           9: "Nine",
                           10: "Ten",
                           11: "Jack",
                           12: "Queen",
                           13: "King"}

    def __init__(self, value, suit, card_size, speed):
        self.card_size = card_size
        self.speed = speed
        self.value = value
        self.suit = suit
        self.long_name = "{} of {}".format(self.card_names[self.value], self.suit)
        if 1 < self.value < 11:
            self.name = "{} of {}".format(self.value, self.suit)
            self.short_name = "{}{}".format(self.value, self.suit[0])
        else:
            self.name = self.long_name
            self.short_name = "{}{}".format(self.card_names[self.value][0], self.suit[0])
        self.load_images()
        self.rect = self.image.get_rect()
        self.pos = self.rect.center
        self.face_up = False

    def load_images(self):
        img_name = self.name.lower().replace(" ", "_")
        image = prepare.GFX[img_name]
        self.image = pg.transform.scale(image, self.card_size)
        self.back_image = pg.Surface(self.card_size).convert()
        self.back_image.fill(pg.Color("dodgerblue"))
        snake = prepare.GFX["pysnakeicon"]
        s_rect = snake.get_rect().fit(self.back_image.get_rect())
        s_rect.midbottom = self.back_image.get_rect().midbottom
        snake = pg.transform.scale(snake, s_rect.size)
        self.back_image.blit(snake, s_rect)
        pg.draw.rect(self.back_image, pg.Color("gray95"), self.back_image.get_rect(), 4)
        pg.draw.rect(self.back_image, pg.Color("gray20"), self.back_image.get_rect(), 1)

    def draw(self, surface):
        if self.face_up:
            surface.blit(self.image, self.rect)
        else:
            surface.blit(self.back_image, self.rect)

    def travel(self, destination):
        angle = get_angle(self.pos, destination)
        self.pos = project(self.pos, angle, self.speed)
        self.rect.center = self.pos


class Deck(object):
    """Class to represent a deck of playing cards. If default_shuffle is True
        the deck will be shuffled upon creation. If reuse_discards is True, the
        discard pile will replenish the deck on exhaustion. If infinite is True, the
        deck will replenish itself with a new deck upon exhaustion. Reusing
        discards supersedes infinite replenishment."""

    def __init__(self, topleft, card_size=prepare.CARD_SIZE, card_speed=16.0,
                        default_shuffle=True, reuse_discards=True, infinite=False):
        self.topleft = topleft
        self.card_size = card_size
        self.card_speed = card_speed
        self.rect = pg.Rect(self.topleft, self.card_size)
        self.discard_rect = self.rect.move(int(self.card_size[0] * 1.2), 0)
        self.default_shuffle = default_shuffle
        self.reuse_discards= reuse_discards
        self.infinite = infinite
        self.num_decks = 1
        self.cards = self.make_cards()
        self.discards = []


    def __len__(self):
        return len(self.cards)

    def make_cards(self):
        """Return a list of Cards."""
        suits = ("Clubs", "Hearts", "Diamonds", "Spades")
        cards = [Card(i, suit, self.card_size, self.card_speed)
                     for suit in suits for i in range(1, 14)]
        for _ in range(self.num_decks - 1):
            cards.extend([Card(i, suit, self.card_size, self.card_speed)
                                 for suit in suits for i in range(1, 14)])
        if self.default_shuffle:
            shuffle(cards)
        return cards

    def discard(self, card):
        """Add card to deck's discards."""
        self.discards.append(card)

    def burn(self):
        """Add top card of deck to discards."""
        self.discards.append(self.cards.pop())

    def draw_card(self):
        """Draw top card from deck. If deck is exhausted
        deck will be replenished according to deck options."""
        try:
            return self.cards.pop()
        except IndexError:
            if self.reuse_discards and self.discards:
                self.cards = self.discards
                for card in self.cards:
                    card.face_up = False
                if self.default_shuffle:
                    shuffle(self.cards)
                self.discards = []
                return self.cards.pop()
            elif self.infinite:
                self.cards = self.make_cards()
                return self.cards.pop()
            else:
                return None

    def make_hand(self, num_cards=5):
        """Create a hand of cards."""
        return [self.draw_card() for _ in range(num_cards)]

    def draw_pile(self, surface, cards, lefttop, x_offset=2,
                           y_offset=-1, toggle_num=4):
        """Draw a deck of cards to surface. Every toggle_num cards, the card
        drawing position will be offset by (x_offset, y_offset). This allows you
        to limit the height of the deck."""
        left, top = lefttop
        for i, card in enumerate(cards, start=1):
            card.rect.topleft = (left, top)
            card.pos = card.rect.center
            card.draw(surface)
            if not i % toggle_num:
                left += x_offset
                top += y_offset

    def draw(self, surface):
        """Draw deck and discard pile to surface."""
        self.draw_pile(surface, self.discards, self.discard_rect.topleft)
        self.draw_pile(surface, self.cards, self.topleft)


class MultiDeck(Deck):
    """A class to represent a deck of cards composed of multiple
    individual decks."""
    def __init__(self, num_decks, card_size=prepare.CARD_SIZE, card_speed=20.0,
                        default_shuffle=True, reuse_discards=True, shuffle_discards=True,
                        infinite=False):
        super(MultiDeck, self).__init__(card_size, card_speed, default_shuffle,
                                                      reuse_discards, infinite)
        self.num_decks = num_decks
        for _ in range(num_decks - 1):
            self.cards.extend(self.make_cards())
        if self.default_shuffle:
            shuffle(self.cards)
