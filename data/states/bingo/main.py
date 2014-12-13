import pygame as pg
from collections import OrderedDict

from ... import tools, prepare
from ...components.labels import Button

from . import statemachine
from . import states
from . import utils
from . import bingocard
from . import patterns
from .settings import SETTINGS as S


class Bingo(statemachine.StateMachine):
    """State to represent a bing game"""

    def __init__(self):
        """Initialise the bingo game"""
        super(Bingo, self).__init__(states.S_INITIALISE)
        #
        self.verbose = False
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
        #
        lobby_label = utils.getLabel('button', (0, 0), 'Lobby')
        self.lobby_button = Button(20, self.screen_rect.bottom - (b_height + 15),
                                                 b_width, b_height, lobby_label)
        #
        self.cards = bingocard.CardCollection(
            'player-card',
            S['player-cards-position'],
            S['player-card-offsets']
        )

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
            else:
                self.done = True
                self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            #
            self.cards.process_events(event, scale)
            #
            pos = tools.scaled_mouse_pos(scale, event.pos)
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
        elif event.type == pg.MOUSEMOTION:
            self.cards.process_events(event, scale)
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.done = True
                self.next = "LOBBYSCREEN"

    def drawUI(self, surface, scale):
        """Update the main surface once per frame"""
        surface.fill(S['table-color'])
        #
        self.lobby_button.draw(surface)
        self.cards.draw(surface)
        #
        if self.play_music:
            surface.blit(self.mute_icon, self.music_icon_rect)
        else:
            surface.blit(self.music_icon, self.music_icon_rect)

    def initUI(self):
        """Initialise the UI display"""

    def initialise(self):
        """Initialise game"""
        patterns_to_show = [
            patterns.CornersPattern(),
            patterns.LinesPattern(),
            patterns.StampPattern(),
            patterns.CoverallPattern(),
        ]
        #
        for card, pattern in zip(self.cards, patterns_to_show):
            self.log.debug('Next pattern {0} - {1}'.format(card, pattern))
            for squares in pattern.get_matches(card):
                for square in squares:
                    square.is_highlighted = True
                yield 100
                for square in squares:
                    square.is_highlighted = False
                yield 10
