from collections import OrderedDict
import pygame as pg
from ... import tools, prepare
from ...prepare import BROADCASTER as B
from .playfield import Playfield
from .ui import *

__all__ = ['Pachinko']

font_size = 64


class Pachinko(tools._State):
    """Pachinko game."""

    def startup(self, now, persistent):
        self.persist = persistent

        # TODO: next two lines must be removed before merge
        from ...components.casino_player import CasinoPlayer
        self.persist['casino_player'] = CasinoPlayer()

        self.casino_player = self.persist['casino_player']
        self.playfield = Playfield()
        self.hud = pg.sprite.RenderUpdates()

        font = pg.font.Font(prepare.FONTS["Saniretro"], font_size)
        self.tray_count = TextSprite('', font)
        self.tray_count.rect.topleft = 960, 0
        self.on_tray()
        self.hud.add(self.tray_count)

        t = TextSprite("Press F to add 25", font)
        t.rect.topleft = 960, 70
        self.hud.add(t)

        b = Button("Test", (1000, 140, 200, 100), None)
        self.hud.add(b)

        B.linkEvent('pachinko_jackpot', self.on_jackpot)
        B.linkEvent('pachinko_gutter', self.on_gutter)
        B.linkEvent('pachinko_tray', self.on_tray)

        if 'Pachinko' not in self.casino_player.stats:
            self.casino_player.stats['Pachinko'] = OrderedDict([
                ('games played', 0),
                ('total winnings', 0),
                ('earned', 0),
                ('jackpots', 0),
                ('gutters', 0),
                ])

        self.casino_player.stats['Pachinko']['games played'] += 1

    def on_jackpot(self, *args):
        self.casino_player.stats["Pachinko"]["jackpots"] += 1

    def on_gutter(self, *args):
        self.casino_player.stats["Pachinko"]["gutters"] += 1

    def on_tray(self, *args):
        self.tray_count.text = '{} balls in play'.format(self.playfield.ball_tray)

    def fill_tray(self):
        cost = 25
        if self.casino_player.stats['cash'] >= cost:
            self.casino_player.stats['cash'] -= cost
            self.playfield.ball_tray += cost
            self.on_tray()

    def cash_out(self):
        winnings = self.playfield.ball_tray
        self.playfield.ball_tray = 0
        self.casino_player.stats['Pachinko']['total winnings'] += winnings

    def cleanup(self):
        B.unlinkEvent('pachinko_jackpot', self.on_jackpot)
        B.unlinkEvent('pachinko_gutter', self.on_gutter)
        B.unlinkEvent('pachinko_tray', self.on_tray)
        self.cash_out()

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.playfield.depress_plunger()

            elif event.key == pg.K_f:
                self.fill_tray()

        elif event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                self.playfield.release_plunger()

    def update(self, surface, keys, current_time, dt, scale):
        self.playfield.update(surface, dt)
        self.hud.clear(surface, self._clear_surface)
        self.hud.draw(surface)

    @staticmethod
    def _clear_surface(surface, rect):
        surface.fill((0, 0, 0), rect)