"""Logging basics"""

import logging
import sys
from .. import prepare

LOGGING_LEVEL = logging.DEBUG if prepare.ARGS['debug'] else logging.ERROR

log = logger = logging.getLogger('pyroller')
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
    """A mixin class that adds a logger to a class

    Each instance of the class will have a *log* attribute and can
    use this to log output. The `log` attribute is a logger with the
    usual *debug*, *warn*, *info*, and *error* methods.

    Classes should ensure that they call addLogger early in the
    initialisation process.

    """

    log = None

    def addLogger(self):
        """Add a logger"""
        if 'log' not in self.__class__.__dict__:
            self.__class__.log = getLogger(self.__class__.__name__)

    def warnOnce(self, text):
        """Warn about some condition but only do this once regardless of how many times it occurs

        This could be probably be done better by using the warnings

        """
        if text not in self.warnOnce._cache:
            self.log.warn(text)
            self.warnOnce._cache.add(text)

    warnOnce._cache = set()