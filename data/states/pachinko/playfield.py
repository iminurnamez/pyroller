import math
import json
import os
import functools
from operator import itemgetter
from itertools import chain
import pymunk
from pymunk import Body, Poly, Segment, Circle
from pymunk import moment_for_box, moment_for_circle
import pymunk.pygame_util
import pygame

supported_shapes = frozenset(('polyline', ))
ball_radius = 10


def load_json(space, filename):
    scale = 1
    ooy = 000


    def get_handler(name):
        return handlers.get(name, None)

    def get_rect(data):
        x, y, w, h = itemgetter('x', 'y', 'width', 'height')(data)
        return pygame.Rect(x, height - y - h, w, h)

    def handle_polyline(data, body=None):
        if body is None:
            body = pymunk.Body()

        def get_point(i):
            pt = [i * scale for i in get_xy(i)]
            return pt[0] + ox, height - (oy + pt[1])

        get_xy = itemgetter('x', 'y')
        ox, oy = [i * scale for i in get_xy(data)]
        points = list(data['polyline'])
        prev_pt = get_point(points[0])
        for new_pt in (get_point(pt) for pt in points[1:]):
            segment = Segment(body, prev_pt, new_pt, 1)
            prev_pt = new_pt
            yield segment

    def handle_object_type_plunger(data, body):
        plunger = PlungerAssembly()
        assembly_rect = get_rect(data)
        plunger.build(space, body, assembly_rect)
        yield plunger

    def handle_objectgroup(layer):
        # if true, then this is playfield geometry and will need a body
        if layer['name'].startswith('geometry'):
            #mass = 999999
            #body = pymunk.Body(mass, pymunk.inf)
            #yield body
            body = pymunk.Body()
            body.position += (200, -150)
        else:
            body = None

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

    height = all_data['tileheight'] * all_data['height']
    print(height)

    for layer in all_data['layers']:
        f = get_handler('handle_{}'.format(layer['type']))
        if f:
            for i in f(layer):
                yield i

files = os.path.join("resources", "pachinko")


def rect_to_poly(rect):
    return rect.topleft, rect.topright, rect.bottomright, rect.bottomleft


class Pocket(pygame.sprite.DirtySprite):
    pass


class Ball(pygame.sprite.DirtySprite):
    def __init__(self):
        super(Ball, self).__init__()
        self.shape = None

    def build(self, space):
        assert (self.shape is None)
        mass = .01
        radius = 20
        moment = moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        shape = pymunk.Circle(body, 10)
        shape.friction = 1.0
        shape.layers = 0
        self.shape = shape
        space.add(body, shape)


class Spinner(pygame.sprite.DirtySprite):
    def __init__(self):
        super(Spinner, self).__init__()
        self.shape = None

    def build(self, space, rect):
        assert (self.shape is None)
        mass = .1
        radius = rect.width / 2
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = rect.center
        top = pymunk.Circle(body, radius)
        top.layers = 2
        rect = pygame.Rect((-rect.width / 2, -rect.height / 2), rect.size)
        cross0 = pymunk.Segment(body, rect.midleft, rect.midright, 1)
        cross1 = pymunk.Segment(body, rect.midtop, rect.midbottom, 1)
        joint = pymunk.PivotJoint(space.static_body, body, body.position)
        space.add(body, top, cross0, cross1, joint)


