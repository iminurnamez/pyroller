import pygame as pg

from data import tools, prepare
from data.components.labels import Blinker, Label, Button, MultiLineLabel
from .video_poker_dealer import Dealer
from .video_poker_data import *


class PayBoard:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)
        self.table = []
        self.lines = []

        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.line_height = 35
        self.text_color = "yellow"

        self.border_size = 5
        self. border_color = pg.Color('yellow')
        self.bg_color = pg.Color('darkblue')
        self.highlight_color = pg.Color("#000050")

        self.col_space = int(self.rect.w / 6)
        self.padding = 10

        self.bet_rect_color = pg.Color("red")
        self.bet_rect = None
        self.rank_rect = None
        self.show_bet_rect = False
        self.show_rank_rect = False

        self.rank_sound = prepare.SFX['bingo-card-success']

        self.build()

    def update_bet_rect(self, bet):
        self.bet_rect.left = self.rect.left + self.col_space * bet
        self.show_bet_rect = True

    def update_rank_rect(self, rank):
        """ 99 is the rank value for no matches"""
        if rank != NO_HAND:
            old_pos = self.rank_rect.top
            self.rank_rect.top = self.rect.top + (self.rank_rect.h * rank)
            if not self.show_rank_rect:
                self.show_rank_rect = True
            if old_pos != self.rank_rect.top:
                self.rank_sound.play()
        else:
            self.show_rank_rect = False
            self.rank_rect.top = 0

    def reset(self):
        self.show_rank_rect = False
        self.rank_rect.top = 0

    def build(self):
        x = self.rect.left + self.padding
        y = y_initial = self.rect.top
        for row in RANKS:
            label = Label(self.font, self.text_size, row, self.text_color,
                          {"topleft": (x, y)})
            self.table.append(label)
            y += self.line_height

        x += self.col_space*2 - self.padding*2
        y = y_initial
        for col in PAYTABLE:
            for row in col:
                text = str(row)
                label = Label(self.font, self.text_size, text, self.text_color,
                              {"topright": (x, y)})
                self.table.append(label)
                y += self.line_height
            x += self.col_space
            y = y_initial

        # borders between cols
        x = self.rect.left + self.col_space
        y0 = self.rect.top
        y1 = self.rect.bottom
        for i in range(5):
            line = [(x, y0), (x, y1)]
            self.lines.append(line)
            x += self.col_space

        self.rank_rect = pg.Rect((self.rect.left, self.rect.top),
                                 (self.rect.w, self.line_height))

        self.bet_rect = pg.Rect((self.rect.left, self.rect.top),
                                (self.col_space, self.rect.h))

    def draw(self, surface):
        pg.draw.rect(surface, self.bg_color, self.rect)
        if self.show_bet_rect:
            pg.draw.rect(surface, self.bet_rect_color, self.bet_rect)
        if self.show_rank_rect:
            pg.draw.rect(surface, self.highlight_color, self.rank_rect)
        pg.draw.rect(surface, self.border_color, self.rect, self.border_size)
        for label in self.table:
            label.draw(surface)

        for line in self.lines:
            pg.draw.line(surface, self.border_color, line[0], line[1], self.border_size)


