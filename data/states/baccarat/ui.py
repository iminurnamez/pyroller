""" Note to maintainers:

Yes, these classes are duplicates of built in types.  I have reimplemented
the built in types because I feel these are a little easier to use.

Perhaps we could look at the existing classes and these and make some new
blending of the two.

performance:
since the scenes are always scaled to the screen, there is marginal
performance gains to dirty rect animation.

i have a very quick method for dirty rect animation here, but
it is commented out.  perhaps on very low end hardware, such as
the raspberry pi, it can be enabled again, along with proper
display updates.

"""
from itertools import product, groupby

import pygame

from ... import prepare
from ...components.animation import *


__all__ = (
    'Sprite',
    'SpriteGroup',
    'Stacker',
    'MetaGroup',
    'Button',
    'NeonButton',
    'TextSprite',
    'OutlineTextSprite',
    'remove_animations_of',
    'make_shadow_surface')


def remove_animations_of(group, target):
    """Find animations that target sprites and remove them
    """
    animations = [ani for ani in group.sprites() if isinstance(ani, Animation)]
    to_remove = [ani for ani in animations if target in ani.targets]
    for ani in to_remove:
        ani.kill()
    group.remove(*to_remove)


def reduce_rect_list(rect, others):
    """Quick, unoptimized way to reduce screen blits
    Areas that overlap will be merged together.
    """
    hits = rect.collidelistall(others)
    for index in hits:
        others[index].union_ip(rect)
    return others


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


def make_shadow_surface(surface):
    """create a surface suitable to be used as a shadow

    slow.  use once and cache the result
    image must have alpha channel or results are undefined
    """
    bg_color = 255, 0, 255
    color = 32, 32, 32
    w, h = surface.get_size()
    shad = pygame.Surface((w, h), flags=pygame.RLEACCEL)
    shad.fill(bg_color)
    shad.set_colorkey(bg_color)
    shad.set_alpha(64)
    mask = pygame.mask.from_surface(surface)
    for pixel in product(range(w), range(h)):
        if mask.get_at(pixel):
            shad.set_at(pixel, color)
    return shad

class Sprite(pygame.sprite.DirtySprite):
    """DirtySprite class with extra support for animations
    """
    pass


