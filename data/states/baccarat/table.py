from collections import defaultdict
from random import choice
from itertools import chain
from functools import partial

import pygame as pg

from .ui import *
from .chips import *
from ... import tools, prepare
from ...components.advisor import Advisor
from ...components.animation import Task, Animation
from ...prepare import BROADCASTER as B


__all__ = ('BettingArea', 'TableGame')

font_size = 64


class BettingArea(object):
    def __init__(self, name, rect, hand=None):
        self.name = name
        self.rect = rect
        self.hand = hand


class TableGame(tools._State):
    """Supports vegas style card games with chips and cards
    """
    name = 'table game base'

    def startup(self, now, persistent):
        self.now = now
        self.persist = persistent
        self.casino_player = self.persist['casino_player']
        self.set_stats()

        # declared here to appease pycharm's syntax checking.
        # will be filled in when configuration is loaded
        self.betting_areas = dict()
        self.dealer_hand = None
        self.player_hand = None
        self.player_chips = None
        self.house_chips = None
        self.shoe = None

        # baccarat only: move out later
        self.confirm_button_rect = None

        self.interested_events = [
            ('SNAP_STACK', self.on_snap_stack),
            ('RETURN_STACK', self.on_return_stack),
            ('SNAP_STACK_MOTION', self.on_snap_stack_motion),
            ('PICKUP_STACK', self.on_pickup_stack),
            ('DROP_STACK', self.on_drop_stack),
            ('PICKUP_STACK_MOTION', self.on_pickup_stack_motion),
        ]

        names = ["cardshove{}".format(x) for x in (1, 3, 4)]
        self.shove_sounds = [prepare.SFX[name] for name in names]
        names = ["cardplace{}".format(x) for x in (2, 3, 4)]
        self.deal_sounds = [prepare.SFX[name] for name in names]
        names = ["chipsstack{}".format(x) for x in (3, 5, 6)]
        self.chip_sounds = [prepare.SFX[name] for name in names]

        self._allow_exit = True
        self._highlight_areas = False
        self._mouse_tooltip = None
        self._enable_chips = False
        self._background = None
        self._clicked_sprite = None
        self._hovered_chip_area = None
        self._grabbed_stack = False
        self._locked_advice = None

        self.font = pg.font.Font(prepare.FONTS["Saniretro"], 64)
        self.large_font = pg.font.Font(prepare.FONTS["Saniretro"], 120)
        self.button_font = pg.font.Font(prepare.FONTS["Saniretro"], 48)

        self.hud = SpriteGroup()
        self.bets = MetaGroup()
        self.metagroup = MetaGroup()
        self.metagroup.add(self.bets)
        self.animations = pg.sprite.Group()

        self._advisor = Advisor(self.hud, self.animations)
        self._advisor.queue_text('Welcome to Baccarat', 3000)

        self.hud.add(NeonButton('lobby', (540, 938, 0, 0), self.goto_lobby))

        spr = Sprite()
        spr.image = prepare.GFX['baccarat-menu-front']
        spr.rect = spr.image.get_rect()
        self.hud.add(spr, layer=1)

        spr = Sprite()
        spr.image = prepare.GFX['baccarat-menu-back']
        spr.rect = spr.image.get_rect()
        self.hud.add(spr, layer=-100)

        self.remove_animations = partial(remove_animations_of, self.animations)

        self.metagroup.add(self.hud)

        self.reload_config()
        self.link_events()
        self.cash_in()
        self.new_round()

    def reload_config(self):
        raise NotImplementedError

    def new_round(self):
        raise NotImplementedError

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        raise NotImplementedError

    def render_background(self, size):
        """Render the background

        Subclasses must implement this

        :param size: (width, height) in pixels
        :return: pygame.surface.Surface
        """
        raise NotImplementedError

    def set_stats(self):
        """Get stats for game and set them.  Will set defaults if needed.
        """
        stats = self.casino_player.stats.get(self.name, None)
        if stats is None:
            stats = self.initialize_stats()
        self.casino_player.stats[self.name] = stats
        self.stats = stats

    def cleanup(self):
        self.unlink_events()
        self.casino_player.stats[self.name] = self.stats
        return super(TableGame, self).cleanup()

    def link_events(self):
        for name, f in self.interested_events:
            B.linkEvent(name, f)

    def unlink_events(self):
        for name, f in self.interested_events:
            B.unlinkEvent(name, f)

    def on_pickup_stack(self, *args):
        """When a stack of chips is picked up
        """
        self._highlight_areas = True
        self._grabbed_stack = True

        self._locked_advice = None
        self._advisor.empty()
        self._advisor.queue_text('Place chips into a betting area', 0)

    def on_drop_stack(self, *args):
        """When a stack of chips is dropped anywhere
        """
        # this is a hack until i have a proper metagroup
        def remove(owner, chips):
            owner.remove(chips)
            if owner is not self.player_chips:
                if owner.value == 0:
                    self.bets.remove(owner)

        # clear the light areas under chips/betting areas
        if self._hovered_chip_area is not None:
            self.clear_drop_area_overlay()

        self._highlight_areas = False
        self._grabbed_stack = False

        d = args[0]
        position = d['position']
        owner = d['object']
        chips = d['chips']

        needs_advice = not self.bets.groups()

        # this value is used to determine where to
        # return chips if this bet wins
        if not hasattr(owner, 'origin'):
            owner.origin = owner

        if self._hovered_chip_area is not None:
            self.clear_drop_area_overlay()

        self._advisor.empty()

        # check if chip is dropped onto a bet pile or player chips
        areas = chain(self.bets.groups(), [self.player_chips])
        for area in areas:
            if area is owner:
                continue

            if area.rect.collidepoint(position):
                remove(owner, chips)
                area.extend(chips)
                area.ignore_until_away = True
                self.clear_background()

                if not self.bets.groups():
                    self.hide_bet_confirm_button()

                return True, area

        # place chips in betting area
        for area in self.betting_areas.values():
            if area.rect.collidepoint(position):
                remove(owner, chips)
                bet = self.place_bet(area.hand, owner.origin, chips)
                bet.origin = owner.origin
                bet.rect.bottomleft = position

                # TODO: should not be hardcoded
                bet.rect.x -= 32
                self.clear_background()

                if bet.result is None:
                    payout = self.options['tie_payout']
                    msg = 'Ties pay {} to 1'.format(payout)
                    self._advisor.queue_text(msg, 3000)

                if bet.result is self.dealer_hand:
                    com = int(self.options['commission'] * 100)
                    msg = 'There is a {}% commission on dealer bets'.format(com)
                    self._advisor.push_text(msg, 3000)

                if needs_advice:
                    # TODO: remove from baseclass
                    self.show_bet_confirm_button()

                return True, bet

        # place chips in the house chips
        if self.house_chips.rect.collidepoint(position):
            remove(owner, chips)
            new_chips = list()
            for chip in chips:
                for value in make_change(chip.value, break_down=True):
                    chip = Chip(value)
                    chip.rect.center = self.house_chips.rect.center
                    new_chips.append(chip)
            self.player_chips.extend(new_chips)

    def on_pickup_stack_motion(self, *args):
        """When mouse is hovering over a stack or moving it
        """
        chips, position = args[0]

        self.on_snap_stack_motion(*args)

        # check if mouse is hovering over betting area
        areas = chain(self.betting_areas.values(), [self.player_chips])
        if self._hovered_chip_area is None:
            for area in areas:
                if area.drop_rect.collidepoint(position):
                    self._hovered_chip_area = area
                    sprite = getattr(area, 'sprite', None)
                    if sprite is None:
                        sprite = Sprite()
                        sprite.rect = area.drop_rect.copy()
                        sprite.image = pg.Surface(sprite.rect.size)
                        sprite.image.fill((255, 255, 255))
                        area.sprite = sprite

                    self.hud.add(sprite)
                    self.remove_animations(sprite.image)
                    ani = Animation(set_alpha=48, initial=0,
                                    duration=500, transition='out_quint')
                    ani.start(sprite.image)
                    self.animations.add(ani)

        # handle when mouse moves outside previously hovered area
        elif not self._hovered_chip_area.drop_rect.collidepoint(position):
            self.clear_drop_area_overlay()

    def on_snap_stack(self, *args):
        """When chips snap to cursor for first time
        """
        value = TextSprite('', self.large_font)
        self._mouse_tooltip = value
        self.hud.add(value, layer=100)

        # essentially just updates the tool tip value
        self.on_snap_stack_motion(*args)

        if self._locked_advice is None:
            self._advisor.empty()
            sprite = self._advisor.queue_text('Click to grab chips', 0)
            self._locked_advice = sprite

    def on_return_stack(self, *args):
        """When a stack of chips was previously snapped, but not any longer
        """
        # remove money tooltip
        self.hud.remove(self._mouse_tooltip)
        self._mouse_tooltip = None

        # remove 'click to grab chips' message
        if self._locked_advice is not None:
            self._advisor.dismiss(self._locked_advice)
            self._locked_advice = None

    def on_snap_stack_motion(self, *args):
        """When snapped stack is moved around
        """
        chips, position = args[0]
        amount = str(chips_to_cash(chips))
        sprite = self._mouse_tooltip
        sprite.text = "${}".format(amount)
        self.update_tooltip(sprite, position)

    def update_tooltip(self, sprite, position):
        sprite.rect.midleft = position
        sprite.rect.x += 30

    def clear_drop_area_overlay(self):
        self.remove_animations(self._hovered_chip_area.sprite.image)

        ani = Animation(
            set_alpha=0,
            initial=self._hovered_chip_area.sprite.image.get_alpha,
            duration=500, transition='out_quint')

        ani.callback = self._hovered_chip_area.sprite.kill
        ani.start(self._hovered_chip_area.sprite.image)
        self.animations.add(ani)

        self._hovered_chip_area = None

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

        if self._enable_chips:
            self.player_chips.get_event(event, scale)
            for bet in self.bets.groups():
                bet.get_event(event, scale)

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
        :return: Card instance
        """
        sound = choice(self.deal_sounds)
        sound.set_volume(1)
        self.delay(100, sound.play)

        sound = choice(self.shove_sounds)
        sound.set_volume(.20)
        sound.play()

        card = self.shoe.pop()
        hand.add(card)

        return card

    def place_bet_with_amount(self, result, owner, amount):
        """Shortcut to place a bet with amount of wager

        :param result: Deck or None
        :param owner: ChipsPile instance
        :param amount: amount to wager in cash (not chips)
        :return: ChipsPile instance
        """
        chips = owner.withdraw_chips(amount)
        return self.place_bet(result, owner, chips)

    def place_bet(self, result, owner, chips):
        """Shortcut to place a bet with chips

        :param result: Deck or None
        :param owner: ChipsPile instance
        :param chips: Chips to wager with
        :return: ChipsPile instance
        """
        choice(self.chip_sounds).play()
        bet = ChipPile((600, 800, 200, 200))
        bet.extend(chips)
        bet.owner = owner
        bet.result = result
        self.bets.add(bet)
        return bet

    def goto_lobby(self, *args):
        """Try to exit to the lobby

        Player will be automatically cashed out if ok
        """
        if self._allow_exit:
            self.quit()

    def do_quit(self, *args):
        """Try to exit to the lobby

        Player will be automatically cashed out if ok
        """
        self.cash_out()
        self.done = True
        self.next = 'LOBBYSCREEN'

    def cash_in(self):
        """Change player's cash to chips
        """
        chips = cash_to_chips(self.casino_player.stats['cash'])
        self.casino_player.stats['cash'] = 0
        self.player_chips.extend(chips)

    def cash_out(self):
        """Change player's chips to cash.  Includes any bets on table.
        """
        cash = self.player_chips.value
        for bet in self.bets.groups():
            if bet.origin is self.player_chips:
                bet.kill_me = True
                cash += bet.value
                bet.empty()
        self.casino_player.stats['cash'] = cash
        self.player_chips.empty()

    def get_bet_totals(self):
        """Get totals of all bets on the table

        :return: Totals of all bets on the table
        :rtype: Dict
        """
        totals = defaultdict(int)
        for name, area in self.betting_areas.items():
            for bet in self.bets.groups():
                if bet.result is area.hand:
                    result = bet.result
                    if result is None:
                        result = 'tie'
                    else:
                        result = name
                    totals[result] += bet.value
        return totals

    def clear_background(self):
        """Force the background to be redrawn
        """
        self._background = None

    def update(self, surface, keys, current_time, dt, scale):
        if self._background is None:
            image = self.render_background(surface.get_size())
            surface.blit(image, (0, 0))
            self._background = image

        self.animations.update(dt)
        self.metagroup.update(dt)
        self.metagroup.clear(surface, self._background)
        self.metagroup.draw(surface)
