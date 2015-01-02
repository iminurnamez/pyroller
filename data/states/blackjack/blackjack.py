from random import choice
import pygame as pg
from ... import tools, prepare
from ...components.angles import get_distance, get_angle, project
from ...components.labels import Label, Button, PayloadButton, Blinker, MultiLineLabel, NeonButton
from ...components.cards import Deck
from ...components.chips import ChipStack, ChipRack, cash_to_chips, chips_to_cash
from .blackjack_dealer import Dealer
from .blackjack_player import Player
from .blackjack_hand import Hand
from .blackjack_advisor_window import AdvisorWindow

class Blackjack(tools._State):
    """State to represent a blackjack game. Player cash
        will be converted to chips for the game and converted
        back into cash before returning to the lobby."""
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

        b_width = 318
        b_height = 101
        side_margin = 10
        vert_space = 20
        left = self.screen_rect.right - (b_width + side_margin)
        top = self.screen_rect.bottom - ((b_height * 5) + vert_space * 4)

        self.hit_button = NeonButton((left, top), "Hit", self.hit)
        self.deal_button = NeonButton((left, top), "Deal")
        top += b_height + vert_space
        self.stand_button = NeonButton((left, top), "Stand", self.stand)
        top += b_height + vert_space
        self.double_down_button = NeonButton((left, top), "Double", 
                                                                    self.double_down) 
        top += b_height + vert_space
        self.split_button = NeonButton((left, top), "Split", self.split_hand)
        self.player_buttons = [self.hit_button, self.stand_button,
                                         self.double_down_button, self.split_button]
        self.new_game_button = NeonButton((self.deal_button.rect.left - (b_width + 15),
                                                                self.screen_rect.bottom - (b_height + 15)),
                                                                "Again")
        self.lobby_button = NeonButton((self.screen_rect.right - (b_width + side_margin),
                                                        self.screen_rect.bottom - (b_height + 15)),
                                                        "Lobby")
        self.buttons = self.player_buttons[:]
        self.buttons.extend([self.deal_button, self.new_game_button, self.lobby_button])
        
    def new_game(self, player_cash, chips=None):
        """Start a new round of blackjack."""
        self.deck = Deck((20, 20), prepare.CARD_SIZE, 20)
        self.dealer = Dealer()
        self.chip_rack = ChipRack((1100, 200), self.chip_size)
        self.moving_cards =  []
        self.moving_stacks = []
        self.player = Player(self.chip_size, player_cash, chips)
        self.state = "Betting"
        for button in self.player_buttons:
            button.active = False
        self.hit_button.active = True
        self.stand_button.active = True
        self.current_player_hand = self.player.hands[0]
        self.advisor_window = None
        self.game_started = True

    def startup(self, current_time, persistent):
        """Get state ready to resume."""
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        if not self.game_started:
            self.new_game(self.casino_player.stats["cash"])

    def hit(self, player, hand):
        """Draw a card from deck and add to hand."""
        choice(self.deal_sounds).play()
        card = self.deck.draw_card()
        card.face_up = True
        card.destination = hand.slots[-1]
        self.moving_cards.append(card)

    def stand(self, player, hand):
        """Player is done with this hand."""
        hand.final = True

    def double_down(self, player, hand):
        """Double player's bet on the hand, deal one
        more card and finalize hand."""
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

    def split_hand(self, player, hand):
        """Split player's hand into two hands, adjust hand locations
        and deal a new card to both hands."""
        chip_total = player.chip_pile.get_chip_total()
        bet = hand.bet.get_chip_total()
        if chip_total < bet:
            return
        if len(hand.cards) == 2:
            c1 = hand.card_values[hand.cards[0].value]
            c2 = hand.card_values[hand.cards[1].value]
            if c1 == c2:
                hand.slots = hand.slots[:-1]
                self.player.move_hands(((self.screen_rect.left + 50) - hand.slots[0].left, 0))
                p_slot = player.hands[-1].slots[0]
                hand_slot = p_slot.move(int(prepare.CARD_SIZE[0] * 3.5), 0)
                card = hand.cards.pop()
                new_hand = Hand((hand_slot.topleft[0], hand_slot.topleft[1]), [card],
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

    def tally_hands(self):
        """Calculate result of each player hand and set appropriate
        flag for each hand."""
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
        """Calculate player win amounts, update stats and return chips
        totalling total win amount."""
        cash = 0
        for hand in self.player.hands:
            bet = hand.bet.get_chip_total()
            self.casino_player.stats["Blackjack"]["hands played"] += 1
            self.casino_player.stats["Blackjack"]["total bets"] += bet
            if hand.busted:
                self.casino_player.stats["Blackjack"]["busts"] += 1
                self.casino_player.stats["Blackjack"]["hands lost"] += 1
            elif hand.loser:
                self.casino_player.stats["Blackjack"]["hands lost"] += 1
            elif hand.blackjack:
                cash += int(bet + (bet * 1.5))
                self.casino_player.stats["Blackjack"]["blackjacks"] += 1
                self.casino_player.stats["Blackjack"]["hands won"] += 1
            elif hand.winner:
                cash += bet * 2
                self.casino_player.stats["Blackjack"]["hands won"] += 1
            elif hand.push:
                cash += bet
                self.casino_player.stats["Blackjack"]["pushes"] += 1

        self.casino_player.stats["Blackjack"]["total winnings"] += cash
        chips = cash_to_chips(cash, self.chip_size)
        return chips

    def cash_out_player(self):
        """Convert player's chips to cash and update stats."""
        self.casino_player.stats["cash"] = self.player.chip_pile.get_chip_total()

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.cash_out_player()
            self.game_started = False
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            self.persist["music_handler"].get_event(event, scale)
            if self.advisor_window:
                self.advisor_window.get_event(pos)
            if self.lobby_button.rect.collidepoint(pos):
                self.cash_out_player()
                self.game_started = False
                self.done = True
                self.next = "LOBBYSCREEN"

            if self.state == "Player Turn":
                if not self.moving_cards:
                    for button in self.player_buttons:
                        if button.active and button.rect.collidepoint(pos):
                            button.payload(self.player, self.current_player_hand)
            elif self.state == "Betting":
                if not self.moving_stacks:
                    if event.button == 1:
                        if self.deal_button.rect.collidepoint(pos):
                            if any(x.bet.chips for x in self.player.hands):
                                self.state = "Dealing"
                                self.casino_player.stats["Blackjack"]["games played"] += 1
                        new_movers = self.player.chip_pile.grab_chips(pos)
                        if new_movers:
                            choice(self.chip_sounds).play()
                            self.moving_stacks.append(new_movers)
                        for hand in self.player.hands:
                            unbet_stack = hand.bet.grab_chips(pos)
                            if unbet_stack:
                                choice(self.chip_sounds).play()
                                self.player.chip_pile.add_chips(unbet_stack.chips)

            elif self.state == "Show Results":
                if event.button == 1:
                    if self.new_game_button.rect.collidepoint(pos):
                        self.new_game(self.player.chip_pile.get_chip_total())

        elif event.type == pg.MOUSEBUTTONUP:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.moving_stacks:
                if event.button == 1:
                    for stack in self.moving_stacks:
                        stack.bottomleft = pos
                        if self.chip_rack.rect.collidepoint(pos):
                            choice(self.chip_sounds).play()
                            self.player.chip_pile.add_chips(self.chip_rack.break_chips(stack.chips))
                        else:
                            self.current_player_hand.bet.add_chips(stack.chips)
                    self.moving_stacks = []
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_a and not self.advisor_window:
                test_text = "This is a test string to simulate the advice that a blackjack advisor would give. The string should be broken up into shorter lines aligned to the left."
                self.advisor_window = AdvisorWindow((700, 500), test_text)

    def update(self, surface, keys, current_time, dt, scale):
        total_text = "Chip Total:  ${}".format(self.player.chip_pile.get_chip_total())
        screen = self.screen_rect
        self.chip_total_label = Label(self.font, 48, total_text, "gold3",
                               {"bottomleft": (screen.left + 3, screen.bottom - 3)})
        mouse_pos = tools.scaled_mouse_pos(scale)
        for button in self.buttons:
            button.update(mouse_pos)
        
        self.persist["music_handler"].update(scale)
        if self.advisor_window:
            if self.advisor_window.done:
                self.advisor_window = None
        
        
        
        
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
                    self.hit(self.dealer, self.dealer.hand)
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
        self.draw(surface, dt)

    def draw(self, surface, dt):
        surface.fill(prepare.FELT_GREEN)
        self.dealer.draw_hand(surface)
        self.deck.draw(surface)
        self.chip_rack.draw(surface)
        self.player.draw(surface)
        for card in self.moving_cards:
            card.draw(surface)
        for stack in self.moving_stacks:
            stack.draw(surface)
        if self.state == "Betting":
            self.deal_button.draw(surface)
        if self.state == "Player Turn":
            for button in self.player_buttons:
                if button.active:
                    button.draw(surface)
            hand = self.current_player_hand
            rects = [x.rect for x in hand.cards]
            pg.draw.rect(
                        surface, pg.Color("gold3"),
                        hand.cards[0].rect.unionall(rects).inflate(8, 8), 3)
        if self.state == "Show Results":
            for blinker in self.result_labels:
                blinker.draw(surface, dt)
            self.new_game_button.draw(surface)
        self.lobby_button.draw(surface)
        self.persist["music_handler"].draw(surface)
        self.chip_total_label.draw(surface)
        if self.advisor_window:
            self.advisor_window.draw(surface)
