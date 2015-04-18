from random import choice
import pygame as pg
from ... import tools, prepare
from ...components.labels import NeonButton, ButtonGroup
from ...components.labels import Label, Blinker, MultiLineLabel
from ...components.angles import get_distance
from ...components.animation import Animation, Task
from ...components.chips import BetPile, cash_to_chips
from ...components.warning_window import WarningWindow
from .blackjack_hand import Hand


class BlackjackState(object):
    screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
    font = prepare.FONTS["Saniretro"]
    def __init__(self):
        self.done = False
        self.quit = False
        self.next = None
        self.animations = pg.sprite.Group()
        self.window = None

    def leave_state(self):
        self.done = True
        self.quit = True

    def back_to_lobby(self, *args):
        if any(hand.bet.get_chip_total() for hand in self.game.player.hands):
            self.bet_warning()
        else:
            self.leave_state()

    def bet_warning(self):
        warn = "You sure? Exiting the game will forfeit your current bets!"
        center = self.screen_rect.center
        self.window = WarningWindow(center, warn, self.leave_state)


    def play_deal_sound(self):
        choice(self.game.deal_sounds).play()

    def play_chip_sound(self):
        choice(self.game.chip_sounds).play()

    def startup(self, game):
        self.game = game

    def get_event(self, event, scale=(1,1)):
        pass

    def update(self, surface, keys, current_time, dt, scale):
        pass

    def draw(self, surface):
        pass

    def draw_advisor(self, surface):
        if self.game.advisor_active:
            surface.blit(self.game.advisor_back, (0, 0))
            self.game.draw_group.draw(surface)
            surface.blit(self.game.advisor_front, (0, 0))
        else:
            surface.blit(self.game.advisor_back_dim, (0, 0))
            surface.blit(self.game.advisor_front_dim, (0, 0))


