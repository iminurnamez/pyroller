from random import choice
import pygame as pg

from ... import tools, prepare
from ...components.angles import get_distance, get_angle, project
from ...components.labels import NeonButton, ButtonGroup
from ...components.labels import Label, Blinker, MultiLineLabel
from ...components.cards import Deck
from ...components.chips import ChipStack, ChipRack, cash_to_chips, chips_to_cash
from ...components.warning_window import NoticeWindow, WarningWindow
from ...components.advisor import Advisor
from .blackjack_dealer import Dealer
from .blackjack_player import Player
from .blackjack_hand import Hand
from .blackjack_advisor_window import AdvisorWindow
from .blackjack_bot import BlackjackBot



class Blackjack(tools._State):
    """
    State to represent a blackjack game. Player cash
    will be converted to chips for the game and converted
    back into cash before returning to the lobby.
    """
    def __init__(self):
        super(Blackjack, self).__init__()
        self.font = prepare.FONTS["Saniretro"]
        self.result_font = prepare.FONTS["Saniretro"]
        names = ["cardplace{}".format(x) for x in (2, 3, 4)]
        self.deal_sounds = [prepare.SFX[name] for name in names]
        names = ["chipsstack{}".format(x) for x in (3, 5, 6)]
        self.chip_sounds = [prepare.SFX[name] for name in names]
        self.chip_size = (48, 30)
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.game_started = False
        self.elapsed = 17.0
        self.window = None
        self.make_buttons()
        self.result_labels = []
        self.labels = []
        self.quick_bet = 0
        self.last_bet = 0
        self.bot = None
        self.bot_queue = []
        self.draw_group = pg.sprite.Group()
        self.move_animations = pg.sprite.Group()
        self.advisor = Advisor(self.draw_group, self.move_animations)
        self.advisor_back = prepare.GFX["advisor_back"]
        self.advisor_front = prepare.GFX["advisor_front"]
        
    def make_buttons(self):
        side_margin = 10
        vert_space = 15
        left = self.screen_rect.right-(NeonButton.width + side_margin)
        top = self.screen_rect.bottom-((NeonButton.height*5)+vert_space*4)
        self.hit_button = NeonButton((left,top), "Hit", self.hit_click)
        self.deal_button = NeonButton((left, top), "Deal", self.deal)
        top += NeonButton.height + vert_space
        self.stand_button = NeonButton((left, top), "Stand", self.stand)
        top += NeonButton.height + vert_space
        self.double_down_button = NeonButton((left,top), "Double",
                                             self.double_down)
        top += NeonButton.height + vert_space
        self.split_button = NeonButton((left, top), "Split", self.split_hand)
        self.player_buttons = ButtonGroup(self.hit_button, self.stand_button,
                                          self.double_down_button,
                                          self.split_button)
        self.nav_buttons = ButtonGroup()
        self.new_game_button = NeonButton((0,0), "Change", self.new_game_click,
                                          None, self.nav_buttons)
        self.quick_bet_button = NeonButton((0, 0), "Again", self.quick_bet_click,
                                           None, self.nav_buttons)
        self.quick_bet_button.rect.midbottom = (self.screen_rect.centerx,
                                               self.screen_rect.centery-30)
        self.new_game_button.rect.center = (self.screen_rect.centerx,
                                             self.screen_rect.centery+30)
        pos = (self.screen_rect.right-(NeonButton.width+side_margin),
               self.screen_rect.bottom-(NeonButton.height+15))
        NeonButton(pos, "Lobby", self.back_to_lobby, None, self.nav_buttons, bindings=[pg.K_ESCAPE])
        self.buttons = ButtonGroup(self.player_buttons, self.nav_buttons)
        self.buttons.add(self.deal_button)

    def make_labels(self):
        labels_info = [
                ("Drop chips in chip rack", 36, "antiquewhite", 100,
                {"midtop": (self.chip_rack.rect.centerx, self.chip_rack.rect.bottom + 5)}),
                ("to make change", 36, "antiquewhite", 100,
                {"midtop": (self.chip_rack.rect.centerx, self.chip_rack.rect.bottom + 60)}),
                ("Blackjack Pays 3 to 2", 64, "gold3", 120, {"midtop": (580, 300)}),
                ("Dealer must draw to 16 and stand on 17", 48, "antiquewhite", 100,
                {"midtop": (580, 240)})
                ]
        labels = []
        for info in labels_info:
            label = Label(self.font, info[1], info[0], info[2], info[4], bg=prepare.FELT_GREEN)
            label.image.set_alpha(info[3])
            labels.append(label)
        return labels

    def new_game_click(self, *args):
        player_chips = self.player.chip_pile.all_chips()
        self.new_game(0, chips=player_chips)

    def quick_bet_click(self, *args):
        self.quick_bet = self.last_bet
        self.new_game_click()

    def get_bot_events(self):
        for event in self.bot_queue:
            if event.type == pg.MOUSEBUTTONDOWN:
                self.buttons.get_event(event)

    def new_game(self, player_cash, chips=None):
        """Start a new round of blackjack."""
        self.deck = Deck((20, 100), prepare.CARD_SIZE, 40)
        self.dealer = Dealer()
        self.chip_rack = ChipRack((1100, 130), self.chip_size)
        self.moving_cards =  []
        self.moving_stacks = []
        self.player = Player(self.chip_size, player_cash, chips)
        self.state = "Betting"
        for button in self.player_buttons:
            button.active = False
        self.hit_button.active = True
        self.stand_button.active = True
        self.labels = self.make_labels()
        self.current_player_hand = self.player.hands[0]
        self.game_started = True
        
        if self.quick_bet and (self.quick_bet <= self.player.chip_pile.get_chip_total()):
            chips = self.player.chip_pile.withdraw_chips(self.quick_bet)
            self.current_player_hand.bet.add_chips(chips)
            self.state = "Dealing"
            self.casino_player.increase("games played")
            self.quick_bet = 0
        else:
            self.advisor.queue_text("Click chips in your chip pile to place bet", dismiss_after=3000)
            self.advisor.queue_text("Click chips in pot to remove from bet", dismiss_after=3000)            

    def startup(self, current_time, persistent):
        """Get state ready to resume."""
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = "Blackjack"
        if prepare.ARGS["bots"]:
            self.bot = BlackjackBot(self)
        if not self.game_started:
            self.new_game(self.casino_player.cash)
        self.window = None

    def deal(self, *args):
        if not self.moving_stacks and not self.window:
            bets = [x.bet.get_chip_total() for x in self.player.hands]
            if any(bets):
                self.last_bet = max(bets)
                self.quick_bet = 0
                self.state = "Dealing"
                self.casino_player.increase("games played", 1)
                self.advisor.empty()
            else:
                text = "You need to make a bet first!"
                center = self.screen_rect.center
                self.window = NoticeWindow(center, text)

    def hit_click(self, *args):
        if not self.window:
            self.hit(self.current_player_hand)

    def hit(self, hand):
        """Draw a card from deck and add to hand."""
        choice(self.deal_sounds).play()
        card = self.deck.draw_card()
        card.face_up = True
        card.destination = hand.slots[-1]
        self.moving_cards.append(card)

    def stand(self, *args):
        """Player is done with this hand."""
        if not self.window:
            self.current_player_hand.final = True

    def double_down(self, *args):
        """
        Double player's bet on the hand, deal one
        more card and finalize hand.
        """
        if not self.window:
            player = self.player
            hand = self.current_player_hand
            chip_total = player.chip_pile.get_chip_total()
            bet = hand.bet.get_chip_total()
            if chip_total >= bet:
                bet_chips = self.player.chip_pile.withdraw_chips(bet)
                hand.bet.add_chips(bet_chips)
                choice(self.deal_sounds).play()
                card = self.deck.draw_card()
                card.face_up = True
                card.destination = hand.slots[-1]
                self.moving_cards.append(card)
                hand.final = True
            else:
                text = "You don't have enough cover that bet!"
                center = self.screen_rect.center
                self.window = NoticeWindow(center, text)

    def split_hand(self, *args):
        """
        Split player's hand into two hands, adjust hand locations
        and deal a new card to both hands.
        """
        if not self.window:
            player = self.player
            hand = self.current_player_hand
            chip_total = player.chip_pile.get_chip_total()
            bet = hand.bet.get_chip_total()
            if chip_total < bet:
                text = "You don't have enough to cover that bet!"
                center = self.screen_rect.center
                self.window = NoticeWindow(center, text)
                return
            if len(hand.cards) == 2:
                c1 = hand.card_values[hand.cards[0].value]
                c2 = hand.card_values[hand.cards[1].value]
                if c1 == c2:
                    hand.slots = hand.slots[:-1]
                    move = ((self.screen_rect.left+50)-hand.slots[0].left, 0)
                    self.player.move_hands(move)
                    p_slot = player.hands[-1].slots[0]
                    hand_slot = p_slot.move(int(prepare.CARD_SIZE[0] * 3.5), 0)
                    card = hand.cards.pop()
                    new_hand = Hand(hand_slot.topleft, [card],
                                    self.player.chip_pile.withdraw_chips(bet))
                    new_hand.slots = [hand_slot]
                    card.rect.topleft = hand_slot.topleft
                    player.hands.append(new_hand)
                    player.add_slot(new_hand)
                    choice(self.deal_sounds).play()
                    card1 = self.deck.draw_card()
                    card1.destination = hand.slots[-1]
                    card1.face_up = True
                    choice(self.deal_sounds).play()
                    card2 = self.deck.draw_card()
                    card2.destination = new_hand.slots[-1]
                    card2.face_up = True
                    self.moving_cards.extend([card1, card2])

    def back_to_lobby(self, *args):
        if not self.window:
            if any(hand.bet.get_chip_total() for hand in self.player.hands):
                if self.state == "Betting":
                    for hand in self.player.hands:
                        self.player.chip_pile.add_chips(hand.bet.chips)
                        hand.bet.chips = []
                        self.leave_state()
                else:
                    self.bet_warning()
            else:
                self.leave_state()

    def tally_hands(self):
        """
        Calculate result of each player hand and set appropriate
        flag for each hand.
        """
        if self.dealer.hand.blackjack:
            for hand in self.player.hands:
                hand.loser = True
        elif self.dealer.hand.busted:
            for hand in self.player.hands:
                if not hand.busted and not hand.blackjack:
                    hand.winner = True
        else:
            d_score = self.dealer.hand.best_score()
            for hand in self.player.hands:
                if not hand.busted:
                    p_score = hand.best_score()
                    if p_score == 21 and len(hand.cards) == 2:
                        hand.blackjack = True
                    elif p_score < d_score:
                        hand.loser = True
                    elif p_score == d_score:
                        hand.push = True
                    else:
                        hand.winner = True

    def pay_out(self):
        """
        Calculate player win amounts, update stats and return chips
        totalling total win amount.
        """
        cash = 0
        for hand in self.player.hands:
            bet = hand.bet.get_chip_total()
            self.casino_player.increase("hands played")
            self.casino_player.increase("total bets", bet)
            if hand.busted:
                self.casino_player.increase("busts")
                self.casino_player.increase("hands lost")
            elif hand.loser:
                self.casino_player.increase("hands lost")
            elif hand.blackjack:
                cash += int(bet + (bet * 1.5))
                self.casino_player.increase("blackjacks")
                self.casino_player.increase("hands won")
            elif hand.winner:
                cash += bet * 2
                self.casino_player.increase("hands won")
            elif hand.push:
                cash += bet
                self.casino_player.increase("pushes")

        self.casino_player.increase("total winnings")
        chips = cash_to_chips(cash, self.chip_size)
        return chips

    def cash_out_player(self):
        """Convert player's chips to cash and update stats."""
        self.casino_player.cash = self.player.chip_pile.get_chip_total()

    def leave_state(self):
        """Prepare to exit game and return to lobby screen."""
        self.cash_out_player()
        self.game_started = False
        self.done = True
        self.next = "LOBBYSCREEN"
        self.quick_bet = 0
        self.last_bet = 0

    def bet_warning(self):
        warn = "You sure? Exiting the game will forfeit your current bets!"
        center = self.screen_rect.center
        self.window = WarningWindow(center, warn, self.leave_state)

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT and not self.window:
            if any([hand.bet.get_chip_total() for hand in self.player.hands]):
                self.bet_warning()
            else:
                self.leave_state()
        elif event.type == pg.MOUSEBUTTONDOWN and not self.window:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.state == "Betting":
                if not self.moving_stacks and event.button == 1:
                    new_movers = self.player.chip_pile.grab_chips(pos)
                    if new_movers:
                        choice(self.chip_sounds).play()
                        self.moving_stacks.append(new_movers)
                    for hand in self.player.hands:
                        unbet_stack = hand.bet.grab_chips(pos)
                        if unbet_stack:
                            choice(self.chip_sounds).play()
                            self.player.chip_pile.add_chips(unbet_stack.chips)
        elif event.type == pg.MOUSEBUTTONUP:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.moving_stacks and event.button == 1:
                for stack in self.moving_stacks:
                    stack.bottomleft = pos
                    if self.chip_rack.rect.collidepoint(pos):
                        choice(self.chip_sounds).play()
                        self.player.chip_pile.add_chips(self.chip_rack.break_chips(stack.chips))
                    else:
                        self.current_player_hand.bet.add_chips(stack.chips)
                self.moving_stacks = []
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                if self.bot:
                    self.bot.active = not self.bot.active
        if self.state == "Player Turn" and not self.moving_cards:
            self.player_buttons.get_event(event)
        elif self.state == "Betting" and not self.moving_stacks:
            self.deal_button.get_event(event)
        self.nav_buttons.get_event(event)
        self.window and self.window.get_event(event)

    def update_game(self, surface, keys, current_time, dt, scale):
        if self.bot:
            self.bot.update()
        total_text = "Chip Total:  ${}".format(self.player.chip_pile.get_chip_total())
        screen = self.screen_rect
        self.chip_total_label = Label(self.font, 48, total_text, "gold3",
                               {"bottomleft": (screen.left + 3, screen.bottom - 3)})
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.deal_button.visible = self.state == "Betting"
        self.new_game_button.visible = self.state == "Show Results"
        self.quick_bet_button.visible = self.state == "Show Results"
        for button in self.player_buttons:
            button.visible = self.state == "Player Turn" and button.active

        if self.state == "Betting":
            if not self.moving_stacks:
                pass
            else:
                for stack in self.moving_stacks:
                    x, y = tools.scaled_mouse_pos(scale)
                    stack.bottomleft = (x - (self.chip_size[0] // 2),
                                                 y + 6)
        elif self.state == "Dealing":
            if not self.moving_cards:
                if len(self.current_player_hand.cards) < 2:
                    choice(self.deal_sounds).play()
                    card = self.deck.draw_card()
                    card.face_up = True
                    card.destination = self.current_player_hand.slots[-1]
                    self.moving_cards.append(card)
                elif len(self.dealer.hand.cards) < 2:
                    choice(self.deal_sounds).play()
                    card = self.deck.draw_card()
                    if len(self.dealer.hand.cards) > 0:
                        card.face_up = True
                    card.destination = self.dealer.hand.slots[-1]
                    self.moving_cards.append(card)
                else:
                    self.state = "Player Turn"
                    

        elif self.state == "Player Turn":
            self.split_button.active = False
            self.double_down_button.active = True

            if not self.moving_cards:
                hand = self.current_player_hand
                hand_score = hand.best_score()
                if hand_score is None:
                    hand.busted = True
                    hand.final = True

                if len(hand.cards) == 2 and len(self.player.hands) < 2:
                    c1 = hand.card_values[hand.cards[0].value]
                    c2 = hand.card_values[hand.cards[1].value]
                    if c1 == c2:
                        self.split_button.active = True
                if len(hand.cards) == 2:
                    if hand_score == 21:
                        hand.blackjack = True
                        hand.final = True
                if hand.final:
                    if all([hand.final for hand in self.player.hands]):
                        self.dealer.hand.cards[0].face_up = True
                        self.state = "Dealer Turn"
                    else:
                        next_hand = [x for x in self.player.hands if not x.final][0]
                        self.current_player_hand = next_hand

        elif self.state == "Dealer Turn":
            if all([hand.busted for hand in self.player.hands]):
                self.dealer.hand.final = True
                self.state = "End Round"
                return
            if not self.moving_cards:
                hand_score = self.dealer.hand.best_score()
                if hand_score is None:
                    self.dealer.hand.busted = True
                    self.dealer.hand.final = True
                elif hand_score == 21 and len(self.dealer.hand.cards) == 2:
                    self.dealer.hand.blackjack = True
                    self.dealer.hand.final = True
                elif hand_score < 17:
                    self.hit(self.dealer.hand)
                else:
                    self.dealer.hand.final = True
                if self.dealer.hand.final:
                    self.state = "End Round"

        elif self.state == "End Round":
            self.tally_hands()
            payout = self.pay_out()
            self.player.chip_pile.add_chips(payout)
            self.result_labels = []
            hands = self.player.hands[:]
            if self.dealer.hand.busted:
                hands.append(self.dealer.hand)
            if len(hands) >2:
                text_size = 64
            elif len(hands) == 2:
                text_size = 80
            else:
                text_size = 96
            for hand in hands:
                if hand.blackjack:
                    text, color = "Blackjack", "gold3"
                    text_size -= 8
                elif hand.winner:
                    text, color = "Win", "gold3"
                elif hand.push:
                    text, color = "Push", "gold3"
                elif hand.busted:
                    text, color = "Bust", "darkred"
                else:
                    text, color = "Loss", "darkred"
                centerx = (hand.slots[0].left + hand.slots[-1].right) // 2
                centery = hand.slots[0].centery
                label = Blinker(self.result_font, text_size, text, color,
                                      {"center": (centerx, centery)},
                                      450)
                self.result_labels.append(label)
                hand.bet.chips = []
            self.state = "Show Results"

        arrived = set()
        for card in self.moving_cards:
            card.travel(card.destination.center)
            if get_distance(card.destination.center, card.pos) < card.speed:
                arrived.add(card)
                card.rect.center = card.destination.center
                card.pos = card.rect.center
                if card.destination in self.dealer.hand.slots:
                    self.dealer.hand.cards.append(card)
                    self.dealer.add_slot()
                else:
                    for hand in self.player.hands:
                        if card.destination in hand.slots:
                            hand.cards.append(card)
                            self.player.add_slot(hand)
        self.moving_cards = [x for x in self.moving_cards if x not in arrived]
        self.chip_rack.update()


    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale, pg.mouse.get_pos())
        self.update_game(surface, keys, current_time, dt, scale)
        self.buttons.update(mouse_pos)
        self.update_windows(mouse_pos)
        for blinker in self.result_labels:
            blinker.update(dt)
        self.move_animations.update(dt)
        
        self.draw(surface, dt)

    def update_windows(self, mouse_pos):
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                self.window = None

    def draw(self, surface, dt):
        surface.fill(prepare.FELT_GREEN)
        for label in self.labels:
            label.draw(surface)
        self.dealer.draw_hand(surface)
        self.deck.draw(surface)
        self.chip_rack.draw(surface)
        draw_bets = True
        if self.state == "Show Results":
            draw_bets = False
        self.player.draw(surface, draw_bets)
        for card in self.moving_cards:
            card.draw(surface)
        for stack in self.moving_stacks:
            stack.draw(surface)
        if self.state == "Player Turn":
            hand = self.current_player_hand
            rects = [x.rect for x in hand.cards]
            pg.draw.rect(surface, pg.Color("gold3"),
                         hand.cards[0].rect.unionall(rects).inflate(8, 8), 3)
        if self.state == "Show Results":
            for blinker in self.result_labels:
                blinker.draw(surface)
        self.chip_total_label.draw(surface)
        if not self.window:
            self.buttons.draw(surface)
        self.window and self.window.draw(surface)
        
        
        surface.blit(self.advisor_back, (0, 0))
        self.draw_group.draw(surface)
        surface.blit(self.advisor_front, (0, 0))
