"""
Contains a class for displaying spotlights on the title screen.
A helper class for non-center axis image rotations is also found here.
If this function is needed elsewhere it can be moved to a more appropriate
location.
"""

import math
import pygame as pg

from .. import prepare


class Rotator(object):
    """
    A helper class for rotating objects about origins other than their centers.
    """
    def __init__(self, center, origin, image_angle=0):
        """
        Arguments are the center of the object being rotated (x,y);
        the origin of rotation (x,y); and the initial rotation of the image
        (given in degrees) if non-zero.
        """
        x_mag = center[0]-origin[0]
        y_mag = center[1]-origin[1]
        self.radius = math.hypot(x_mag,y_mag)
        self.start_angle = math.atan2(-y_mag,x_mag)-math.radians(image_angle)

    def __call__(self, angle, origin):
        """
        Returns the new center of the object.
        Arguments are the angle to rotate by (in degrees);
        and the origin of rotation (x,y).
        """
        new_angle = math.radians(angle)+self.start_angle
        new_x = origin[0] + self.radius*math.cos(new_angle)
        new_y = origin[1] - self.radius*math.sin(new_angle)
        return (new_x, new_y)


class SpotLight(object):
    """An oscillating spotlight."""
    cache = {}

    @classmethod
    def clear_cache(cls):
        """
        The cache of image rotations can be fairly heavy on memory.
        Call this function when switching to a state that doesn't need
        spotlights to reclaim that memory.
        """
        cls.cache = {}

    def __init__(self, pos, period, arc, start=0):
        """
        Argument pos is the midbottom point of the spotlight image (the axis
        of rotation); period is the time needed to osciallate a full cycle
        (given in seconds); arc is the span of one full oscillation (given in
        degrees); start is a float between 0 and 1 indicating how far through
        first oscillation to start (start=0.5 for example will start in the
        opposite direction as start=0 being exactly half way through the
        cycle).
        """
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
        """
        Check to see if image has already been cached at given angle.
        If not, perform rotation and cache it.
        The position of the new rectangle of the rotated image is found
        using the Rotator helper class.
        """
        angle = int(self.angle)
        if angle in SpotLight.cache:
            self.image = SpotLight.cache[angle]
        else:
            self.image = pg.transform.rotozoom(self.raw_image, angle, 1)
            SpotLight.cache[angle] = self.image
        new_center = self.rotator(angle, self.origin)
        self.rect = self.image.get_rect(center=new_center)

    def update(self, dt):
        """
        Calculate the location in the osciallator based on elapsed time.
        After finding the new angle set the image appropriately.
        """
        self.elapsed += dt
        interp = math.sin(2*math.pi*(self.elapsed/float(self.period)))
        self.elapsed %= self.period
        self.angle = self.arc*interp
        self.make_image()

    def draw(self, surface):
        """
        Draw the spotlight using additive blending mode.  This is a huge
        performance hit, but as performance is not critical in the title
        screen it should be a non-issue.
        """
        flags = pg.BLEND_RGB_ADD
        surface.blit(self.image, self.rect, special_flags=flags)
