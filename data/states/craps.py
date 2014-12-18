'''
TO DO

- set highlight positions for each bet position
- position chip placement for each bet position
- calculate payoffs for bets
- setup AI rollers and betters
- setup buttons (roll, bet, info)
- make point chip image
- dice animation

'''


from collections import OrderedDict
import pygame as pg
from .. import tools, prepare
from ..components.labels import Button, Label
from ..components.craps_bet import Bet



class Craps(tools._State):
    """Class to represent a casino game."""
    def __init__(self):
        super(Craps, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.font = prepare.FONTS["Saniretro"]
        self.music_icon = prepare.GFX["speaker"]
        topright = (self.screen_rect.right - 10, self.screen_rect.top + 10)
        b_width = 360
        b_height = 90
        font_size = 64
        lobby_label = Label(self.font, font_size, "Lobby", "gold3", {"center": (0, 0)})
        self.lobby_button = Button(20, self.screen_rect.bottom - (b_height + 15),
                                                 b_width, b_height, lobby_label)
        self.music_icon_rect = self.music_icon.get_rect(topright=topright)
        self.mute_icon = prepare.GFX["mute"]
        self.play_music = True
        
        self.table_orig = prepare.GFX['craps_table']
        self.table_color = (0, 153, 51)
        self.set_table()
        
        
        all_rolls = list(range(2,13))
        self.bets = {
        
            #name: Bet(highlighter_size, highlighter_topleft, display_name, payoff)

            'come'          :Bet((652,120),(178,252), 'Come',           {'1/1':all_rolls}),
            'field'         :Bet((542,117),(288,373), 'Field',          {'1/1':[3,4,9,10,11], '2/1':[2,12]}),
            'dont_pass'     :Bet((542,65),(288,493), 'Dont\'t Pass',    {'1/1':all_rolls}),
            'pass'          :Bet((662,65),(170,570), 'Pass',            {'1/1':all_rolls}),
            'dont_come'     :Bet((100,190),(180,53), 'Dont\'t Come',    {'1/1':all_rolls}),
            'any_seven'     :Bet((388,45),(964,295), 'Any Seven',       {'5/1':all_rolls}),
            'hard_6'        :Bet((194,80),(964,342), 'Hard 6',          {'10/1':all_rolls}),
            'hard_10'       :Bet((194,80),(1161,342), 'Hard 10',        {'8/1':all_rolls}),
            'hard_4'        :Bet((194,80),(1161,431), 'Hard 4',         {'8/1':all_rolls}),
            'hard_8'        :Bet((194,80),(965,431), 'Hard 8',          {'10/1':all_rolls}),
            'size_five'     :Bet((194,80),(965,603), 'Siz Five',        {'16/1':all_rolls}),
            'ace_deuce'     :Bet((194,80),(1161,603), 'Ace Deuce',      {'16/1':all_rolls}),
            'aces'          :Bet((194,80),(965,517), 'Aces',            {'31/1':all_rolls}),
            'two_sixes'     :Bet((194,80),(1161,517), 'Two Sixes',      {'31/1':all_rolls}),
            'any_craps'     :Bet((388,45),(964,689), 'Any Seven',       {'8/1':all_rolls}),
            'big 6'         :Bet((67,125),(113,371), 'Big 6',           {'1/1':all_rolls}),
            'big 8'         :Bet((105,67),(179,497), 'Big 8',           {'1/1':all_rolls}),
            'place_lose_4'  :Bet((106,15),(288,53), 'Place Lose 4',     {'5/11':all_rolls}),
            'lay_4'         :Bet((106,15),(288,75), 'Lay 4',            {'1/1':all_rolls}),
            'buy_4'         :Bet((106,15),(288,206), 'Buy 4',           {'1/1':all_rolls}),
            'place_win_4'   :Bet((106,15),(288,229), 'Place Win 4',     {'9/5':all_rolls}),
            'place_lose_5'  :Bet((106,15),(396,53), 'Place Lose 5',     {'4/6':all_rolls}),
            'lay_5'         :Bet((106,15),(396,75), 'Lay 5',            {'1/1':all_rolls}),
            'buy_5'         :Bet((106,15),(396,206), 'Buy 5',           {'1/1':all_rolls}),
            'place_win_5'   :Bet((106,15),(396,229), 'Place Win 5',     {'7/6':all_rolls}),
            'place_lose_6'  :Bet((106,15),(506,53), 'Place Lose 6',     {'4/6':all_rolls}),
            'lay_6'         :Bet((106,15),(506,75), 'Lay 6',            {'1/1':all_rolls}),
            'buy_6'         :Bet((106,15),(506,206), 'Buy 6',           {'1/1':all_rolls}),
            'place_win_6'   :Bet((106,15),(506,229), 'Place Win 6',     {'7/6':all_rolls}),
            'place_lose_8'  :Bet((106,15),(615,53), 'Place Lose 8',     {'4/6':all_rolls}),
            'lay_8'         :Bet((106,15),(615,75), 'Lay 8',            {'1/1':all_rolls}),
            'buy_8'         :Bet((106,15),(615,206), 'Buy 8',           {'1/1':all_rolls}),
            'place_win_8'   :Bet((106,15),(615,229), 'Place Win 8',     {'7/6':all_rolls}),
            'place_lose_9'  :Bet((106,15),(725,53), 'Place Lose 9',     {'5/8':all_rolls}),
            'lay_9'         :Bet((106,15),(725,75), 'Lay 9',            {'1/1':all_rolls}),
            'buy_9'         :Bet((106,15),(725,206), 'Buy 9',           {'1/1':all_rolls}),
            'place_win_9'   :Bet((106,15),(725,229), 'Place Win 9',     {'7/5':all_rolls}),
            'place_lose_10' :Bet((106,15),(834,53), 'Place Lose 10',    {'5/11':all_rolls}),
            'lay_10'        :Bet((106,15),(834,75), 'Lay 10',           {'1/1':all_rolls}),
            'buy_10'        :Bet((106,15),(834,206), 'Buy 10',          {'1/1':all_rolls}),
            'place_win_10'  :Bet((106,15),(834,229), 'Place Win 10',    {'9/5':all_rolls}),
        }
        
    def set_table(self):
        self.table_y = (self.screen_rect.height // 4)*3 
        self.table_x = self.screen_rect.width
        self.table = pg.transform.scale(self.table_orig, (self.table_x, self.table_y))
        self.table_rect = self.table.get_rect()

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]

    def get_event(self, event, scale=(1,1)):
        """This method will be called for each event in the event queue
        while the state is active.
        """
        if event.type == pg.QUIT:
            #self.cash_out_player()
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            #Use tools.scaled_mouse_pos(scale, event.pos) for correct mouse
            #position relative to the pygame window size.
            event_pos = tools.scaled_mouse_pos(scale, event.pos)
            pos = tools.scaled_mouse_pos(scale, event.pos)
            if self.music_icon_rect.collidepoint(pos):
                self.play_music = not self.play_music
                if self.play_music:
                    pg.mixer.music.play(-1)
                else:
                    pg.mixer.music.stop()
            elif self.lobby_button.rect.collidepoint(pos):
                #self.cash_out_player()
                self.game_started = False
                self.done = True
                self.next = "LOBBYSCREEN"
        elif event.type == pg.VIDEORESIZE:
            self.set_table()

    def cash_out_player(self):
        """Convert player's chips to cash and update stats."""
        self.casino_player.stats["cash"] = self.player.get_chip_total()

    def draw(self, surface):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(self.table_color)
        surface.blit(self.table, self.table_rect)
        self.lobby_button.draw(surface)
        if self.play_music:
            surface.blit(self.mute_icon, self.music_icon_rect)
        else:
            surface.blit(self.music_icon, self.music_icon_rect)
            
        for h in self.bets.keys():
            self.bets[h].draw(surface)
        

    def update(self, surface, keys, current_time, dt, scale):
        """
        This method will be called once each frame while the state is active.
        Surface is a reference to the rendering surface which will be scaled
        to pygame's display surface, keys is the return value of the last call
        to pygame.key.get_pressed. current_time is the number of milliseconds
        since pygame was initialized. dt is the number of milliseconds since
        the last frame.
        """
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.draw(surface)
        for h in self.bets.keys():
            self.bets[h].update(mouse_pos)
        print(mouse_pos)


