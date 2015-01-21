""" Note to maintainers:

Yes, these classes are duplicates of built in types.  I have reimplemented
the built in types because I feel these are a little easier to use.

Perhaps we could look at the existing classes and these and make some new
blending of the two.
"""

import random
import collections
from math import pi, cos
from itertools import product, groupby
from operator import attrgetter
import pygame
from pygame.transform import smoothscale
from ... import tools, prepare
from ...components.angles import *
from ...components.animation import *
from ...prepare import BROADCASTER as B

__all__ = ['TextSprite', 'Button', 'NeonButton', 'Card', 'Deck', 'Chip',
           'ChipPile', 'ChipRack', 'SpriteGroup', 'cash_to_chips',
           'chips_to_cash', 'OutlineTextSprite', 'BettingArea', 'MetaGroup']


two_pi = pi * 2
denominations = [100, 25, 10, 5, 1]


def make_change(value, break_down=False):
    """Return list of numbers whose sum equals value passed

    Optionally, passing True to break_down will prevent it from
    passing back the value if it is a common denomination.  In
    other words, it will break down value into smaller values.

    :param value: Value to be broken down
    :param break_down: If True, will break down common denominations
    :return: List
    """
    retval = list()
    if value == 1:
        return [1]
    if break_down:
        break_down = value
    for d in denominations:
        if break_down == d:
            continue
        i, value = divmod(value, d)
        retval.extend([d] * i)
    return retval


def cash_to_chips(value):
    """Return a list of chips whose sum equals the value passed
    """
    return [Chip(i) for i in make_change(value)]


def chips_to_cash(chips):
    return sum(i.value for i in chips)


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


class BettingArea(object):
    def __init__(self, name, rect, hand=None):
        self.name = name
        self.rect = rect
        self.hand = hand


class Sprite(pygame.sprite.DirtySprite):
    """DirtySprite class with extra support for animations
    """
    pass


class SpriteGroup(pygame.sprite.LayeredUpdates):
    """Like OrderedUpdates, but supports visible/invisible sprites
    """
    def __init__(self, *args, **kwargs):
        super(SpriteGroup, self).__init__(*args, **kwargs)
        self._animations = pygame.sprite.Group()

    @property
    def bounding_rect(self):
        sprites = self.sprites()
        if len(sprites) == 0:
            return self.rect
        elif len(sprites) == 1:
            return pygame.Rect(sprites[0].rect)
        else:
            return sprites[0].rect.unionall([s.rect for s in sprites[1:]])

    def update(self, *args):
        super(SpriteGroup, self).update(*args)
        self._animations.update(*args)

    def delay(self, amount, callback, args=None, kwargs=None):
        """Convenience function to delay a function call

        :param amount: milliseconds to wait until callback is called
        :param callback: function to call
        :param args: arguments to pass to callback
        :param kwargs: keywords to pass to callback
        :return: Task instance
        """
        task = Task(callback, amount, 1, args, kwargs)
        self._animations.add(task)
        return task


class MetaGroup(object):
    """Capable of correctly rendering a bunch of groups
    """
    def __init__(self):
        self._groups = list()

    def __len__(self):
        return len(self._groups)

    def sprites(self):
        retval = list()
        for group in self.groups():
            for sprite in group.sprites():
                retval.append(sprite)
        return retval

    def groups(self):
        return list(self._groups)

    def empty(self):
        for group in self.groups():
            group.empty()
        self._groups = list()

    def add(self, *groups):
        for group in groups:
            self._groups.append(group)

    def remove(self, *groups):
        for group in groups:
            try:
                self._groups.remove(group)
            except ValueError:
                pass

    def update(self, *args):
        for group in self.groups():
            group.update(*args)

    def clear(self, surface, background):
        for group in self.groups():
            group.clear(surface, background)

    def draw(self, surface):
        for group in self.groups():
            group.draw(surface)


class EventButton(Sprite):
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


