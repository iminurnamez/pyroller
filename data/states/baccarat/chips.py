from collections import defaultdict
from itertools import groupby
from operator import attrgetter
from random import choice
import time

import pygame

from .ui import *
from ... import prepare, tools
from ...components.angles import *
from ...components.animation import Animation
from ...prepare import BROADCASTER as B


__all__ = (
    'denominations',
    'make_change',
    'cash_to_chips',
    'chips_to_cash',
    'Chip',
    'ChipPile',
    'ChipRack')

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


def get_chip_images():
    CHIP_Y = {"blue": 0,
              "red": 64,
              "black": 128,
              "green": 192,
              "white": 256}

    image = prepare.GFX["chips"]
    sub = image.subsurface
    scale = pygame.transform.smoothscale
    # small_dim = 32, 32
    # dim = 2, 4
    # images = dict()
    # flat_images = dict()
    # colors = ['blue', 'red', 'black', 'green', 'white']
    # for x, y, surface in cut_sheet(image, dim):
    # if not x:
    #         color = colors.pop(0)
    #     images['large'] = surface
    #     images['small'] = scale(surface, small_dim).convert_alpha()
    #
    #

    images = {(32, 19): {col: sub(64, CHIP_Y[col], 64, 38) for col in CHIP_Y}}
    images[(48, 30)] = {col: scale(images[(32, 19)][col], (48, 30)) for col in
                        CHIP_Y}
    flat_images = {
        (32, 19): {col: sub(0, CHIP_Y[col], 64, 64) for col in CHIP_Y}}
    flat_images[(48, 30)] = {col: scale(flat_images[(32, 19)][col], (48, 48))
                             for col in CHIP_Y}
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
    shadow = make_shadow_surface(images[chip_size]['white'])

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
    """Represents a pile of chips
    """
    chip_sounds = [prepare.SFX[name] for name in
                   ["chipsstack{}".format(x) for x in (3, 5, 6)]]

    __current_stack = None
    _initial_snapping = 45
    _fine_snapping = 20
    _maximum_distance_until_drop = 100
    _last_sound = 0
    animation_time = 300
    sound_interval = .03

    def __init__(self, rect, value=0, **kwargs):
        super(ChipPile, self).__init__(rect, **kwargs)
        self.stacking = 70, -10
        self.ignore_until_away = True
        self.arrange_function = self.animate_pop
        self._clicked_sprite = None
        self._followed_sprite = None
        self._popped_chips = list()
        self._initial_snap = None
        self._desired_pos = None
        self._selected_stack = False
        self._grabbed = False
        self._shadows = SpriteGroup()
        self._shadows_dict = dict()

        self._running_animations = dict()
        B.linkEvent('DO_DROP_STACK', self.return_stack)
        if value:
            self.add(*cash_to_chips(value))

    def __del__(self):
        B.unlinkEvent('DO_DROP_STACK', self.return_stack)

    def draw(self, surface):
        dirty0 = self._shadows.draw(surface)
        dirty1 = super(ChipPile, self).draw(surface)
        dirty0.extend(dirty1)
        return dirty0

    def remove_internal(self, sprite):
        super(ChipPile, self).remove_internal(sprite)
        for name in ('_clicked_sprite', '_followed_sprite'):
            if getattr(self, name) is sprite:
                setattr(self, name, None)
        try:
            self._popped_chips.remove(sprite)
        except ValueError:
            pass
        try:
            shadow = self._shadows_dict.pop(sprite)
            self._shadows.remove(shadow)
        except KeyError:
            pass
        B.processEvent(('CHIPS_VALUE_CHANGE', self))

    def add_internal(self, *args, **kwargs):
        super(ChipPile, self).add_internal(*args, **kwargs)
        B.processEvent(('CHIPS_VALUE_CHANGE', self))

    # def update(self, *args):
    #     super(ChipPile, self).update(*args)
    #     self._animations.update(*args)

    def play_chip_sound(self):
        """Play a sound, but limit it a bit

        :return: None
        """
        elapsed = time.time() - self._last_sound
        if elapsed > self.sound_interval:
            self._last_sound = time.time()
            sound = choice(self.chip_sounds)
            sound.play()

    def get_event(self, event, scale):
        if event.type == pygame.MOUSEMOTION:
            self.handle_motion(tools.scaled_mouse_pos(scale))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = tools.scaled_mouse_pos(scale)
                self.handle_click(True, pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                pos = tools.scaled_mouse_pos(scale)
                self.handle_click(False, pos)

    def handle_click(self, value, pos=None):
        value = bool(value)
        if not self._selected_stack == value:

            # the button is clicked and something is following
            # so we assume it is a pickup.
            followed = self._followed_sprite is not None
            if value and followed:
                self._grabbed = True
                B.processEvent(('PICKUP_STACK', self))

            # button is released and and we are followed, so
            # lets drop whatever is following up
            elif not value and followed:
                self._grabbed = False
                self.ignore_until_away = True
                self.drop_followed(pos)

            # this triggers animation changes, essentially
            self._selected_stack = value
            self.handle_motion(pos)

    def handle_motion(self, pos):
        """Do stuff with the mouse/touch pointer

        :param pos: Mouse/Touch position in screen coordinates
        :return:
        """
        # check if mouse is close to a sprite, and snap to it
        closest_sprite = self.snap_sprite(pos)

        if self.ignore_until_away:
            if closest_sprite is None:
                self.ignore_until_away = False
                return

        # ignore chips in motion
        if closest_sprite in self._running_animations.keys():
            return

        # this will snap chips to the cursor
        elif not self._grabbed and closest_sprite is not None:

            # prevent multiple stacks from being hovered at once
            if ChipPile.__current_stack is not self:
                if ChipPile.__current_stack is None:
                    ChipPile.__current_stack = self

                elif ChipPile.__current_stack._grabbed:
                    return

                else:
                    ChipPile.__current_stack.return_stack()
                    ChipPile.__current_stack = self

            if self._followed_sprite is not closest_sprite:
                choice(self.chip_sounds).play()
                self._followed_sprite = closest_sprite
                self._popped_chips.append(closest_sprite)
                self._initial_snap = closest_sprite.rect.center

        # we have a sprite following the pointer
        # if self._followed_sprite is not None:
        if self._popped_chips:
            self.move_followed_sprite(pos)

            close_enough = (abs(get_distance(pos, self._initial_snap))
                            < self._maximum_distance_until_drop)

            # we've moved too far away without selecting the stack
            # so the stack is returned to the pile
            if not close_enough and not self._selected_stack:
                self.return_stack()

    def handle_drop(self, results):
        """Collect results from the 'DROP_STACK' event

        NOTE: needs work

        If anyone was interested in the stack, then return True
        """
        for i in results:
            # junk, chips_pile = i
            return True

        return False

    @property
    def height_offset(self):
        return -20 if self._selected_stack else 15

    def move_followed_sprite(self, pos):
        B.processEvent(('HOVER_STACK', (self._popped_chips, pos)))
        self._desired_pos = pos[0], pos[1] + self.height_offset
        self._needs_arrange = True

    def snap_sprite(self, pos, distance=None):
        """Get closest sprite to pos, with snapping rules, and
        ignoring sprites that are in the popped stack

        :param pos: Mouse/Touch position in screen coordinates
        :param distance: Optional distance to check
        :return: Closest sprite to pos, or None
        """
        if distance is None:
            if self.ignore_until_away:
                distance = self._maximum_distance_until_drop
            elif self._followed_sprite:
                distance = self._fine_snapping
            else:
                distance = self._initial_snapping

        closest_sprite = None
        nearest_sprites = self.get_nearest_sprites(pos, distance)
        for dist, sprite in nearest_sprites:
            if sprite not in self._popped_chips:
                closest_sprite = sprite
                break

        return closest_sprite

    def drop_followed(self, pos):
        d = {'object': self,
             'position': pos,
             'chips': list(self._popped_chips)}

        # drop will be be true when somebody
        # has accepted the dropped stack
        drop = self.handle_drop(B.processEvent(('DROP_STACK', d)))
        if drop:
            self.return_stack()

    def return_stack(self, *args):
        B.processEvent(('RETURN_STACK', self))
        self._grabbed = False
        self._selected_stack = False
        self._needs_arrange = False
        self._initial_snap = None
        self._followed_sprite = None
        self._popped_chips = list()
        self.ignore_until_away = True
        self.arrange()

    def get_nearest_sprites(self, point, limit=None):
        sprites = self.sprites()
        l = [(get_distance(point, sprite.rect.center), i, sprite)
             for i, sprite in enumerate(sprites)]
        if limit is not None:
            l = [i for i in l if i[0] <= limit]
        l.sort()
        l = [(i[0], i[2]) for i in l]
        return l

    def animate_pop(self, sprite, initial, final, index=1):
        """Animate chips moving to popped stack
        """
        # cancel animation that is already running on this sprite
        ani = self._running_animations.get(sprite, None)
        if ani is not None:
            del self._running_animations[sprite]
            self._animations.remove(ani)
            ani.kill()

        shadow = self._shadows_dict.get(sprite, None)
        if shadow is not None:
            shadow.rect = sprite.rect.move(0, 5)

        d = get_distance(sprite.rect.topleft, final)
        if d == 0:
            return None

        fx, fy = final
        ani = Animation(x=fx, y=fy, duration=self.animation_time,
                        transition='out_quint', round_values=True)

        def update_sprite():
            setattr(sprite, 'dirty', 1)
            offset = 20 - self.height_offset
            shadow = self._shadows_dict.get(sprite, None)
            if shadow is not None:
                shadow.rect = sprite.rect.move(0, offset)

        ani.update_callback = update_sprite

        def finalize():
            del self._running_animations[sprite]
            if d > 1:
                self.play_chip_sound()

        ani.callback = finalize

        ani.start(sprite.rect)
        self._running_animations[sprite] = ani

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

    def get_shadow(self, sprite):
        # reused a shadow object to place under a stack
        try:
            return self._shadows_dict[sprite]
        except KeyError:
            shadow = Sprite()
            shadow.image = Chip.shadow
            shadow.rect = shadow.image.get_rect()
            self._shadows.add(shadow)
            self._shadows_dict[sprite] = shadow

    def arrange(self, sprites=None, offset=(0, 0), noclip=False):
        self.sort()
        needs_shadow = list()
        ox, oy = offset
        arrange = super(ChipPile, self).arrange

        for k, g in groupby(self.sprites(), attrgetter('value')):
            stack_offset = 0, 0
            sprites = list(g)

            bottom_sprite = sprites[0]
            self.get_shadow(bottom_sprite)
            needs_shadow.append(bottom_sprite)

            if self._followed_sprite in sprites:
                self.get_shadow(self._followed_sprite)
                needs_shadow.append(self._followed_sprite)

                # arrange sprites lower than the followed one
                i = sprites.index(self._followed_sprite)
                self._popped_chips = list(sprites[i:])

                # arrange sprites over the followed one
                if i > 0:
                    xx, yy = arrange(sprites[:i], (ox, oy))
                    rect = sprites[i - 1].rect

                # this handles the case when the followed sprite
                # is the bottom of the stack
                else:
                    original_pos = sprites[0].rect.topleft
                    xx, yy = arrange(sprites[:1], (ox, oy), animate=False)
                    rect = pygame.Rect(sprites[0].rect)
                    sprites[0].rect.topleft = original_pos

                # TODO: fix this iter_delay nonsense
                previous = self.iter_delay
                self.iter_delay = 0
                stack_offset = xx, yy
                xx += self._desired_pos[0] - rect.centerx
                yy += self._desired_pos[1] - rect.bottom
                arrange(self._popped_chips, (ox + xx, yy), noclip=True)
                self.iter_delay = previous

            else:
                stack_offset = arrange(sprites, (ox, oy))

            ox += self.stacking[0] + stack_offset[0]

        # remove unused shadows
        for sprite, shadow in list(self._shadows_dict.items()):
            if sprite not in needs_shadow:
                del self._shadows_dict[sprite]
                self._shadows.remove(shadow)

        self._needs_arrange = False


class ChipRack(ChipPile):
    """Class to represent a dealer/teller's rack of chips
    """

    def __init__(self, rect):
        super(ChipRack, self).__init__(rect)
        self._origin_offset = 9, -6
        self.stacking = 57, 6
        self.nominal_row_size = 10
        self.max_row_size = 30
        self.background = prepare.GFX["chip_rack_medium"]
        self.front = prepare.GFX["rack_front_medium"]
        rect = self.background.get_rect(topleft=self.rect.topleft)
        self.front_rect = self.front.get_rect(bottomleft=rect.bottomleft)

    def add(self, sprite, **kwargs):
        """Add chip to the rack.

        Chips will have their flat attribute set to True
        and resized to fit the rack graphic
        """
        chips = self.get_groups()
        if len(chips[sprite.value]) < self.max_row_size:
            sprite.chip_size = 48, 30
            sprite.flat = True
            super(ChipRack, self).add(sprite, **kwargs)

    def clear(self, surface, background):
        super(ChipRack, self).clear(surface, self.background)

    def draw(self, surface):
        # redraw = self._needs_arrange
        # if redraw:
        #     surface.blit(self.background, self.rect)
        # HACK: will draw rack front every frame.  :(
        surface.blit(self.background, self.rect)
        dirty = super(ChipRack, self).draw(surface)
        surface.blit(self.front, self.front_rect)
        return dirty

    def get_groups(self):
        chips = defaultdict(list)
        for chip in self.sprites():
            chips[chip.value].append(chip)
        return chips

    def normalize(self):
        """Make sure all rows have same number of chips
        """
        chips = self.get_groups()
        row_size = self.nominal_row_size
        for value in denominations:
            current = len(chips[value])
            if current < row_size:
                for i in range(current, row_size):
                    self.add(Chip(value))
            elif current > row_size:
                for i in range(row_size, current):
                    self.remove(chips[value].pop())