class Betting(BlackjackState):
    def __init__(self):
        super(Betting, self).__init__()
        self.make_buttons()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        self.lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, None, self.buttons, bindings=[pg.K_ESCAPE])

    def back_to_lobby(self, *args):
        player = self.game.player
        for hand in player.hands:
            player.chip_pile.add_chips(cash_to_chips(hand.bet.get_chip_total()))
        self.leave_state()

    def startup(self, game):
        self.game = game
        if self.game.quick_bet and (self.game.quick_bet <= self.game.player.chip_pile.get_chip_total()):
            chips = self.game.player.chip_pile.withdraw_chips(self.game.quick_bet)
            self.game.current_player_hand.bet.add_chips(chips)
            self.deal()
        elif self.game.advisor_active:
            self.game.advisor.queue_text("Click chips in your chip pile to place bet", dismiss_after=3000)
            self.game.advisor.queue_text("Click chips in pot to remove from bet", dismiss_after=3000)

    def make_buttons(self):
        self.buttons = ButtonGroup()
        side_margin = 10
        vert_space = 15
        left = self.screen_rect.right-(NeonButton.width + side_margin)
        top = self.screen_rect.bottom-((NeonButton.height*5)+vert_space*4)
        self.deal_button = NeonButton((left, top), "Deal", self.deal, None, self.buttons)

    def deal(self, *args):
        bets = [x.bet.get_chip_total() for x in self.game.player.hands]
        self.game.last_bet = max(bets)
        self.game.quick_bet = 0
        self.next = "Dealing"
        self.game.casino_player.increase("games played")
        self.game.advisor.empty()
        self.done = True

    def get_event(self, event, scale):
        self.game.get_event(event)
        if event.type == pg.QUIT:
            self.back_to_lobby()
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if not self.game.moving_stacks and event.button == 1:
                new_movers = self.game.player.chip_pile.grab_chips(pos)
                self.last_click = pg.time.get_ticks()
                if new_movers:
                    self.play_chip_sound()
                    self.game.moving_stacks.append(new_movers)
                for hand in self.game.player.hands:
                    unbet_stack = hand.bet.grab_chips(pos)
                    if unbet_stack:
                        self.play_chip_sound()
                        self.game.player.chip_pile.add_chips(unbet_stack.chips)

        elif event.type == pg.MOUSEBUTTONUP:
            now = pg.time.get_ticks()
            span = now - self.last_click
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.game.moving_stacks and event.button == 1:
                for stack in self.game.moving_stacks:
                    stack.rect.bottomleft = pos
                    if self.game.chip_rack.rect.collidepoint(pos):
                        self.play_chip_sound()
                        self.game.player.chip_pile.add_chips(self.game.chip_rack.break_chips(stack.chips))
                    elif span > 300 and self.game.player.chip_pile.rect.collidepoint(pos):
                        self.play_chip_sound()
                        self.game.player.chip_pile.add_chips(stack.chips)
                    else:
                        self.play_chip_sound()
                        self.game.current_player_hand.bet.add_chips(stack.chips)
                self.game.moving_stacks = []
        if self.window:
            self.window.get_event(event)
        else:
            self.lobby_button.get_event(event)
            self.deal_button.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        self.game.update(dt, mouse_pos)
        bets = [x.bet.get_chip_total() for x in self.game.player.hands]
        self.deal_button.visible = any(bets) and not self.game.moving_stacks

        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None
        else:
            self.lobby_button.update(mouse_pos)
            self.deal_button.update(mouse_pos)
        for stack in self.game.moving_stacks:
            x, y = mouse_pos
            stack.rect.bottomleft = (x - (self.game.chip_size[0] // 2),
                                         y + 6)

    def draw(self, surface):
        g = self.game
        surface.fill(prepare.FELT_GREEN)
        for label in g.labels:
            label.draw(surface)
        g.player.draw_hands(surface)
        g.player.draw_hand_bets(surface)
        g.player.chip_pile.draw(surface)
        g.chip_total_label.draw(surface)
        g.dealer.draw_hand(surface)
        g.deck.draw(surface)
        g.chip_rack.draw(surface)
        for stack in g.moving_stacks:
            stack.draw(surface)
        self.buttons.draw(surface)
        self.draw_advisor(surface)
        self.window and self.window.draw(surface)


class Dealing(BlackjackState):
    def __init__(self):
        super(Dealing, self).__init__()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        self.lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, None, bindings=[pg.K_ESCAPE])

    def startup(self, game):
        self.game = game
        self.make_card_animations()

    def flip_card(self, card):
        card.face_up = True

    def make_card_animations(self):
        g = self.game
        self.animations = pg.sprite.Group()
        deal_delay = 0
        for i in range(2):
            card = g.deck.draw_card()
            destination = g.current_player_hand.slots[-1]
            dest_x, dest_y = destination.topleft
            dur = get_distance(destination.center, card.pos) * 20 // card.speed
            ani = Animation(x=dest_x, y=dest_y, duration=dur,
                                    delay=deal_delay, round_values=True)
            ani2 = Task(self.play_deal_sound, deal_delay)
            ani3 = Task(self.flip_card, deal_delay + dur, args=(card,))
            g.current_player_hand.cards.append(card)
            if not i % 2:
                g.player.add_slot(g.current_player_hand)
            ani.start(card.rect)
            self.animations.add(ani, ani2, ani3)
            deal_delay += dur
        for i in range(2):
            card = g.deck.draw_card()
            destination = g.dealer.hand.slots[-1]
            dest_x, dest_y = destination.topleft
            dur = get_distance(destination.center, card.pos) * 20 // card.speed
            ani = Animation(x=dest_x, y=dest_y, duration=dur,
                                    delay=deal_delay, round_values=True)
            ani2 = Task(self.play_deal_sound, deal_delay)
            ani.start(card.rect)
            g.dealer.hand.cards.append(card)
            g.dealer.add_slot()
            self.animations.add(ani, ani2)
            if i:
                ani3 = Task(self.flip_card, deal_delay + dur, args=(card,))
                self.animations.add(ani3)
            deal_delay += dur

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.game.get_event(event)
        if self.window:
            self.window.get_event(event)
        else:
            self.lobby_button.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        self.game.update(dt, mouse_pos)
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None
        else:
            self.lobby_button.update(mouse_pos)
            if self.animations:
                self.animations.update(dt)
            else:
                self.next = "Player Turn"
                self.done = True

    def draw(self, surface):
        g = self.game
        surface.fill(prepare.FELT_GREEN)
        for label in g.labels:
            label.draw(surface)
        g.player.draw_hand_bets(surface)

        g.chip_total_label.draw(surface)
        g.dealer.draw_hand(surface)
        g.deck.draw(surface)
        g.chip_rack.draw(surface)
        self.lobby_button.draw(surface)
        g.player.draw_hands(surface)
        g.player.chip_pile.draw(surface)
        self.draw_advisor(surface)
        self.window and self.window.draw(surface)