class SpriteGroup(pygame.sprite.LayeredUpdates):
    """Enhanced pygame sprite group.
    """
    _init_rect = pygame.Rect(0, 0, 0, 0)

    def __init__(self, *args, **kwargs):
        self._spritelayers = {}
        self._spritelist = []
        pygame.sprite.AbstractGroup.__init__(self)
        self._default_layer = kwargs.get('default_layer', 0)
        self._animations = pygame.sprite.Group()

    def extend(self, sprites, **kwargs):
        """A a sequence of sprites to the SpriteGroup
        :param sprites: Sequence (list, set, etc)
        :param kwargs:
        :return: None
        """
        if '_index' in kwargs.keys():
            raise KeyError
        for index, sprite in enumerate(sprites):
            kwargs['_index'] = index
            self.add(sprite, **kwargs)

    def add(self, sprite, **kwargs):
        """Add a sprite to group.  do not pass a sequence or iterator

        LayeredUpdates.add(*sprites, **kwargs): return None

        If the sprite you add has an attribute _layer, then that layer will be
        used. If **kwarg contains 'layer', then the passed sprites will be
        added to that layer (overriding the sprite._layer attribute). If
        neither the sprite nor **kwarg has a 'layer', then the default layer is
        used to add the sprites.
        """
        if not sprite:
            return

        layer = kwargs.get('layer', None)
        if isinstance(sprite, pygame.sprite.Sprite):
            if not self.has_internal(sprite):
                self.add_internal(sprite, layer)
                sprite.add_internal(self)
        else:
            raise ValueError

    def pop(self):
        sprite = self._spritelist[-1]
        self.remove(sprite)
        return sprite

    # def draw(self, surface):
    #     """draw all sprites in the right order onto the passed surface
    #
    #     LayeredUpdates.draw(surface): return Rect_list
    #
    #     """
    #     spritedict = self.spritedict
    #     surface_blit = surface.blit
    #     dirty = self.lostsprites
    #     self.lostsprites = []
    #     dirty_append = dirty.append
    #     init_rect = self._init_rect
    #     for sprite in self.sprites():
    #         if not sprite.dirty:
    #             continue
    #         if not sprite.dirty == 2:
    #             sprite.dirty -= 1
    #         rect = spritedict[sprite]
    #         newrect = surface_blit(sprite.image, sprite.rect)
    #         if rect is init_rect:
    #             dirty_append((newrect, sprite.dirty))
    #         else:
    #             if newrect == rect:
    #                 dirty_append((newrect, sprite.dirty))
    #             elif newrect.colliderect(rect):
    #                 sprite.dirty = 1
    #                 dirty_append((newrect.union(rect), 1))
    #             else:
    #                 dirty_append((newrect, sprite.dirty))
    #                 dirty_append((rect, 1))
    #         spritedict[sprite] = newrect
    #     return dirty

    @property
    def bounding_rect(self):
        """A rect object that contains all sprites of this group
        """
        sprites = self.sprites()
        if len(sprites) == 0:
            return self.rect
        elif len(sprites) == 1:
            return pygame.Rect(sprites[0].rect)
        else:
            return sprites[0].rect.unionall([s.rect for s in sprites[1:]])

    def update(self, *args):
        self._animations.update(*args)
        super(SpriteGroup, self).update(*args)

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
        self._dirty = list()

    def __len__(self):
        return len(self._groups)

    def sprites(self):
        retval = list()
        for group in self.groups():
            retval.extend(group.sprites())
        return retval

    def groups(self):
        return list(self._groups)

    def empty(self):
        for group in self.groups():
            group.empty()
        self._groups = list()

    def add(self, *groups, **kwargs):
        index = kwargs.get('index', None)
        if index is None:
            for group in groups:
                self._groups.append(group)
        else:
            for group in groups:
                self._groups.insert(index, group)

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
        [surface.blit(background, rect, rect) for rect in self._dirty]

    def draw(self, surface):
        """draw all sprites in the right order onto the given surface
        """
        dirty = list()
        dirty_append = dirty.append

        self._needs_update = False
        for group in self.groups():
            for rect in group.draw(surface):
                # try:
                #     rect, clear_flag = rect
                # except ValueError:
                #     clear_flag = True

                clear_flag = 1
                if clear_flag:
                    index = rect.collidelist(dirty)
                    if index == -1:
                        dirty_append(rect)
                    else:
                        dirty = reduce_rect_list(rect, dirty)

        # remove duplicates
        dirty.sort()
        dirty = [k for k, v in groupby(dirty)]

        # # debugging to show overdraw
        # for rect in dirty:
        #     pygame.gfxdraw.box(surface, rect, (255, 32, 32, 64))

        # for sprite in self.sprites():
        #     if sprite.rect.collidelist(dirty):
        #         sprite.dirty = 1

        self._dirty = dirty
        return dirty


class EventButton(Sprite):
    def __init__(self, callback, args=None, kwargs=None):
        super(EventButton, self).__init__()
        assert (callable(callback))
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


class Stacker(SpriteGroup):
    def __init__(self, rect, stacking=None):
        self.arrange_function = None
        super(Stacker, self).__init__()
        self.rect = pygame.Rect(rect)
        self.auto_arrange = True
        self._needs_arrange = True
        self._constraint = 'height'
        self._origin = None
        self._origin_offset = (0, 0)
        self._sprite_anchor = None
        self.iter_delay = 6
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

    def add(self, item, **kwargs):
        """Add something to the stacker

        do not add iterables to this function.  use 'extend'

        :param item: stuff to add
        :return: None
        """
        super(Stacker, self).add(item, **kwargs)
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
        return super(Stacker, self).draw(surface)

    def arrange(self, sprites=None, offset=(0, 0), noclip=False, animate=True):
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
        delay_index = 0

        for index, sprite in enumerate(sprites):
            rect = sprite.rect

            original_anchor = getattr(rect, anchor)

            if constraint == "height":
                new_anchor = x + xx, y + yy

                setattr(rect, anchor, new_anchor)

                if self.rect.colliderect(rect) or noclip:
                    yy += oy
                else:
                    xx += ox
                    yy = oy
                    setattr(rect, anchor, (x + xx, y))

            if hasattr(sprite, 'dirty'):
                sprite.dirty = 1
                sprite.visible = 1

            f = self.arrange_function
            if f is not None and animate:
                final_value = getattr(rect, 'topleft')
                setattr(rect, anchor, original_anchor)
                ani = f(sprite, original_anchor, final_value, index)
                if ani is not None:
                    ani.delay = delay_index * float(self.iter_delay)
                    self._animations.add(ani)
                    delay_index += 1
                else:
                    setattr(rect, anchor, original_anchor)

        return xx, yy


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
        cx = w / 2 - ww / 2
        cy = h / 2 - hh / 2
        for x in range(-6, 6):
            for y in range(-6, 6):
                image.blit(outline, (x + cx, y + cy))
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
