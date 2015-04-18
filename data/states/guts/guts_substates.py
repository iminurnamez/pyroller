from random import choice
import pygame as pg
from ... import prepare, tools
from ...components.labels import Label, NeonButton, ButtonGroup, MoneyIcon, Button, Blinker
from ...components.labels import MultiLineLabel
from ...components.animation import Animation, Task
from ...components.advisor import Advisor
from ...components.warning_window import WarningWindow


class GutsState(object):
    font = prepare.FONTS["Saniretro"]
    deal_sounds = [prepare.SFX["cardshove{}".format(x)] for x in (1,3,4)]
    flip_sounds = [prepare.SFX["cardplace{}".format(x)] for x in (2,3,4)]
    cha_ching = prepare.SFX["coins"]
    screen_rect = pg.Rect((0,0), prepare.RENDER_SIZE)
    money_icon = MoneyIcon((0, screen_rect.bottom - 75))
    draw_group = pg.sprite.Group()
    move_animations = pg.sprite.Group()
    advisor = Advisor(draw_group, move_animations)
    advisor.active = True
    advisor_back = prepare.GFX["advisor_back"]
    advisor_front = prepare.GFX["advisor_front"]
    advisor_back_dim = prepare.GFX["advisor_back_dim"]
    advisor_front_dim = prepare.GFX["advisor_front_dim"]
    advisor_active = True
    window = None
    def __init__(self):
        self.done = False
        self.quit = False
        self.next = None
        rect = self.advisor_back.get_rect().union(self.advisor_front.get_rect())
        self.advisor_button = Button(rect, call=self.toggle_advisor)
        self.buttons = ButtonGroup()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        lobby_button = NeonButton(pos, "Lobby", self.back_to_lobby, None, self.buttons, bindings=[pg.K_ESCAPE])
        self.animations = pg.sprite.Group()
        

    def warn(self, *args):
        warning = "Exiting the game will abandon the current pot!"
        GutsState.window = WarningWindow(self.screen_rect.center, warning, self.leave)
    
    def back_to_lobby(self, *args):
        if self.game.pot:
            self.warn()
        else:
            self.leave()
            
    def leave(self):
        self.quit = True
        self.advisor.empty()

    def toggle_advisor(self, *args):
        GutsState.advisor_active = not GutsState.advisor_active

    def draw_advisor(self, surface):
        if self.advisor_active:
            surface.blit(self.advisor_back, (0, 0))
            self.draw_group.draw(surface)
            surface.blit(self.advisor_front, (0, 0))
        else:
            surface.blit(self.advisor_back_dim, (0, 0))
            surface.blit(self.advisor_front_dim, (0, 0))

    def general_update(self, dt, mouse_pos):
        if self.window:
            self.window.update(mouse_pos)
            if self.window.done:
                GutsState.window = None
        else:        
            self.advisor_button.update(mouse_pos)
            self.animations.update(dt)
            self.buttons.update(mouse_pos)
            self.money_icon.update(self.game.player.cash)
            self.advisor_button.update(mouse_pos)
            if self.advisor_active:
                self.move_animations.update(dt)
            self.game.update()
       

    def startup(self, game):
        self.game = game

    def update(self, dt, scale):
        pass

    def get_event(self, event):
        pass

    def draw(self, surface):
        pass

    def play_deal_sound(self):
        choice(self.deal_sounds).play()

    def play_flip_sound(self):
        choice(self.flip_sounds).play()

    def play_stay_sound(self):
        choice(self.stay_sounds).play()

    def play_pass_sound(self):
        choice(self.fold_sounds).play()


class Tutorial(GutsState):
    def __init__(self):
        super(Tutorial, self).__init__()
        self.next = "Start Game"

    def startup(self, game):
        self.game = game
        self.make_labels()


    def make_labels(self):
        self.animations = pg.sprite.Group()
        rules = [
                "Players place their ante in the pot",
                "Two cards are dealt to each player",
                "Players choose whether to stay or pass",
                "Players that stayed show their cards",
                "The player with the best poker hand wins the pot",
                "Players that stay and lose must match the pot",
                "If two players lose, the pot doubles",
                "If three players lose, the pot triples...",
                "Ties split the pot",
                "The game ends when there is nothing in the pot",
                "Good Luck!"
                ]
        labels = []
        for rule in rules:
            label = MultiLineLabel(self.font, 72, rule, "gold3",
                                              {"center": self.screen_rect.center},
                                              bg=prepare.FELT_GREEN, align="center",
                                              char_limit=28)
            label.alpha = 255
            labels.append(label)
        self.labels = iter(labels)
        self.label = next(self.labels)
        ani = Animation(alpha=0, duration=3000, round_values=True)
        ani.start(self.label)
        self.animations.add(ani)

    def next_label(self):
        try:
            self.label = next(self.labels)
            ani = Animation(alpha=0, duration=3000, round_values=True)
            ani.start(self.label)
            self.animations.add(ani)
        except StopIteration:
            self.label = None

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:    
            self.buttons.get_event(event)
            self.advisor_button.get_event(event)
        
            if event.type == pg.MOUSEBUTTONDOWN:
                self.next_label()

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)
        if not self.window:
            if self.label:
                self.label.image.set_alpha(self.label.alpha)
                if self.label.alpha <= 0:
                    self.next_label()
            else:
                self.done = True

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        if self.label:
            self.label.draw(surface)
        self.buttons.draw(surface)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)
        
