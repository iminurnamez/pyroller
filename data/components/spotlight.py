import math
import pygame as pg

from .. import prepare


class Rotator(object):
    def __init__(self, center, origin, image_angle=0):
        x_mag = center[0]-origin[0]
        y_mag = center[1]-origin[1]
        self.radius = math.hypot(x_mag,y_mag)
        self.start_angle = math.atan2(-y_mag,x_mag)-math.radians(image_angle)

    def __call__(self,angle,origin):
        new_angle = math.radians(angle)+self.start_angle
        new_x = origin[0] + self.radius*math.cos(new_angle)
        new_y = origin[1] - self.radius*math.sin(new_angle)
        return (new_x, new_y)


class SpotLight(object):
    cache = {}
    caching = True

    @classmethod
    def clear_cache(cls):
        cls.cache = {}

    def __init__(self, pos, period, arc, start=0):
        self.angle = 0
        self.raw_image = prepare.GFX["spotlight"]
        self.rect = self.raw_image.get_rect(midbottom=pos)
        self.origin = self.rect.midbottom
        self.rotator = Rotator(self.rect.center, self.origin, self.angle)
        self.period = period*1000
        self.elapsed = self.period*start
        self.arc = arc//2
        self.make_image()

    def make_image(self):
        if not self.caching:
            angle = self.angle
            self.image = pg.transform.rotozoom(self.raw_image, angle, 1)
        else:
            angle = int(self.angle)
            if angle in SpotLight.cache:
                self.image = SpotLight.cache[angle]
            else:
                self.image = pg.transform.rotozoom(self.raw_image, angle, 1)
                SpotLight.cache[angle] = self.image
        new_center = self.rotator(angle, self.origin)
        self.rect = self.image.get_rect(center=new_center)

    def update(self, dt):
        self.elapsed += dt
        interp = math.sin(2*math.pi*(self.elapsed/float(self.period)))
        self.elapsed %= self.period
        self.angle = self.arc*interp
        self.make_image()

    def draw(self, surface):
        flags = pg.BLEND_RGB_ADD
##        flags = 0
        surface.blit(self.image, self.rect, special_flags=flags)