class Card(Sprite):
    """pretty much components.cards.Card that is also pygame sprite"""

    face_cache = None
    card_suits = 'clubs', 'spades', 'hearts', 'diamonds'
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


class Stacker(SpriteGroup):
    def __init__(self, rect, stacking=None):
        super(Stacker, self).__init__()
        self.rect = pygame.Rect(rect)
        self.auto_arrange = True
        self._needs_arrange = True
        self._constraint = 'height'
        self._origin = None
        self._origin_offset = (0, 0)
        self._sprite_anchor = None
        self._animations = pygame.sprite.Group()
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
        if self.auto_arrange and self._needs_arrange:
            self.arrange()
            self._needs_arrange = False
        super(Stacker, self).draw(surface)

    def arrange(self, sprites=None, offset=(0, 0), animate=None, noclip=False):
        """ position sprites into piles.

        Constraint can be "width" or "height".
        If constraint is "width", sprite piles grow down.
        If constraint is "height", sprite piles grow to left.
        If rect is too small, other sprites will not be shown
        """
        if sprites is None:
            sprites = list(self.sprites())

        if not sprites:
            return 0, 0

        if self.stacking is None:
            pos = self.rect.topleft
            sprites[-1].visible = 1
            sprites[-1].rect.topleft = pos
            for sprite in sprites[:-1]:
                sprite.visible = 0
                sprite.rect.topleft = pos
            return 0, 0

        anchor = self._sprite_anchor
        constraint = self._constraint
        x, y = getattr(self.rect, self._origin)
        x += self._origin_offset[0] + offset[0]
        y += self._origin_offset[1] + offset[1]
        ox, oy = self.stacking
        xx = 0
        yy = 0
        for index, sprite in enumerate(sprites):
            rect = sprite.rect

            if hasattr(sprite, 'dirty'):
                sprite.dirty = 1
                sprite.visible = 1

            original_value = getattr(rect, anchor)

            if constraint == "height":
                setattr(rect, anchor, (x + xx, y + yy))

                if self.rect.colliderect(rect) or noclip:
                    yy += oy
                else:
                    xx += ox
                    yy = oy
                    setattr(rect, anchor, (x + xx, y))

            if animate is not None:
                final_value = getattr(rect, 'topleft')
                setattr(rect, anchor, original_value)
                animate(sprite, original_value, final_value, index)

        return xx, yy


class Deck(Stacker):
    """Class to represent a deck of playing cards. If default_shuffle is True
    the deck will be shuffled upon creation.
    """
    def __init__(self, rect, card_size=prepare.CARD_SIZE, shuffle=True,
                 decks=0, stacking=None):
        rect = pygame.Rect(rect)
        if rect.size == (0, 0):
            rect = pygame.Rect(rect.topleft, card_size)
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


class Chip(Sprite):
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
        self.dirty = 1
        self.image = None
        self._flat = False
        self.color = Chip.chip_values[value]
        if chip_size is not None:
            self.chip_size = chip_size
        self.rect = pygame.Rect((0, 0), self.chip_size)
        self.update_image()

    def update_image(self):
        if self._flat:
            self.image = Chip.flat_images[self.chip_size][self.color]
        else:
            self.image = Chip.images[self.chip_size][self.color]
        self.rect = self.image.get_rect(center=self.rect.center)
        self.dirty = 1

    @property
    def flat(self):
        return self._flat

    @flat.setter
    def flat(self, value):
        value = bool(value)
        if not value == self._flat:
            self._flat = value
            self.update_image()


