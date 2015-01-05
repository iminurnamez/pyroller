import pygame as pg
from ... import tools, prepare
from ...components.labels import Blinker, Label, Button
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

        self.bet_rect = pg.Rect(( self.rect.left + self.col_space, self.rect.top),
                                 (self.col_space, self.rect.h))
        self.bet_rect_color = pg.Color("red")

        self.build()
        
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
        pg.draw.rect(surface, self.bet_rect_color, self.bet_rect)
        pg.draw.rect(surface, self.border_color, self.rect, self.border_size)
        for label in self.table:
            label.draw(surface)
        
        for line in self.lines:
            pg.draw.line(surface, self.border_color, line[0], line[1], self.border_size)

class CardsTable:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)

        self.deck = Deck((20, 20), card_size=(200,300), infinite=True)
        self.hand = self.deck.make_hand()

        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.big_text_size = 100
        self.line_height = 35
        self.text_color = "white"
        self.big_text_color = "red"
        self.text_bg_color = "darkblue"

        
        self.text = "Play 1 to 5 coins"
        self.standby_label = Blinker(self.font, self.big_text_size, self.text, self.big_text_color,
                                      {"center":self.rect.center}, 700, self.text_bg_color)

        self.card_spacing = 50

        self.build()

    def build(self):
        x = self.rect.left
        y = self.rect.top
        for card in self.hand:
            card.rect.left = x
            card.rect.top = y
            # card.face_up = True
            x += self.card_spacing + card.rect.w

    def draw(self, surface, dt):
        for card in self.hand:
            card.draw(surface)
        self.standby_label.draw(surface, dt)


class Machine:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)
        
        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.text_color = "white"
        self.padding = 25

        self.buttons = []
        self.btn_width = self.btn_height = 100
        self.btn_padding = 40
        self.info_labels = []

        self.credits = 20
        self.coins = 1

        self.build()



    def test(self):
        print("Hello world")



    def build(self):
        x, y = self.rect.topleft
        w, h = self.rect.size

        # calculate pay board position
        x += self.padding
        y += self.padding
        w -= self.padding*2 + 150
        h = 330
        self.pay_board = PayBoard((x,y), (w,h))

        # calculate cards table position position
        y += self.padding + self.pay_board.rect.h
        h = 300
        self.cards_table = CardsTable((x,y), (w,h))

        # game info
        y += self.padding + self.cards_table.rect.h
        credit_text = 'Credit {}'.format(self.credits)
        label = Label(self.font, self.text_size, credit_text, self.text_color, 
                        {"topright": (w, y)})
        self.info_labels.append(label)
        coins_text = "Coins in {}".format(self.coins)
        label = Label(self.font, self.text_size, coins_text, self.text_color, 
                        {"topleft": (x, y)})
        self.info_labels.append(label)

        # buttons
        y += self.padding + self.btn_padding
        button_list = ['bet', 'held', 'held', 'held', 'held',
                        'held', 'bet max', 'draw']
        for text in button_list:
            label = Label(self.font, self.text_size, text, self.text_color, {})
            button = Button(x, y, self.btn_width, self.btn_height, label)
            self.buttons.append(button)
            x += self.btn_width + self.btn_padding





    def draw(self, surface, dt):
        self.pay_board.draw(surface)
        self.cards_table.draw(surface, dt)
        for label in self.info_labels:
            label.draw(surface)
        for button in self.buttons:
            button.draw(surface)


