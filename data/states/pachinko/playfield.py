import json
import os
import random
from math import degrees
from operator import itemgetter
import pymunk
import pymunk.pygame_util
from pymunk import Body, Poly, Segment, Circle, GrooveJoint, DampedSpring
from pymunk import moment_for_circle, PivotJoint, SimpleMotor
import pygame
import pygame.draw
from pygame.transform import rotozoom, smoothscale
from ...prepare import BROADCASTER as B
from ...prepare import GFX

__all__ = ['Playfield']

supported_shapes = frozenset(('polyline', ))
plunger_mass = 5
ball_mass = 1
ball_radius = 10
ball_type = 100
sensor0_type = 101
sensor1_type = 102
plunger_type = 103
pocket_win_type = 104
pocket_fail_type = 105
pocket_return_type = 106


def get_timers(group, callback):
    for sprite in group.sprites():
        if sprite.callback is callback:
            yield sprite


def rect_to_poly(rect):
    return rect.topleft, rect.topright, rect.bottomright, rect.bottomleft


def load_json(space, filename):
    scale = 1
    ooy = 150

    def get_rect(data):
        x, y, w, h = itemgetter('x', 'y', 'width', 'height')(data)
        return pygame.Rect(x, y - ooy, w, h)

    def handle_polyline(data, body=None):
        def get_point(i):
            pt = [i * scale for i in get_xy(i)]
            return pt[0] + ox, (oy + pt[1]) - ooy

        get_xy = itemgetter('x', 'y')
        ox, oy = [i * scale for i in get_xy(data)]
        points = list(data['polyline'])
        prev_pt = get_point(points[0])
        for new_pt in (get_point(pt) for pt in points[1:]):
            segment = Segment(body, prev_pt, new_pt, 1)
            prev_pt = new_pt
            yield segment

    def handle_object_type_plunger(data, body):
        yield PlungerAssembly(space, get_rect(data), body)

    def handle_object_type_spinner(data, body):
        s = Spinner(space, get_rect(data), body)
        s._layer = 2
        yield s

    def handle_object_type_pocket(data, body):
        yield Pocket(space, get_rect(data), body, win=True)

    def handle_object_type_mulligan(data, body):
        yield Pocket(space, get_rect(data), body, returns=True)

    def handle_object_type_fail(data, body):
        yield Pocket(space, get_rect(data), body)

    def handle_object_type_pin(data, body):
        pin = Circle(body, 2, get_rect(data).center)
        pin.elasticity = 1.0
        yield pin

    def handle_objectgroup(layer):
        body = Body()

        for thing in layer['objects']:
            for kind in supported_shapes.intersection(thing.keys()):
                f = get_handler('handle_{}'.format(kind))
                if f:
                    for i in f(thing, body):
                        yield i

            f = get_handler('handle_object_type_{}'.format(thing['type']))
            if f:
                for i in f(thing, body):
                    yield i

    get_handler = lambda name: handlers.get(name, None)
    handlers = {k: v for k, v in locals().items() if k.startswith('handle_')}
    with open(os.path.join("resources", "pachinko", "default.json")) as fp:
        all_data = json.load(fp)

    for layer in all_data['layers']:
        f = get_handler('handle_{}'.format(layer['type']))
        if f:
            for i in f(layer):
                yield i


class Task(pygame.sprite.Sprite):
    def __init__(self, callback, interval=0, loops=1, args=None, kwargs=None):
        assert (callable(callback))
        assert (loops >= -1)
        super(Task, self).__init__()
        self.interval = interval
        self.loops = loops
        self.callback = callback
        self._timer = 0
        self._args = args if args else list()
        self._kwargs = kwargs if kwargs else dict()
        self._loops = loops

    def update(self, delta):
        self._timer += delta
        if self._timer >= self.interval:
            self._timer -= self.interval
            self.callback(*self._args, **self._kwargs)
            if not self._loops == -1:
                self._loops -= 1
                if self._loops <= 0:
                    self.kill()


class PhysicsSprite(pygame.sprite.DirtySprite):
    def __init__(self):
        super(PhysicsSprite, self).__init__()
        self._original_image = None
        self._old_angle = None
        self.shapes = None
        self.dirty = 0
        self.visible = 1
        self.image = None
        self.rect = None

    @property
    def shape(self):
        return self.shapes[0]

    @shape.setter
    def shape(self, value):
        if self.shapes is None:
            self.shapes = [value]
        else:
            self.shapes[0] = value

    def update(self, dt):
        if not self.visible:
            return

        if hasattr(self.shape, "needs_remove"):
            self.kill()
        else:
            angle = round(degrees(self.shape.body.angle), 0)
            if not angle == self._old_angle:
                self.image = rotozoom(self._original_image, -angle, 1)
                self.rect = self.image.get_rect()
                self._old_angle = angle
                self.dirty = 1
            if not self.rect.center == self.shape.body.position:
                self.rect.center = self.shape.body.position
                self.dirty = 1

    def kill(self):
        # TODO: make work for joints, sensors and other odd entities
        for shape in self.shapes:
            space = shape.body._space
            if not shape.body.is_static:
                space.remove(shape.body)
            space.remove(shape)
        self.shapes = None
        self._original_image = None
        super(PhysicsSprite, self).kill()


