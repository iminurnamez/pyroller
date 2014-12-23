import time
import sys
import pygame as pg
from collections import OrderedDict

from ... import tools, prepare
from ...components.labels import Button
from ...prepare import BROADCASTER as B

from . import statemachine
from . import states
from . import utils
from . import playercard
from . import dealercard
from . import patterns
from . import ballmachine
from . import events
from .settings import SETTINGS as S


class Bingo(statemachine.StateMachine):
    """State to represent a bing game"""

    def __init__(self):
        """Initialise the bingo game"""
        #
        self.verbose = False
        self.sound_muted = False
        #
        self.font = prepare.FONTS["Saniretro"]
        font_size = 64
        b_width = 360
        b_height = 90
        #
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.music_icon = prepare.GFX["speaker"]
        topright = (self.screen_rect.right - 10, self.screen_rect.top + 10)
        self.music_icon_rect = self.music_icon.get_rect(topright=topright)
        self.mute_icon = prepare.GFX["mute"]
        self.play_music = True
        self.auto_pick = S['debug-auto-pick']
        #
        lobby_label = utils.getLabel('button', (0, 0), 'Lobby')
        self.lobby_button = Button(20, self.screen_rect.bottom - (b_height + 15),
                                   b_width, b_height, lobby_label)
        #
        self.cards = playercard.PlayerCardCollection(
            'player-card',
            S['player-cards-position'],
            S['player-card-offsets'],
            self
        )
        self.dealer_cards = dealercard.DealerCardCollection(
            'dealer-card',
            S['dealer-cards-position'],
            S['dealer-card-offsets'],
            self
        )
        #
        self.ui = utils.ClickableGroup(self.cards)
        #
        self.winning_pattern = patterns.PATTERNS[0]
        #
        self.pattern_buttons = utils.DrawableGroup()
        self.speed_buttons = utils.DrawableGroup()
        self.debug_buttons = utils.DrawableGroup()
        self.buttons = utils.DrawableGroup([self.pattern_buttons, self.speed_buttons])
        #
        if prepare.DEBUG:
            self.buttons.append(self.debug_buttons)
        #
        super(Bingo, self).__init__(states.S_INITIALISE)
        #
        self.ball_machine = ballmachine.BallMachine('ball-machine', self)
        self.ball_machine.start_machine()
        #
        self.all_cards = utils.DrawableGroup()
        self.all_cards.extend(self.cards)
        self.all_cards.extend(self.dealer_cards)
        #
        B.linkEvent(events.E_PLAYER_PICKED, self.player_picked)
        B.linkEvent(events.E_PLAYER_UNPICKED, self.player_unpicked)
        #
        self.current_pick_sound = 0
        self.last_pick_time = 0

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        #
        # Make sure the player has stat markers
        if 'Bingo' not in self.casino_player.stats:
            self.casino_player.stats['Bingo'] = OrderedDict([
                ('games played', 0),
                ('games won', 0),
                ])
        #
        self.casino_player.stats['Bingo']['games played'] += 1

    def get_event(self, event, scale=(1,1)):
        """Check for events"""
        super(Bingo, self).get_event(event, scale)
        if event.type == pg.QUIT:
            if prepare.ARGS['straight']:
                pg.quit()
                sys.exit()
            else:
                self.done = True
                self.next = "LOBBYSCREEN"
        elif event.type in (pg.MOUSEBUTTONDOWN, pg.MOUSEMOTION):
            #
            self.ui.process_events(event, scale)
            #
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.music_icon_rect.collidepoint(pos):
                    self.play_music = not self.play_music
                    if self.play_music:
                        pg.mixer.music.play(-1)
                    else:
                        pg.mixer.music.stop()
                elif self.lobby_button.rect.collidepoint(pos):
                    self.game_started = False
                    self.done = True
                    self.next = "LOBBYSCREEN"
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.done = True
                self.next = "LOBBYSCREEN"
            elif event.key == pg.K_SPACE:
                self.next_ball(None)
            elif event.key == pg.K_m:
                self.sound_muted = not self.sound_muted

    def drawUI(self, surface, scale):
        """Update the main surface once per frame"""
        surface.fill(S['table-color'])
        #
        self.lobby_button.draw(surface)
        self.all_cards.draw(surface)
        self.ball_machine.draw(surface)
        self.buttons.draw(surface)
        #
        if self.play_music:
            surface.blit(self.mute_icon, self.music_icon_rect)
        else:
            surface.blit(self.music_icon, self.music_icon_rect)

    def initUI(self):
        """Initialise the UI display"""
        #
        # Buttons that show the winning patterns
        for idx, pattern in enumerate(patterns.PATTERNS):
            self.pattern_buttons.append(utils.ImageOnOffButton(
                pattern.name, (200 + idx * 240, 400),
                'bingo-red-button', 'bingo-red-off-button', 'button',
                pattern.name,
                pattern == self.winning_pattern,
                self.change_pattern, pattern
            ))
        self.ui.extend(self.pattern_buttons)
        #
        # Buttons that show the speed
        for idx, (name, interval) in enumerate(S['machine-speeds']):
            self.speed_buttons.append(utils.ImageOnOffButton(
                name, (150 + idx * 130, 200),
                'bingo-blue-button', 'bingo-blue-off-button', 'small-button',
                name,
                interval == S['machine-interval'],
                self.change_speed, (idx, interval),
                scale=S['small-button-scale']
            ))
        self.ui.extend(self.speed_buttons)
        #
        # Simple generator to flash the potentially winning squares
        self.add_generator('potential-winners', self.flash_potential_winners())
        #
        # Debugging buttons
        if prepare.DEBUG:
            self.debug_buttons.append(utils.ImageOnOffButton(
                'auto-pick', S['debug-auto-pick-position'],
                'bingo-yellow-button', 'bingo-yellow-off-button', 'small-button',
                'Auto pick',
                S['debug-auto-pick'],
                self.toggle_auto_pick, None,
                scale=S['small-button-scale']
            ))
            #
            self.debug_buttons.append(utils.ImageButton(
                'restart', S['debug-restart-position'],
                'bingo-yellow-button', 'small-button',
                'Restart',
                self.restart_game, None,
                scale=S['small-button-scale']
            ))
            #
            self.debug_buttons.append(utils.ImageButton(
                'next-ball', S['debug-next-ball-position'],
                'bingo-yellow-button', 'small-button',
                'Next Ball',
                self.next_ball, None,
                scale=S['small-button-scale']
            ))
            self.ui.extend(self.debug_buttons)

    def change_pattern(self, pattern):
        """Change the winning pattern"""
        self.log.info('Changing pattern to {0}'.format(pattern.name))
        self.winning_pattern = pattern
        self.highlight_patterns(self.winning_pattern, one_shot=True)
        #
        # Clear all flashing squares
        for card in self.all_cards:
            card.potential_winning_squares = []
            for square in card.squares.values():
                square.is_focused = False
        #
        # Update UI
        for button in self.pattern_buttons:
            button.state = (button.arg == self.winning_pattern)

    def change_speed(self, arg):
        """Change the speed of the ball machine"""
        selected_idx, interval = arg
        self.log.info('Changing machine speed to {0}'.format(interval))
        for idx, button in enumerate(self.speed_buttons):
            button.state = idx == selected_idx
        #
        self.ball_machine.reset_timer(interval * 1000)

    def toggle_auto_pick(self, arg):
        """Toggle whether we are auto-picking numbers"""
        self.log.debug('Toggling auto-pick')
        self.auto_pick = not self.auto_pick
        self.debug_buttons[0].state = self.auto_pick

    def restart_game(self, arg):
        """Restart the game"""
        self.log.info('Restart game')
        self.ball_machine.reset_machine(self.ball_machine.interval)
        self.cards.reset()
        self.dealer_cards.reset()
        self.current_pick_sound = 0
        self.last_pick_time = 0

    def next_ball(self, arg):
        """Move on to the next ball"""
        self.ball_machine.call_next_ball()

    def highlight_patterns(self, pattern, one_shot):
        """Test method to cycle through the winning patterns"""
        for card in self.cards:
            self.add_generator(
                'highlight-patterns-card-%s' % card.name,
                self.highlight_pattern(card, pattern, one_shot)
            )

    def highlight_pattern(self, card, pattern, one_shot):
        """Highlight a particular pattern on a card"""
        for squares in pattern.get_matches(card):
            for square in squares:
                square.is_highlighted = True
            yield 100
            for square in squares:
                square.is_highlighted = False
            yield 10
        #
        if not one_shot:
            self.add_generator('highlight', self.highlight_pattern(card, pattern, one_shot=False))

    def initialise(self):
        """Start the game state"""
        yield 0
        self.add_generator('main-game-loop', self.main_game_loop())

    def main_game_loop(self):
        """The main game loop"""
        while True:
            yield 0

    def ball_picked(self, ball):
        """A ball was picked"""
        #
        # If auto-picking then update the cards
        auto_pick_cards = list(self.dealer_cards)
        if self.auto_pick:
            auto_pick_cards.extend(self.cards)
        for card in auto_pick_cards:
            card.call_square(ball.number)
        #
        # Highlight the card labels
        for card in self.all_cards:
            card.highlight_column(ball.letter)

    def player_picked(self, square, arg):
        """The player picked a square"""
        if not square.card.is_active:
            return
        #
        # Check to see if we created a new potentially winning square
        called_squares = list(square.card.called_squares)
        prior_called_squares = list(called_squares)
        prior_called_squares.remove(square.text)
        #
        _, winners = self.winning_pattern.get_number_to_go_and_winners(square.card, called_squares)
        _, prior_winners = self.winning_pattern.get_number_to_go_and_winners(square.card, prior_called_squares)
        self.log.debug('{0} / {1}'.format(winners, prior_winners))
        #
        if len(winners) > len(prior_winners):
            self.play_sound('bingo-potential-winner')
        #
        # Increment sound if we did this quickly
        if time.time() - self.last_pick_time < S['player-pick-interval']:
            self.current_pick_sound = min(self.current_pick_sound + 1, len(S['player-pick-sounds']) - 1)
        else:
            self.current_pick_sound = 0
        self.last_pick_time = time.time()
        self.play_sound(S['player-pick-sounds'][self.current_pick_sound])
        #
        self.log.info('Player picked {0}'.format(square))

    def player_unpicked(self, square, arg):
        """The player unpicked a square"""
        self.log.info('Player unpicked {0}'.format(square))
        self.play_sound('bingo-unpick')

    def flash_potential_winners(self):
        """Flash the squares that are potential winners"""
        while True:
            for state, delay in S['card-focus-flash-timing']:
                for card in self.all_cards:
                    for square in card.potential_winning_squares:
                        square.is_focused = state
                yield delay * 1000

    def play_sound(self, name):
        """Play a named sound - respects the mute settings"""
        if not self.sound_muted:
            prepare.SFX[name].play()