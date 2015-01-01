"""Represents the machine that picks numbers"""

import random

from . import utils
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


class BallMachine(utils.Drawable, loggable.Loggable):
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
        self.speed_buttons = utils.DrawableGroup()
        self.buttons = utils.ClickableGroup()
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
        components = utils.DrawableGroup()
        #
        # The display of the current ball
        self.current_ball_ui = utils.getLabel(
            'machine-ball',
            S['machine-ball-position'],
            '0'
        )
        components.append(self.current_ball_ui)
        #
        # The display of all the balls that have been called
        self.called_balls_ui = CalledBallTray(S['called-balls-position'])
        components.append(self.called_balls_ui)
        #
        # Buttons that show the speed
        for idx, (name, interval, number_balls) in enumerate(S['machine-speeds']):
            self.speed_buttons.append(utils.ImageOnOffButton(
                name,
                (150 + idx * 65, 200),
                'bingo-blue-button', 'bingo-blue-off-button', 'tiny-button',
                name,
                interval == self.initial_interval / 1000,
                self.change_speed, (idx, interval),
                scale=S['tiny-button-scale']
            ))
            self.speed_transitions[number_balls] = (idx, interval)
        components.extend(self.speed_buttons)
        self.buttons.extend(self.speed_buttons)
        #
        return components

    def change_speed(self, arg):
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
        self.current_ball_ui.set_text('-')
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
                self.change_speed((button_idx, new_interval))
            #
            # Wait for next ball
            yield self.interval

    def set_current_ball(self, ball):
        """Set the current ball"""
        self.log.info('Current ball is {0}'.format(ball.full_name))
        #
        self.current_ball = ball
        self.current_ball_ui.set_text(ball.full_name)
        self.state.ball_picked(ball)
        self.called_balls_ui.call_ball(ball)

    def draw(self, surface):
        """Draw the machine"""
        self.ui.draw(surface)

    def call_next_ball(self):
        """Immediately call the next ball"""
        self.timer.next_step()


class CalledBallTray(utils.Drawable, loggable.Loggable):
    """A display of the balls that have been called"""

    def __init__(self, position):
        """Initialise the display"""
        self.addLogger()
        self.x, self.y = position
        self.balls = utils.KeyedDrawableGroup()
        self.called_balls = []
        #
        w, h = S['called-balls-size']
        dx, dy = S['called-balls-offsets']
        #
        for number in S['machine-balls']:
            xi = (number - 1) % w
            yi = (number - 1) // w
            self.balls[number] = utils.getLabel(
                'called-ball-number', (self.x + xi * dx, self.y + yi * dy), number
            )

    def call_ball(self, ball):
        """Call a particular ball"""
        self.called_balls.append(ball)
        ball_colours = S['called-ball-font-colors']
        for colour, ball in zip(ball_colours, reversed(self.called_balls[-len(ball_colours):])):
            self.balls[ball.number].text_color = colour
            self.balls[ball.number].update_text()

    def draw(self, surface):
        """Draw the tray"""
        self.balls.draw(surface)

    def reset_display(self):
        """Reset the display of the balls"""
        for ball in self.balls.values():
            ball.text_color = S['called-ball-number-font-color']
            ball.update_text()
        self.called_balls = []