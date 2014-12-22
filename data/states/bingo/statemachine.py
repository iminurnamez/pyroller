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
        self.last_delay = self.delay = delay
        self.done = False
        #
        self.state_clock = pygame.time.Clock()

    def update(self, dt):
        """Update the state"""
        self.state_clock.tick(dt)
        self.delay -= self.state_clock.get_time()
        if not self.done and self.delay < 0:
            try:
                self.last_delay = self.delay = next(self.generator)
            except StopIteration:
                self.done = True

    def next_step(self):
        """Immediately make the generator go to the next step"""
        self.delay = 0

    def update_interval(self, interval):
        """Update the interval we are waiting for

        This behaves as though the last delay requested is
        immediately changed to the specified value.

        If we have already waited for the specified time
        then immediately go to the next step

        """
        time_elapsed = self.last_delay - self.delay
        time_to_go = interval - time_elapsed
        self.delay = time_to_go

    def stop(self):
        """Stop this executor"""
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
        new_generator = StateExecutor(name, generator)
        self.generators.append(new_generator)
        return new_generator

    def stop_generator(self, name):
        """Stop a generator with a specific name"""
        for generator in self.generators[:]:
            if generator.name == name:
                self.generators.remove(generator)
                break
        else:
            raise ValueError('A generator named {0} was not found'.format(name))