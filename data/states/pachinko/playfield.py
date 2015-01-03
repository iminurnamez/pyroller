import json
import os
from math import degrees
from operator import itemgetter
import pymunk
from pymunk import Body, Poly, Segment, Circle, GrooveJoint, DampedSpring
from pymunk import moment_for_circle
import pymunk.pygame_util
import pygame
import pygame.draw
import pygame.gfxdraw
from pygame.transform import rotozoom

pymunk.pygame_util.flip_y = False
files = os.path.join("resources", "pachinko")
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


def rect_to_poly(rect):
    return rect.topleft, rect.topright, rect.bottomright, rect.bottomleft


def load_json(space, filename):
    scale = 1
    ooy = 150
    get_handler = lambda name: handlers.get(name, None)

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
        yield Spinner(space, get_rect(data), body)

    def handle_object_type_pocket(data, body):
        yield Pocket(space, get_rect(data), body, win=True, walls=True)

    def handle_object_type_fail(data, body):
        yield Pocket(space, get_rect(data), body)

    def handle_object_type_pin(data, body):
        pin = Circle(body, 2, get_rect(data).center)
        pin.elasticity = 1.0
        yield pin

    def handle_objectgroup(layer):
        body = pymunk.Body()

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

    handlers = {k:v for k,v in locals().items() if k.startswith('handle_')}
    with open(os.path.join(files, "default.json")) as fp:
        all_data = json.load(fp)

    for layer in all_data['layers']:
        f = get_handler('handle_{}'.format(layer['type']))
        if f:
            for i in f(layer):
                yield i


class PhysicsSprite(pygame.sprite.DirtySprite):
    def __init__(self):
        super(PhysicsSprite, self).__init__()
        self.original_image = None
        self.shapes = None
        self._old_angle = None

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
        if hasattr(self.shape, "needs_remove"):
            self.kill()
        else:
            angle = degrees(self.shape.body.angle)
            if not angle == self._old_angle or self.dirty:
                self.image = rotozoom(self.original_image, angle, 1)
                self.rect = self.image.get_rect()
                self._old_angle = angle
                self.dirty = False
            self.rect.center = self.shape.body.position
            self.dirty = 1

    def kill(self):
        for shape in self.shapes:
            space = shape.body._space
            if not shape.body.is_static:
                space.remove(shape.body)
            space.remove(shape)
        self.shapes = None
        super(PhysicsSprite, self).kill()


class Pocket(PhysicsSprite):
    def __init__(self, space, rect, playfield=None, win=False, walls=False):
        super(Pocket, self).__init__()
        color = (220, 100, 0)
        inside = rect.inflate(-3, -3)
        cover = Poly.create_box(playfield, inside.size, rect.center)
        self.shapes = [cover]
        if walls:
            s0 = Segment(playfield, rect.topleft, rect.bottomleft, 1)
            s1 = Segment(playfield, rect.bottomleft, rect.bottomright, 1)
            s2 = Segment(playfield, rect.bottomright, rect.topright, 1)
            self.shapes.extend((s0, s1, s2))
        self.original_image = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(self.original_image, color, rect)
        self.rect = pygame.Rect(rect)
        self.shape.collision_type = pocket_win_type if win else pocket_fail_type
        self.update(None)


class Ball(PhysicsSprite):
    def __init__(self, space, rect):
        super(Ball, self).__init__()
        color = (192, 192, 220)
        radius = rect.width / 2
        body = Body(ball_mass, moment_for_circle(ball_mass, 0, radius))
        body.position = rect.center
        self.shape = Circle(body, radius)
        self.shape.friction = .5
        self.shape.layers = 1
        self.shape.collision_type = ball_type
        self.rect = pygame.Rect(0, 0, rect.width, rect.width)
        self.original_image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, color, self.rect.center, radius)
        self.update(None)


class Spinner(PhysicsSprite):
    def __init__(self, space, rect, playfield=None):
        super(Spinner, self).__init__()
        color = (220, 220, 220)
        radius = rect.width / 2
        body = pymunk.Body(.1, moment_for_circle(.1, 0, radius))
        body.position = rect.center
        top = Circle(body, radius)
        top.layers = 2
        rect2 = pygame.Rect((-rect.width / 2, -rect.height / 2), rect.size)
        cross0 = pymunk.Segment(body, rect2.midleft, rect2.midright, 1)
        cross1 = pymunk.Segment(body, rect2.midtop, rect2.midbottom, 1)
        joint = pymunk.PivotJoint(playfield, body, body.position)
        self.shapes = [top, cross0, cross1, joint]
        self.rect = pygame.Rect(rect)
        self.original_image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, color, (radius, radius), radius)
        self.update(None)


