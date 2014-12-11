"""Logging basics"""

import logging
import sys

LOGGING_LEVEL = 5

log = logger = logging.getLogger('serge')
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(relativeCreated)6d] :: %(levelname)7s %(name)20s :: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
log.level = LOGGING_LEVEL


def getLogger(name):
    """Return a new logger with the name"""
    l = logging.getLogger(name)
    l.addHandler(handler)
    l.setLevel(logger.level)
    l.propagate = False
    return l


class Loggable(object):
    """A helper class that adds a logger to a class

    Each instance of the class will have a *log* attribute and can
    use this to log output. The `log` attribute is a logger with the
    usual *debug*, *warn*, *info*, and *error* methods.

    """

    log = None

    def addLogger(self):
        """Add a logger"""
        if 'log' not in self.__class__.__dict__:
            self.__class__.log = getLogger(self.__class__.__name__)