class ChipPile(Stacker):
    """Represents a player's pile of chips
    """
    chip_sounds = [prepare.SFX[name] for name in
                   ["chipsstack{}".format(x) for x in (3, 5, 6)]]

    _initial_snapping = 50
    _fine_snapping = 30

    def __init__(self, rect, value=0, **kwargs):
        super(ChipPile, self).__init__(rect, **kwargs)
        self.stacking = 80, -10
        self._clicked_sprite = None
        self._followed_sprite = None
        self._popped_chips = list()
        self._initial_snap_x = None
        self._desired_pos = None
        self._selected_stack = False
        if value:
            self.add(*cash_to_chips(value))

    def get_event(self, event, scale):
        if event.type == pygame.MOUSEMOTION:
            self.handle_pointer(tools.scaled_mouse_pos(scale))

        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = tools.scaled_mouse_pos(scale)
                self.handle_select(True, pos)

        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                pos = tools.scaled_mouse_pos(scale)
                self.handle_select(False, pos)

    def handle_select(self, value, pos=None):
        value = bool(value)
        if not self._selected_stack == value:
            self._selected_stack = value

            if value:
                B.processEvent(('PICKUP_STACK', self))
            else:
                d = {'object': self,
                     'position': pos,
                     'chips': list(self._popped_chips)}
                drop = self.handle_drop(B.processEvent(('DROP_STACK', d)))
                if drop:
                    self.return_stack()
                    return

            self.handle_pointer(pos)

    def handle_drop(self, results):
        """Collect results from the 'DROP_STACK' event

        If anyone was interested in the stack, then return True
        """
        for i in results:
            junk, chips_pile = i

        return True

    def handle_pointer(self, pos):
        if self._followed_sprite:
            distance = self._initial_snapping
        else:
            distance = self._fine_snapping

        if not self._selected_stack:
            closest_sprite = None
            nearest_sprites = self.get_nearest_sprites(pos, distance)
            for dist, sprite in nearest_sprites:
                if sprite not in self._popped_chips:
                    closest_sprite = sprite
                    break

            if closest_sprite is not None:
                if self._followed_sprite is not closest_sprite:
                    random.choice(self.chip_sounds).play()
                    self._followed_sprite = closest_sprite
                    self._initial_snap_x = closest_sprite.rect.centerx

        if self._followed_sprite:
            close_enough = abs(pos[0] - self._initial_snap_x) < 100

            if close_enough or self._selected_stack:
                B.processEvent(('HOVER_STACK', (self, pos)))
                self._needs_arrange = True
                if self._selected_stack:
                    self._desired_pos = pos[0], pos[1] - 20
                else:
                    self._desired_pos = pos[0], pos[1] + 15

            elif not self._selected_stack:
                self.return_stack()

    def return_stack(self):
        def animate_return_to_pile(sprite, initial, final, index=1):
            """Used to animate chips returning to the pile
            """
            def cleanup_animation():
                random.choice(self.chip_sounds).play()
                try:
                    self._popped_chips.remove(sprite)
                except ValueError:
                    pass

            fx, fy = final
            ani = Animation(x=fx, y=fy, duration=300, transition='out_quint')
            ani.callback = cleanup_animation
            ani.update_callback = lambda: setattr(sprite, 'dirty', 1)
            ani.start(sprite.rect)
            self.delay((index - 1) * 10, self._animations.add, (ani, ))
            return ani

        B.processEvent(('RETURN_STACK', self))
        self._animations.empty()
        self._selected_stack = False
        self._needs_arrange = False
        self._initial_snap_x = None
        self._followed_sprite = None
        self.arrange(animate=animate_return_to_pile)

    def get_nearest_sprites(self, point, limit=None):
        sprites = self.sprites()
        l = [(get_distance(point, sprite.rect.center), sprite, i)
             for i, sprite in enumerate(sprites)]
        if limit is not None:
            l = [i for i in l if i[0] <= limit]
        l.sort()
        l = [i[:2] for i in l]
        return l

    def animate_pop(self, sprite, initial, final, index=1):
        """Animate chips moving to popped stack
        """
        fx, fy = final
        ani = Animation(x=fx, y=fy, duration=200, transition='out_quint')
        ani.update_callback = lambda: setattr(sprite, 'dirty', 1)
        ani.start(sprite.rect)
        self._animations.add(ani)
        return ani

    @property
    def value(self):
        """"Returns total cash value of self.chips."""
        return chips_to_cash(self.sprites())

    def sort(self):
        self._spritelist.sort(key=attrgetter('value'), reverse=True)

    def withdraw_chips(self, amount):
        """Withdraw chips totalling amount
        """
        self.sort()
        withdraw = list()
        for chip in self.sprites():
            if chip.value <= amount:
                amount -= chip.value
                withdraw.append(chip)
                if amount == 0:
                    break
        else:
            raise ValueError

        self.remove(withdraw)
        return withdraw

    def arrange(self, sprites=None, offset=(0, 0), animate=None, noclip=False):
        self.sort()
        ox, oy = offset
        arrange = super(ChipPile, self).arrange
        for k, g in groupby(self.sprites(), attrgetter('value')):
            sprites = list(g)
            if self._followed_sprite in sprites:

                # arrange sprites lower than the followed one
                i = sprites.index(self._followed_sprite)
                self._popped_chips = list(sprites[i:])

                # arrange sprites over the followed one
                if i > 0:
                    xx, yy = arrange(sprites[:i], (ox, oy))
                    rect = sprites[i-1].rect
                else:
                    original_pos = sprites[0].rect.topleft
                    xx, yy = arrange(sprites[:1], (ox, oy))
                    rect = pygame.Rect(sprites[0].rect)
                    sprites[0].rect.topleft = original_pos

                xx += self._desired_pos[0] - rect.centerx
                yy += self._desired_pos[1] - rect.bottom
                self._animations.empty()
                arrange(self._popped_chips, (ox + xx, yy),
                        animate=self.animate_pop, noclip=True)

            else:
                arrange(sprites, (ox, oy), animate)

            ox += self.stacking[0]


