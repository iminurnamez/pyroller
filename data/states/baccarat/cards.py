import random
import pygame
from functools import partial
from pygame.transform import smoothscale
from math import pi, cos
from .ui import Stacker, Sprite
from ... import prepare
from ...components.animation import Animation


__all__ = [
    'Card',
    'Deck']

two_pi = pi * 2


def make_cards(decks, card_size, shuffle=False):
    """Return a list of Cards
    """

    def build_decks():
        suits = ("Clubs", "Hearts", "Diamonds", "Spades")
        rect = ((0, 0), card_size)
        for deck in range(decks):
            for suit in suits:
                for value in range(1, 14):
                    yield Card(value, suit, rect)

    cards = list(c for c in build_decks())

    if shuffle:
        random.shuffle(cards)

    return cards


class Card(Sprite):
    """Enhanced components.cards.Card that is also pygame sprite
    """

    face_cache = None
    card_suits = 'clubs', 'spades', 'hearts', 'diamonds'
    card_names = {
        1: "Ace",
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

    def __init__(self, value, suit, rect, face_up=False):
        super(Card, self).__init__()
        self.value = value
        self.suit = suit
        self.rect = pygame.Rect(rect)
        if self.face_cache is None:
            self.initialize_cache(self.rect.size)
        self._face_up = face_up
        self._rotation = 0 if self._face_up else 180
        self._needs_update = True
        self.front_face = self.get_front(self.name, self.rect.size)
        self.back_face = self.get_back(self.rect.size)
        self.dirty = 1
        self.update_image()

    @property
    def image(self):
        if self._needs_update:
            self.update_image()
        return self._image

    def update_image(self):
        image = self.front_face if self._face_up else self.back_face
        if self._rotation:
            width, height = image.get_size()
            value = 180 * cos(two_pi * self._rotation / 180.) + 180
            width *= value / 360.0
            width = int(round(max(1, abs(width)), 0))
            image = smoothscale(image, (width, int(height)))
        rect = image.get_rect(center=self.rect.center)
        self._image = image
        self.rect.size = rect.size
        self.rect.center = rect.center
        self.dirty = 1

    @classmethod
    def initialize_cache(cls, size):
        cls.face_cache = dict()
        for suit in cls.card_suits:
            for value, name in cls.card_names.items():
                Card(value, suit, ((0, 0), size))

    def get_front(self, name, size):
        try:
            return Card.face_cache[name]
        except KeyError:
            image = self.render_front(name, size)
            Card.face_cache[size] = image
            return image

    def get_back(self, size):
        try:
            return Card.face_cache["back"]
        except KeyError:
            image = self.render_back(size)
            Card.face_cache["back"] = image
            return image

    @staticmethod
    def render_front(name, size):
        front = prepare.GFX[name.lower().replace(" ", "_")]
        if not size == front.get_size():
            front = smoothscale(front, size).convert_alpha()
        return front

    @staticmethod
    def render_back(size):
        snake = prepare.GFX["pysnakeicon"]
        rect = pygame.Rect((0, 0), size)
        back = pygame.Surface(size)
        back.fill(pygame.Color("dodgerblue"))
        s_rect = snake.get_rect().fit(rect)
        s_rect.midbottom = rect.midbottom
        snake = smoothscale(snake, s_rect.size)
        back.blit(snake, s_rect)
        pygame.draw.rect(back, pygame.Color("gray95"), rect, 4)
        pygame.draw.rect(back, pygame.Color("gray20"), rect, 1)
        return back

    @property
    def face_up(self):
        return self._face_up

    @face_up.setter
    def face_up(self, value):
        face_up = bool(value)
        if not self._face_up == face_up:
            self.rotation = 0 if face_up else 180
            self._face_up = face_up
            self._needs_update = True
            self.update_image()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        value %= 360
        if not value == self._rotation:
            face = value < 90
            if not face:
                face = value > 270
            self._face_up = face
            self._rotation = value
            self._needs_update = True

    @property
    def name(self):
        if 1 < self.value < 11:
            return "{} of {}".format(self.value, self.suit)
        else:
            return self.long_name

    @property
    def short_name(self):
        if 1 < self.value < 11:
            return "{}{}".format(self.value, self.suit[0])
        else:
            return "{}{}".format(self.card_names[self.value][0], self.suit[0])

    @property
    def long_name(self):
        return "{} of {}".format(self.card_names[self.value], self.suit)


class Deck(Stacker):
    """Class to represent a deck of playing cards.

    If default_shuffle is True the deck will be
    shuffled upon creation.
    """

    def __init__(self, rect, card_size=prepare.CARD_SIZE, shuffle=True,
                 decks=0, stacking=None):
        rect = pygame.Rect(rect)
        if rect.size == (0, 0):
            rect = pygame.Rect(rect.topleft, card_size)
        super(Deck, self).__init__(rect, stacking)
        self.arrange_function = self.animate_deal
        self.card_size = card_size
        self.shuffle = shuffle
        self.decks = decks
        self.add_decks(decks)

    def add_decks(self, decks):
        cards = make_cards(decks, self.card_size, self.shuffle)
        self.extend(cards)

    def draw_cards(self, cards=5):
        """Remove top cards and return them
        """
        if len(self) >= cards:
            for i in range(cards):
                yield self.pop()
        else:
            yield None

    def flip(self, sprite):
        set_dirty = lambda: setattr(sprite, 'dirty', 1)
        fx = sprite.rect.centerx - sprite.rect.width
        ani0 = Animation(rotation=0, duration=350, transition='out_quint')
        ani0.update_callback = set_dirty
        ani0.start(sprite)
        ani1 = Animation(centerx=fx, duration=340, transition='out_quint')
        ani1.update_callback = set_dirty
        ani1.start(sprite.rect)
        self._animations.add(ani0, ani1)

    def animate_deal(self, sprite, initial, final, index):
        if hasattr(sprite, '_already_animated'):
            return None

        sprite._already_animated = True
        fx, fy = final
        ani = Animation(x=fx, y=fy, duration=400.,
                        transition='in_out_quint', round_values=True)
        ani.update_callback = lambda: setattr(sprite, 'dirty', 1)

        # HACK
        if 1:
            sprite.face_up = False
            ani.callback = partial(self.flip, sprite)

        ani.start(sprite.rect)
        return ani
