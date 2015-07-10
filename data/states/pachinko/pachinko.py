from collections import OrderedDict

import pygame as pg

from data import tools, prepare
from data.prepare import BROADCASTER as B
import data.state
from .playfield import Playfield
from .ui import *

__all__ = ['Pachinko']

font_size = 64


class Pachinko(data.state.State):
    """Pachinko game."""
    show_in_lobby = True
    name = 'Pachinko'

    # hack related to game states that do not finish
    did_startup = False

    def startup(self, now, persistent):
        self.now = now
        self.persist = persistent

        # stuff that might get moved to a gui layer sometime?
        self._needs_clear = True
        self._clicked_sprite = None

        self._power = .5
        self._should_autoplay = False

        B.linkEvent('pachinko_jackpot', self.on_jackpot)
        B.linkEvent('pachinko_gutter', self.on_gutter)
        B.linkEvent('pachinko_tray', self.on_tray)

        # hack related to game states that do not finish
        try:
            self.on_tray()
        except:
            pass
        self.done = False
        try:
            self.playfield.background = None
        except AttributeError:
            pass

        # hack related to game states that do not finish
        if self.did_startup:
            return

        self.did_startup = True

        self.casino_player = self.persist['casino_player']
        self.casino_player.current_game = self.name

        self.playfield = Playfield()
        self.hud = pg.sprite.RenderUpdates()

        font = pg.font.Font(prepare.FONTS["Saniretro"], font_size)
        self.tray_count = TextSprite('', font)
        self.tray_count.rect.topleft = 960, 100
        self.hud.add(self.tray_count)
        self.on_tray()

        t = TextSprite("Press F to add 25", font)
        t.rect.topleft = 960, 170
        self.hud.add(t)

        t = TextSprite("Spacebar Shoots", font)
        t.rect.topleft = 960, 250
        self.hud.add(t)

        def lower_power():
            self.playfield.auto_power -= .01

        def raise_power():
            self.playfield.auto_power += .01

        font = pg.font.Font(prepare.FONTS["Saniretro"], 50)
        fg = pg.Color('gold2')
        text = TextSprite("- POWER", font, fg=fg)
        self.hud.add(Button(text, (1000, 370, 350, 80), lower_power))

        text = TextSprite("AUTO", font, fg=fg)
        self.auto_button = Button(text, (1000, 460, 350, 80),
                                  self.toggle_autoplay)
        self.hud.add(self.auto_button)

        text = TextSprite("+ POWER", font, fg=fg)
        self.hud.add(Button(text, (1000, 550, 350, 80), raise_power))

        b = NeonButton('lobby', (1000, 920, 0, 0), self.goto_lobby)
        self.hud.add(b)

        if 'Pachinko' not in self.casino_player.stats:
            self.casino_player.stats['Pachinko'] = OrderedDict([
                ('games played', 0),
                ('total winnings', 0),
                ('earned', 0),
                ('jackpots', 0),
                ('gutters', 0),
            ])

        self.casino_player.stats['Pachinko']['games played'] += 1

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([('games played', 0),
                            ('total winnings', 0),
                            ('earned', 0),
                            ('jackpots', 0),
                            ('gutters', 0),
                            ])
        return stats

    def goto_lobby(self):
        self.cash_out()
        self.done = True
        self.next = 'LOBBYSCREEN'

    def on_jackpot(self, *args):
        self.casino_player.stats["Pachinko"]["jackpots"] += 1

    def on_gutter(self, *args):
        self.casino_player.stats["Pachinko"]["gutters"] += 1

    def on_tray(self, *args):
        self.tray_count.text = '{} balls in play'.format(
            self.playfield.ball_tray)

    def fill_tray(self):
        cost = 25
        if self.casino_player.stats['cash'] >= cost:
            self.casino_player.stats['cash'] -= cost
            self.playfield.ball_tray += cost
            self.on_tray()

    def toggle_autoplay(self):
        self._should_autoplay = not self._should_autoplay
        self.playfield.auto_play = self._should_autoplay
        self.auto_button.pressed = self._should_autoplay

    def cash_out(self):
        winnings = self.playfield.ball_tray
        self.playfield.ball_tray = 0
        self.casino_player.stats['cash'] += winnings

    def cleanup(self):
        B.unlinkEvent('pachinko_jackpot', self.on_jackpot)
        B.unlinkEvent('pachinko_gutter', self.on_gutter)
        B.unlinkEvent('pachinko_tray', self.on_tray)
        return self.persist

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.goto_lobby()
                return

            if event.key == pg.K_SPACE:
                self.playfield.depress_plunger()

            elif event.key == pg.K_f:
                self.fill_tray()

            elif event.key == pg.K_a:
                self.toggle_autoplay()

        elif event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                self.playfield.release_plunger()

        if event.type == pg.MOUSEMOTION:
            pos = tools.scaled_mouse_pos(scale)
            sprite = self._clicked_sprite
            if sprite is not None:
                sprite.pressed = sprite.rect.collidepoint(pos)

            for sprite in self.hud.sprites():
                if hasattr(sprite, 'on_mouse_enter'):
                    if sprite.rect.collidepoint(pos):
                        sprite.on_mouse_enter(pos)

                elif hasattr(sprite, 'on_mouse_leave'):
                    if not sprite.rect.collidepoint(pos):
                        sprite.on_mouse_leave(pos)

        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale)
            for sprite in self.hud.sprites():
                if hasattr(sprite, 'on_mouse_click'):
                    if sprite.rect.collidepoint(pos):
                        sprite.pressed = True
                        self._clicked_sprite = sprite

        elif event.type == pg.MOUSEBUTTONUP:
            pos = tools.scaled_mouse_pos(scale)
            sprite = self._clicked_sprite
            if sprite is not None:
                if sprite.rect.collidepoint(pos):
                    sprite.pressed = False
                    sprite.on_mouse_click(pos)
                self._clicked_sprite = None

    def update(self, surface, keys, current_time, dt, scale):
        if self._needs_clear:
            surface.fill(prepare.BACKGROUND_BASE)
            self._needs_clear = False

        self.playfield.update(surface, dt)
        self.hud.clear(surface, self._clear_surface)
        self.hud.draw(surface)

    @staticmethod
    def _clear_surface(surface, rect):
        surface.fill((0, 0, 0), rect)
