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
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self._needs_clear = True

        self.persist = persistent
        self.casino_player = self.persist['casino_player']
        self.playfield = Playfield()
        self.hud = pg.sprite.RenderUpdates()

        font = pg.font.Font(prepare.FONTS["Saniretro"], font_size)
        self.tray_count = TextSprite('', font)
        self.tray_count.rect.topleft = 960, 100
        self.on_tray()
        self.hud.add(self.tray_count)

        t = TextSprite("Press F to add 25", font)
        t.rect.topleft = 960, 170
        self.hud.add(t)

        b = Button("Test", (1000, 140, 200, 100), None)
        self.hud.add(b)

        b = NeonButton('lobby', (960, 250, 0, 0),
                       self.goto_lobby)
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

    def goto_lobby(self):
        self.cash_out()
        self.done = True
        self.next = 'LOBBYSCREEN'

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
        return self.persist

    def get_event(self, event, scale=(1, 1)):
        # this music stuff really needs to be moved to the core
        self.persist["music_handler"].get_event(event, scale)

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.playfield.depress_plunger()

            elif event.key == pg.K_f:
                self.fill_tray()

        elif event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                self.playfield.release_plunger()

        if event.type == pg.MOUSEMOTION:
            pos = tools.scaled_mouse_pos(scale)
            for sprite in self.hud.sprites():
                if hasattr(sprite, 'on_mouse_enter'):
                    if sprite.rect.collidepoint(pos):
                        sprite.on_mouse_enter(pos)

                elif hasattr(sprite, 'on_mouse_leave'):
                    if not sprite.rect.collidepoint(pos):
                        sprite.on_mouse_leave(pos)

        elif event.type == pg.MOUSEBUTTONUP:
            pos = tools.scaled_mouse_pos(scale)
            for sprite in self.hud.sprites():
                if hasattr(sprite, 'on_mouse_click'):
                    if sprite.rect.collidepoint(pos):
                        sprite.on_mouse_click(pos)

    def update(self, surface, keys, current_time, dt, scale):
        if self._needs_clear:
            surface.fill(prepare.BACKGROUND_BASE)
            self._needs_clear = False

        self.playfield.update(surface, dt)
        self.hud.clear(surface, self._clear_surface)
        self.hud.draw(surface)

        # this music stuff really needs to be moved to the core
        self.persist["music_handler"].update(scale)
        self.persist["music_handler"].draw(surface)

    @staticmethod
    def _clear_surface(surface, rect):
        surface.fill((0, 0, 0), rect)
