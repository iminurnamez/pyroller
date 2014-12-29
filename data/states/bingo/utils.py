"""Stub file for compatibility - this should eventually be removed

At one point this was where the utility code sat

"""

from ...components.common import *
from ...components import common
from .settings import SETTINGS as S


# The following functions / classes are intended to provide temporary backwards
# compatibility to minimize changes while this framework change is being
# evaluated

def ImageButton(name, position, filename, text_properties, text, callback, arg, scale=1.0):
    obj = common.ImageButton(name, position, filename, text_properties, text, S, scale)
    obj.linkEvent(E_MOUSE_CLICK, lambda o, a: callback(arg))
    obj.arg = arg
    return obj


def ImageOnOffButton(name, position, on_filename, off_filename, text_properties, text, state, callback, arg, scale=1.0):
    obj = common.ImageOnOffButton(name, position, on_filename, off_filename, text_properties, text, state,
                                   S, scale)
    obj.linkEvent(E_MOUSE_CLICK, lambda o, a: callback(arg))
    obj.arg = arg
    return obj
