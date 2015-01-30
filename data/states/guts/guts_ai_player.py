from random import randint, choice
import pygame as pg
from ... import prepare
from ...components.labels import Label

STAY_PERCENTS = {
            "11,10": 8,
            "12,10": 14,
            "12,11": 16,
            "13,8": 20,
            "13,9": 22,
            "13,10": 24,
            "13,11": 26,
            "13,12": 28,
            "2,1": 36,
            "3,1": 39,
            "4,1": 42,
            "5,1": 46,
            "6,1": 50,
            "7,1": 54,
            "8,1": 58,
            "9,1": 62,
            "10,1": 66,
            "11,1": 70,
            "12,1": 74,
            "13,1": 78,
            "2,2": 84,
            "3,3": 86,
            "4,4": 88,
            "5,5": 90,
            "6,6": 92,
            "7,7": 94,
            "8,8": 97,
            "9,9": 100,
            "10,10": 105,
            "11,11": 110,
            "12,12": 115,
            "13,13": 120,
            "1,1": 130
            }

class AIPlayer(object):
    def __init__(self, name, orientation, hand_topleft):
        self.name = name
        self.orientation = orientation
        self.cards = []
        self.stayed = False
        self.passed = False
        self.hand_topleft = hand_topleft

        font = prepare.FONTS["Saniretro"]
        slot_rect = pg.Rect(self.hand_topleft, prepare.CARD_SIZE)
        if orientation == "left":
            name_pos = hand_topleft[0] + 60, hand_topleft[1] + 240
            db_pos = hand_topleft[0] + 170, hand_topleft[1] + 80
            self.card_slots = [slot_rect, slot_rect.move(0, 60)]
        elif orientation == "right":
            name_pos = hand_topleft[0] + 60, hand_topleft[1] + 240
            db_pos = hand_topleft[0] - 120, hand_topleft[1] + 80
            self.card_slots = [slot_rect, slot_rect.move(0, 60)] 
        else:
            name_pos = hand_topleft[0] + 90, hand_topleft[1] + 210
            db_pos = hand_topleft[0] + 60, hand_topleft[1] + 285
            self.card_slots = [slot_rect, slot_rect.move(60, 0)]
        
        self.name_label = Label(font, 48, self.name, "antiquewhite", {"center": name_pos}, bg=prepare.FELT_GREEN)
        self.name_label.image.set_alpha(100)
        center = self.name_label.rect.midbottom
        label_center = center[0], center[1] + 20
        self.stay_label = Label(font, 48, "Stayed in", "gold3", {"center": label_center}, bg=prepare.FELT_GREEN)
        self.pass_label = Label(font, 48, "Passed", "darkred", {"center": label_center}, bg=prepare.FELT_GREEN)
        self.pass_label.image.set_alpha(200)
        self.label = None
        self.dealer_button_topleft = db_pos
        self.guts = randint(-10, 20)
        self.won = 0
        self.lost = 0
        
       
    def stay(self):
        self.stayed = True
        self.label = self.stay_label
        
    def stay_out(self):
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
        
    def play_hand(self, game):
        others = [x for x in game.players if x is not self]
        stays = len([x for x in others if x.stayed])
        if game.dealer is self and stays < 1:
            self.stay()
            return
        card_vals = [card.value for card in self.cards]
        card_vals.sort(reverse=True)
        vals = "{},{}".format(*card_vals)

        if vals in STAY_PERCENTS:
            percent = STAY_PERCENTS[vals]
            percent += self.guts
            percent -= stays * 5
            risk_it = randint(1, 100)
            if risk_it < percent:
                self.stay()
            else:
                if randint(1, 100) < self.guts:
                    self.stay()
                else:
                    self.stay_out()
        else:
            risk_it = self.guts
            if stays < 1:
                if randint(1, 100) < risk_it:
                    self.stay()
                else:
                    self.stay_out()
            else:
                self.stay_out()
                    
    def draw(self, surface):
        self.name_label.draw(surface)
        for card in self.cards[::-1]:
            card.draw(surface)
        if self.label:
            self.label.draw(surface)
            
    def draw_from_deck(self, deck):
        card = deck.draw_card()
        x, y = deck.rect.center
        card.rect.center = (x + 16, y - 10)
        self.cards.append(card)
        return card
        
    def align_cards(self):
        for card in self.cards:
            center = card.rect.center
            if self.orientation == "left":
                card.rect = pg.Rect(0,0,card.rect.height, card.rect.width)
                card.image = pg.transform.rotate(card.image, -90)
                card.back_image = pg.transform.rotate(card.back_image, -90)
            elif self.orientation == "right":
                card.rect = pg.Rect(0,0,card.rect.height, card.rect.width)
                card.image = pg.transform.rotate(card.image, 90)
                card.back_image = pg.transform.rotate(card.back_image, 90)
            card.rect.center = center
            