class BankruptScreen(GutsState):
    """Direct player to ATM if short on cash."""
    def __init__(self):
        super(BankruptScreen, self).__init__()

    def startup(self, game):
        self.game = game
        self.advisor.queue_text("Sorry, you need at least ${} to play".format(self.game.bet), dismiss_after=3000)
        self.advisor.queue_text("You can visit the ATM for a cash advance", dismiss_after=3000)
        self.animations.add(Task(self.back_to_lobby, 6500))
        self.animations.add(Task(self.advisor.empty, 6500))
       
    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.animations.update(dt)
        self.move_animations.update(dt)
        self.money_icon.update(self.game.player.cash)

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)    
        

class StartGame(GutsState):
    """Choose between starting a new game or view tutorial."""
    def __init__(self):
        super(StartGame, self).__init__()

    def startup(self, game):
        self.game = game
        sr = self.screen_rect
        title = Label(self.font, 128, "Two-Card Guts", "gold3",
                          {"midtop": (sr.centerx, 5)},
                          bg=prepare.FELT_GREEN)
        title.image.set_alpha(160)
        title2 = Label(self.font, 96, "${} Ante".format(self.game.bet), "darkred",
                            {"midtop": (sr.centerx, title.rect.bottom)},
                            bg=prepare.FELT_GREEN)
        title2.image.set_alpha(140)
        self.titles = [title, title2]
        self.player_buttons = ButtonGroup()
        w, h = NeonButton.width, NeonButton.height
        pos = sr.centerx - (w//2), sr.centery - (h//2)
        NeonButton(pos, "Ante Up", self.start_game, None, self.player_buttons)
        pos2 = sr.centerx - (w//2), sr.centery + (h//2) + 50
        self.tutorial_button = NeonButton(pos2, "Tutorial", self.to_tutorial,
                                          None, self.player_buttons)
        self.advisor.queue_text("Ante Up ${} to play".format(self.game.bet), dismiss_after=2500)
        self.advisor.queue_text("Press Tutorial to learn how to play", dismiss_after=2500)
        self.advisor.queue_text("Press the Lobby button to exit", dismiss_after=2500)
        
    def start_game(self, *args):
        self.done = True
        self.next = "Betting"
        self.advisor.empty()

    def to_tutorial(self, *args):
        self.done = True
        self.next = "Tutorial"
        self.advisor.empty()

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:
            self.buttons.get_event(event)
            self.player_buttons.get_event(event)
            self.advisor_button.get_event(event)

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)
        if not self.window:
            self.player_buttons.update(mouse_pos)


    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        for title in self.titles:
            title.draw(surface)
        self.buttons.draw(surface)
        self.player_buttons.draw(surface)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)


class Betting(GutsState):
    def __init__(self):
        super(Betting, self).__init__()
        self.buttons = ButtonGroup()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        lobby_button = NeonButton(pos, "Lobby", self.warn, None, self.buttons, bindings=[pg.K_ESCAPE])

    def add_bet_to_pot(self):
        self.game.pot += self.game.bet

    def make_labels(self):
        sr = self.screen_rect
        self.labels = []
        self.alpha = 255
        self.animations = pg.sprite.Group()
        if self.game.free_ride:
            label = Label(self.font, 192, "Free Ride", "gold3",
                               {"center": sr.center}, bg=prepare.FELT_GREEN)
            label.image.set_colorkey(prepare.FELT_GREEN)
            self.labels.append(label)
            left, top = label.rect.topleft
            ani = Animation(x=left, y=top-500, duration=2000, round_values=True)
            fade = Animation(alpha=0, duration=2000, round_values=True)
            fade.start(self)
            ani.start(label.rect)
            self.animations.add(ani, fade)
        else:
            dest = self.game.pot_label.rect.center
            for p in self.game.players:
                pos = p.name_label.rect.center
                label = Label(self.font, 96, "${}".format(self.game.bet), "darkred",
                                    {"center": pos}, bg=prepare.FELT_GREEN)
                label.image.set_colorkey(prepare.FELT_GREEN)
                left, top = label.rect.topleft
                self.labels.append(label)
                ani = Animation(centerx=dest[0], centery=dest[1], duration=2000,
                                        round_values=True, transition="in_quart")
                ani.callback = self.add_bet_to_pot
                ani.start(label.rect)
                self.animations.add(ani)
            fader = Animation(alpha=0, duration=2100, round_values=True)
            fader.start(self)
            self.animations.add(fader)

    
    def startup(self, game):
        self.game = game
        if not self.game.free_ride:
            if self.game.player.cash < self.game.bet:
                self.next = "Bankrupt Screen"
                self.done = True
            else:    
                self.game.player.cash -= self.game.bet
                self.game.casino_player.increase("games played")
                self.game.casino_player.increase("total bets", self.game.bet)
        self.game.casino_player.increase("hands played")
        self.make_labels()

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:
            self.buttons.get_event(event)
            self.advisor_button.get_event(event)

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)

        if not self.animations:
            self.done = True
            self.next = "Dealing"
        for label in self.labels:
            label.image.set_alpha(self.alpha)

    def draw(self, surface):
        if not self.done:
            surface.fill(prepare.FELT_GREEN)
            self.game.draw(surface)
            for p in self.game.players:
                p.draw(surface)
            for label in self.labels:
                label.draw(surface)
        self.buttons.draw(surface)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)


