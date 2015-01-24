"""A module of funtions dealing with angles in pygame.
    All functions (other than project) take lists or tuples
    of pygame coordinates as origin, destination
    and return the appropriate angle in radians."""

from math import pi, hypot, cos, sin, atan2, degrees, radians
import pygame as pg


def get_distance(origin, destination):
    """Returns distance from origin to destination."""
    return hypot(destination[0] - origin[0],
                 destination[1] - origin[1])


def get_midpoint(origin, destination):
    """ Return the midpoint between two points on cartesian plane.
    :param origin: (x, y)
    :param destination: (x, y)
    :return: (x, y)
    """
    x_dist = destination[0] + origin[0]
    y_dist = destination[1] + origin[1]
    return x_dist / 2, y_dist / 2


def get_angle(origin, destination):
    """Returns angle in radians from origin to destination.
        This is the angle that you would get if the points were
        on a cartesian grid. Arguments of (0,0), (1, -1)
        return pi/4 (45 deg) rather than  7/4
        """
    x_dist = destination[0] - origin[0]
    y_dist = destination[1] - origin[1]
    return atan2(-y_dist, x_dist) % (2 * pi)


def get_xaxis_reflection(origin, destination):
    """Returns angle in radians reflected on x-axis. This is the
        reflection angle of a top or bottom collision."""
    x_dist = origin[0] - destination[0]
    y_dist = origin[1] - destination[1]
    return atan2(-y_dist, -x_dist) % (2 * pi)


def get_yaxis_reflection(origin, destination):
    """Returns angle in radians reflected on y-axis.
        This is the angle of reflection for a side collision."""
    x_dist = origin[0] - destination[0]
    y_dist = origin[1] - destination[1]
    return atan2(y_dist, x_dist) % (2 * pi)


def get_opposite_angle(origin, destination):
    """Returns angle in radians from destination to origin."""
    x_dist = origin[0] - destination[0]
    y_dist = origin[1] - destination[1]
    return atan2(-y_dist, x_dist) % (2 * pi)


def project(pos, angle, distance):
    """Returns tuple of pos projected distance at angle
        adjusted for pygame's y-axis"""
    return (pos[0] + (cos(angle) * distance),
            pos[1] - (sin(angle) * distance))


def get_collision_side(rect, other_rect):
    """Finds whether collision is left/right, top/bottom or corner."""
    thickness = 1
    width, height = rect.size
    left_bumper = pg.Rect(rect.left - thickness, rect.top - thickness,
                          thickness, height + (thickness * 2))
    right_bumper = pg.Rect(rect.right, rect.top - thickness, thickness,
                           height + (thickness * 2))
    top_bumper = pg.Rect(rect.left - thickness, rect.top - thickness,
                         width + (thickness * 2), thickness)
    bottom_bumper = pg.Rect(rect.left - thickness, rect.bottom,
                            width + (thickness * 2), thickness)

    colls = {"left": (other_rect.colliderect(left_bumper)
                      and not other_rect.colliderect(right_bumper)),
             "right": (other_rect.colliderect(right_bumper)
                       and not other_rect.colliderect(left_bumper)),
             "top": (other_rect.colliderect(top_bumper)
                     and not other_rect.colliderect(bottom_bumper)),
             "bottom": (other_rect.colliderect(bottom_bumper)
                        and not other_rect.colliderect(top_bumper))}
    for side in colls:
        if colls[side]:
            return side
    return "corner"


if __name__ == "__main__":
    print(get_distance((100, 100), (200, 100)))
    print(get_distance((100, 100), (0, 200)))