class PlayerTurn(BlackjackState):
    def __init__(self):
        super(PlayerTurn, self).__init__()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        self.make_buttons()
        self.lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, None, self.buttons, bindings=[pg.K_ESCAPE])
        self.last_click = 0

    def play_deal_sound(self):
        choice(self.game.deal_sounds).play()

    def make_buttons(self):
        side_margin = 10
        vert_space = 12
        left = self.screen_rect.right-(NeonButton.width + side_margin)
        top = self.screen_rect.bottom-((NeonButton.height*5)+vert_space*5)
        self.hit_button = NeonButton((left,top), "Hit", self.hit_click)
        top += NeonButton.height + vert_space
        self.stand_button = NeonButton((left, top), "Stand", self.stand)
        top += NeonButton.height + vert_space
        self.double_down_button = NeonButton((left,top), "Double",
                                             self.double_down)
        top += NeonButton.height + vert_space
        self.split_button = NeonButton((left, top), "Split", self.split_hand)
        self.buttons = ButtonGroup(self.hit_button, self.stand_button,
                                          self.double_down_button,
                                          self.split_button)

    def hit_click(self, *args):
        self.hit(self.game.current_player_hand)

    def hit(self, hand):
        """Draw a card from deck and add to hand."""
        self.play_deal_sound()
        self.game.player.add_slot(hand)
        card = self.game.deck.draw_card()
        card.face_up = True
        destination = hand.slots[-1]
        dest_x, dest_y = destination.topleft
        hand.cards.append(card)
        dur = get_distance(destination.center, card.pos) * 20 // card.speed
        ani = Animation(x=dest_x, y=dest_y, duration=dur, round_values=True)
        ani.start(card.rect)
        self.animations.add(ani)


    def stand(self, *args):
        """Player is done with this hand."""
        self.game.current_player_hand.final = True

    def double_down(self, *args):
        """
        Double player's bet on the hand, deal one
        more card and finalize hand.
        """
        hand = self.game.current_player_hand
        bet = hand.bet.get_chip_total()
        bet_chips = self.game.player.chip_pile.withdraw_chips(bet)
        hand.bet.add_chips(bet_chips)
        self.hit(hand)
        hand.final = True

    def split_hand(self, *args):
        """
        Split player's hand into two hands, adjust hand locations
        and deal a new card to both hands.
        """
        player = self.game.player
        hand = self.game.current_player_hand
        bet = hand.bet.get_chip_total()

        hand.slots = hand.slots[:-1]
        move = ((self.screen_rect.left+50)-hand.slots[0].left, 0)
        player.move_hands(move)
        p_slot = player.hands[-1].slots[0]
        hand_slot = p_slot.move(int(prepare.CARD_SIZE[0] * 3.5), 0)
        card = hand.cards.pop()
        new_hand = Hand(hand_slot.topleft, [card],
                        player.chip_pile.withdraw_chips(bet))
        new_hand.slots = [hand_slot]
        card.rect.topleft = hand_slot.topleft
        player.hands.append(new_hand)
        player.add_slot(new_hand)

        self.play_deal_sound()
        self.game.player.add_slot(hand)
        card1 = self.game.deck.draw_card()
        dest = hand.slots[-1]
        dest_x, dest_y = dest.topleft
        card1.face_up = True
        hand.cards.append(card1)
        ani = Animation(x=dest_x, y=dest_y, duration=1000, round_values=True)
        ani.start(card1.rect)

        card2 = self.game.deck.draw_card()
        dest = new_hand.slots[-1]
        dest_x, dest_y = dest.topleft
        card2.face_up = True
        new_hand.cards.append(card2)
        ani2 = Animation(x=dest_x, y=dest_y, duration=1000, delay=500, round_values=True)
        ani2.start(card2.rect)
        ani3 = Task(self.play_deal_sound, 1500)
        self.animations.add(ani, ani2, ani3)

    def startup(self, game):
        self.game = game
        self.animations = pg.sprite.Group()

    def get_event(self, event, scale):
        now = pg.time.get_ticks()
        span = now - self.last_click
        if event.type == pg.QUIT:
            self.back_to_lobby()
        if event.type == pg.MOUSEBUTTONUP:
            self.last_click = now
        self.game.get_event(event)
        if span > 300:
            if self.window:
                self.window.get_event(event)
            else:
                self.buttons.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        g = self.game
        g.update(dt, mouse_pos)

        self.split_button.active = False
        self.split_button.visible = False
        self.double_down_button.active = False
        self.double_down_button.visible = False

        hand = g.current_player_hand
        hand_score = hand.best_score()
        if hand_score is None:
            hand.busted = True
            hand.final = True
        chip_total = g.player.chip_pile.get_chip_total()
        bet = hand.bet.get_chip_total()

        if len(hand.cards) == 2 and len(g.player.hands) < 2:
            c1 = hand.card_values[hand.cards[0].value]
            c2 = hand.card_values[hand.cards[1].value]
            if c1 == c2 and chip_total >= bet:
                self.split_button.active = True
                self.split_button.visible = True
        if len(hand.cards) == 2:
            if hand_score == 21:
                hand.blackjack = True
                hand.final = True
            elif chip_total >= bet:
                self.double_down_button.active = True
                self.double_down_button.visible = True

        if hand.final:
            if all([hand.final for hand in g.player.hands]):
                if not self.animations:
                    g.dealer.hand.cards[0].face_up = True
                    self.next = "Dealer Turn"
                    self.done = True
            else:
                next_hand = [x for x in g.player.hands if not x.final][0]
                g.current_player_hand = next_hand
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None
        else:
            self.buttons.update(mouse_pos)
            self.animations.update(dt)

    def draw_hand_frame(self, surface):
        hand = self.game.current_player_hand
        rects = [x for x in hand.slots]
        pg.draw.rect(surface, pg.Color("gold3"),
                     hand.slots[0].unionall(rects).inflate(8, 8), 3)

    def draw(self, surface):
        g = self.game
        surface.fill(prepare.FELT_GREEN)
        for label in g.labels:
            label.draw(surface)
        g.player.draw_hand_bets(surface)
        g.player.chip_pile.draw(surface)
        g.chip_total_label.draw(surface)
        g.dealer.draw_hand(surface)
        g.deck.draw(surface)
        g.chip_rack.draw(surface)
        self.buttons.draw(surface)
        self.lobby_button.draw(surface)
        g.player.draw_hands(surface)
        self.draw_advisor(surface)
        self.draw_hand_frame(surface)
        self.game.player.chip_pile.draw(surface)
        self.window and self.window.draw(surface)


