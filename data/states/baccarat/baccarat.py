"""
todo:
exchange chips
add cards when deck is low
clicking stacks
lose bet amount if bailing
"""

from collections import OrderedDict
from random import choice
from itertools import chain
from functools import partial
import pygame as pg
from .ui import *
from . import layout
from ... import tools, prepare
from ...components.animation import Task, Animation
from ...components.angles import get_midpoint
import json
import os
import math
from pygame.compat import *


__all__ = ['Baccarat']

font_size = 64


def count_card(value):
    return 0 if value > 9 else value


def count_deck(deck):
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
    return count_deck(deck) >= 8 and len(deck) == 2


def points_message(value):
    return '{} point' if value == 1 else '{} points'


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
            stats = self.initialize_stats()
        self.casino_player.stats['baccarat'] = stats
        self.stats = stats

        # declared here to appease pycharm's syntax checking.
        # will be filled in when configuration is loaded
        self.betting_areas = dict()
        self.dealer_hand = None
        self.player_hand = None
        self.player_chips = None
        self.house_chips = None
        self.shoe = None

        names = ["cardshove{}".format(x) for x in (1, 3, 4)]
        self.shove_sounds = [prepare.SFX[name] for name in names]
        names = ["cardplace{}".format(x) for x in (2, 3, 4)]
        self.deal_sounds = [prepare.SFX[name] for name in names]
        names = ["chipsstack{}".format(x) for x in (3, 5, 6)]
        self.chip_sounds = [prepare.SFX[name] for name in names]

        self._background = None
        self._clicked_sprite = None
        self.font = pg.font.Font(prepare.FONTS["Saniretro"], 64)
        self.large_font = pg.font.Font(prepare.FONTS["Saniretro"], 120)
        self.button_font = pg.font.Font(prepare.FONTS["Saniretro"], 48)
        self.bets = list()
        self.groups = list()
        self.animations = pg.sprite.Group()
        self.hud = pg.sprite.RenderUpdates()
        self.hud.add(NeonButton('lobby', (540, 938, 0, 0), self.goto_lobby))
        self.groups.append(self.hud)
        self.reload_config()
        self.cash_in()
        self.new_round()

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
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
        return stats

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
        self.player_chips.get_event(event, scale)

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
            if event.button == 1:
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

    def deal_card(self, hand):
        """Shortcut to draw card from shoe and add to a hand

        :param hand: Deck instance
        :return: Card instance, Animation instance
        """
        def flip(card):
            fx = card.rect.centerx - card.rect.width
            ani0 = Animation(rotation=0, duration=350, transition='out_quint')
            ani0.start(card)
            ani1 = Animation(centerx=fx, duration=340, transition='out_quint')
            ani1.start(card.rect)
            self.animations.add(ani0, ani1)

        sound = choice(self.deal_sounds)
        sound.set_volume(1)
        self.delay(100, sound.play)

        sound = choice(self.shove_sounds)
        sound.set_volume(.20)
        sound.play()

        card = self.shoe.pop()
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

        if self.options['dealt_face_up']:
            card.face_up = False
            ani.callback = partial(flip, card)
        self.animations.add(ani)
        return card, ani

    def place_bet(self, result, owner, amount):
        """Shortcut to place a bet

        :param result: "player", "dealer", or "tie"
        :param owner: ChipsPile instance
        :param amount: amount to wager in cash (not chips)
        :return: ChipsPile instance
        """
        choice(self.chip_sounds).play()
        bet = ChipPile((600, 800, 200, 200))
        bet.add(owner.withdraw_chips(amount))
        bet.owner = owner
        bet.result = result
        self.bets.append(bet)
        return bet

    def new_round(self):
        """Start new round of baccarat.

        Also:
              forcibly clears card hands in case animations bugged out
              refills the house's chip rack
        """
        def force_empty():
            self.player_hand.empty()
            self.dealer_hand.empty()
            self.show_bet_confirm_button()

        self.bets = list()
        self.house_chips.fill()
        self.clear_table()
        self.delay(500, force_empty)

    def deal_cards(self):
        self.stats['Hands Dealt'] += 1
        self.delay(0, self.deal_card, (self.player_hand,))
        self.delay(700, self.deal_card, (self.player_hand,))
        self.delay(2000, self.deal_card, (self.dealer_hand,))
        task = self.delay(2700, self.deal_card, (self.dealer_hand,))
        task.chain(Task(self.count_naturals))

    def count_naturals(self):
        if natural(self.player_hand):
            self.stats['Player Naturals'] += 1
            self.delay(800, self.final_count_hands)
        elif natural(self.dealer_hand):
            self.stats['Dealer Naturals'] += 1
            self.delay(800, self.final_count_hands)
        else:
            self.count_player_hand()

    def count_player_hand(self):
        player_count = count_deck(self.player_hand)
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
        dealer_count = count_deck(self.dealer_hand)
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
        self.delay(800, self.final_count_hands)

    def final_count_hands(self):
        player_result = count_deck(self.player_hand)
        dealer_result = count_deck(self.dealer_hand)
        stats = self.stats

        if player_result > dealer_result:
            winner = self.player_hand
            stats['Player Wins'] += 1

        elif player_result < dealer_result:
            winner = self.dealer_hand
            stats['Dealer Wins'] += 1

        else:
            winner = None
            stats['Tie Result'] += 1

        for bet in self.bets:
            self.process_bet(bet, winner)

        self.display_scores()
        self.show_winner_text(winner)
        self.show_finish_round_button()

    def show_winner_text(self, winner):
        """Display a label under the winning hand
        """
        if winner is None:
            status_text = "Tie"
            midtop = get_midpoint(self.player_hand.bounding_rect.midbottom,
                                  self.dealer_hand.bounding_rect.midbottom)
        else:
            status_text = "Dealer" if winner is self.dealer_hand else "Player"
            status_text += " Wins"
            midtop = winner.bounding_rect.midbottom

        text = OutlineTextSprite(status_text, self.large_font)
        text.rect.midtop = midtop
        text.rect.y += 170
        text.kill_me_on_clear = True
        self.hud.add(text)

    def process_bet(self, bet, winner):
        """Calculate winnings for the bet, apply the winnings, and clear it

        :param bet: ChipsPile instance
        :param winner: Deck instance
        :return: None
        """
        player_natural = natural(self.player_hand)
        dealer_natural = natural(self.dealer_hand)
        is_player = bet.owner is self.player_chips
        stats = self.stats

        if bet.result is winner:
            winnings = bet.value

            if winner is None:   # Tie
                winnings *= self.options['tie_payout']

            fee = 0
            commission = self.options['commission']
            if winner is self.dealer_hand and commission:
                fee = int(math.ceil(bet.value * commission))
                winnings -= fee

            bet.owner.add(cash_to_chips(winnings))
            bet.owner.add(bet.sprites())

            if is_player:
                pn_win = winner is self.player_hand and player_natural
                bn_win = winner is self.dealer_hand and dealer_natural
                record = stats['Largest Win']
                stats['Largest Win'] = max(record, winnings)
                stats['Earned'] += winnings
                stats['Paid in Commission'] += fee
                if winner is None:
                    stats['Bets Tied'] += 1
                else:
                    stats['Bets Won'] += 1
                if pn_win or bn_win:
                    stats['Bets Won by Naturals'] += 1

        elif is_player:
            pn_loss = bet.result is self.player_hand and dealer_natural
            bn_loss = bet.result is self.dealer_hand and player_natural
            record = stats['Largest Loss']
            stats['Largest Loss'] = max(record, bet.value)
            stats['Bets Lost'] += 1
            stats['Earned'] -= bet.value
            if pn_loss or bn_loss:
                stats['Bets Lost by Naturals'] += 1

        bet.empty()

    def display_scores(self):
        """Create and add TextSprites with score under each card hand
        """
        player_result = count_deck(self.player_hand)
        dealer_result = count_deck(self.dealer_hand)

        msg = points_message(player_result)
        text = TextSprite(msg.format(player_result), self.font)
        text.rect.midtop = self.player_hand.bounding_rect.midbottom
        text.rect.y += 35
        text.kill_me_on_clear = True
        self.hud.add(text)

        msg = points_message(dealer_result)
        text = TextSprite(msg.format(dealer_result), self.font)
        text.rect.midtop = self.dealer_hand.bounding_rect.midbottom
        text.rect.y += 35
        text.kill_me_on_clear = True
        self.hud.add(text)

    def clear_table(self):
        """Remove all cards from the table.  Animated.
        """
        def clear_card(card):
            sound = choice(self.deal_sounds)
            sound.set_volume(.6)
            sound.play()
            fx, fy = card.rect.move(-1400, -200).topleft
            ani0 = Animation(x=fx, y=fy, duration=400,
                             transition='in_out_quint', round_values=True)
            ani0.callback = card.kill
            ani0.start(card.rect)
            ani1 = Animation(rotation=180, duration=400, transition='out_quart')
            ani1.start(card)
            self.animations.add(ani0, ani1)

        def play_shove_sound():
            self.shove_sounds[0].set_volume(1)
            self.shove_sounds[0].play()

        self.delay(20, play_shove_sound)

        cards = list(chain(self.player_hand, self.dealer_hand))
        for i, card in enumerate(reversed(cards)):
            self.delay(i * 115, clear_card, (card,))

        for sprite in self.hud.sprites():
            if hasattr(sprite, 'kill_me_on_clear'):
                sprite.kill()

    def goto_lobby(self, *args):
        self.cash_out()
        self.done = True
        self.next = 'LOBBYSCREEN'

    def cash_in(self):
        """Change player's cash to chips
        """
        chips = cash_to_chips(self.casino_player.stats['cash'])
        self.casino_player.stats['cash'] = 0
        self.player_chips.add(chips)

    def cash_out(self):
        """Change player's chips to cash.  Includes any bets on table.
        """
        cash = self.player_chips.value
        for bet in list(self.bets):
            if bet.owner == self.player_chips:
                self.bets.remove(bet)
                cash += bet.value
                bet.kill()
        self.casino_player.stats['cash'] = cash
        self.player_chips.empty()

    def show_deal_player_third_card_buttons(self):
        """Give the player option to draw third card or not

        Some game rules allow this option, while others will force
        the player to draw card based on a rule.
        """
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
        rect.topright = self.player_hand.moudning_rect.midbottom
        rect.move_ip(50, -24)
        b0 = Button(text, rect, f0)

        text = TextSprite('Decline', self.button_font)
        rect = pg.Rect(text.rect).inflate(48, 48)
        rect.topleft = self.player_hand.bounding_rect.midbottom
        rect.move_ip(50, 24)
        b1 = Button(text, rect, f1)
        self.hud.add(b0, b1)

    def show_finish_round_button(self):
        def f(sprite):
            sprite.kill()
            self.new_round()

        text = TextSprite('Again?', self.button_font)
        rect = pg.Rect(0, 0, 300, 75)
        rect.center = self.player_chips.rect.move(0, 75).midbottom
        self.hud.add(Button(text, rect, f))

    def show_bet_confirm_button(self):
        def f(sprite):
            sprite.kill()
            self.deal_cards()

        text = TextSprite('Confirm Bet', self.button_font)
        rect = pg.Rect(0, 0, 300, 75)
        rect.center = self.player_chips.rect.move(0, 75).midbottom
        self.hud.add(Button(text, rect, f))

    def render_background(self, size):
        """Render the background

        :param size: (width, height) in pixels
        :return: pygame.surface.Surface
        """
        background = pg.Surface(size)
        background.fill(prepare.FELT_GREEN)
        if hasattr(self, 'background_filename'):
            im = prepare.GFX[self.background_filename]
            background.blit(im, (0, 0))
        label = TextSprite('', self.font, bg=prepare.FELT_GREEN)
        for name, rect in self.betting_areas.items():
            label.text = name
            label.rect.center = rect.center
            image = label.draw()
            image.set_alpha(128)
            background.blit(image, label.rect)
        return background

    def update(self, surface, keys, current_time, dt, scale):
        if self._background is None:
            image = self.render_background(surface.get_size())
            surface.blit(image, (0, 0))
            self._background = image

        self.animations.update(dt)
        for group in chain(self.bets, self.groups):
            group.update(dt)
            group.clear(surface, self._background)
            group.draw(surface)
