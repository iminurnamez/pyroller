"""Stub file for compatibility - this should eventually be removed

At one point this was where the utility code sat

"""

from ...components.common import *
from ...components import common
from .settings import SETTINGS as S


# The following functions are intended to provide temporary backwards
# compatibility to minimize changes while this framework change is being
# evaluated

def getLabel(name, position, text):
    """Return a label using the current settings"""
    return common.getLabel(name, position, text, S)


def ImageButton(name, position, filename, text_properties, text, callback, arg, scale=1.0):
    return common.ImageButton(name, position, filename, text_properties, text, callback, arg, S, scale)


def ImageOnOffButton(name, position, on_filename, off_filename, text_properties, text, state, callback, arg, scale=1.0):
    return common.ImageOnOffButton(name, position, on_filename, off_filename, text_properties, text, state,
                                   callback, arg, S, scale)