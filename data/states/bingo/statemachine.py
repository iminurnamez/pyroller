from ... import tools
import pygame
from . import loggable


class StateMachine(tools._State, loggable.Loggable):
    """A state machine to use for handling the screen"""

    verbose = True

    def __init__(self, initial_state, speed_factor=1.0):
        """Initialise the machine"""
        super(StateMachine, self).__init__()
        #
        self.addLogger()
        self.method = None
        self.state = initial_state
        self.state_clock = pygame.time.Clock()
        self.delay = 0.0
        self.speed_factor = speed_factor
        self.verbose = True
        #
        self.initUI()

    def initUI(self):
        """Initialise the user interface"""
        raise NotImplementedError('Need to implement initUI')

    def drawUI(self, surface, scale):
        """Draw the user interface"""
        raise NotImplementedError('Need to implement drawUI')

    def update(self, surface, keys, now, dt, scale):
        """Update the game state"""
        self.state_clock.tick(dt)
        self.delay -= self.state_clock.get_time() * self.speed_factor
        #
        # Process this state
        if self.state and self.delay < 0:
            if self.method is None:
                self.method = getattr(self, self.state.lower())()
                if self.verbose:
                    self.log.debug('Calling state: %s' % self.state)
            try:
                self.delay = next(self.method)
            except StopIteration:
                self.method = None
        #
        # Draw the interface
        self.drawUI(surface, scale)