class ChipRack(ChipPile):
    """Class to represent a dealer/teller's rack of chips
    """
    def __init__(self, rect):
        super(ChipRack, self).__init__(rect)
        self._origin_offset = 9, -6
        self.stacking = 57, 6
        self.row_size = 30
        self.background = prepare.GFX["chip_rack_medium"]
        self.front = prepare.GFX["rack_front_medium"]
        rect = self.background.get_rect(topleft=self.rect.topleft)
        self.front_rect = self.front.get_rect(bottomleft=rect.bottomleft)

    def add(self, *items):
        """Add chips to the rack.

        Chips will have their flat attribute set to True
        and resized to fit the rack graphic
        """
        for chip in items:
            chip.chip_size = 48, 30
            chip.flat = True
        super(ChipRack, self).add(*items)

    def fill(self):
        """Add enough chips of each value to fill the rack completely
        """
        d = collections.defaultdict(int)
        for chip in self.sprites():
            d[chip.value] += 1
        for value in denominations:
            for i in range(self.row_size - d[value]):
                self.add(Chip(value))

    def clear(self, surface, background):
        super(ChipRack, self).clear(surface, self.background)

    def draw(self, surface):
        redraw = self._needs_arrange
        if redraw:
            surface.blit(self.background, self.rect)
        dirty = super(ChipRack, self).draw(surface)
        # HACK: will draw rack front every frame.  :(
        surface.blit(self.front, self.front_rect)
        return dirty


class TextSprite(Sprite):
    def __init__(self, text, font=None, fg=None, bg=None, cache=True):
        super(TextSprite, self).__init__()
        self.rect = pygame.Rect((0, 0), font.size(text))
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


class OutlineTextSprite(TextSprite):
    def draw(self, surface=None, rect=None):
        bg = self._bg
        if bg is None:
            bg = (0, 0, 0)
        w, h = self._font.size(self._text)
        w += 12
        h += 12
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        outline = self._font.render(self._text, 1, bg)
        inner = self._font.render(self._text, 1, self._fg)
        ww, hh = outline.get_size()
        cx = w/2-ww/2
        cy = h/2-hh/2
        for x in range(-6, 6):
            for y in range(-6, 6):
                image.blit(outline, (x+cx, y+cy))
        image.blit(inner, (cx, cy))
        return image


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
