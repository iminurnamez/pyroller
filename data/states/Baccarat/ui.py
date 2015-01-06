""" Note to maintainers:

Yes, these classes are duplicates of built in types.  I have reimplemented
the built in types because I felt that these offer lower memory use and
better performance, as well as useful features.

Perhaps we could look at the existing classes and these and make some new
blending of the two.
"""

import random
import pygame
from pygame.transform import smoothscale
from ... import prepare

__all__ = ['TextSprite', 'Button', 'NeonButton', 'Card', 'Deck']


def make_cards(decks, card_size, shuffle=False):
    """Return a list of Cards."""

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


class Card(pygame.sprite.DirtySprite):
    """pretty much components.cards.Card that is also pygame sprite"""

    face_cache = {}
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

    def __init__(self, value, suit, rect, face_up=True):
        super(Card, self).__init__()
        self.value = value
        self.suit = suit
        self.rect = pygame.Rect(rect)
        self._face_up = face_up
        self.get_images()
        self.update_image()

    @property
    def face_up(self):
        return self._face_up

    @face_up.setter
    def face_up(self, value):
        face_up = bool(value)
        if not self._face_up == face_up:
            self._face_up = face_up
            self.update_image()

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

    def get_images(self):
        key = (self.value, self.suit)
        try:
            self.front_face, self.back_face = Card.face_cache[key]
        except KeyError:
            front, back = self.render_card(self.name, self.rect.size)
            self.front_face, self.back_face = front, back
            Card.face_cache[key] = front, back

    def update_image(self):
        self.image = self.front_face if self.face_up else self.back_face

    @staticmethod
    def render_card(name, size):
        rect = pygame.Rect((0, 0), size)
        image = prepare.GFX[name.lower().replace(" ", "_")]
        snake = prepare.GFX["pysnakeicon"]
        front = smoothscale(image, size).convert_alpha()
        back = pygame.Surface(size)
        back.fill(pygame.Color("dodgerblue"))
        s_rect = snake.get_rect().fit(rect)
        s_rect.midbottom = rect.midbottom
        snake = smoothscale(snake, s_rect.size)
        back.blit(snake, s_rect)
        pygame.draw.rect(back, pygame.Color("gray95"), rect, 4)
        pygame.draw.rect(back, pygame.Color("gray20"), rect, 1)
        return front, back


class Deck(pygame.sprite.OrderedUpdates):
    """Class to represent a deck of playing cards. If default_shuffle is True
        the deck will be shuffled upon creation. If reuse_discards is True, the
        discard pile will replenish the deck on exhaustion. If infinite is True,
        the deck will replenish itself with a new deck upon exhaustion. Reusing
        discards supersedes infinite replenishment."""

    def __init__(self, rect, card_size=prepare.CARD_SIZE, shuffle=True,
                 infinite=False, decks=0, stacking=(6, 6)):
        super(Deck, self).__init__()
        if rect[2:] == (0, 0):
            self.rect = pygame.Rect(rect[:2], card_size)
        else:
            self.rect = pygame.Rect(rect)

        self.card_size = card_size
        self.shuffle = shuffle
        self.infinite = infinite
        self.decks = decks
        self.stacking = stacking
        self.add_decks(decks)
        self._needs_update = True

    def add_decks(self, decks):
        cards = make_cards(decks, self.card_size, self.shuffle)
        self.add(*cards)

    def remove_all(self):
        for card in self.sprites():
            self.remove(card)

    def add(self, *items):
        super(Deck, self).add(*items)
        self._needs_update = True

    def remove(self, *items):
        super(Deck, self).remove(*items)
        self._needs_update = True

    def draw_cards(self, cards=5):
        """Remove top card and return it"""
        if len(self) >= cards:
            for i in range(cards):
                yield self.pop()
        else:
            yield None

    def pop(self):
        try:
            card = self._spritelist[-1]
        except IndexError:
            return None
        else:
            self.remove(card)
            return card

    def draw(self, surface):
        if self._needs_update:
            self.arrange_cards()
            self._needs_update = False
        super(Deck, self).draw(surface)

    def arrange_cards(self, constraint="height"):
        """ position cards into piles.

        Constraint can be "width" or "height".
        If constraint is "width", card piles grow down.
        If constraint is "height", card piles grow to left.
        If rect is too small, other cards will not be shown
        """
        if self.stacking == (0, 0):
            pos = self.rect.topleft
            for card in self.sprites():
                card.rect.topleft = pos
            return

        x, y = self.rect.topleft
        ox, oy = self.stacking
        for card in self.sprites():
            card.rect.topleft = x, y
            if constraint == "height":
                if self.rect.contains(card.rect.move(0, oy)):
                    y += oy
                else:
                    y = self.rect.top
                    x += ox + card.rect.width


