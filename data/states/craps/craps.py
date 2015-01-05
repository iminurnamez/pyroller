'''
TO DO

x set highlight positions for each bet position
- position chip placement for each bet position
- calculate payoffs for bets
- setup AI rollers and betters
- setup buttons (roll, bet, info)
- make point chip image
x dice animation

'''


from collections import OrderedDict
import pygame as pg
from ... import tools, prepare
from ...components.labels import Button, Label, FunctionButton
from . import data, dice, point_chip
import random

class Craps(tools._State):
    def __init__(self):
        super(Craps, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        topright = (self.screen_rect.right - 10, self.screen_rect.top + 10)
        b_width = 360
        b_height = 90
        self.font_size = 64
        lobby_label = Label(self.font, self.font_size, "Lobby", "gold3", {"center": (0, 0)})
        self.lobby_button = Button(
            20, self.screen_rect.bottom - (b_height + 15), b_width, b_height, lobby_label
        )
        roll_label = Label(self.font, self.font_size, "Roll", "gold3", {"center": (0, 0)})
        self.roll_button = FunctionButton(
            420, self.screen_rect.bottom - (b_height + 15),b_width, b_height, roll_label, self.roll, None
        )

        self.table_orig = prepare.GFX['craps_table']
        self.table_color = (0, 153, 51)
        self.set_table()
        self.bets = data.BETS

        self.dice = [dice.Die(self.screen_rect), dice.Die(self.screen_rect, 50)]
        self.dice_total = 0
        self.update_total_label()
        self.history = [] #[(1,1),(5,4)]
        self.dice_sounds = [
            prepare.SFX['dice_sound1'],
            prepare.SFX['dice_sound2'],
            prepare.SFX['dice_sound3'],
            prepare.SFX['dice_sound4'],
        ]
        
        self.pointchip = point_chip.PointChip()
        self.points = [4,5,6,8,9,10]
        self.point = 0 #off position

    def roll(self):
        if not self.dice[0].rolling:
            self.update_history()
            for die in self.dice:
                die.reset()
            if prepare.DEBUG:
                print(self.history)
            random.choice(self.dice_sounds).play()


    def set_table(self):
        self.table_y = (self.screen_rect.height // 4)*3
        self.table_x = self.screen_rect.width
        self.table = pg.transform.scale(self.table_orig, (self.table_x, self.table_y))
        self.table_rect = self.table.get_rect()

    def startup(self, current_time, persistent):
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]
        for die in self.dice:
            die.draw_dice = False
        self.history = []

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            #self.cash_out_player()
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            #Use tools.scaled_mouse_pos(scale, event.pos) for correct mouse
            #position relative to the pygame window size.
            event_pos = tools.scaled_mouse_pos(scale, event.pos)
            pos = tools.scaled_mouse_pos(scale, event.pos)
            self.persist["music_handler"].get_event(event, scale)
            if self.lobby_button.rect.collidepoint(pos):
                #self.cash_out_player()
                self.game_started = False
                self.done = True
                self.next = "LOBBYSCREEN"
            elif self.roll_button.rect.collidepoint(pos):
                self.roll()
        elif event.type == pg.VIDEORESIZE:
            self.set_table()

    def cash_out_player(self):
        self.casino_player.stats["cash"] = self.player.get_chip_total()

    def update_total_label(self):
        self.dice_total_label = Label(self.font, self.font_size, str(self.dice_total), "gold3", {"center": (1165, 245)})
    
    def update_history(self):
        dice = []
        for die in self.dice:
            dice.append(die.value())
        if dice[0]:
            self.history.append(dice)
        if len(self.history) > 10:
            self.history.pop(0)
            
    def set_point(self):
        if self.dice_total in self.points:
            self.point = self.dice_total
        elif self.dice_total == 7:
            self.point = 0
            
    def get_dice_total(self, current_time):
        self.dice_total = 0
        for die in self.dice:
            die.update(current_time)
            v = die.value()
            if v:
                self.dice_total += v
 
    def draw(self, surface):
        surface.fill(self.table_color)
        surface.blit(self.table, self.table_rect)
        self.lobby_button.draw(surface)
        self.roll_button.draw(surface)
        self.persist["music_handler"].draw(surface)

        for h in self.bets.keys():
            self.bets[h].draw(surface)

        for die in self.dice:
            die.draw(surface)
        if not self.dice[0].rolling and self.dice[0].draw_dice:
            self.dice_total_label.draw(surface)
        self.pointchip.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        self.persist["music_handler"].update(scale)
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.draw(surface)
        for h in self.bets.keys():
            self.bets[h].update(mouse_pos)
        self.get_dice_total(current_time)
        self.set_point()
        print(self.point)
        self.pointchip.update(current_time, self.dice_total, self.dice[0].draw_dice)
        self.update_total_label()
        #print(mouse_pos)
