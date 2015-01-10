""" Note to maintainers:

Yes, these classes are duplicates of built in types.  I have reimplemented
the built in types because I felt that these offer lower memory use and
better performance, as well as useful features.

Perhaps we could look at the existing classes and these and make some new
blending of the two.
"""

import random
from itertools import product, groupby
from operator import attrgetter
import pygame
from pygame.transform import smoothscale
from ... import prepare

__all__ = ['TextSprite', 'Button', 'NeonButton', 'Card', 'Deck', 'Chip',
           'ChipPile', 'SpriteGroup', 'cash_to_chips']


def cash_to_chips(value):
    retval = list()
    demoninations = [100, 25, 10, 5, 1]
    for d in demoninations:
        number, value = divmod(value, d)
        for i in range(number):
            retval.append(Chip(d))
    return retval


def cut_sheet(surface, dim, margin=0, spacing=0, subsurface=True):
    """ Automatically cut a sprite sheet into individual images

    :param surface: pygame Surface
    :param dim: the dimensions of the image in tiles
    :param margin: number of pixels around all tiles
    :param spacing: number of pixels around each tile
    :param subsurface: if true, images will be subsurfaces
    :return: generator of (tile_x, tile_y, surface)
    """
    if subsurface:
        surface = surface.convert_alpha()

    width, height = surface.get_size()
    tilewidth = int(width / dim[0])
    tileheight = int(height / dim[0])

    p = product(
        range(margin, height + margin - tilewidth + 1, tileheight + spacing),
        range(margin, width + margin - tileheight + 1, tilewidth + spacing))

    for real_gid, (y, x) in p:
        rect = (x, y, tilewidth, tileheight)
        if subsurface:
            yield x, y, surface.subsurface(rect)
        else:
            tile = pygame.Surface(rect.size, pygame.SRCALPHA)
            tile.blit(surface, (0, 0), rect)
            yield x, y, tile


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


class SpriteGroup(pygame.sprite.OrderedUpdates):
    def draw(self, surface):
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = list()
        dirty_append = dirty.append
        for s in self.sprites():
            if not s.visible:
                continue
            r = spritedict[s]
            newrect = surface_blit(s.image, s.rect)
            if r:
                if newrect.colliderect(r):
                    dirty_append(newrect.union(r))
                else:
                    dirty_append(newrect)
                    dirty_append(r)
            else:
                dirty_append(newrect)
            spritedict[s] = newrect
        return dirty


class EventButton(pygame.sprite.DirtySprite):
    def __init__(self, callback, args=None, kwargs=None):
        super(EventButton, self).__init__()
        assert(callable(callback))
        kwargs = kwargs if kwargs is not None else dict()
        args = args if args is not None else list()
        self._callback = callback, args, kwargs

    def on_mouse_click(self, pos):
        cb, args, kwargs = self._callback
        cb(self, *args, **kwargs)

    def on_mouse_enter(self, pos):
        pass

    def on_mouse_leave(self, pos):
        pass


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

    def __init__(self, value, suit, rect, face_up=False):
        super(Card, self).__init__()
        self.value = value
        self.suit = suit
        self.rect = pygame.Rect(rect)
        self._face_up = face_up
        self.get_images()
        self.update_image()

    def update_image(self):
        self.image = self.front_face if self.face_up else self.back_face

    def get_images(self):
        try:
            self.front_face = Card.face_cache[self.value]
        except KeyError:
            image = self.render_front(self.name, self.rect.size)
            self.front_face = image
            Card.face_cache[self.value] = image

        try:
            self.back_face = Card.face_cache["back"]
        except KeyError:
            image = self.render_back(self.rect.size)
            self.back_face = image
            Card.face_cache["back"] = image

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


class Stacker(SpriteGroup):
    def __init__(self, rect, stacking=None):
        super(Stacker, self).__init__()
        self.rect = pygame.Rect(rect)
        self._needs_arrange = True
        self._constraint = 'height'
        self._origin = None
        self._sprite_anchor = None
        self.stacking = stacking

    @property
    def stacking(self):
        return self._stacking

    @stacking.setter
    def stacking(self, value):
        self._stacking = value
        if value is not None:
            if value[1] >= 0:
                self._origin = 'topleft'
                self._sprite_anchor = 'topleft'
            else:
                self._origin = 'bottomleft'
                self._sprite_anchor = 'bottomleft'

    def add(self, *items):
        super(Stacker, self).add(*items)
        self._needs_arrange = True

    def remove(self, *items):
        super(Stacker, self).remove(*items)
        self._needs_arrange = True

    def pop(self):
        try:
            sprite = self._spritelist[-1]
        except IndexError:
            return None
        else:
            self.remove(sprite)
            return sprite

    def draw(self, surface):
        if self._needs_arrange:
            self.arrange()
            self._needs_arrange = False
        super(Stacker, self).draw(surface)

    def arrange(self, sprites=None, offset=(0, 0)):
        """ position sprites into piles.

        Constraint can be "width" or "height".
        If constraint is "width", sprite piles grow down.
        If constraint is "height", sprite piles grow to left.
        If rect is too small, other sprites will not be shown
        """
        if sprites is None:
            sprites = list(self.sprites())

        if not sprites:
            return

        if self.stacking is None:
            pos = self.rect.topleft
            sprites[-1].visible = 1
            sprites[-1].rect.topleft = pos
            for sprite in sprites[:-1]:
                sprite.visible = 0
                sprite.rect.topleft = pos
            return

        x, y = getattr(self.rect, self._origin)
        x += offset[0]
        y += offset[1]
        rx, ry = x, y
        ox, oy = self.stacking
        for sprite in sprites:
            sprite.visible = 1
            setattr(sprite.rect, self._sprite_anchor, (x, y))
            if hasattr(sprite, 'dirty'):
                sprite.dirty = 1
            if self._constraint == "height":
                if self.rect.contains(sprite.rect.move(0, oy)):
                    y += oy
                else:
                    y = ry
                    x += ox + sprite.rect.width

        return x, y


