"""
todo:
exchange chips
add cards when deck is low
betting areas
clicking stacks
lose bet amount if bailing
sounds?
"""

from collections import OrderedDict
from random import choice
from itertools import chain
import pygame as pg
from ... import tools, prepare
from . import layout
from .ui import *
from ...components.animation import Task, Animation, AnimationTransition
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
    return divmod(sum(count_card(card.value) for card in deck), 10)[1]


def bankers_deal_rule(banker_count, last_player_card):
    value = last_player_card
    if value == 9:
        value = -1
    if value == 8:
        value = -2
    value = int(value / 2)
    if abs(value) - 1 == 0:
        value = 0
    value += 3
    return banker_count <= value


def players_deal_rule(count):
    return count < 6


def natural(deck):
    return count_card(deck) >= 8 and len(deck) == 2


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

        stats = self.casino_player.stats.get('baccarat', None)
        if stats is None:
            stats = OrderedDict([
                ('Hands Dealt', 0),
                ('Bets Won', 0),
                ('Bets Tied', 0),
                ('Bets Lost', 0),
                ('Bets Won by Naturals', 0),
                ('Bets Lost by Naturals', 0),
                ('Player Wins', 0),
                ('Player Naturals', 0),
                ('Dealer Wins', 0),
                ('Dealer Naturals', 0),
                ('Tie Result', 0),
                ('Largest Win', 0),
                ('Largest Loss', 0),
                ('Declined Third Card', 0),
                ('Earned', 0),
                ('Paid in Commission', 0)
            ])
            self.casino_player.stats['baccarat'] = stats
        self.stats = stats

        # declared here to appease pycharm's syntax checking
        # will be filled in when configuration is loaded
        self.dealer_hand = None
        self.player_hand = None
        self.player_chips = None
        self.shoe = None

        names = ["cardplace{}".format(x) for x in (2, 3, 4)]
        self.deal_sounds = [prepare.SFX[name] for name in names]
        names = ["chipsstack{}".format(x) for x in (3, 5, 6)]
        self.chip_sounds = [prepare.SFX[name] for name in names]

        self._background = None
        self._clicked_sprite = None
        self.font = pg.font.Font(prepare.FONTS["Saniretro"], font_size)
        self.button_font = pg.font.Font(prepare.FONTS["Saniretro"], 48)
        self.bets = list()
        self.groups = list()
        self.animations = pg.sprite.Group()
        self.hud = pg.sprite.RenderUpdates()
        self.hud.add(NeonButton('lobby', (1000, 920, 0, 0), self.goto_lobby))
        self.groups.append(self.hud)
        self.reload_config()
        self.cash_in()
        self.on_new_round()

    def cleanup(self):
        self.casino_player.stats['baccarat'] = self.stats
        return super(Baccarat, self).cleanup()

    def reload_config(self):
        """Read baccarat configuration, rules, and table layout
        """
        filename = os.path.join('resources', 'baccarat-rules.json')
        with open(filename) as fp:
            data = json.load(fp)
        config = data['baccarat'][self.variation]
        self.options = dict(config['options'])
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

    def delay(self, amount, callback, args=None, kwargs=None):
        """Convenience function to delay a function call

        :param amount: milliseconds to wait until callback is called
        :param callback: function to call
        :param args: arguments to pass to callback
        :param kwargs: keywords to pass to callback
        :return: Task instance
        """
        task = Task(callback, amount, 1, args, kwargs)
        self.animations.add(task)
        return task

    def on_new_round(self):
        self.bets = list()
        self.clear_table()
        self.show_bet_confirm_button()

    def deal_card(self, hand):
        """Shortcut to draw card from shoe and add to a hand

        :param hand: Deck instance
        :return: Card instance, Animation instance
        """
        choice(self.deal_sounds).play()
        card = self.shoe.pop()
        card.face_up = self.options['dealt_face_up']
        originals = {sprite: sprite.rect.topleft for sprite in hand.sprites()}
        originals[card] = card.rect.topleft
        hand.add(card)
        hand.arrange()
        fx, fy = card.rect.topleft
        for sprite in hand.sprites():
            sprite.rect.topleft = originals[sprite]
        ani = Animation(x=fx, y=fy, duration=400.,
                        transition='in_out_quint', round_values=True)
        ani.start(card.rect)
        self.animations.add(ani)
        return card, ani

    def place_bet(self, result, owner, amount):
        """Shortcut to place a bet

        :param result: "player", "dealer", or "tie"
        :param owner: ChipsPile instance
        :param amount: amount to wager
        :return: ChipsPile instance
        """
        choice(self.chip_sounds).play()
        bet = ChipPile((600, 800, 200, 200))
        bet.add(owner.withdraw_chips(amount))
        bet.owner = owner
        bet.result = result
        self.bets.append(bet)
        return bet

    def deal_cards(self):
        self.stats['Hands Dealt'] += 1
        self.delay(0, self.deal_card, (self.player_hand,))
        self.delay(200, self.deal_card, (self.player_hand,))
        self.delay(600, self.deal_card, (self.dealer_hand,))
        self.delay(800, self.deal_card, (self.dealer_hand,))
        self.delay(1000, self.count_naturals)

    def count_naturals(self):
        if natural(self.player_hand):
            self.stats['Player Naturals'] += 1
            self.final_count_hands()
        elif natural(self.dealer_hand):
            self.stats['Dealer Naturals'] += 1
            self.final_count_hands()
        else:
            self.count_player_hand()

    def count_player_hand(self):
        player_count = count_hand(self.player_hand)
        if players_deal_rule(player_count):
            if self.options['third_card_option']:
                self.show_deal_player_third_card_buttons()
            else:
                self.delay(500, self.deal_player_third_card)
        else:
            self.count_dealer_hand()

    def deal_player_third_card(self):
        self.deal_card(self.player_hand)
        self.count_dealer_hand()

    def count_dealer_hand(self):
        dealer_count = count_hand(self.dealer_hand)
        if len(self.player_hand) == 2:
            deal_again = players_deal_rule(dealer_count)
        else:
            value = count_card(self.player_hand.sprites()[-1].value)
            deal_again = bankers_deal_rule(dealer_count, value)

        if deal_again:
            self.delay(500, self.deal_dealer_third_card)
        else:
            self.delay(800, self.final_count_hands)

    def deal_dealer_third_card(self):
        self.deal_card(self.dealer_hand)
        self.delay(500, self.final_count_hands)

    def final_count_hands(self):
        stats = self.stats
        player_result = count_hand(self.player_hand)
        dealer_result = count_hand(self.dealer_hand)
        player_natural = natural(self.player_hand)
        dealer_natural = natural(self.dealer_hand)

        if player_result > dealer_result:
            stats['Player Wins'] += 1
            status_rect = self.player_hand.rect.move(0, 400)
            status_text = "Player Wins"
            result = "player"

        elif player_result < dealer_result:
            stats['Dealer Wins'] += 1
            status_rect = self.dealer_hand.rect.move(0, 400)
            status_text = "Dealer Wins"
            result = "dealer"

        else:
            stats['Tie Result'] += 1
            status_rect = self.player_hand.rect.move(0, 400)
            status_text = "Tie"
            result = "tie"

        for bet in self.bets:
            is_player = bet.owner is self.player_chips

            if bet.result == result:
                winnings = bet.value
                if result == 'tie':
                    winnings *= self.options['tie_payout']

                fee = 0
                commission = self.options['commission']
                if result == "dealer" and commission:
                    fee = int(math.ceil(bet.value * commission))
                    winnings -= fee

                bet.owner.add(cash_to_chips(winnings))
                bet.owner.add(bet.sprites())

                if is_player:
                    pn_win = result == 'player' and player_natural
                    bn_win = result == 'dealer' and dealer_natural
                    record = stats['Largest Win']
                    stats['Largest Win'] = max(record, winnings)
                    stats['Earned'] += winnings
                    stats['Paid in Commission'] += fee
                    if result == 'tie':
                        stats['Bets Tied'] += 1
                    else:
                        stats['Bets Won'] += 1
                    if pn_win or bn_win:
                        stats['Bets Won by Naturals'] += 1

            elif is_player:
                pn_loss = bet.result == 'player' and dealer_natural
                bn_loss = bet.result == 'dealer' and player_natural
                record = stats['Largest Loss']
                stats['Largest Loss'] = max(record, bet.value)
                stats['Bets Lost'] += 1
                stats['Earned'] -= bet.value
                if pn_loss or bn_loss:
                    stats['Bets Lost by Naturals'] += 1

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
        text.rect = status_rect
        text.kill_me_on_clear = True
        self.hud.add(text)

        self.show_finish_round_button()

    def clear_table(self):
        def clear(card):
            choice(self.deal_sounds).play()
            card.face_up = False
            fx, fy = card.rect.move(-1400, -200).topleft
            ani = Animation(x=fx, y=fy, duration=400,
                            transition='in_out_quint', round_values=True)
            ani.start(card.rect)
            self.animations.add(ani)

        self.delay(500, self.player_hand.empty)
        self.delay(500, self.dealer_hand.empty)
        cards = list(chain(self.player_hand, self.dealer_hand))
        for i, card in enumerate(reversed(cards)):
            self.delay(i * 100, clear, (card,))

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

    def show_deal_player_third_card_buttons(self):
        def f0(sprite):
            b0.kill()
            b1.kill()
            self.deal_player_third_card()

        def f1(sprite):
            self.stats['Declined Third Card'] += 1
            b0.kill()
            b1.kill()
            self.count_dealer_hand()

        text = TextSprite('Draw Again', self.button_font)
        rect = pg.Rect(text.rect).inflate(48, 48)
        rect.topright = self.player_hand.rect.midbottom
        rect.x -= 24
        b0 = Button(text, rect, f0)

        text = TextSprite('Decline', self.button_font)
        rect = pg.Rect(text.rect).inflate(48, 48)
        rect.topleft = self.player_hand.rect.midbottom
        rect.x += 24
        b1 = Button(text, rect, f1)
        self.hud.add(b0, b1)

    def show_finish_round_button(self):
        def f(sprite):
            sprite.kill()
            self.on_new_round()

        text = TextSprite('Again?', self.button_font)
        self.hud.add(Button(text, (960, 800, 300, 75), f))

    def show_bet_confirm_button(self):
        def f(sprite):
            sprite.kill()
            self.deal_cards()

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

        self.animations.update(dt)
        for group in chain(self.bets, self.groups):
            group.update(dt)
            group.clear(surface, self._background)
            group.draw(surface)
