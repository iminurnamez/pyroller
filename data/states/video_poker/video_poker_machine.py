import pygame as pg
from ... import tools, prepare
from ...components.labels import Blinker, Label

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
        self.font = prepare.FONTS["Saniretro"]
        self.text_size = 30
        self.line_height = 35
        self.text_color = "yellow"
        self.border_size = 3
        self.col_space = int(self.rect.w / 6) # the first col is colspan 2
        self.padding = 10

        self.build()

        print self.rect.w
        print self.col_space
        
    def build(self):
        info_col = ('ROYAL FLUSH', 'STR. FLUSH', '4 OF A KIND', 'FULL HOUSE',
        'FLUSH','STRAIGHT', 'THREE OF A KIND', 'TWO PAIR', 'JACKS OR BETTER')
        x = self.rect.left + self.padding
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



    def draw(self, surface):
        pg.draw.rect(surface, pg.Color('blue'), self.rect)
        pg.draw.rect(surface, pg.Color('gold'), self.rect, self.border_size)
        for label in self.table:
            label.draw(surface)

class Machine:
    def __init__(self, topleft, size):
        self.rect = pg.Rect(topleft, size)
        self.font = prepare.FONTS["Saniretro"]
        self.padding = 20
        x, y = topleft
        w, h = size
        x += self.padding
        y += self.padding
        w -= self.padding*2
        h = 330

        self.board = PayBoard((x,y), (w,h))


    def draw(self, surface):
        self.board.draw(surface)


