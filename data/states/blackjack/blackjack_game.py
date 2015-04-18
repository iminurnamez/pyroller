import pygame as pg
from ... import prepare
from ...components.labels import Button
from ...components.cards import Deck
from ...components.chips import ChipStack, ChipRack, cash_to_chips, chips_to_cash
from ...components.advisor import Advisor
from ...components.labels import Label
from .blackjack_dealer import Dealer
from .blackjack_player import Player
from .blackjack_hand import Hand


class BlackjackGame(object):
    """Represents a single game of blackjack."""
    draw_group = pg.sprite.Group()
    move_animations = pg.sprite.Group()
    advisor = Advisor(draw_group, move_animations)
    advisor.active = True
    advisor_back = prepare.GFX["advisor_back"]
    advisor_front = prepare.GFX["advisor_front"]
    advisor_back_dim = prepare.GFX["advisor_back_dim"]
    advisor_front_dim = prepare.GFX["advisor_front_dim"]
    font = prepare.FONTS["Saniretro"]
    result_font = prepare.FONTS["Saniretro"]
    deal_sounds = [prepare.SFX[name] for name in ["cardplace{}".format(x) for x in (2, 3, 4)]]
    chip_sounds = [prepare.SFX[name] for name in ["chipsstack{}".format(x) for x in (3, 5, 6)]]
    chip_size = (48, 30)
    screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
    advisor_active = True
    
    def __init__(self, casino_player, player_cash, chips=None, chip_pile=None):
        self.deck = Deck((20, 100), prepare.CARD_SIZE, 40)
        self.dealer = Dealer()
        self.chip_rack = ChipRack((1100, 130), self.chip_size)
        self.moving_stacks = []
        self.casino_player = casino_player
        self.player = Player(self.chip_size, player_cash, chips, chip_pile)
        self.labels = self.make_labels()
        self.current_player_hand = self.player.hands[0] 
        self.quick_bet = 0
        self.last_bet = 0   
        rect = self.advisor_back.get_rect().union(self.advisor_front.get_rect())
        self.advisor_button = Button(rect, call=self.toggle_advisor)
        
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
        
    def toggle_advisor(self, *args):
        BlackjackGame.advisor_active = not BlackjackGame.advisor_active
        
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
                cash += int(bet * 2.5)
                self.casino_player.increase("blackjacks")
                self.casino_player.increase("hands won")
            elif hand.winner:
                cash += bet * 2
                self.casino_player.increase("hands won")
            elif hand.push:
                cash += bet
                self.casino_player.increase("pushes")

        self.casino_player.increase("total winnings",  cash)
        chips = cash_to_chips(cash, self.chip_size)
        return chips
        
    def get_event(self, event):
        self.advisor_button.get_event(event)
        
    def update(self, dt, mouse_pos):
        self.advisor_button.update(mouse_pos)
        total_text = "Chip Total:  ${}".format(self.player.chip_pile.get_chip_total())
        screen = self.screen_rect
        self.chip_total_label = Label(self.font, 48, total_text, "gold3",
                               {"bottomleft": (screen.left + 3, screen.bottom - 3)})
        self.chip_rack.update()
        if self.advisor_active:
            self.move_animations.update(dt)