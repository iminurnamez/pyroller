import pygame as pg
from ... import tools, prepare
from ...components.labels import Blinker, Label, FunctionButton, _Button
from ...components.cards import Deck

PAYTABLE = [
    (800, 50, 25, 8, 6, 4, 3, 2, 1),
    (1600, 100, 50, 16, 12, 8, 6, 4, 2),
    (2400, 150, 75, 24, 18, 12, 9, 6, 3),
    (3200, 200, 100, 32, 24, 16, 12, 8, 4),
    (4000, 250, 125, 40, 30, 20, 15, 10, 5),
]

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
        self. border_color =pg.Color('gold')
        self.bg_color = pg.Color('darkblue')

        self.col_space = int(self.rect.w / 6)
        self.padding = 10

        self.bet_rect = pg.Rect(( self.rect.left, self.rect.top),
                                 (self.col_space, self.rect.h))
        self.bet_rect_color = pg.Color("red")
        self.show_bet_rect = False


        self.build()

    def update_bet_rect(self, bet):
        self.bet_rect.left = self.rect.left + self.col_space * bet
        self.show_bet_rect = True
        
    def build(self):
        info_col = ('ROYAL FLUSH', 'STR. FLUSH', '4 OF A KIND', 'FULL HOUSE',
        'FLUSH','STRAIGHT', 'THREE OF A KIND', 'TWO PAIR', 'JACKS OR BETTER')
        x = x_initial = self.rect.left + self.padding
        y = y_initial = self.rect.top + self.padding
        for row in info_col:
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


    def draw(self, surface):
        pg.draw.rect(surface, self.bg_color, self.rect)
        if self.show_bet_rect:
            pg.draw.rect(surface, self.bet_rect_color, self.bet_rect)
        pg.draw.rect(surface, self.border_color, self.rect, self.border_size)
        for label in self.table:
            label.draw(surface)
        
        for line in self.lines:
            pg.draw.line(surface, self.border_color, line[0], line[1], self.border_size)

class Dealer:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)

        self.deck = Deck((20, 20), card_size=(187, 271), infinite=True)

        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.big_text_size = 100
        self.line_height = 35
        self.text_color = "white"
        self.big_text_color = "red"
        self.text_bg_color = "darkblue"

        self.held_labels = []
        

        
        self.text = " insert coins "
        self.standby_label = Blinker(self.font, self.big_text_size, self.text, self.big_text_color,
                                      {"center":self.rect.center}, 700, self.text_bg_color)

        self.text = " play 1 to 5 coins "
        self.help_text = Blinker(self.font, self.big_text_size, self.text, self.big_text_color,
                                      {"center":self.rect.center}, 700, self.text_bg_color)

        self.card_spacing = 30

        self.animation_speed = 170.0
        self.elapsed = self.animation_speed

        self.deal_sound = prepare.SFX["cardplace2"]
        self.held_sound = prepare.SFX["bingo-speed-up"]


    def startup(self):
        self.hand = self.deck.make_hand()
        self.hand_len = len(self.hand)
        self.build()
        self.standby = True
        self.card_index = 0
        self.max_cards = len(self.hand)
        self.revealing = False
        self.held_cards = []
        self.changing_cards = list(range(5))
        self.ready2play = False

    def draw_cards(self):
        for index in range(self.hand_len):
            if index not in self.held_cards:
                self.hand[index] = self.deck.draw_card()
        self.build()
        self.revealing = True

    def build(self):
        x = self.rect.left
        y = self.rect.top  + self.line_height
        for card in self.hand:
            card.rect.left = x
            card.rect.top = y
            label = Label(self.font, self.text_size, 'held', self.text_color,
                                {"bottom":card.rect.top, "centerx":card.rect.centerx})
            self.held_labels.append(label)
            x += self.card_spacing + card.rect.w



    def face_up_cards(self):
        for card in self.hand:
            card.face_up = True

    def toogle_held(self, index):
        if index in self.held_cards:
            self.held_cards.remove(index)
            self.changing_cards.append(index)
        else:
            self.held_cards.append(index)
            self.changing_cards.remove(index)        
        self.held_sound.play()
        self.changing_cards.sort()


    def get_event(self, playing, mouse_pos):
        if playing:
            for index, card in enumerate(self.hand):
                if card.rect.collidepoint(mouse_pos):
                    self.toogle_held(index)

    def update(self, playing, ready2play, dt):
        if playing:
            self.ready2play = ready2play
            if self.revealing:
                self.elapsed += dt
                while self.elapsed >= self.animation_speed:
                    self.elapsed -= self.animation_speed
                    index = self.changing_cards[self.card_index]
                    self.hand[index].face_up = True
                    self.deal_sound.play()
                    self.card_index += 1
                    if self.card_index >= len(self.changing_cards):
                        self.card_index = 0
                        self.revealing = False
            self.standby = False
        else:
            self.standby = True


    def draw(self, surface, dt):
        for card in self.hand:
            card.draw(surface)
        for index in self.held_cards:
            self.held_labels[index].draw(surface)
        if self.standby:
            self.standby_label.draw(surface, dt)
        elif not self.ready2play:
            self.help_text.draw(surface, dt)


