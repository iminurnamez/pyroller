"""
todo:
exchange chips
add cards when deck is low
betting areas
clicking stacks
lose bet amount if bailing
sounds?
"""

from itertools import chain
import pygame as pg
from ... import tools, prepare
from . import layout
from .ui import *
import fysom
import json
import os
import math
from pygame.compat import *


__all__ = ['Baccarat']

font_size = 64


def count_card(value):
    if value > 9:
        return 0
    return value


def count_hand(deck):
    value = 0
    for card in deck:
        value += count_card(card.value)
        if value > 9:
            value -= 10
    return value


class Baccarat(tools._State):
    """Baccarat game.  rules are configured in baccarat.json

    Rules were compiled by quick study on the Internet.  As expected, there is
    a considerable amount of variation on the stated rules, so artistic license
    was taken in determining what the rules should be.
    """
    def startup(self, now, persistent):
        self.now = now
        self.persist = persistent
        self.casino_player = self.persist['casino_player']
        self.variation = "mini"

        # stuff that might get moved to a gui layer sometime?
        self._background = None
        self._clicked_sprite = None
        self.font = pg.font.Font(prepare.FONTS["Saniretro"], font_size)
        self.button_font = pg.font.Font(prepare.FONTS["Saniretro"], 48)
        self.bets = list()
        self.groups = list()
        self.hud = pg.sprite.RenderUpdates()
        self.groups.append(self.hud)
        self.reload_config()
        self.hud.add(NeonButton('lobby', (1000, 920, 0, 0), self.goto_lobby))
        self.cash_in()
        self.on_new_round()

    def reload_config(self):
        filename = os.path.join('resources', 'baccarat-rules.json')
        with open(filename) as fp:
            data = json.load(fp)
        config = data['baccarat'][self.variation]
        self.options = dict(config['options'])
        self.fsm = fysom.Fysom(**config['rules'])

        filename = os.path.join('resources', 'baccarat-layout.json')
        layout.load_layout(self, filename)

    def get_event(self, event, scale=(1, 1)):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.goto_lobby()
                return

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

    def on_new_round(self):
        self.bets = list()
        self.clear_table()
        self.show_bet_confirm_button()

    def draw_card(self, hand):
        """Shortcut to draw card from shoe and add to a hand

        :param hand: Deck instance
        :return: Card instance
        """
        card = self.shoe.pop()
        card.face_up = True
        hand.add(card)
        return card

    def place_bet(self, result, owner, amount):
        """Shortcut to place a bet

        :param result: "player", "dealer", or "tie"
        :param owner: ChipsPile instance
        :param amount: amount to wager
        :return: ChipsPile instance
        """
        bet = ChipPile((600, 800, 200, 200))
        chips = owner.withdraw_chips(amount)
        bet.add(chips)
        bet.owner = owner
        bet.result = result
        self.bets.append(bet)
        return bet

    def deal_cards(self):
        self.draw_card(self.player_hand)
        self.draw_card(self.player_hand)
        self.draw_card(self.dealer_hand)
        self.draw_card(self.dealer_hand)
        player_count = count_hand(self.player_hand)
        dealer_count = count_hand(self.dealer_hand)

        # natural
        if player_count >= 8 or dealer_count >= 8:
            self.count_hands()
            return

        # punto rules only
        self.players_three_rule(player_count, self.player_hand)
        if len(self.player_hand) == 2:
            self.players_three_rule(dealer_count, self.dealer_hand)
        else:
            self.bankers_three_rule(dealer_count)

        self.count_hands()

    def bankers_three_rule(self, banker_count):
        # TODO: needs testing
        value = count_card(self.player_hand.sprites()[-1].value)
        if value == 9:
            value = -1
        if value == 8:
            value = -2
        value = int(value / 2)
        if abs(value) - 1 == 0:
            value = 0
        value += 3
        if banker_count <= value:
            self.draw_card(self.dealer_hand)

    def players_three_rule(self, count, hand):
        if count < 6:
            self.draw_card(hand)

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
            if bet.result == result:
                commission = self.options.get('commission', 0.0)
                winnings = bet.value
                if result == "dealer" and commission:
                    fee = int(math.ceil(bet.value * commission))
                    winnings -= fee
                bet.owner.add(cash_to_chips(winnings))
                bet.owner.add(bet.sprites())
                bet.empty()

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

    def clear_table(self):
        self.player_hand.empty()
        self.dealer_hand.empty()
        for sprite in self.hud.sprites():
            if hasattr(sprite, 'kill_me_on_clear'):
                sprite.kill()

    def goto_lobby(self, *args):
        self.cash_out()
        self.done = True
        self.next = 'LOBBYSCREEN'

    def cash_in(self):
        chips = cash_to_chips(self.casino_player.stats['cash'])
        self.casino_player.stats['cash'] = 0
        self.player_chips.add(chips)

    def cash_out(self):
        cash = self.player_chips.value
        for bet in list(self.bets):
            if bet.owner == self.player_chips:
                self.bets.remove(bet)
                cash += bet.value

        self.casino_player.stats['cash'] = cash
        self.player_chips.empty()

    def show_finish_round_button(self):
        def f(sprite):
            sprite.kill()
            self.on_new_round()

        text = TextSprite('Again?', self.button_font)
        rect = 960, 800, 300, 75
        b = Button(text, rect, f)
        self.hud.add(b)

    def show_bet_confirm_button(self):
        def f(sprite):
            sprite.kill()
            self.deal_cards()

        # TODO: no automatic bet
        self.place_bet("dealer", self.player_chips, 100)

        text = TextSprite('Confirm Bet', self.button_font)
        self.hud.add(Button(text, (960, 800, 300, 75), f))

    def update(self, surface, keys, current_time, dt, scale):
        if self._background is None:
            self._background = pg.Surface(surface.get_size())
            self._background.fill(prepare.FELT_GREEN)
            if hasattr(self, 'background_filename'):
                im = prepare.GFX[self.background_filename]
                self._background.blit(im, (0, 0))
            surface.blit(self._background, (0, 0))

        for group in chain(self.bets, self.groups):
            group.update(dt)
            group.clear(surface, self._background)
            group.draw(surface)