class Pocket(PhysicsSprite):
    def __init__(self, space, rect, playfield=None, win=False, returns=False):
        super(Pocket, self).__init__()
        color = (220, 100, 0)
        inside = rect.inflate(-10, -10)
        cover = Poly.create_box(playfield, inside.size, rect.center)
        self.shapes = [cover]
        if win:
            self.shapes.extend((
                Segment(playfield, rect.topleft, rect.bottomleft, 1),
                Segment(playfield, rect.bottomleft, rect.bottomright, 1),
                Segment(playfield, rect.bottomright, rect.topright, 1)))
        self._original_image = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(self._original_image, color, rect)
        self.rect = pygame.Rect(rect)
        if win:
            self.shape.collision_type = pocket_win_type
        elif returns:
            self.shape.collision_type = pocket_return_type
        else:
            self.shape.collision_type = pocket_fail_type


class Ball(PhysicsSprite):
    def __init__(self, space, rect):
        super(Ball, self).__init__()
        color = (192, 192, 220)
        radius = rect.width / 2
        body = Body(ball_mass, moment_for_circle(ball_mass, 0, radius))
        body.position = rect.center
        self.shape = Circle(body, radius)
        self.shape.elasticity = .5
        self.shape.friction = 0
        self.shape.layers = 1
        self.shape.collision_type = ball_type
        self.rect = pygame.Rect(0, 0, rect.width, rect.width)
        image = smoothscale(GFX.get('ball-bearing'), self.rect.size)
        self._original_image = image.convert_alpha()
        # pygame.draw.circle(self._original_image, color, self.rect.center,
        #                   radius)


class Spinner(PhysicsSprite):
    def __init__(self, space, rect, playfield=None):
        super(Spinner, self).__init__()
        color = (220, 220, 220)
        r, cy = rect.width / 2, rect.height / 2
        assert (r == cy)
        body = Body(.1, moment_for_circle(.1, 0, r))
        body.position = rect.center
        top = Circle(body, r)
        top.layers = 2
        rect2 = pygame.Rect((-r, -cy), rect.size)
        cross0 = Segment(body, rect2.midleft, rect2.midright, 1)
        cross1 = Segment(body, rect2.midtop, rect2.midbottom, 1)
        j0 = PivotJoint(playfield, body, body.position)
        j1 = SimpleMotor(playfield, body, 0)
        j1.max_force = 200
        self.shapes = [top, cross0, cross1, j0, j1]
        self.rect = pygame.Rect(rect)
        self._original_image = GFX['pachinko-spinner']


class PlungerAssembly(PhysicsSprite):
    def __init__(self, space, rect, playfield=None):
        super(PlungerAssembly, self).__init__()
        self.chute_counter = 0

        spring_strength = 100 * plunger_mass
        chute_opening = playfield.position + rect.center - (rect.width / 2 - ball_radius * 4, 0)
        plunger_rect = pygame.Rect(0, 0, rect.width * .2, ball_radius / 2)
        anchor0 = chute_opening - playfield.position - (ball_radius * 3, 0)
        anchor1 = anchor0 + (rect.width * .8, 0)
        anchor2 = -plunger_rect.width / 2, 0

        plunger_body = Body(plunger_mass, pymunk.inf)
        plunger_shape = Poly.create_box(plunger_body, plunger_rect.size)
        plunger_shape.layers = 1
        plunger_shape.friction = 0
        plunger_shape.elasticity = 1.0
        plunger_shape.collision_type = plunger_type
        plunger_body.position = chute_opening + (plunger_rect.width / 2, 0)

        j0 = GrooveJoint(playfield, plunger_body, anchor0, anchor1, anchor2)
        j1 = DampedSpring(playfield, plunger_body, anchor0, anchor2, 0, spring_strength, 1)

        s0 = Circle(Body(), ball_radius / 2)
        s0.layers = 1
        s0.sensor = True
        s0.collision_type = sensor0_type
        s0.body.position = chute_opening + (ball_radius * 4, 0)

        s1 = Circle(Body(), ball_radius * 3)
        s1.layers = 1
        s1.sensor = True
        s1.collision_type = sensor1_type
        s1.body.position = chute_opening

        def inc_counter(space, arbiter):
            self.chute_counter += 1
            return True

        def dec_counter(space, arbiter):
            self.chute_counter -= 1

        f = space.add_collision_handler
        f(sensor1_type, plunger_type, begin=inc_counter, separate=dec_counter)

        self.spring_strength = spring_strength
        self.plunger_body = plunger_body
        self.ball_chute = pygame.Rect(0, 0, ball_radius * 2, ball_radius * 2)
        self.ball_chute.center = chute_opening
        self._original_image = pygame.Surface(plunger_rect.size)
        self._original_image.fill((192, 255, 255))
        self.shapes = [plunger_shape, s0, s1, j0, j1]
        self.visible = 0