class PlungerAssembly(pygame.sprite.DirtySprite):
    def __init__(self):
        super(PlungerAssembly, self).__init__()
        self.plunger_body = None
        self.chute_opening = None
        self.spring_strength = None
        self._ball_chute_sensor = None
        self._chute_counter = 0
        self._chute_latch = True

    def add_ball(self, space, arbiter):
        sensor, plunger = arbiter.shapes

        if not self._chute_latch:
            mass = 1
            body = pymunk.Body(mass, moment_for_circle(mass, 0, 1))
            shape = pymunk.Circle(body, 10)
            shape.friction = 1.0
            shape.layers = 1
            body.position = self.chute_opening
            space.add(body, shape)

    def build(self, space, assembly_body, assembly_rect):
        plunger_mass = 5
        plunger_elasticity = 1.0
        plunger_rect = pygame.Rect(0, 0,
                                  ball_radius * 10,
                                  ball_radius / 2)
        spring_strength = 100 * plunger_mass
        spring_dampening = 1
        spring_length = assembly_rect.width * .8

        sensor0_type = 100
        sensor1_type = 101
        plunger_type = 102

        assembly_body_position = assembly_body.position + assembly_rect.center
        chute_opening = assembly_body_position - (assembly_rect.width / 2 -ball_radius * 4, 0)

        assembly_shape = Poly.create_box(assembly_body,
                                         assembly_rect.size,
                                         assembly_rect.center)
        assembly_shape.layers = 0
        space.add(assembly_shape)

        plunger_body = Body(plunger_mass, pymunk.inf)
        plunger_shape = Poly.create_box(plunger_body, plunger_rect.size)
        plunger_shape.layers = 1
        plunger_shape.friction = 0
        plunger_shape.elasticity = plunger_elasticity
        plunger_shape.collision_type = plunger_type
        plunger_body.position = chute_opening + (plunger_rect.width / 2, 0)
        space.add(plunger_body, plunger_shape)

        anchor0 = chute_opening - assembly_body.position - (ball_radius * 3, 0)
        anchor1 = anchor0 + (spring_length, 0)
        anchor2 = -plunger_rect.width / 2, 0

        plunger_joint = pymunk.GrooveJoint(assembly_body, plunger_body,
                                          anchor0, anchor1, anchor2)
        space.add(plunger_joint)

        spring = pymunk.DampedSpring(assembly_body, plunger_body,
                                     anchor0, anchor2, 0,
                                     spring_strength,
                                     spring_dampening)
        space.add(spring)

        body = Body()
        sensor = pymunk.Circle(body, ball_radius / 2)
        sensor.layers = 1
        sensor.sensor = True
        sensor.collision_type = sensor0_type
        sensor.body.position = chute_opening + (ball_radius * 4, 0)
        space.add(sensor)
        space.add_collision_handler(sensor0_type, plunger_type,
                                    separate=self.add_ball)

        def inc_chute_counter(space, arbiter):
            a, b, = arbiter.shapes
            self._chute_counter += 1
            return True

        def dec_chute_counter(*args, **kwargs):
            self._chute_counter -= 1
            self._chute_latch = bool(self._chute_counter)

        body = Body()
        sensor = pymunk.Circle(body, ball_radius * 3)
        sensor.layers = 1
        sensor.sensor = True
        sensor.collision_type = sensor1_type
        sensor.body.position = chute_opening
        space.add(sensor)
        space.add_collision_handler(sensor1_type, plunger_type,
                                    begin=inc_chute_counter,
                                    separate=dec_chute_counter)

        self._ball_chute_sensor = sensor
        self.plunger_body = plunger_body
        self.sensor = sensor
        self.chute_opening = chute_opening
        self.spring_strength = spring_strength

        return plunger_body


class Playfield(pygame.sprite.RenderUpdates):
    def __init__(self, *args, **kwargs):
        super(Playfield, self).__init__(*args, **kwargs)
        self._dirty = False
        self._space = None
        self._members = list()
        self.depress = False
        self.plunger_body = None

    def load(self, filename):
        for i in load_json(self._space, 'default.json'):
            if isinstance(i, PlungerAssembly):
                self.plunger_body = i.plunger_body
            else:
                self._space.add(i)

    def build(self):
        assert (not self._members)
        size = pygame.Rect(0, 0, 100, 1000)
        self._space = pymunk.Space()
        self._space.gravity = (0, -1000)
        self.load(None)

    def update(self, surface, dt):
        dt = 1 / 30. / 10.
        if self.depress:
            self.plunger_body.apply_force((8000, 0))

        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)
        self._space.step(dt)

        # super(Playfield, self).draw(surface)
        surface.fill((0, 0, 0))
        pymunk.pygame_util.draw(surface, self._space)

    def depress_plunger(self):
        self.depress = True

    def release_plunger(self):
        self.depress = False
        self.plunger_body.reset_forces()