class Dealing(GutsState):
    def __init__(self):
        super(Dealing, self).__init__()

    def startup(self, game):
        self.game = game
        self.make_dealing_animations()

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:
            self.advisor_button.get_event(event)
            self.buttons.get_event(event)

    def make_dealing_animations(self):
        self.animations = pg.sprite.Group()
        delay_time = 100
        for player in self.game.deal_queue:
            toggle = 0
            for slot in player.card_slots:
                card = player.draw_from_deck(self.game.deck)
                fx, fy = slot.topleft
                ani = Animation(x=fx, y=fy, duration=400,
                                        delay=delay_time, #transition="in_out_quint",
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

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)
        if not self.animations:
            self.done = True
            self.next = "Player Turn"

    
    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for player in self.game.players: #deal_queue[::-1]:
            player.draw(surface)
        
        self.buttons.draw(surface)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)


class PlayerTurn(GutsState):
    def __init__(self):
        super(PlayerTurn, self).__init__()

    def startup(self, game):
        self.game = game
        self.current_player = self.game.deal_queue[self.game.current_player_index]
        self.player_buttons = ButtonGroup()
        self.animations = pg.sprite.Group()
        self.timer  = 0
        self.time_limit = 600

        if self.current_player is self.game.dealer:
            self.next = "Show Cards"
        else:
            self.next = "Player Turn"
        if self.current_player is self.game.player:
            x, y = self.screen_rect.centerx -120, 695
            NeonButton((x, y - 55), "Stay", self.stay, None, self.player_buttons)
            NeonButton((x, y + 55), "Pass", self.stay_out, None, self.player_buttons)
            if self.current_player is self.game.dealer:
                stays = [x for x in self.game.players if x.stayed]
                if not stays:
                    self.stay()
        else:
            self.current_player.play_hand(self.game)

    def toggle_player_buttons(self, boolean):
        for b in self.player_buttons:
            b.active = boolean
            b.visible = boolean

    def end_player_turn(self):
        self.done = True
        self.game.current_player_index += 1

    def stay(self, *args):
        self.current_player.stay()
        self.game.casino_player.increase("stays")
        self.animations.add(Task(self.end_player_turn, 1000))
        self.toggle_player_buttons(False)

    def stay_out(self, *args):
        self.current_player.stay_out()
        self.game.casino_player.increase("passes")
        self.animations.add(Task(self.end_player_turn, 1000))
        self.toggle_player_buttons(False)

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)
        if not self.window:
            self.timer += dt
            if self.current_player is not self.game.player:
                if self.timer > self.time_limit:
                    self.done = True
            self.player_buttons.update(mouse_pos)

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        for player in self.game.players:
            player.draw(surface)
        self.game.draw(surface)
        self.buttons.draw(surface)
        self.player_buttons.draw(surface)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:
            self.buttons.get_event(event)
            self.player_buttons.get_event(event)
            self.advisor_button.get_event(event)
        

class ShowCards(GutsState):
    def __init__(self):
        super(ShowCards, self).__init__()
        self.next = "Show Results"
        for button in self.buttons:
            button.active = False
            
    def startup(self, game):
        self.game = game
        self.timer = 0.0
        for p in self.game.players:
            if p.stayed:
                for card in p.cards:
                    card.face_up = True

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:
            self.advisor_button.get_event(event)

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)

        if self.timer > 3000:
          self.done = True
        if not self.window:
            self.timer += dt

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for player in self.game.players:
            player.draw(surface)
        self.buttons.draw(surface)
        self.money_icon.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)


