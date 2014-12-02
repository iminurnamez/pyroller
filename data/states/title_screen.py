import os
import json
import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, Blinker, MarqueeFrame, Button
from ..components.casino_player import CasinoPlayer
from ..components.cards import Deck

class TitleScreen(tools._State):
    """Initial state of the game. Introduecs the game and lets user load a
    saved game if there's one present."""
    
    def __init__(self):
        super(TitleScreen, self).__init__()
        self.next = "LOBBYSCREEN"
        screen_rect = pg.display.get_surface().get_rect()
        font = prepare.FONTS["Saniretro"]
        self.title = Blinker(font, 128, "Py Rollers", "darkred", 
                                   {"midtop": (screen_rect.centerx, 
                                                     screen_rect.top + 50)}, 600)
        self.title2 = Blinker(font, 128, "Casino", "darkred", 
                                    {"midtop": (screen_rect.centerx, 
                                                     self.title.rect.bottom + 120)}, 600)
        self.title.rect.left -= 1200
        self.title2.rect.left += 1600       
        self.title.blinking = False
        self.title2.blinking = False
        
        b_width = 180
        b_height = 80
        left = screen_rect.centerx - (b_width / 2)
        top = self.title2.rect.bottom + 100
        new_game = Label(font, 32, "New Game", "goldenrod3", 
                                     {"center": (0, 0)})
        self.new_game_button = Button(left, top, b_width, b_height, new_game)                                          
        self.new_game_button.active = False
        top = self.new_game_button.rect.bottom + 50
        load_game = Label(font, 32, "Load Game", "goldenrod3", 
                                         {"center": (0, 0)})
        self.load_game_button = Button(left, top, b_width, b_height, load_game)
        self.load_game_button.active = False
        self.buttons = [self.new_game_button, self.load_game_button]
        
        try:
            with open(os.path.join("resources", "save_game.json")) as saved_file:
                stats = json.load(saved_file)
        except:
            stats = None   
        self.stats = stats
        self.screen_rect = screen_rect
        self.marquees = []
        
    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.new_game_button.rect.collidepoint(event.pos):
                if self.new_game_button.active:
                    self.persist["casino_player"] = CasinoPlayer()
                    self.done = True
            elif self.load_game_button.rect.collidepoint(event.pos):
                if self.load_game_button.active:
                    self.persist["casino_player"] = CasinoPlayer(self.stats)
                    self.done = True
            
    def update(self, surface, keys, current_time, dt):       
        if self.title.rect.centerx < self.screen_rect.centerx:
            self.title.rect.left += 6
        if self.title2.rect.centerx > self.screen_rect.centerx:
            self.title2.rect.left -= 6
        else:
            if not self.marquees:
                for title in (self.title, self.title2):
                    self.marquees.append(MarqueeFrame(title))
                    title.blinking = True
                self.new_game_button.active = True
                if self.stats is not None:
                    self.load_game_button.active = True                
        for marquee in self.marquees:
            marquee.update(dt)
        self.draw(surface, dt)
        
    def draw(self, surface, dt):
        surface.fill(pg.Color("black"))
        self.title.draw(surface, dt)
        self.title2.draw(surface, dt)
        for marquee in self.marquees:
            marquee.draw(surface)
        for button in self.buttons:
            if button.active:
                button.draw(surface)