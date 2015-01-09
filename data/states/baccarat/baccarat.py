from collections import OrderedDict
import pygame as pg
from ... import tools, prepare
from ...components.labels import NeonButton
from ...prepare import BROADCASTER as B
from . import layout
from .ui import *
import fysom
import json
import os
from pygame.compat import *


__all__ = ['Baccarat']

font_size = 64


def count_hand(deck):
    value = 0
    for card in deck.sprites():
        if card.value > 9:
            continue
        value += card.value
    if value > 9:
        value -= 10
    return value


class Baccarat(tools._State):
    """Baccarat game.  rules are configured in baccarat.json

    Rules were compiled by quick study on the Internet.  As expected, there is
    a considerable amount of variation on the stated rules, so artistic license
    was taken in determining what the rules should be.
    """

    # hack related to game states that do not finish
    did_startup = False

    def startup(self, now, persistent):
        self.now = now
        self.persist = persistent
        self.casino_player = self.persist['casino_player']
        self.variation = "mini"
        self.load_json(os.path.join('resources', 'baccarat-rules.json'))
        self.players = list()

        # stuff that might get moved to a gui layer sometime?
        self._background = None
        self._clicked_sprite = None
        self.font = pg.font.Font(prepare.FONTS["Saniretro"], font_size)
        self.button_font = pg.font.Font(prepare.FONTS["Saniretro"], 48)

        # hack related to game states that do not finish
        self.done = False
        if self.did_startup:
            return
        self.did_startup = True

        self.hud = pg.sprite.RenderUpdates()
        self.shoe = Deck((0, 0, 800, 600), decks=7, stacking=(0, 0))
        self.groups = [self.hud, self.shoe]

        self.bets = list()

        b = NeonButton('lobby', (1000, 920, 0, 0), self.goto_lobby)
        self.hud.add(b)

        # filename = os.path.join('resources', 'baccarat-layout.json')
        # layout.load_layout(self, filename)
        self.player_hand = Deck((150, 150, 200, 200), stacking=(12, 200))
        self.dealer_hand = Deck((750, 150, 200, 200), stacking=(12, 200))
        self.groups.extend((self.player_hand, self.dealer_hand))
        self.player_chips = ChipPile((0, 800, 200, 200), value=1000)
        self.groups.append(self.player_chips)
        self.on_new_round()

    def load_json(self, filename):
        return

        with open(filename) as fp:
            data = json.load(fp)

        config = data['baccarat'][self.variation]
        self.options = dict(config['options'])
        self.fsm = fysom.Fysom(**config['rules'])

    def goto_lobby(self):
        self.cash_out()
        self.done = True
        self.next = 'LOBBYSCREEN'

    def cash_out(self):
        self.casino_player.stats['cash'] = self.player_chips.get_chip_total()
        self.player_chips.empty()

    def cleanup(self):
        return self.persist

    def get_event(self, event, scale=(1, 1)):
        # hack allows game to play before title
        if not self.did_startup:
            d = {'casino_player': None}
            self.startup(0, d)
            return

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.goto_lobby()
                return

        elif event.type == pg.KEYUP:
            pass

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

            for sprite in reversed(self.shoe.sprites()):
                if sprite.rect.collidepoint(pos):
                    self.on_clicked_shoe_card(sprite, pos)
                    break

        elif event.type == pg.MOUSEBUTTONUP:
            pos = tools.scaled_mouse_pos(scale)
            sprite = self._clicked_sprite
            if sprite is not None:
                if sprite.rect.collidepoint(pos):
                    sprite.pressed = False
                    sprite.on_mouse_click(pos)
                self._clicked_sprite = None

    def place_bet(self, position, owner, amount):
        bet = ChipPile((300, 800, 200, 200))
        chips = owner.withdraw_chips(amount)
        bet.add(*chips)
        bet.owner = owner
        bet.bet = position
        self.bets.append(bet)

    def deal_cards(self):
        for card in self.shoe.draw_cards(2):
            card.face_up = True
            self.player_hand.add(card)

        for card in self.shoe.draw_cards(2):
            card.face_up = True
            self.dealer_hand.add(card)

        self.count_hands()

    def count_hands(self):
        player_result = count_hand(self.player_hand)
        dealer_result = count_hand(self.dealer_hand)

        if player_result > dealer_result:
            status_text = "Player Wins"
            result = "player"
        elif player_result < dealer_result:
            status_text = "Dealer Wins"
            result = "dealer"
        else:
            status_text = "Tie"
            result = "tie"

        for bet in self.bets:
            if bet.bet == result:
                chips = cash_to_chips(bet.value)
                bet.owner.add(*chips)
                bet.owner.add(*bet.sprites())

        self.clear_bets()

        msg = '{} points'
        text = TextSprite(msg.format(player_result), self.font)
        text.rect = self.player_hand.rect.move(0, 250)
        text.kill_me_on_clear = True
        self.hud.add(text)

        text = TextSprite(msg.format(dealer_result), self.font)
        text.rect = self.dealer_hand.rect.move(0, 250)
        text.kill_me_on_clear = True
        self.hud.add(text)

        text = TextSprite(status_text, self.font)
        text.rect = self.player_hand.rect.move(0, 400)
        text.kill_me_on_clear = True
        self.hud.add(text)

        self.show_finish_round_button()

    def on_clicked_shoe_card(self, card, pos):
        pass

    def on_confirm_bet(self):
        self.deal_cards()

    def on_new_round(self):
        self.bets = list()
        self.clear_table()
        self.show_bet_confirm_button()

    def clear_bets(self):
        for group in self.bets:
            group.empty()

    def clear_table(self):
        self.player_hand.empty()
        self.dealer_hand.empty()
        for sprite in self.hud.sprites():
            if hasattr(sprite, 'kill_me_on_clear'):
                sprite.kill()

    def show_finish_round_button(self):
        def f(sprite):
            sprite.kill()
            self.on_new_round()

        text = TextSprite('Again?', self.button_font)
        rect = 960, 800, 250, 75
        b = Button(text, rect, f)
        self.hud.add(b)

    def show_bet_confirm_button(self):
        def f(sprite):
            sprite.kill()
            self.on_confirm_bet()

        self.place_bet("player", self.player_chips, 100)

        text = TextSprite('Confirm?', self.button_font)
        rect = 960, 800, 250, 75
        b = Button(text, rect, f)
        self.hud.add(b)

    def update(self, surface, keys, current_time, dt, scale):
        if self._background is None:
            self._background = pg.Surface(surface.get_size())
            self._background.fill(prepare.FELT_GREEN)
            surface.blit(self._background, (0, 0))

        for group in self.bets:
            group.update(dt)
            group.clear(surface, self._background)
            group.draw(surface)

        for group in self.groups:
            group.update(dt)
            group.clear(surface, self._background)
            group.draw(surface)