class ShowResults(GutsState):
    def __init__(self):
        super(ShowResults, self).__init__()
        self.buttons = ButtonGroup()
        pos = (self.screen_rect.right-(NeonButton.width+10),
               self.screen_rect.bottom-(NeonButton.height+15))
        lobby_button = NeonButton(pos, "Lobby", self.warn, None, self.buttons, bindings=[pg.K_ESCAPE])

    def make_player_buttons(self, free_ride):
        self.player_buttons = ButtonGroup()
        w, h = NeonButton.width, NeonButton.height
        sr = self.screen_rect
        pos = sr.centerx - (w//2), sr.centery + 120
        text = "OK" if free_ride else "Ante Up"
        NeonButton(pos, text, self.new_game, None, self.player_buttons)

    def new_game(self, *args):
        self.game.game_over = True
        self.done = True
        self.next = "Betting"

    def add_player_cash(self, amount):
        self.game.player.cash += amount

    def add_to_pot(self, amount):
        self.game.pot += amount

    def toggle_buttons(self, boolean):
        for button in self.player_buttons:
            button.active = boolean
            button.visible = boolean

    def startup(self, game):
        self.game = game
        self.timer = 0.0
        self.fade_timer = 0.0
        self.fade_freq = 8.0
        self.alpha = 255
        self.labels = []
        self.blinkers = []
        self.calculated = False
        self.animations = pg.sprite.Group()
        
        
        stayers = [x for x in self.game.players if x.stayed]
        winners = self.game.get_winners()
        share = self.game.pot // len(winners)

        ani_duration = 2000
        free_ride = False
        
        for stayer in stayers:
            pos = stayer.name_label.rect.center
            dest = pos[0], pos[1] - 120
            cards_center = stayer.cards[0].rect.union(stayer.cards[1].rect).center
            if stayer not in winners:
                text = "${}".format(self.game.pot)
                color = "darkred"
                stayer.lost = self.game.pot
                free_ride = True
                dest = self.game.pot_label.rect.center
                if stayer is self.game.player:
                    pos = self.money_icon.rect.center
                    self.add_player_cash(-stayer.lost)
                task = Task(self.add_to_pot, ani_duration, args=[stayer.lost])
                self.animations.add(task)
                lose_label = Blinker(self.font, 96, "Loser", color, {"center": cards_center}, 500)
                self.animations.add(Task(self.blinkers.append, ani_duration, args=[lose_label]))
            else:
                text = "${}".format(share)
                color = "darkgreen"
                stayer.won = share
                pos = self.game.pot_label.rect.center
                if stayer is self.game.player:
                    self.cha_ching.play()
                    dest = self.money_icon.rect.center
                    task = Task(self.add_player_cash, ani_duration, args=[share])
                    self.animations.add(task)
                win_label = Blinker(self.font, 96, "Winner", color, {"center": cards_center}, 500)
                self.animations.add(Task(self.blinkers.append, ani_duration, args=[win_label]))
            label = Label(self.font, 128, text, color,
                    {"center": pos}, bg=prepare.FELT_GREEN)
            label.image.set_colorkey(prepare.FELT_GREEN)
            self.labels.append(label)
            move = Animation(centerx=dest[0], centery=dest[1], duration=ani_duration,
                                        round_values=True, transition="in_quart")
            move.start(label.rect)
            self.animations.add(move)
             
        fader = Animation(alpha=0, duration=ani_duration + 200, round_values = True)
        fader.start(self)
        self.animations.add(fader)
        self.game.pot = 0

        self.make_player_buttons(free_ride)
        self.toggle_buttons(False)

    def fade_labels(self):
        for label in self.labels:
            label.image.set_alpha(self.alpha)

    def update(self, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.general_update(dt, mouse_pos)
        if not self.window:
            for blinker in self.blinkers:
                blinker.update(dt)
            self.player_buttons.update(mouse_pos)
            self.fade_labels()
            if self.alpha < 1:
                self.toggle_buttons(True)

    def get_event(self, event):
        if self.window:
            self.window.get_event(event)
        else:
            self.buttons.get_event(event)
            self.player_buttons.get_event(event)
            self.advisor_button.get_event(event)

    def draw(self, surface):
        surface.fill(prepare.FELT_GREEN)
        self.game.draw(surface)
        for p in self.game.players:
            p.draw(surface)
        self.money_icon.draw(surface)
        self.buttons.draw(surface)
        self.player_buttons.draw(surface)
        for label in self.labels:
            label.draw(surface)
        for blinker in self.blinkers:
            blinker.draw(surface)
        self.draw_advisor(surface)
        if self.window:
            self.window.draw(surface)
