import json
import os
import math
from collections import OrderedDict, defaultdict
from random import choice
from itertools import chain
from functools import partial
import pygame as pg
from .ui import *
from .cards import *
from .chips import *
from .table import TableGame
from ... import tools, prepare
from ...components.animation import Task, Animation
from ...components.angles import get_midpoint
from ...prepare import BROADCASTER as B
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


class Baccarat(TableGame):
    """Baccarat game.  rules are configured in baccarat.json

    Rules were compiled by quick study on the Internet.  As expected, there is
    a considerable amount of variation on the stated rules, so artistic license
    was taken in determining what the rules should be.
    """
    name = 'baccarat'
    variation = "mini"

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

    def reload_config(self):
        """Read baccarat configuration, rules, and table layout
        """
        from . import layout
        filename = os.path.join('resources', 'baccarat-rules.json')
        with open(filename) as fp:
            data = json.load(fp)
        config = data['baccarat'][self.variation]
        self.options = dict(config['options'])
        filename = os.path.join('resources', 'baccarat-layout.json')
        layout.load_layout(self, filename)

        # set the hands.  needed since loading may have been out of order
        hands = {
            'player': self.player_hand,
            'dealer': self.dealer_hand,
            'tie': None
        }
        for name, area in self.betting_areas.items():
            area.hand = hands[area.name]

    def new_round(self):
        """Start new round of baccarat.

        Also:
              forcibly clears card hands in case animations bugged out
              refills the house's chip rack
        """
        def force_empty():
            self.player_hand.empty()
            self.dealer_hand.empty()

        self.dismiss_advisor()
        self._enable_chips = True
        self.clear_background()
        self.bets.empty()
        self.house_chips.normalize()
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

        player_total = 0
        for bet in self.bets.groups():
            earnings = self.process_bet(bet, winner)
            if bet.owner is self.player_chips:
                player_total += earnings

        # show advisor message
        if player_total > 0:
            message = 'You have won ${}'.format(player_total)
        elif player_total < 0:
            message = 'You have lost ${}'.format(abs(player_total))
        else:
            message = 'You have broke even'
        self.create_advisor_dialog(message, 0)

        # move cards down
        for card in chain(self.player_hand, self.dealer_hand):
            ani = Animation(y=250, duration=300,
                            round_values=True, transition='out_quint')
            ani.start(card.rect)
            self.animations.add(ani)

        self.delay(300, self.display_scores)

        self.show_winner_text(winner)
        self.show_finish_round_button()

    def build_image_cache(self):
        """certain surfaces/images are created here.
           saves generated files to game root
           this is just a utility function, not needed for normal play
        """
        def create_text_sprite(text):
            sprite = OutlineTextSprite(text, self.large_font)
            return sprite

        for text, filename in [('Player Wins', 'baccarat-player-wins.png'),
                               ('Dealer Wins', 'baccarat-dealer-wins.png'),
                               ('Tie', 'baccarat-tie.png')]:
            image = create_text_sprite(text)
            pg.image.save(image.image, filename)

    def show_winner_text(self, winner):
        """Display a label under the winning hand
        """
        if winner is None:
            image = prepare.GFX['baccarat-tie']
            midtop = get_midpoint(self.player_hand.bounding_rect.midbottom,
                                  self.dealer_hand.bounding_rect.midbottom)
        else:
            text = "dealer" if winner is self.dealer_hand else "player"
            image = prepare.GFX['baccarat-{}-wins'.format(text)]
            midtop = winner.bounding_rect.midbottom

        sprite = Sprite()
        sprite.kill_me_on_clear = True
        sprite.image = image
        sprite.rect = image.get_rect()
        sprite.rect.midtop = midtop
        sprite.rect.y += 200
        self.hud.add(sprite, layer=100)
        return sprite

    def process_bet(self, bet, winner):
        """Calculate winnings for the bet, apply the winnings, and clear it

        :param bet: ChipsPile instance
        :param winner: Deck instance
        :return: Amount of earnings, or negative will be loss
        """
        player_natural = natural(self.player_hand)
        dealer_natural = natural(self.dealer_hand)
        is_player = bet.owner is self.player_chips
        stats = self.stats

        winnings = bet.value
        if bet.result is winner:
            if winner is None:   # Tie
                winnings *= self.options['tie_payout']

            fee = 0
            commission = self.options['commission']
            if winner is self.dealer_hand and commission:
                fee = int(math.ceil(bet.value * commission))
                winnings -= fee

            new_chips = cash_to_chips(winnings)
            for chip in new_chips:
                chip.rect.center = (0, 0)

            bet.owner.extend(bet.sprites())
            self.delay(800, bet.owner.extend, (new_chips, ))
            bet.empty()

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

        else:
            winnings = -bet.value
            self.house_chips.extend(bet.sprites())
            bet.empty()

            if is_player:
                pn_loss = bet.result is self.player_hand and dealer_natural
                bn_loss = bet.result is self.dealer_hand and player_natural
                record = stats['Largest Loss']
                stats['Largest Loss'] = max(record, bet.value)
                stats['Bets Lost'] += 1
                stats['Earned'] -= bet.value
                if pn_loss or bn_loss:
                    stats['Bets Lost by Naturals'] += 1

        return winnings

    def display_scores(self):
        """Create and add TextSprites with score under each card hand
        """
        player_result = count_deck(self.player_hand)
        dealer_result = count_deck(self.dealer_hand)

        msg = points_message(player_result)
        text = TextSprite(msg.format(player_result), self.font)
        text.rect.midtop = self.player_hand.bounding_rect.midbottom
        text.rect.y += 25
        text.kill_me_on_clear = True
        self.hud.add(text)

        msg = points_message(dealer_result)
        text = TextSprite(msg.format(dealer_result), self.font)
        text.rect.midtop = self.dealer_hand.bounding_rect.midbottom
        text.rect.y += 25
        text.kill_me_on_clear = True
        self.hud.add(text)

    def clear_table(self):
        """Remove all cards from the table.  Animated.
        """
        def clear_card(card):
            sound = choice(self.deal_sounds)
            sound.set_volume(.6)
            sound.play()
            set_dirty = lambda: setattr(card, 'dirty', 1)
            fx, fy = card.rect.move(-1400, -200).topleft
            ani0 = Animation(x=fx, y=fy, duration=400,
                             transition='in_out_quint', round_values=True)
            ani0.update_callback = set_dirty
            ani0.callback = card.kill
            ani0.start(card.rect)
            ani1 = Animation(rotation=180, duration=400, transition='out_quart')
            ani1.update_callback = set_dirty
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

        text = TextSprite('Play Again', self.button_font)
        rect = self.confirm_button_rect
        self.hud.add(Button(text, rect, f))

    def show_bet_confirm_button(self):
        def f(sprite):
            if len(self.bets) > 0:
                self.dismiss_advisor()
                self._enable_chips = False
                sprite.kill()
                self.deal_cards()

        text = TextSprite('Confirm Bets', self.button_font)
        rect = self.confirm_button_rect
        sprite = Button(text, rect, f)
        self.hide_bet_confirm_button = sprite.kill
        self.hud.add(sprite)

    def render_background(self, size):
        """Render the background

        :param size: (width, height) in pixels
        :return: pygame.surface.Surface
        """
        def render_text(text):
            label.text = text
            return label.draw()

        background = pg.Surface(size)
        background.fill(prepare.FELT_GREEN)
        if hasattr(self, 'background_filename'):
            im = prepare.GFX[self.background_filename]
            background.blit(im, (0, 0))

        label = TextSprite('', self.font, bg=prepare.FELT_GREEN)
        totals = self.get_bet_totals()
        for name, area in self.betting_areas.items():
            total = totals[name]
            if total:
                image = render_text(area.name)
                image.set_alpha(128)
                label.rect.midbottom = area.rect.center
                background.blit(image, label.rect)

                image = render_text('${}'.format(totals[name]))
                image.set_alpha(192)
                label.rect.midtop = area.rect.center
                background.blit(image, label.rect)
            else:
                image = render_text(area.name)
                image.set_alpha(128)
                label.rect.center = area.rect.center
                background.blit(image, label.rect)

        return background