class Machine:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)
        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 35
        self.text_color = "white"
        self.padding = 25
        self.btn_width = self.btn_height = 100
        self.btn_padding = 35
        self.credits_sound = prepare.SFX["bingo-pay-money"]
        self.bet_sound = prepare.SFX["bingo-pick-1"]

        self.main_buttons = []
        self.coins_button = None
        self.cash_button = None
        self.yes_no_buttons = []

        self.info_labels = []
        self.help_labels = []

        self.max_bet = 5
        self.bet_value = 1

        self.current_bet = 0
        self.last_bet = 0
        self.credits = 0

        self.win = 0
        self.state = "GAME OVER"

        self.player = None
        self.pay_board = None
        self.dealer = None

    def startup(self, player):
        self.state = "GAME OVER"
        self.current_bet = 0
        self.last_bet = 0
        self.credits = 0
        self.win = 0
        self.player = player
        self.build()
        self.dealer.startup()

    def build(self):
        x, y = self.rect.topleft
        w, h = self.rect.size

        # calculate pay board position
        x += self.padding
        y += self.padding
        w -= self.padding*2
        h = 319
        self.pay_board = PayBoard((x, y), (w, h))

        # calculate cards table position
        y += self.padding + self.pay_board.rect.h
        h = 300
        self.dealer = Dealer((x, y), (w, h))

        # buttons
        y = self.dealer.rect.bottom + self.padding*4 + self.btn_padding
        self.build_main_buttons(x, y)
        self.build_coins_button(y)
        self.build_cash_button(y)
        self.build_yes_no_buttons()

    def build_main_buttons(self, x, y):
        self.main_buttons = []

        button_list = [('bet', self.bet_one, None), ('bet max', self.bet_max, None),
                       ('hold', self.make_held, '0'), ('hold', self.make_held, '1'),
                       ('hold', self.make_held, '2'), ('hold', self.make_held, '3'),
                       ('hold', self.make_held, '4'), ('draw', self.draw_cards, None)]

        settings = {"fill_color": pg.Color("#222222"),
                    "font": self.font,
                    "font_size": 25,
                    "hover_text_color": pg.Color("white"),
                    "disable_text_color": pg.Color("#cccccc"),
                    "hover_fill_color": pg.Color("#353535"),
                    "disable_fill_color": pg.Color("#999999"),
                    "active": False}

        for text, func, args in button_list:
            rect_style = (x, y, self.btn_width, self.btn_height)
            settings.update({'text': text, 'hover_text': text,
                            'disable_text': text, 'call': func, 'args': args})
            button = Button(rect_style, **settings)
            self.main_buttons.append(button)
            x += self.btn_width + self.btn_padding

    def build_coins_button(self, y):
        settings = {"text": "Insert coin",
                    "hover_text": "Insert coin",
                    "fill_color": pg.Color("gold"),
                    "font": self.font,
                    "font_size": self.text_size,
                    "text_color": pg.Color("#333333"),
                    "hover_text_color": pg.Color("#333333"),
                    "disable_text_color": pg.Color("#cccccc"),
                    "hover_fill_color": pg.Color("yellow"),
                    "disable_fill_color": pg.Color("#999999"),
                    "call": self.insert_coin}

        rect_style = ((self.rect.right + self.padding), y, 200, 60,)
        self.coins_button = Button(rect_style, **settings)

    def build_cash_button(self, y):
        settings = {"text": "Cash out",
                    "hover_text": "Cash out",
                    "fill_color": pg.Color("gold"),
                    "font": self.font,
                    "font_size": self.text_size,
                    "text_color": pg.Color("#333333"),
                    "hover_text_color": pg.Color("#333333"),
                    "disable_text_color": pg.Color("#cccccc"),
                    "hover_fill_color": pg.Color("yellow"),
                    "disable_fill_color": pg.Color("#999999"),
                    "call": self.cash_out}

        rect_style = ((self.rect.right + self.padding), (y - 300), 200, 60,)
        self.cash_button = Button(rect_style, **settings)

    def build_yes_no_buttons(self):
        self.yes_no_buttons = []
        from_center = 125
        settings = {"text": "Yes",
                    "hover_text": "Yes",
                    "font": self.font,
                    "font_size": 80,
                    "text_color": pg.Color("white"),
                    "hover_text_color": pg.Color("white"),
                    "fill_color": pg.Color("#0000c3"),
                    "hover_fill_color": pg.Color("blue"),
                    "call": self.check_double_up,
                    "args": (True,),
                    "bindings": [pg.K_y]}
        rect_style = (0, 0, 200, 100)
        button = Button(rect_style, **settings)
        button.rect.centerx = self.dealer.rect.centerx - from_center
        button.rect.centery = self.dealer.rect.centery
        self.yes_no_buttons.append(button)

        settings.update({'text': 'No',
                         'hover_text': 'No',
                         'call': self.check_double_up,
                         'args': (False,),
                         "bindings": [pg.K_n]})
        rect_style = (0, 0, 200, 100)
        button = Button(rect_style, **settings)
        button.rect.centerx = self.dealer.rect.centerx + from_center
        button.rect.centery = self.dealer.rect.centery
        self.yes_no_buttons.append(button)

    def make_help_labels(self, rect):
        labels = []
        text = "Double up ?"
        label = Blinker(self.font, 100, text, "red",
                        {"centerx": rect.centerx, "top": rect.top}, 700)
        labels.append(label)
        text = "If selected card beats dealers, player wins. Ace is highest, two is lowest"
        label = MultiLineLabel(self.font, self.text_size, text,
                               self.text_color, {"center": rect.center}, align="center")
        labels.append(label)

        return labels

    def make_info_label(self, rect):
        labels = []
        y = rect.bottom + self.padding
        if self.state == "WON" or self.state == "DOUBLE UP":
            text = "you have won: {} double up to: {}".format(self.win, self.win*2)
            label = MultiLineLabel(self.font, 35, text, self.text_color,
                                   {"centerx": rect.centerx, "top": y},
                                   char_limit=20, align="center")
            labels.append(label)
        else:
            if self.state == "GAME OVER":
                if self.win > 0:
                    text = 'you win {}'.format(self.win)
                    label = Label(self.font, self.text_size, text,
                                  self.text_color,
                                  {"centerx": rect.centerx, "top": y})
                    labels.append(label)
                elif self.current_bet == 0:
                    text = "game over"
                    label = Label(self.font, self.text_size, text,
                                  self.text_color,
                                  {"centerx": rect.centerx, "top": y})
                    labels.append(label)

        text = 'Credits {}'.format(self.credits)
        label = Label(self.font, self.text_size, text, self.text_color,
                      {"topright": (rect.right, y)})
        labels.append(label)
        coins_text = "Current Bet {}".format(self.current_bet)
        label = Label(self.font, self.text_size, coins_text, self.text_color,
                      {"topleft": (rect.x, y)})
        labels.append(label)

        balance = 'Balance: ${}'.format(self.player.cash)
        pos = ((self.rect.right + self.padding), (self.rect.top + 300))
        label = Label(self.font, 50, balance, self.text_color,
                      {"topleft": pos})
        labels.append(label)

        return labels

    def insert_coin(self, *args):
        if self.state == "GAME OVER":
            self.start_waiting()
            self.credits += self.bet_value
            self.player.cash -= self.bet_value
            self.credits_sound.play()

    def start_waiting(self):
        self.dealer.playing = True
        self.dealer.waiting = True

    def cash_out(self, *args):
        total_credits = self.credits
        self.credits = 0

        if self.state == "GAME OVER":
            total_credits += self.current_bet
            self.current_bet = 0

        self.player.cash += total_credits
        for _ in range(total_credits):
            self.credits_sound.play()

    def toggle_buttons(self, buttons, active=True):
        for button in buttons:
                button.active = active

    def bet_one(self, *args):
        if self.credits > 0 and self.current_bet < self.max_bet:
            self.current_bet += 1
            self.credits -= 1
            self.bet_sound.play()
        elif self.current_bet > 1:
            self.credits += self.current_bet - 1
            self.current_bet = 1
            self.bet_sound.play()
        self.pay_board.update_bet_rect(self.current_bet)
        self.main_buttons[-1].active = True  # draw button

    def bet_max(self, *args):
        if self.credits > 0:
            if self.credits >= (self.max_bet - self.current_bet):
                aux = self.max_bet - self.current_bet
                self.current_bet += aux
                self.credits -= aux
            else:
                self.current_bet += self.credits
                self.credits = 0
            self.bet_sound.play()
            self.draw_cards()
        self.pay_board.update_bet_rect(self.current_bet)
        self.main_buttons[-1].active = True  # draw button

    def make_last_bet(self):
        """ """
        if self.credits > 0:
            if self.credits >= self.last_bet:
                self.current_bet = self.last_bet
                self.credits -= self.last_bet
            else:
                self.current_bet = self.credits
                self.credits = 0
        self.pay_board.update_bet_rect(self.current_bet)

    def new_game(self):
        self.state = "PLAYING"
        self.dealer.startup()
        self.dealer.playing = True
        self.dealer.waiting = False
        self.win = 0
        self.player.increase('games played')

        if self.current_bet == 0 and self.last_bet > 0:
            self.make_last_bet()

        self.player.increase('total wagered', self.current_bet)
        self.dealer.draw_cards()
        rank = self.dealer.evaluate_hand()
        self.pay_board.update_rank_rect(rank)

        for button in self.main_buttons:
            button.active = True
        # bet and bet max buttons
        self.toggle_buttons((self.main_buttons[0], self.main_buttons[1]), False)

    def evaluate_final_hand(self):
        self.dealer.draw_cards()
        rank = self.dealer.evaluate_hand()
        self.pay_board.update_rank_rect(rank)
        if rank != NO_HAND:
            index = self.current_bet - 1
            self.win = PAYTABLE[index][rank]
            self.help_labels = self.make_help_labels(self.pay_board.rect)
            self.player.increase('games won')
            self.state = "WON"
        else:
            self.player.increase('games lost')
            self.player.increase('total lost', self.current_bet)
            self.state = "GAME OVER"
            self.start_waiting()

        self.last_bet = self.current_bet
        self.current_bet = 0

    def draw_cards(self, *args):
        if self.current_bet > 0 or self.last_bet > 0:
            if self.state == "GAME OVER":
                self.pay_board.reset()
                self.new_game()
            elif self.state == "PLAYING":
                self.evaluate_final_hand()

    def make_held(self, *args):
        """ Some unknown issue with 0 Int args,
            so Str values passed to the func and
            here are converted to Int"""
        index = int(args[0])
        if self.state == "PLAYING":
            self.dealer.toggle_held(index)

        elif self.state == "DOUBLE UP":
            if index > 0:  # if is not the first card
                win = self.dealer.select_card(index)
                self.dealer.draw_cards()
                if win:
                    self.win *= 2
                    self.player.increase('double ups won')
                    self.state = "WON"
                    self.pay_board.rank_sound.play()
                else:
                    self.win = 0
                    self.player.increase('double ups lost')
                    # Use last_bet because it has already been updated to the bet from the current hand
                    self.player.increase('total lost', self.last_bet)
                    self.state = "GAME OVER"
                    self.start_waiting()

    def check_double_up(self, *args):
        double_up = args[0][0]
        if double_up:
            self.help_labels = self.make_help_labels(self.pay_board.rect)
            self.dealer.start_double_up()
            self.state = "DOUBLE UP"
            self.dealer.double_up = True
        else:
            self.credits += self.win
            self.player.increase('total won', self.win)
            self.state = "GAME OVER"
            self.start_waiting()

    def get_event(self, event, scale):
        self.coins_button.get_event(event)
        self.cash_button.get_event(event)
        for button in self.main_buttons:
            button.get_event(event)
        if self.state == "WON":
            for button in self.yes_no_buttons:
                button.get_event(event)

        if event.type == pg.MOUSEBUTTONDOWN:
            if self.state == "PLAYING" or self.state == "DOUBLE UP":
                mouse_pos = tools.scaled_mouse_pos(scale)
                index = self.dealer.get_event(mouse_pos)
                if type(index) == int:
                    self.make_held(str(index))  # Little hack

    def update(self, mouse_pos, dt):
        self.info_labels = self.make_info_label(self.dealer.rect)

        if self.state == "GAME OVER":
            if self.credits == 0:
                if self.current_bet == 0:
                    # Turn all the buttons off
                    self.toggle_buttons(self.main_buttons, False)
                    self.dealer.playing = False
                elif self.current_bet == 1:
                    # Turn everything except Draw off
                    self.toggle_buttons(self.main_buttons[0:-1], False)
                    # Turn Draw on
                    self.toggle_buttons([self.main_buttons[-1]])
                else:
                    # Turn everything except Draw and Bet One off
                    self.toggle_buttons(self.main_buttons[1:-1], False)
                    # Turn Bet On and Draw on
                    self.toggle_buttons([self.main_buttons[0], self.main_buttons[-1]])
            else:
                if self.current_bet > 0 or self.last_bet > 0:
                    # Turn on Bet, Bet Max and Draw Buttons
                    self.toggle_buttons([self.main_buttons[0],
                                        self.main_buttons[1],
                                        self.main_buttons[-1]])
                    # Turn other buttons off
                    self.toggle_buttons(self.main_buttons[2:-1], False)
                else:
                    # Turn on Bet and Bet Max
                    self.toggle_buttons(self.main_buttons[0:2])
                    # Turn other buttons off
                    self.toggle_buttons(self.main_buttons[2:], False)

        self.dealer.update(dt)

        if self.state == "WON":
            for button in self.yes_no_buttons:
                button.update(mouse_pos)
        if self.state == "WON" or self.state == "DOUBLE UP":
            for label in self.help_labels:
                if isinstance(label, Blinker):
                    label.update(dt)
            self.main_buttons[-1].active = False

        self.coins_button.update(mouse_pos)
        self.cash_button.update(mouse_pos)
        for button in self.main_buttons:
            button.update(mouse_pos)

    def draw(self, surface):
        self.dealer.draw(surface)
        for label in self.info_labels:
            label.draw(surface)
        for button in self.main_buttons:
            button.draw(surface)
        self.coins_button.draw(surface)
        self.cash_button.draw(surface)
        if self.state == "WON":
            for button in self.yes_no_buttons:
                button.draw(surface)
        if self.state == "WON" or self.state == "DOUBLE UP":
            for label in self.help_labels:
                label.draw(surface)
        else:
            self.pay_board.draw(surface)
