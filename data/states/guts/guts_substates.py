from random import choice
import pygame as pg
from ... import prepare, tools
from ...components.labels import Label, NeonButton, ButtonGroup
from ...components.animation import Animation, Task


class GutsState(object):
    def __init__(self, game):
        self.done = False
        self.game = game
        self.players = game.players
        self.timer = 0.0
        
    def startup(self):
        pass
        
    def update(self, game):
        pass

    def get_event(self, event):
        pass

    def draw(self, surface):
        pass    

        
class StartGame(GutsState):
    def __init__(self, game):
        super(StartGame, self).__init__(game)
        self.font = prepare.FONTS["Saniretro"]
        screen_rect = pg.Rect((0,0), prepare.RENDER_SIZE)
        self.buttons = ButtonGroup()
        w, h = NeonButton.width, NeonButton.height
        pos = screen_rect.centerx - (w//2), screen_rect.centery - (h//2) 
        NeonButton(pos, "Again", self.start_game, None, self.buttons) #shoulde be "Play", not "Play Again"
        
    def start_game(self, *args):
        self.done = True

    def get_event(self, event):
        self.buttons.get_event(event)
        
    def update(self, dt, scale):
        self.buttons.update(tools.scaled_mouse_pos(scale))
        
    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.buttons.draw(surface)
        
    
class Betting(GutsState):
    def __init__(self, game):
        super(Betting, self).__init__(game)
        self.font = prepare.FONTS["Saniretro"]
        screen_rect = pg.Rect((0,0), prepare.RENDER_SIZE)
        self.labels = []
        self.alpha = 255
        self.animations = pg.sprite.Group()
        if self.game.free_ride:
            label = Label(self.font, 128, "Free Ride", "gold3",
                               {"center": screen_rect.center}, bg=prepare.FELT_GREEN)
            label.image.set_colorkey(prepare.FELT_GREEN)
            self.labels.append(label)
            left, top = label.rect.topleft
            ani = Animation(x=left, y=top-500, duration=2000, round_values=True)           
            fade = Animation(alpha=0, duration=2000, round_values=True)
            fade.start(self)
            ani.start(label.rect)
            self.animations.add(ani, fade)
        else:
            for p in self.players:
                pos = p.name_label.rect.center
                label = Label(self.font, 64, "- ${}".format(self.game.bet), "darkred",
                                    {"center": pos}, bg=prepare.FELT_GREEN)
                label.image.set_colorkey(prepare.FELT_GREEN)
                left, top = label.rect.topleft
                self.labels.append(label)
                ani = Animation(x=left, y=top-300, duration=1500, round_values=True)           
                fade = Animation(alpha=0, duration=1500, round_values=True)
                fade.start(self)
                ani.start(label.rect)
                self.animations.add(ani, fade)
        
    def startup(self):
        if not self.game.free_ride:
            self.game.player.cash -= self.game.bet
            self.game.casino_player.increase("games played")
            self.game.casino_player.increase("total bets", self.game.bet)
        self.game.casino_player.increase("hands played")    
            
    def get_event(self, event):
        pass
        
    def update(self, dt, scale):
        self.timer += dt
        self.animations.update(dt)
        if not self.animations:        
            self.done = True
        for label in self.labels:
            label.image.set_alpha(self.alpha)
            
    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for p in self.game.players:
            p.draw(surface)
        if self.labels:
            for label in self.labels:
                label.draw(surface)
        
    
class Dealing(GutsState):
    def __init__(self, game):
        super(Dealing, self).__init__(game)
        self.make_dealing_animations()
        self.deal_sounds = [prepare.SFX["cardshove{}".format(x)] for x in (1,3,4)]
        self.flip_sounds = [prepare.SFX["cardplace{}".format(x)] for x in (2,3,4)]
    
    def make_dealing_animations(self):    
        self.animations = pg.sprite.Group()
        delay_time = 100
        for player in self.game.deal_queue:
            toggle = 0
            for slot in player.card_slots:
                card = player.draw_from_deck(self.game.deck)
                fx, fy = slot.topleft          
                ani = Animation(x=fx, y=fy, duration=400,
                                        delay=delay_time, transition="in_out_quint",
                                        round_values=True)
                
                if toggle > 0:
                    if player is self.game.player:
                        ani.callback = player.flip_cards
                    else:
                        ani.callback = player.align_cards
                ani.start(card.rect)
                self.animations.add(ani)
                task = Task(self.play_deal_sound, delay_time + 20)
                task2 = Task(self.play_flip_sound, delay_time - 20)
                self.animations.add(task)
                self.animations.add(task2)
                delay_time += 100
                toggle += 1

    def play_deal_sound(self):
        choice(self.deal_sounds).play()
        
    def play_flip_sound(self):
        choice(self.flip_sounds).play()
        
    def update(self, dt, scale):
        self.animations.update(dt)
        if not self.animations:
            self.done = True

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for player in self.game.deal_queue[::-1]:
            player.draw(surface)


class PlayerTurn(GutsState):
    def __init__(self, game, player):
        super(PlayerTurn, self).__init__(game)
        screen_rect = pg.Rect((0,0), prepare.RENDER_SIZE)
        self.player = player
        x,y = screen_rect.centerx -120, 620
        self.buttons = ButtonGroup()
        NeonButton((x, y - 55), "Hit", self.stay, None, self.buttons) #"Stay"
        NeonButton((x, y + 55), "Stand", self.stay_out, None, self.buttons) #"Pass"
                
    def stay(self, *args):
        self.player.stay()
        self.done = True
        self.game.casino_player.increase("stays")
        
    def stay_out(self, *args):
        self.player.stay_out()
        self.done = True
        self.game.casino_player.increase("passes")
        
    def update(self, dt, scale):            
        if self.player is self.game.dealer:
            stays = [x for x in self.game.players if x.stayed]
            if not stays:
                self.stay()
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        
        
    def draw(self, surface):
        self.game.draw(surface)
        self.buttons.draw(surface)
        
    def get_event(self, event):
        self.buttons.get_event(event)

            
class AITurn(GutsState):
    def __init__(self, game, player):
        super(AITurn, self).__init__(game)
        self.timer = 0.0
        self.player = player
        
    def update(self, dt, scale):
        self.timer += dt
        if self.timer > 500:
            self.player.play_hand(self.game)
            self.done = True
            
    def get_event(self, event):
        pass
        
    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        for player in self.game.players:
            player.draw(surface)
        self.game.draw(surface)
    
    
class ShowCards(GutsState):
    def __init__(self, game):
        super(ShowCards, self).__init__(game)
        
        self.timer = 0.0
        
    def update(self, dt, scale):
        if self.timer == 0:
            for p in self.game.players:
                if p.stayed:
                    for card in p.cards:
                        card.face_up = True
        if self.timer > 3000:
          self.done = True
        self.timer += dt
        
    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for player in self.game.players:
            player.draw(surface)
            
    
class ShowResults(GutsState):
    def __init__(self, game):
        super(ShowResults, self).__init__(game)
        self.font  = prepare.FONTS["Saniretro"]
        self.timer = 0.0
        self.fade_timer = 0.0
        self.fade_freq = 8.0
        self.alpha = 255
        self.labels = []
        self.calculated = False
        self.animations = pg.sprite.Group()
        
    def fade_labels(self):
        self.alpha = max(0, self.alpha - 1)
        for label in self.labels:
            label.image.set_alpha(self.alpha)
        

    def update(self, dt, scale):
        self.timer += dt 
        self.animations.update(dt)
        if self.timer > 500 and not self.calculated:
            self.calculated = True
            stayers = [x for x in self.players if x.stayed]
            winners = self.game.get_winners()
            share = self.game.pot // len(winners)
            ani_duration = 1700
            for stayer in stayers:
                pos = stayer.name_label.rect.center
                if stayer not in winners:
                    text = "-${}".format(self.game.pot)
                    color = "darkred"
                    stayer.lost = self.game.pot
                else:
                    text = "+${}".format(share)
                    color = "darkgreen"
                    stayer.won = share                    
                label = Label(self.font, 96, text, color,
                        {"center": pos}, bg=prepare.FELT_GREEN)
                label.image.set_colorkey(prepare.FELT_GREEN)
                self.labels.append(label)
                left, top = label.rect.topleft
                move = Animation(x=left, y=top-120, duration=ani_duration,
                                            round_values=True)
                move.start(label.rect)
                self.animations.add(move)
                        
        if self.labels:
            self.fade_timer += dt
            while self.fade_timer >= self.fade_freq:
                self.fade_timer -= self.fade_freq
                self.fade_labels()
        if self.alpha < 1:
            self.done = True

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for p in self.game.players:
            p.draw(surface)
        if self.labels:
            for label in self.labels:
                label.draw(surface)