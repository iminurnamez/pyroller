import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, Button, PayloadButton
import os, json

class StatsMenu(tools._State):
    """This state allows the player to choose which game's stats they
    want to view or return to the lobby."""
    def __init__(self):
        super(StatsMenu, self).__init__()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.title = Label(self.font, 64, "Statistics", "darkred",
                                 {"midtop": (screen_rect.centerx, screen_rect.top + 10)})
        self.games = ["Blackjack", "Bingo", "Craps"]
        b_width = 180
        b_height = 80
        left = screen_rect.centerx - (b_width / 2)
        top = self.title.rect.bottom + 50
        self.game_buttons = []
        for game in self.games:
            label = Label(self.font, 48, game, "gold3", {"center": (0, 0)})
            button = PayloadButton(left, top, b_width, b_height, label, game)
            self.game_buttons.append(button)
            top += button.rect.height + 20
        done_label = Label(self.font, 48, "Lobby", "gold4", {"center": (0, 0)})
        self.done_button = Button(left, screen_rect.bottom - (b_height + 10),
                                                b_width, b_height, done_label)
        rebuy_label = Label(self.font, 48, "Rebuy", "gold3", {"center": (0, 0)})
        self.rebuy_button = Button(left,
                                                screen_rect.bottom - ((b_height + 20) * 3),
                                                b_width, b_height, rebuy_label)

    def startup(self, current_time, persistent):
        self.start_time = current_time
        self.persist = persistent
        self.player = self.persist["casino_player"]
        #try:
        with open(os.path.join("resources", "save_game.json")) as saved_file:
            stats = json.load(saved_file)
            print "cash: {}. Buy-ins: {}".format(stats['cash'], stats['rebuys'])
            self.stats = stats

    def rebuy(self):
        self.player.stats["cash"] += 1000
        self.player.stats["rebuys"] +=1
        with open(os.path.join("resources", "save_game.json"), "w") as f:
            json.dump(self.persist["casino_player"].stats, f)

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.done_button.rect.collidepoint(pos):
                self.done = True
                self.next = "LOBBYSCREEN"
            elif self.rebuy_button.rect.collidepoint(pos):
                if not self.player:
                    self.player = self.persist["casino_player"]
                self.rebuy()
                self.done = True
                self.next = "TITLESCREEN"
            for button in self.game_buttons:
                if button.rect.collidepoint(pos):
                    self.persist["current_game_stats"] = button.payload
                    self.next = "STATSSCREEN"
                    self.done = True

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        self.title.draw(surface)
        for button in self.game_buttons:
            button.draw(surface)
        self.done_button.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        self.draw(surface)
        self.rebuy_button.draw(surface)