class Deck(Stacker):
    """Class to represent a deck of playing cards. If default_shuffle is True
    the deck will be shuffled upon creation.
    """
    def __init__(self, rect, card_size=prepare.CARD_SIZE, shuffle=True,
                 decks=0, stacking=None):
        if rect[2:] == (0, 0):
            rect = rect[:2], card_size
        super(Deck, self).__init__(rect, stacking)
        self.card_size = card_size
        self.shuffle = shuffle
        self.decks = decks
        self.add_decks(decks)

    def add_decks(self, decks):
        cards = make_cards(decks, self.card_size, self.shuffle)
        self.add(*cards)

    def draw_cards(self, cards=5):
        """Remove top cards and return them"""
        if len(self) >= cards:
            for i in range(cards):
                yield self.pop()
        else:
            yield None


CHIP_Y = {"blue"  : 0,
          "red"   : 64,
          "black" : 128,
          "green" : 192,
          "white" : 256}


def get_chip_images():
    image = prepare.GFX["chips"]
    sub = image.subsurface
    scale = pygame.transform.smoothscale
    # small_dim = 32, 32
    # dim = 2, 4
    # images = dict()
    # flat_images = dict()
    # colors = ['blue', 'red', 'black', 'green', 'white']
    # for x, y, surface in cut_sheet(image, dim):
    #     if not x:
    #         color = colors.pop(0)
    #     images['large'] = surface
    #     images['small'] = scale(surface, small_dim).convert_alpha()
    #
    #

    images = {(32, 19): {col: sub(64, CHIP_Y[col], 64, 38) for col in CHIP_Y}}
    images[(48, 30)] = {col: scale(images[(32, 19)][col], (48, 30)) for col in CHIP_Y}
    flat_images = {(32, 19): {col: sub(0, CHIP_Y[col], 64, 64) for col in CHIP_Y}}
    flat_images[(48, 30)] = {col: scale(flat_images[(32,19)][col], (48, 48)) for col in CHIP_Y}
    return images, flat_images


class Chip(pygame.sprite.DirtySprite):
    """Class to represent a single casino chip."""
    chip_values = {100: 'black',
                   25: 'blue',
                   10: 'green',
                   5: 'red',
                   1: 'white'}

    images, flat_images = get_chip_images()
    thicknesses = {19: 5, 30: 7}
    chip_size = prepare.CHIP_SIZE

    def __init__(self, value, chip_size=None):
        super(Chip, self).__init__()
        self.value = value
        if chip_size is not None:
            self.chip_size = chip_size
        self.dirty = 1

        color = Chip.chip_values[value]
        self.image = Chip.images[self.chip_size][color]
        self.flat_image = Chip.flat_images[self.chip_size][color]
        self.rect = self.image.get_rect()


class ChipPile(Stacker):
    """Represents a player's pile of chips."""

    def __init__(self, rect, value=0):
        super(ChipPile, self).__init__(rect, (0, -7))
        if value:
            self.add(*cash_to_chips(value))

    @property
    def value(self):
        """"Returns total cash value of self.chips."""
        return sum(chip.value for chip in self.sprites())

    def sort(self):
        self._spritelist.sort(key=attrgetter('value'))

    def withdraw_chips(self, amount):
        """Withdraw chips totalling amount"""
        self.sort()
        withdraw = list()
        for chip in reversed(self.sprites()):
            if chip.value <= amount:
                amount -= chip.value
                self.remove(chip)
                withdraw.append(chip)
                if amount == 0:
                    break
        else:
            raise ValueError

        return withdraw

    def arrange(self, sprites=None, offset=(0, 0)):
        self.sort()
        x = 0
        for k, g in groupby(self.sprites(), attrgetter('value')):
            x, y = super(ChipPile, self).arrange(list(g), (x, 0))
            x += 70


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
