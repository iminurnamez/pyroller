import pygame as pg
from ....components.labels import Label
from .... import prepare
from .helpers import is_winner

class RoundHistory(object):
    '''Round history showing hits per round.'''
    def __init__(self, card):
        self.rect = pg.Rect(24, 200, 304, 554)
        self.font = prepare.FONTS["Saniretro"]
        self.color = '#181818'
        self.card = card

        self.header_labels = []
        self.header_labels.extend([Label(self.font, 32, 'ROUND', 'white', {'center':(100,224)})])
        self.header_labels.extend([Label(self.font, 32, 'HITS', 'white', {'center':(280,224)})])

        self.result_labels = []

        self.round_x = 100
        self.hit_x   = 280
        self.row_y   = 224+32

        self.rounds  = 1

    def clear(self):
        self.rounds = 1
        self.result_labels = []
        self.row_y = 224+32

    def update(self, spot, hits):
        if self.rounds % 17 == 0:
            self.clear()

        color = "white"

        if is_winner(spot, hits):
            color = "gold3"

        self.result_labels.extend([Label(self.font, 32, str(self.rounds), color, {'center':(self.round_x, self.row_y)})])
        self.result_labels.extend([Label(self.font, 32, str(hits), color, {'center':(self.hit_x, self.row_y)})])
        self.row_y+=32
        self.rounds+=1

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)

        for label in self.header_labels:
            label.draw(surface)

        for label in self.result_labels:
            label.draw(surface)
