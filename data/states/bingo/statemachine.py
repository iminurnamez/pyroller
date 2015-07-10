"""Classes to help in running and / or chaining long running statefull operations

This is useful if you want to implement long running processes (ie across many frames).
You can write these as simple generators and you don't have to worry about keeping
track of where you are in the sequence as this is done for you. The sequence can
include many steps and can branch and repeat etc.


The normal way to use these classes is to make your State a subclass of StateMachine.
This requires you to implement two methods to set up and render your on screen items.
There is nothing special going on here, it just keeps your logic away from the
statefull machinery.

1. When initialising the state will call a method initUI that you must implement.
You can do whatever you want in there but normally you would initialise any UI
components.

2. Calls drawUI(surface, scale) whenever you need to redraw the current frame.


The rest is where the magic happens,

You can start a long running process with a call to add_generator('<name>', some_generator)
Your generator will be called repeatedly until it exits. You can also stop it manually by
calling stop_generator() on the state, by calling stop() on the StateExecutor that
is returned by add_generator, or by raising a StopIteration in the generator.

Your generator can yield in two ways,

A - "yield": stops execution and returns to the same point next frame

B - "yield <N>: stops execution and returns to the same point <N> ms later


For an example of usage, let's say the player does something and you want to
move a card across the screen, flash it three times, then move it down the screen.
If the player clicks somewhere else in the meantime then the motion should stop.
The generator approach allows you to write this very logically and not worry about
keeping state (moving across, flashing, moving down etc).

In your State you would detect two conditions a) the motion should state, b) the
motion should be interrupted, and a generator method move_card()

    class MyState(StateMachine):
        def drawUI(self, surface, scale):
            ...
            if condition_to_initiate_motion:
                self.card_mover = self.add_generator('move-card', self.move_card(50, 100))
            if condition_to_interrupt_card:
                self.card_mover.stop()
            ...

        def move_card(self, dx, dy):
            # Move card over to the right
            for x in range(dx):
                self.card.x += 1
                yield 100 # Pause for 100ms

            # Flash the card three times
            for repeat in range(dy):
                self.card.visible = False
                yield 100 # Hide for short time
                self.card.visible = True
                yield 900 # Show for a longer time

            # Move the card down
            for y in range(100):
                self.card.y -= 1
                yield 100 # Pause for 100ms


The above example shows how a single stateful operation can be written very cleanly.
Another use case is to chain states together.

Suppose you want to show cards shuffling, then being dealt and then being turned
over, one-by-one. You can chain these by calling add_generator at the end of each
operation.


    class State(StateMachine):

        def drawUI(...):
            if condition_to_start_dealing:
                self.add_generator('shuffle-cards', self.shuffle_cards())

        def shuffle_cards(self):
            ... code to show shuffling of cards (runs over many frames, yielding as needed) ...
            self.add_generator('deal-cards', self.deal_cards())

        def deal_cards(self):
            ... code to move cards from deck to table (like move_card above) ...
            self.add_generator('turn-cards', self.turn_cards)

        def turn_cards(self):
            for card in self.cards:
                card.turn_over()
                yield 1000

            ... add_generator for the next step in the process ...


You states can easily wait for conditions, eg if you detect a click on a card by
setting a property "card_selected" on the state.


    def wait_for_card_selection(self):
        while self.card_selected is None:
            yield # We will wait in this state until a card is selected
        if self.card_selected in deck:
            self.add_generator('move-from-deck', self.move_card_from_deck(self.card_selected)
        else:
            self.add_generator('move-from-hand', self.move_card_from_hand(self.card_selected)


"""

import pygame

from data.components import loggable
import data.state


class NotFound(Exception):
    """Generator was not found"""


class StateExecutor(loggable.Loggable):
    """Executes a generator through a sequence with delays"""

    def __init__(self, name, generator, delay=0):
        """Initialise the executor"""
        self.addLogger()
        self.name = name
        self.generator = generator
        self.last_delay = self.delay = delay
        self.done = False
        self.verbose = False
        self.paused = False
        #
        self.state_clock = pygame.time.Clock()

    def update(self, dt):
        """Update the state"""
        self.state_clock.tick(dt)
        if not self.paused:
            self.delay -= self.state_clock.get_time()
            if not self.done and self.delay < 0:
                if self.verbose:
                    self.log.debug('{0} {1} doing action'.format(self.name, id(self)))
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

    def get_fraction_to_go(self):
        """Return the fraction of our time to go"""
        if self.last_delay == 0:
            return 1
        else:
            return max(0, min(1, self.delay / self.last_delay))


class StateMachine(data.state.State, loggable.Loggable):
    """A state machine to use for handling the screen"""

    verbose = True

    def __init__(self):
        """Initialise the machine"""
        super(StateMachine, self).__init__()
        #
        self.addLogger()
        self.generators = []
        self.state_clock = pygame.time.Clock()
        self.delay = 0.0
        self.verbose = True
        #
        self.initUI()
        self.dt = 0

    def initUI(self):
        """Initialise the user interface"""
        raise NotImplementedError('Need to implement initUI')

    def drawUI(self, surface, scale):
        """Draw the user interface"""
        raise NotImplementedError('Need to implement drawUI')

    def update(self, surface, keys, now, dt, scale):
        """Update the game state"""
        self.dt = dt
        self.state_clock.tick(dt)
        self.delay -= self.state_clock.get_time()
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
        new_generator = StateExecutor(name, generator)
        self.log.debug('Adding new executor {0}, {1}'.format(name, id(new_generator)))
        self.generators.append(new_generator)
        return new_generator

    def stop_generator(self, name):
        """Stop a generator with a specific name"""
        for generator in self.generators[:]:
            if generator.name == name:
                self.generators.remove(generator)
                self.log.debug('Removing executor {0}, {1}'.format(name, id(generator)))
                break
        else:
            raise NotFound('A generator named {0} was not found'.format(name))