class DealerTurn(BlackjackState):
    def __init__(self):
        super(DealerTurn, self).__init__()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        self.lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, bindings=[pg.K_ESCAPE])

    def startup(self, game):
        self.game = game
        g = game
        if all([hand.busted for hand in g.player.hands]):
            g.dealer.hand.final = True
            self.state = "End Round"
        delay = 1000
        while not g.dealer.hand.final:
            hand_score = g.dealer.hand.best_score()
            if hand_score is None:
                g.dealer.hand.busted = True
                g.dealer.hand.final = True
            elif hand_score == 21 and len(g.dealer.hand.cards) == 2:
                g.dealer.hand.blackjack = True
                g.dealer.hand.final = True
            elif hand_score < 17:
                self.hit(g.dealer.hand, delay)
                delay += 1000
            else:
                g.dealer.hand.final = True

    def hit(self, hand, delay_time=0):
        """Draw a card from deck and add to hand."""
        self.play_deal_sound()
        card = self.game.deck.draw_card()
        card.face_up = True
        destination = hand.slots[-1]
        dest_x, dest_y = destination.topleft
        dur = get_distance(destination.center, card.pos) * 20 // card.speed
        self.game.dealer.add_slot()
        hand.cards.append(card)
        ani = Animation(x=dest_x, y=dest_y, duration=dur,
                                delay=delay_time, round_values=True)
        ani.start(card.rect)
        self.animations.add(ani)

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.game.get_event(event)
        if self.window:
            self.window.get_event(event)
        else:
            self.lobby_button.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        self.game.update(dt, mouse_pos)
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None
        else:
            self.lobby_button.update(mouse_pos)
            self.animations.update(dt)
            if not self.animations:
                self.next = "Show Results"
                self.done = True

    def draw(self, surface):
        g = self.game
        surface.fill(prepare.FELT_GREEN)
        for label in g.labels:
            label.draw(surface)
        g.player.draw_hand_bets(surface)
        g.player.chip_pile.draw(surface)
        g.chip_total_label.draw(surface)
        g.dealer.draw_hand(surface)
        g.deck.draw(surface)
        g.chip_rack.draw(surface)
        self.lobby_button.draw(surface)
        g.player.draw_hands(surface)
        self.draw_advisor(surface)
        self.game.player.chip_pile.draw(surface)
        self.window and self.window.draw(surface)


