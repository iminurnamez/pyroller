import pygame as pg

from data.components.labels import Label
from data import prepare
from .helpers import PAYTABLE


class PayTable(object):
    '''Paytable readout for desired spot count'''
    def __init__(self, card):
        self.rect = pg.Rect(1036, 200, 340, 554)
        self.font = prepare.FONTS["Saniretro"]
        self.color = '#181818'
        self.card = card

        self.header_labels = []
        self.header_labels.extend([Label(self.font, 32, 'HIT', 'white', {'center':(1080,224)})])
        self.header_labels.extend([Label(self.font, 32, 'WIN', 'white', {'center':(1280,224)})])

        self.pay_labels = []

    def update(self, spot, bet=1):
        self.pay_labels = []
        row = PAYTABLE[spot]
        hit_x = 1080
        win_x = 1280
        row_y = 224+32
        for entry in row:
            hit, win = entry
            win *= bet
            self.pay_labels.extend([Label(self.font, 32, str(hit), 'white', {'center':(hit_x, row_y)})])
            self.pay_labels.extend([Label(self.font, 32, str(win), 'white', {'center':(win_x, row_y)})])
            row_y+=32


    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)

        for label in self.header_labels:
            label.draw(surface)

        for label in self.pay_labels:
            label.draw(surface)
