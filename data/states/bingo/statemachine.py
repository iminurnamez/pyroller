"""Implementation of classes to help in running long running statefull operations"""

import collections
import pygame as pg

from ... import tools
import pygame
from . import loggable


class StateExecutor(loggable.Loggable):
    """Executes a generator through a sequence with delays"""

    def __init__(self, name, generator, delay=0):
        """Initialise the executor"""
        self.addLogger()
        self.name = name
        self.generator = generator
        self.delay = delay
        self.done = False
        #
        self.state_clock = pygame.time.Clock()

    def update(self, dt):
        """Update the state"""
        self.state_clock.tick(dt)
        self.delay -= self.state_clock.get_time()
        if not self.done and self.delay < 0:
            try:
                self.delay = next(self.generator)
            except StopIteration:
                self.done = True


class StateMachine(tools._State, loggable.Loggable):
    """A state machine to use for handling the screen"""

    verbose = True

    def __init__(self, initial_state, speed_factor=1.0):
        """Initialise the machine"""
        super(StateMachine, self).__init__()
        #
        self.addLogger()
        self.generators = []
        self.state_clock = pygame.time.Clock()
        self.delay = 0.0
        self.speed_factor = speed_factor
        self.verbose = True
        #
        self.add_generator(initial_state, getattr(self, initial_state)())
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
        if pg.key.get_mods():
            self.log.debug('Frame rate {0}'.format(1000 / dt))
        #
        # Process all states
        for executor in list(self.generators):
            executor.update(dt)
            if executor.done:
                self.generators.remove(executor)
        #
        # Draw the interface
        self.drawUI(surface, scale)

    def add_generator(self, name, generator):
        """Add a new generator to run"""
        self.log.debug('Adding new executor {0}, {1}'.format(name, generator))
        self.generators.append(StateExecutor(name, generator))

    def stop_generator(self, name):
        """Stop a generator with a specific name"""
        for generator in self.generators[:]:
            if generator.name == name:
                self.generators.remove(generator)
                break
        else:
            raise ValueError('A generator named {0} was not found'.format(name))