class ShowResults(BlackjackState):
    def __init__(self):
        super(ShowResults, self).__init__()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        self.lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, bindings=[pg.K_ESCAPE])
        self.coin_sound = prepare.SFX["coins"]

    def startup(self, game):
        self.game = game
        self.game.result_labels = []
        self.fade_labels = []
        self.alpha = 255
        total_ani_time = 2000
        fade_ani = Animation(alpha=0, duration=total_ani_time)
        fade_ani.start(self)
        self.animations.add(fade_ani)
        self.game.tally_hands()
        payout = self.game.pay_out()
        if payout:
            self.coin_sound.play()
        hands = self.game.player.hands
        if len(hands) >2:
            text_size = 64
        elif len(hands) == 2:
            text_size = 80
        else:
            text_size = 96
        win_piles = []
        loss_piles = []
        self.winnings = []
        self.losses = []
        for hand in hands:
            amount = hand.bet.get_chip_total()
            hand.bet_amount  = amount
            bl = hand.bet.stacks[0].rect.bottomleft
            if hand.blackjack:
                text, color = "Blackjack", "gold3"
                text_size -= 8
                chips = cash_to_chips(int(amount * 2.5))
                amount = int(amount * 1.5)
                win_piles.append(BetPile(bl, self.game.chip_size, chips))
            elif hand.winner:
                text, color = "Win", "gold3"
                chips = cash_to_chips(amount * 2)
                win_piles.append(BetPile(bl, self.game.chip_size, chips))
            elif hand.push:
                text, color = "Push", "gold3"
                chips = cash_to_chips(amount)
                win_piles.append(BetPile(bl, self.game.chip_size, chips))
            elif hand.busted:
                text, color = "Bust", "darkred"
                chips = cash_to_chips(amount)
                loss_piles.append(BetPile(bl, self.game.chip_size, chips))
                amount *= -1
            else:
                text, color = "Loss", "darkred"
                chips = cash_to_chips(amount)
                loss_piles.append(BetPile(bl, self.game.chip_size, chips))
                amount *= -1
            centerx = (hand.slots[0].left + hand.slots[-1].right) // 2
            centery = hand.slots[0].centery
            label = Blinker(self.font, text_size, text, color,
                                  {"center": (centerx, centery)},
                                  450)
            self.game.result_labels.append(label)
            amt_color = "darkgreen" if amount >= 0 else "darkred"

            bet_label = Label(self.font, 120, "{:+}".format(amount), amt_color,
                                      {"bottomleft": bl}, bg=prepare.FELT_GREEN)
            move_ani = Animation(bottom=bl[1]-150, duration=total_ani_time, round_values=True)
            move_ani.start(bet_label.rect)
            self.animations.add(move_ani)
            self.fade_labels.append(bet_label)
            hand.bet.chips = []
            hand.bet.stacks = []

        payout_duration = 1000
        center = self.game.player.chip_pile.rect.center
        for pile in win_piles:
            self.winnings.append(pile)
            for stack in pile.stacks:
                ani = Animation(left=center[0], bottom=center[1], duration=payout_duration, round_values=True)
                ani.start(stack.rect)
                self.animations.add(ani)
        center = self.game.chip_rack.rect.center
        for loss_pile in loss_piles:
            self.losses.append(loss_pile)
            for stack in loss_pile.stacks:
                ani = Animation(left=center[0], bottom=center[1], duration=payout_duration, round_values=True)
                ani.start(stack.rect)
                self.animations.add(ani)
        pay_ani = Task(self.game.player.chip_pile.add_chips, payout_duration, args=[payout])
        remove_chips = Task(self.remove_chips, payout_duration)
        end_it = Task(self.end_state, total_ani_time)
        self.animations.add(pay_ani, remove_chips, end_it)

    def remove_chips(self):
        self.winnings = []
        self.losses = []

    def end_state(self):
        self.next = "End Round"
        self.done = True

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.game.get_event(event)
        if self.window:
            self.window.get_event(event)
        else:
            self.lobby_button.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        self.game.update(dt, mouse_pos)
        for blinker in self.game.result_labels:
            blinker.update(dt)
        self.animations.update(dt)
        for fader in self.fade_labels:
            fader.image.set_alpha(self.alpha)
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None
        else:
            self.lobby_button.update(mouse_pos)

    def draw(self, surface):
        g = self.game
        surface.fill(prepare.FELT_GREEN)
        for label in g.labels:
            label.draw(surface)
        g.player.draw_hand_bets(surface)
        g.player.chip_pile.draw(surface)
        g.chip_total_label.draw(surface)
        g.dealer.draw_hand(surface)
        g.deck.draw(surface)
        g.chip_rack.draw(surface)
        self.lobby_button.draw(surface)
        g.player.draw_hands(surface)
        for blinker in self.game.result_labels:
            blinker.draw(surface)
        for fader in self.fade_labels:
            fader.draw(surface)
        self.draw_advisor(surface)
        self.game.player.chip_pile.draw(surface)
        for pile in self.winnings:
            pile.draw(surface)
        for pile_ in self.losses:
            pile_.draw(surface)
        self.window and self.window.draw(surface)