class Playfield(pygame.sprite.LayeredUpdates):
    def __init__(self, *args, **kwargs):
        super(Playfield, self).__init__(*args, **kwargs)
        self._depress = False
        self._plunger = None
        self._plunger_force = None
        self._hopper = 100
        self.jackpot_amount = 5
        self.ball_tray = 0
        self.background = None
        self.step_amount = 1 / 30. / 10
        self.step_times = 10
        self.timers = pygame.sprite.Group()

        def on_jackpot(space, arbiter):
            ball, pocket = arbiter.shapes
            ball.needs_remove = True
            self.ball_tray += self.jackpot_amount + 1
            B.processEvent(('pachinko_jackpot', self))
            B.processEvent(('pachinko_tray', self))
            return True

        def on_ball_return(space, arbiter):
            ball, pocket = arbiter.shapes
            ball.needs_remove = True
            self.ball_tray += 1
            B.processEvent(('pachinko_tray', self))
            return True

        def on_ball_fail(space, arbiter):
            ball, pocket = arbiter.shapes
            ball.needs_remove = True
            B.processEvent(('pachinko_gutter', self))
            return True

        self._space = pymunk.Space()
        self._space.gravity = (0, 1000)
        for item in load_json(self._space, 'default.json'):
            self.add(item)

        f = self._space.add_collision_handler
        f(ball_type, pocket_win_type, begin=on_jackpot)
        f(ball_type, pocket_return_type, begin=on_ball_return)
        f(ball_type, pocket_fail_type, begin=on_ball_fail)
        f(sensor0_type, plunger_type, separate=self.new_ball)

    def auto_push_plunger(self):
        desired_force = 6800
        force = random.randint(desired_force - 200, desired_force + 200)
        self._plunger.plunger_body.apply_impulse((force, 0))

    def new_ball(self, space, arbiter):
        if not self._plunger.chute_counter and self.ball_tray:
            self.add(Ball(space, self._plunger.ball_chute))
            self.ball_tray -= 1
            B.processEvent(('pachinko_tray', self))

    def add(self, *items):
        for item in items:
            if isinstance(item, PhysicsSprite):
                if not item.shape.body.is_static:
                    self._space.add(item.shape.body)
                for shape in item.shapes:
                    self._space.add(shape)

            if isinstance(item, PlungerAssembly):
                self._plunger_force = item.spring_strength * 11
                self._plunger = item
                item._parent = self

            if isinstance(item, pygame.sprite.Sprite):
                super(Playfield, self).add(item)

            else:
                self._space.add(item)

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

    def update(self, surface, dt):
        self.timers.update(dt)
        if self._depress:
            self._plunger.plunger_body.apply_force((self._plunger_force, 0))

        step = self._space.step
        dt = self.step_amount
        for i in xrange(self.step_times):
            step(dt)

        if self.background is None:
            self.background = pygame.image.load(
                os.path.join('resources', 'pachinko', 'playfield.jpg'))
            self.background.scroll(0, -150)
            surface.blit(self.background, (0, 0))

        super(Playfield, self).update(dt)
        self.clear(surface, self.background)
        self.draw(surface)

    def depress_plunger(self):
        self._depress = True

    def release_plunger(self):
        self._depress = False
        self._plunger.plunger_body.reset_forces()

    @property
    def auto_play(self):
        return bool([get_timers(self.timers, self.auto_push_plunger)])

    @auto_play.setter
    def auto_play(self, value):
        if bool(value):
            for sprite in get_timers(self.timers, self.auto_push_plunger):
                sprite.kill()
            self.timers.add(Task(self.auto_push_plunger, 500, -1))
        else:
            for sprite in get_timers(self.timers, self.auto_push_plunger):
                sprite.kill()