class PlungerAssembly(PhysicsSprite):
    def __init__(self, space, rect, playfield=None):
        super(PlungerAssembly, self).__init__()
        self._chute_counter = 0

        plunger_rect = pygame.Rect(0, 0, rect.width * .2, ball_radius / 2)
        spring_strength = 100 * plunger_mass
        spring_length = rect.width * .8
        assembly_body_position = playfield.position + rect.center
        chute_opening = assembly_body_position - (rect.width / 2 -ball_radius * 4, 0)
        anchor0 = chute_opening - playfield.position - (ball_radius * 3, 0)
        anchor1 = anchor0 + (spring_length, 0)
        anchor2 = -plunger_rect.width / 2, 0

        assembly_shape = Poly.create_box(playfield, rect.size, rect.center)
        assembly_shape.layers = 0
        space.add(assembly_shape)

        plunger_body = Body(plunger_mass, pymunk.inf)
        plunger_shape = Poly.create_box(plunger_body, plunger_rect.size)
        plunger_shape.layers = 1
        plunger_shape.friction = 0
        plunger_shape.elasticity = 1.0
        plunger_shape.collision_type = plunger_type
        plunger_body.position = chute_opening + (plunger_rect.width / 2, 0)

        space.add(GrooveJoint(playfield, plunger_body, anchor0, anchor1, anchor2))
        space.add(DampedSpring(playfield, plunger_body, anchor0, anchor2, 0, spring_strength, 1))

        sensor = Circle(space.static_body, ball_radius / 2)
        sensor.layers = 1
        sensor.sensor = True
        sensor.collision_type = sensor0_type
        sensor.body.position = chute_opening + (ball_radius * 4, 0)
        space.add(sensor)
        space.add_collision_handler(sensor0_type, plunger_type,
                                    separate=self.add_ball)

        def inc_chute_counter(*args):
            self._chute_counter += 1
            return True

        def dec_chute_counter(*args):
            self._chute_counter -= 1

        sensor = Circle(space.static_body, ball_radius * 3)
        sensor.layers = 1
        sensor.sensor = True
        sensor.collision_type = sensor1_type
        sensor.body.position = chute_opening
        space.add(sensor)
        space.add_collision_handler(sensor1_type, plunger_type,
                                    begin=inc_chute_counter,
                                    separate=dec_chute_counter)

        self.original_image = pygame.Surface(plunger_rect.size)
        self.original_image.fill((128, 128, 128))
        self.plunger_body = plunger_body
        self.chute_opening = pygame.Rect(0, 0, ball_radius * 2, ball_radius * 2)
        self.chute_opening.center = chute_opening
        self.spring_strength = spring_strength
        self.shapes = [plunger_shape]
        self.update(None)

    def add_ball(self, space, arbiter):
        if not self._chute_counter:
            self._parent.add(Ball(space, self.chute_opening))


class Playfield(pygame.sprite.Group):
    def __init__(self, *args, **kwargs):
        super(Playfield, self).__init__(*args, **kwargs)
        self.depress = False
        self.plunger_body = None
        self.background = None

        def on_jackpot(space, arbiter):
            ball, pocket = arbiter.shapes
            ball.needs_remove = True
            return True

        def on_ball_fail(space, arbiter):
            ball, pocket = arbiter.shapes
            ball.needs_remove = True
            return True

        self._space = pymunk.Space()
        self._space.gravity = (0, 1000)
        for item in load_json(self._space, 'default.json'):
            self.add(item)

        f = self._space.add_collision_handler
        f(ball_type, pocket_win_type, begin=on_jackpot)
        f(ball_type, pocket_fail_type, begin=on_ball_fail)

    def add(self, *items):
        for item in items:
            if isinstance(item, PhysicsSprite):
                if not item.shape.body.is_static:
                    self._space.add(item.shape.body)
                for shape in item.shapes:
                    self._space.add(shape)

            if isinstance(item, PlungerAssembly):
                self.plunger_body = item.plunger_body
                item._parent = self

            if isinstance(item, pygame.sprite.Sprite):
                super(Playfield, self).add(item)

            else:
                self._space.add(item)

    def update(self, surface, dt):
        steps = 10
        dt = 1 / 30. / 10.
        if self.depress:
            self.plunger_body.apply_force((8000, 0))

        step = self._space.step
        for i in xrange(steps):
            step(dt)

        if self.background is None:
            self.background = pygame.Surface(surface.get_size())
            self.background = pygame.image.load("resources/pachinko/playfield.jpg")
            self.background.scroll(0, -150)
            pymunk.pygame_util.draw(self.background, self._space)
            surface.blit(self.background, (0, 0))

        sup = super(Playfield, self)
        sup.update(dt)
        sup.clear(surface, self.background)
        sup.draw(surface)

    def depress_plunger(self):
        self.depress = True

    def release_plunger(self):
        self.depress = False
        self.plunger_body.reset_forces()