class EndRound(BlackjackState):
    def __init__(self):
        super(EndRound, self).__init__()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        self.lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, bindings=[pg.K_ESCAPE])
        self.make_buttons()

    def make_buttons(self):
        self.buttons = ButtonGroup()
        self.new_game_button = NeonButton((0,0), "Change", self.new_game_click,
                                          None, self.buttons)
        self.quick_bet_button = NeonButton((0, 0), "Again", self.quick_bet_click,
                                           None, self.buttons)
        self.quick_bet_button.rect.midbottom = (self.screen_rect.centerx,
                                               self.screen_rect.centery-30)
        self.new_game_button.rect.center = (self.screen_rect.centerx,
                                             self.screen_rect.centery+30)

    def new_game_click(self, *args):
        self.game.advisor.empty()
        self.next = "Betting"
        self.done = True

    def quick_bet_click(self, *args):
        self.game.quick_bet = self.game.last_bet
        self.new_game_click()

    def startup(self, game):
        self.game = game
        if game.advisor_active:
            text = "The current bet amount is ${}".format(self.game.last_bet)
            self.game.advisor.queue_text(text, dismiss_after=3000)
            text2 = "Press Change Bet for a different amount"
            self.game.advisor.queue_text(text2, dismiss_after=3000)
            text3 = "Press the Lobby button to exit"
            self.game.advisor.queue_text(text3, dismiss_after=3000)

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.back_to_lobby()
        self.game.get_event(event)
        if self.window:
            self.window.get_event(event)
        else:
            self.buttons.get_event(event)
            self.lobby_button.get_event(event)


    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(pg.mouse.get_pos(), scale)
        self.game.update(dt, mouse_pos)
        for label in self.game.result_labels:
            label.update(dt)
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None
        else:
            self.buttons.update(mouse_pos)
            self.lobby_button.update(mouse_pos)

    def draw(self, surface):
        g = self.game
        surface.fill(prepare.FELT_GREEN)
        for label in g.labels:
            label.draw(surface)
        g.player.draw_hand_bets(surface)
        g.player.chip_pile.draw(surface)
        g.chip_total_label.draw(surface)
        g.dealer.draw_hand(surface)
        g.deck.draw(surface)
        g.chip_rack.draw(surface)
        self.lobby_button.draw(surface)
        g.player.draw_hands(surface)
        for blinker in self.game.result_labels:
            blinker.draw(surface)
        self.buttons.draw(surface)
        self.draw_advisor(surface)
        self.game.player.chip_pile.draw(surface)
        self.window and self.window.draw(surface)