class TextSprite(pygame.sprite.DirtySprite):
    def __init__(self, text, font=None, fg=None, bg=None, cache=True):
        super(TextSprite, self).__init__()
        self.rect = pygame.Rect(0, 0, 0, 0)
        self._fg = fg if fg is not None else (255, 255, 255)
        self._bg = bg
        self._text = text
        self._font = font
        self.dirty = 0
        self.image = None
        if cache:
            self.update_image()

    def draw(self, surface=None, rect=None):
        if self._bg is None:
            image = self._font.render(self._text, True, self._fg)
        else:
            image = self._font.render(self._text, True, self._fg, self._bg)
        if surface is not None and rect is not None:
            surface.blit(image, rect)
        return image

    def update_image(self):
        image = self.draw()
        self.image = image.convert_alpha()
        self.rect = image.get_rect(topleft=self.rect.topleft)
        self.dirty = 1

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.update_image()


class EventButton(pygame.sprite.DirtySprite):
    def __init__(self, callback, args=None, kwargs=None):
        super(EventButton, self).__init__()
        assert(callable(callback))
        kwargs = kwargs if kwargs is not None else dict()
        args = args if args is not None else list()
        self._callback = callback, args, kwargs

    def on_mouse_click(self, pos):
        cb, args, kwargs = self._callback
        cb(*args, **kwargs)

    def on_mouse_enter(self, pos):
        pass

    def on_mouse_leave(self, pos):
        pass


class NeonButton(EventButton):
    """Button class that responds to mouse events"""

    def __init__(self, label, rect, callback, args=None, kwargs=None):
        super(NeonButton, self).__init__(callback, args, kwargs)
        self.label = label.lower()
        self.image = None
        if rect[2:] == (0, 0):
            image = prepare.GFX['neon_button_on_{}'.format(self.label)]
            self.rect = pygame.Rect(rect[:2], image.get_size())
        else:
            self.rect = pygame.Rect(rect)
        self.on_mouse_leave(None)
        self.dirty = 1

    def on_mouse_enter(self, pos):
        self.image = prepare.GFX['neon_button_on_{}'.format(self.label)]
        self.dirty = 1

    def on_mouse_leave(self, pos):
        self.image = prepare.GFX['neon_button_off_{}'.format(self.label)]
        self.dirty = 1


class Button(EventButton):
    """Button class that responds to mouse events"""

    _fg0 = pygame.Color('gold2')
    _bg0 = pygame.Color('gray10')
    _bg1 = pygame.Color(48, 48, 48)

    def __init__(self, sprite, rect, callback, args=None, kwargs=None):
        super(Button, self).__init__(callback, args, kwargs)
        self.sprite = sprite
        self.rect = pygame.Rect(rect)
        self.image = None
        self.dirty = 1
        self._pressed = False
        self.update_image()

    @property
    def pressed(self):
        return self._pressed

    @pressed.setter
    def pressed(self, value):
        pressed = bool(value)
        if not self._pressed == pressed:
            self._pressed = pressed
            self.update_image()

    def update_image(self):
        """This is functional equivalent to components.labels.Button.draw"""
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        border = pygame.Rect((0, 0), self.rect.size)
        rect = border.inflate(-16, -18)
        other_color = self._fg0
        if self._pressed:
            border_color = self._bg1
            rect = rect.move(0, 3)
        else:
            border_color = self._bg0
            rect = rect.move(0, -3)
        pygame.draw.rect(surface, border_color, rect)
        pygame.draw.rect(surface, border_color, border)
        pygame.draw.rect(surface, other_color, rect, 3)
        pygame.draw.rect(surface, other_color, border, 4)
        image = self.sprite.draw()
        surface.blit(image, image.get_rect(center=rect.center))
        points = [(rect.topleft, border.topleft),
                  (rect.topright, border.topright),
                  (rect.bottomleft, border.bottomleft),
                  (rect.bottomright, border.bottomright)]
        for pair in points:
            pygame.draw.line(surface, other_color, pair[0], pair[1], 2)
        self.image = surface
        self.dirty = 1
