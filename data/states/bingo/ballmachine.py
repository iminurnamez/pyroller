"""Represents the machine that picks numbers"""

import random

from ...components import common
from . import loggable
from .settings import SETTINGS as S


class Ball(object):
    """A ball representing a number in the game"""

    def __init__(self, number):
        """Initialise the ball"""
        self.number = number
        #
        # Get the name for this ball (eg B1, I20)
        number_lookup = S['card-numbers']
        for letter, col in zip('BINGO', sorted(number_lookup.keys())):
            numbers = number_lookup[col]
            if number in numbers:
                self.letter = letter
                self.col = col
                break
        else:
            raise ValueError('Could not locate details for {0}'.format(number))
        #
        self.full_name = '{0}{1}'.format(self.letter, self.number)


class BallMachine(common.Drawable, loggable.Loggable):
    """A machine to pick balls at random"""

    def __init__(self, name, state):
        """Initialise the machine"""
        self.addLogger()
        self.name = name
        self.state = state
        #
        self.all_balls = [Ball(n) for n in S['machine-balls']]
        self.balls = []
        self.called_balls = []
        self.speed_buttons = common.DrawableGroup()
        self.buttons = common.ClickableGroup()
        self.current_ball = None
        self.interval = self.initial_interval = S['machine-speeds'][0][1] * 1000
        self.running = False
        self.timer = None
        self.speed_transitions = {}
        #
        self.ui = self.create_ui()
        self.reset_machine()

    def create_ui(self):
        """Create the UI components"""
        components = common.DrawableGroup()
        #
        # The display of the current ball
        self.conveyor = common.DrawableGroup()
        components.append(self.conveyor)
        #
        # The display of all the balls that have been called
        self.called_balls_ui = CalledBallTray(S['called-balls-position'])
        components.append(self.called_balls_ui)
        #
        # Buttons that show the speed
        for idx, (name, interval, number_balls) in enumerate(S['machine-speeds']):
            self.speed_buttons.append(common.ImageOnOffButton(
                name,
                (150 + idx * 65, 300),
                'bingo-blue-button', 'bingo-blue-off-button', 'tiny-button',
                name,
                interval == self.initial_interval / 1000,
                S, scale=S['tiny-button-scale']
            ))
            self.speed_buttons[-1].linkEvent(common.E_MOUSE_CLICK, self.change_speed, (idx, interval))
            self.speed_transitions[number_balls] = (idx, interval)
        components.extend(self.speed_buttons)
        self.buttons.extend(self.speed_buttons)
        #
        return components

    def change_speed(self, obj,  arg):
        """Change the speed of the ball machine"""
        selected_idx, interval = arg
        self.log.info('Changing machine speed to {0}'.format(interval))
        #
        # Play appropriate sound
        if interval < self.interval / 1000:
            self.state.play_sound('bingo-speed-up')
        else:
            self.state.play_sound('bingo-slow-down')
        #
        # Set button visibility
        for idx, button in enumerate(self.speed_buttons):
            button.state = idx == selected_idx
        #
        # Set speed of the machine
        self.reset_timer(interval * 1000)

    def start_machine(self):
        """Start the machine"""
        self.running = True
        if self.timer:
            self.state.stop_generator('ball-machine')
        self.timer = self.state.add_generator('ball-machine', self.pick_balls())

    def stop_machine(self):
        """Stop the machine"""
        self.running = False

    def reset_timer(self, interval):
        """Reset the timer on the machine"""
        self.interval = interval
        self.timer.update_interval(interval)

    def reset_machine(self, interval=None):
        """Reset the machine"""
        self.balls = list(self.all_balls)
        self.called_balls = []
        random.shuffle(self.balls)
        self.called_balls_ui.reset_display()
        self.interval = interval if interval else self.initial_interval
        self.conveyor.clear()
        self.start_machine()

    def pick_balls(self):
        """Pick the balls"""
        for idx, ball in enumerate(self.balls):
            #
            # Under some circumstances we will restart this iterator so this
            # makes sure we don't repeat balls
            if ball.number in self.called_balls:
                continue
            #
            self.called_balls.append(ball.number)
            self.set_current_ball(ball)
            self.state.play_sound('bingo-ball-chosen')
            #
            # Watch for speed transition
            try:
                button_idx, new_interval = self.speed_transitions[idx]
            except KeyError:
                # No transition
                pass
            else:
                self.change_speed(None, (button_idx, new_interval))
            #
            # Wait for next ball
            yield self.interval

    def set_current_ball(self, ball):
        """Set the current ball"""
        self.log.info('Current ball is {0}'.format(ball.full_name))
        #
        self.current_ball = ball
        self.conveyor.append(
            SingleBallDisplay('ball', S['machine-ball-position'], ball)
        )
        self.state.ball_picked(ball)
        self.called_balls_ui.call_ball(ball)

    def draw(self, surface):
        """Draw the machine"""
        self.ui.draw(surface)
        self.called_balls_ui.update(S['conveyor-speed'] / self.interval)

    def call_next_ball(self):
        """Immediately call the next ball"""
        self.timer.next_step()


class CalledBallTray(common.Drawable, loggable.Loggable):
    """A display of the balls that have been called"""

    def __init__(self, position):
        """Initialise the display"""
        self.addLogger()
        self.x, self.y = position
        self.called_balls = []
        #
        self.conveyor = common.NamedSprite(
            'bingo-conveyor',
            S['conveyor-position'],
        )
        self.initial_x = S['conveyor-position'][0]
        self.current_x = 0

    def call_ball(self, ball):
        """Call a particular ball"""
        self.called_balls.append(ball)

    def draw(self, surface):
        """Draw the tray"""
        self.conveyor.draw(surface)

    def reset_display(self):
        """Reset the display of the balls"""
        self.called_balls = []

    def update(self, increment):
        """Update the display of the tray"""
        self.current_x += increment
        if self.current_x > S['conveyor-repeat']:
            self.current_x -= S['conveyor-repeat']
        self.conveyor.rect.x = self.initial_x + self.current_x


class SingleBallDisplay(common.Drawable, loggable.Loggable):
    """A ball displayed on the screen"""

    def __init__(self, name, position, ball):
        """Initialise the ball"""
        self.addLogger()
        #
        self.name = name
        #
        # Create the background chip
        self.background = common.NamedSprite.from_sprite_sheet(
            'chips', (2, 5),
            S['called-ball-sprite-lookup'][ball.col], position,
            scale=S['machine-ball-sprite-scale']
        )
        #
        # And the text for the number
        self.text = common.getLabel(
            'machine-ball',
            (self.background.rect.width / 2, self.background.rect.height / 2), str(ball.number), S
        )
        self.text.text_color = S['called-ball-font-color'][ball.col]
        self.text.update_text()
        #
        # Write the number on the background
        self.text.draw(self.background.sprite)
        #
        # And rotate a bit
        self.background.rotate_to(random.uniform(*S['machine-ball-angle-range']))

    def draw(self, surface):
        """Draw the ball"""
        self.background.draw(surface)