class Machine:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)
        
        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.text_color = "white"
        self.padding = 25

        self.buttons = []
        self.btn_width = self.btn_height = 100
        self.btn_padding = 35
        self.info_labels = []

        self.max_bet = 5
        


    def startup(self):
        self.playing = False
        self.ready2play = False
        self.bet = 0
        self.credits = 0
        self.coins = 0
        self.build()
        self.dealer.startup()


    def build(self):
        x, y = self.rect.topleft
        w, h = self.rect.size

        # calculate pay board position
        x += self.padding
        y += self.padding
        w -= self.padding*2
        h = 330

        self.pay_board = PayBoard((x,y), (w,h))

        # use in info labels
        self.label_x1 = x 
        self.label_x2 = w

        # calculate cards table position position
        y += self.padding + self.pay_board.rect.h
        h = 300
        self.dealer = Dealer((x,y), (w,h))

        y = self.dealer.rect.bottom + self.padding*2
        self.label_y = y # use in info labels

        # buttons
        y += self.padding + self.btn_padding
        button_list = [
            ('bet', self.bet_one, None), ('bet max', self.bet_max, None),
            ('held', self.make_held, '0'), ('held', self.make_held, '1'), 
            ('held', self.make_held, '2'), ('held', self.make_held, '3'), 
            ('held', self.make_held, '4'), ('draw', self.draw_cards, None)]
        settings = {
            "fill_color"         : pg.Color("#222222"),
            "font"               : self.font,
            "font_size"          : 25,
            "hover_text_color"   : pg.Color("white"),
            "disable_text_color" : pg.Color("#cccccc"),
            "hover_fill_color"   : pg.Color("#353535"),
            "disable_fill_color" : pg.Color("#999999"),
            "active"             : True}
        for text, func, args in button_list:
            rect_style = (x, y, self.btn_width, self.btn_height)            
            settings.update({'text':text, 'hover_text':text, 'disable_text':text, 
                                                        'call':func, 'args':args})
            button = _Button(rect_style, **settings)
            self.buttons.append(button)
            x += self.btn_width + self.btn_padding


        label = Label(self.font, self.text_size, 'get credits', self.text_color, {})
        self.play_button = FunctionButton(self.rect.right + self.padding, y, 
                                            200, 60, label, self.insert_coin, None)
        
        self.credits_sound = prepare.SFX["bingo-pay-money"]
        self.bet_sound = prepare.SFX["bingo-pick-1"]
        


    def insert_coin(self):
        self.playing = True
        self.credits += 1
        # bet and bet max buttons
        self.buttons[0].active = True
        self.buttons[1].active = True
        self.credits_sound.play()


    def bet_one(self, *args):
        if self.credits > 0:
            if self.bet < self.max_bet:
                self.bet += 1
                if self.coins < self.max_bet:
                    self.coins += 1
                else:
                    self.coins = 1
                self.credits -= 1
            else:
                self.bet = 1
                self.coins = 1
                self.credits += 4
            self.ready2play = True
            self.bet_sound.play()
        self.pay_board.update_bet_rect(self.coins)
        # draw button
        self.buttons[-1].active = True

    
    def bet_max(self, *args):
        if self.credits > 0:
            if self.credits >= self.max_bet:
                aux = self.max_bet - self.coins
                self.bet += aux
                self.coins += aux
                self.credits -= aux
            else:
                self.bet += self.credits
                self.coins += self.credits
                self.credits = 0
            self.ready2play = True
            self.bet_sound.play()
            self.draw_cards()
        self.pay_board.update_bet_rect(self.coins)
        # draw button
        self.buttons[-1].active = True

    
    def make_last_bet(self):
        """ """
        if self.credits > 0:
            if self.credits >= self.coins:
                self.bet = self.coins
                self.credits -= self.bet            
                self.bet = 0
            else:
                self.bet = self.credits
                self.coins = self.credits
                self.credits = 0
            self.ready2play = True
            self.pay_board.update_bet_rect(self.coins)

    
    def draw_cards(self, *args):
        if self.bet > 0:
            self.dealer.draw_cards()
            self.bet = 0
        else:
            if self.coins > 0:
                self.make_last_bet()
                self.dealer.draw_cards()
                self.bet = 0
        for button in self.buttons:
            button.active = True
        # bet and bet max buttons
        self.buttons[0].active = False
        self.buttons[1].active = False


    def make_held(self, *args):
        """ Some unkonow issue with Int args, 
            so Str values passed to the func and
            here are converter tonn Int"""
        index = int(args[0])
        self.dealer.toogle_held(index)
    



    def get_event(self, event, scale):
        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_pos = tools.scaled_mouse_pos(scale)
            self.dealer.get_event(self.playing, mouse_pos)
            self.play_button.get_event(mouse_pos)
        for button in self.buttons:
            button.get_event(event)

    def update(self, mouse_pos, dt):
        # game info labels
        self.info_labels = []
        credit_text = 'Credit {}'.format(self.credits)
        label = Label(self.font, self.text_size, credit_text, self.text_color, 
                        {"topright": (self.label_x2, self.label_y)})
        self.info_labels.append(label)
        coins_text = "Coins in {}".format(self.coins)
        label = Label(self.font, self.text_size, coins_text, self.text_color, 
                        {"topleft": (self.label_x1, self.label_y)})
        self.info_labels.append(label)


        if self.credits == 0:
            self.playing = False
            for button in self.buttons:
                button.active = False

        
        if self.bet == 0:
            self.ready2play = False

        self.dealer.update(self.playing, self.ready2play, dt)

        for button in self.buttons:
            button.update(mouse_pos)

    def draw(self, surface, dt):
        self.pay_board.draw(surface)
        self.dealer.draw(surface, dt)
        for label in self.info_labels:
            label.draw(surface)
        for button in self.buttons:
            button.draw(surface)
        self.play_button.draw(surface)


