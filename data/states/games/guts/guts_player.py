from random import choice
import pygame as pg
from data import prepare
from data.components.chips import ChipPile
from data.components.labels import Label


class GutsPlayer(object):
    fold_sounds = [prepare.SFX[x] for x in ["cardslide{}".format(num) for num in (2, 3, 4)]]
    stay_sounds = [prepare.SFX[x] for x in ["knock{}".format(num) for num in range(1, 7)]]
    def __init__(self, cash=0, chips=None):
        self.name = "YOU"
        self.cards = []
        self.cash = cash
        chip_size = prepare.CHIP_SIZE
        self.stayed = False
        self.passed = False
        font = prepare.FONTS["Saniretro"]
        label_center = (700, 820)
        self.stay_label = Label(font, 48, "Stayed in", "gold3", {"center": label_center}, bg=prepare.FELT_GREEN)
        self.pass_label = Label(font, 48, "Passed", "darkred", {"center": label_center}, bg=prepare.FELT_GREEN)
        self.name_label = Label(font, 48, self.name, "gold3", {"center": (label_center[0], label_center[1] + 60)})
        for label in [self.stay_label, self.pass_label, self.name_label]:
            label.image.set_alpha(200)
        self.label = None
        self.dealer_button_topleft = label_center[0] - 40, label_center[1] - 100
        slot_rect = pg.Rect((645, 860), prepare.CARD_SIZE)
        self.card_slots = [slot_rect, slot_rect.move(60, 0)]
        self.orientation = "bottom"
        self.won = 0
        self.lost = 0
               
    def draw_from_deck(self, deck):
        card = deck.draw_card()
        x, y = deck.rect.center
        card.rect.center = (x + 16, y - 10)
        self.cards.append(card)
        return card
    
    def flip_cards(self):
        for card in self.cards:
            card.face_up = True
            
    def draw(self, surface):
        self.draw_hand(surface)
        if self.label:
            self.label.draw(surface)
            
    def draw_hand(self, surface):
        for card in self.cards:
            card.draw(surface)
    
    def stay(self):
        if not self.stayed:
            choice(self.stay_sounds).play()
            self.stayed = True
            self.label = self.stay_label
        
    def stay_out(self):
        if not self.passed:
            choice(self.fold_sounds).play()
            self.passed = True
            self.label = self.pass_label
            self.fold()
        
    def fold(self):
        for card in self.cards:
            center = card.rect.center
            card.face_up = False
            card.image = pg.transform.rotate(card.image, -90)
            card.back_image = pg.transform.rotate(card.back_image, -90)
            card.rect = card.image.get_rect(center=center)    
        self.cards[1].rect = self.cards[0].rect        
        
    def bet(self, amount):
        self.chip_pile.withdraw_chips(amount)
        
