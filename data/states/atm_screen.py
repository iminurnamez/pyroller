import string
import pygame as pg
from .. import tools, prepare
from ..components.labels import Label, ButtonGroup, Button, TextBox, MoneyIcon


class ATMScreen(tools._State):
    """
    Allows the player to deposit and withdraw cash from
    their bank account as well as taking cash advances.
    Every five minutes, interest is paid or charged depending
    on the account balance.
    
    Uses a state system to handle the different ATM screens.
    """
    
    def __init__(self):
        super(ATMScreen, self).__init__()
        self.use_music_handler = False
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)       
        self.next = "LOBBYSCREEN"
        self.states = {"MAINMENU": ATMMenu(), 
                             "DEPOSIT": DepositScreen(),
                             "WITHDRAWAL": WithdrawalScreen(),
                             "ADVANCE": AdvanceScreen(),
                             "ACCOUNTSCREEN": AccountScreen(),
                             "MESSAGESCREEN": MessageScreen()
                            }
        self.state_name = "MAINMENU"
        self.state = self.states[self.state_name]
        self.frame = prepare.GFX["atm_frame"]
        topleft = self.screen_rect.left, self.screen_rect.bottom - 88
        self.cash_icon = MoneyIcon(topleft, (195, 88))
        
    def startup(self, current, persistent):
        self.persist = persistent
        self.player = self.persist["casino_player"]
            
    def get_event(self, event, scale):
        self.state.get_event(event, scale)
    
    def update(self, surface, keys, current, dt, scale):
        self.player.account.update(current)
        self.cash_icon.update(self.player.cash)
        if self.state.quit:
            self.state.quit = False
            self.done = True
        elif self.state.done:
            next_state = self.state.next
            persistent = self.state.persist
            persistent["previous"] = self.state_name
            self.state.done = False
            self.state_name = next_state
            self.state = self.states[self.state_name]
            self.state.startup(persistent)
        else:
            self.state.update(surface, keys, current, dt, scale, self.player)
        
        surface.blit(self.frame, (0, 0))
        self.cash_icon.draw(surface)
       
       
class ATMState(object):
    """Base class for different ATM screen states."""
    def __init__(self):
        self.done = False
        self.quit = False
        self.next = None
        self.font = prepare.FONTS["PerfectDOSVGA437"]
        self.screen_rect = pg.Rect((0,0), prepare.RENDER_SIZE)
        self.message = None
        self.persist = {}
        self.beep_sound = prepare.SFX["atm_beep"]
        
    def startup(self, persistent):
        self.persist = persistent
        
    def beep(self):
        self.beep_sound.play()
        
    def get_event(self, event, scale):
        pass
        
    def update(self, surface, keys, current, dt, scale, player):
        pass
        
    def draw(self, surface):
        pass
    

class MessageScreen(ATMState):
    """
    Displays a message from the previous state to the screen
    and returns to the ATM Menu.
    """
    def __init__(self):
        super(MessageScreen, self).__init__()
        self.buttons = ButtonGroup()
        Button(((1278, 840), (88, 65)), self.buttons,
                   call=self.back_to_menu)
    
    def startup(self, persistent):
        self.persist = persistent
        msg = self.persist["message"]
        self.label = Label(self.font, 36, msg, "white", 
                    {"center": self.screen_rect.center})
        self.exit_label = Label(self.font, 36, "OK", "white",
                    {"midright": (1251, 872)})
                    
    def update(self, surface, keys, current, dt, scale, player):
        self.buttons.update(tools.scaled_mouse_pos(scale))
        self.draw(surface)
        
    def back_to_menu(self, *args):
        self.beep()
        self.next = "MAINMENU"
        self.done = True
        
    def get_event(self, event, scale):
        self.buttons.get_event(event)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.back_to_menu()

    def draw(self, surface):
        surface.fill(pg.Color("blue2"))
        self.label.draw(surface)
        self.exit_label.draw(surface)
    
    
class ATMMenu(ATMState):
    def __init__(self):
        super(ATMMenu, self).__init__()
        self.make_buttons()
        
    def set_next(self, next_state):
        self.beep()
        self.next = next_state
        self.done = True
        
    def make_buttons(self):
        self.buttons = ButtonGroup()
        self.labels = []
        buttons = [
                ("Balance Inquiry", "ACCOUNTSCREEN", (34, 450)),  
                ("Deposit", "DEPOSIT", (34, 580)), 
                ("Withdrawal", "WITHDRAWAL", (1278, 450)),
                ("Cash Advance", "ADVANCE", (1278, 580)),
                ("Exit", "", (1278, 840))
                ]
        for text, next_state_name, topleft in buttons:
            callback = self.set_next
            bound = []
            if text == "Exit":
                callback = self.back_to_lobby
                bound = [pg.K_ESCAPE]
            Button((topleft, (88, 65)), self.buttons,
                       args=next_state_name, call=callback, bindings=bound)
            if topleft[0] == 34:
                rect_pos = {"midleft": (topleft[0] + 115, topleft[1] + 32)}
            else:
                rect_pos = {"midright": (topleft[0] - 27, topleft[1] + 32)}           
            label = Label(self.font, 36, text, "white", rect_pos, bg="blue2")
            self.labels.append(label)
        title = Label(self.font, 48, "Select Transaction Type", "white", 
                    {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 80)})
        self.labels.append(title)
        
    def back_to_lobby(self, *args):
        self.beep()
        self.quit = True
        
    def get_event(self, event, scale):
        self.buttons.get_event(event)
        if event.type == pg.QUIT:
            self.back_to_lobby()
            
    def update(self, surface, keys, current, dt, scale, player):      
        self.buttons.update(tools.scaled_mouse_pos(scale))
        self.draw(surface)
        
    def draw(self, surface):
        surface.fill(pg.Color("blue2"))        
        for label in self.labels:
            label.draw(surface)

    
class DepositScreen(ATMState):
    def __init__(self):
        super(DepositScreen, self).__init__()  
        
        self.title = Label(self.font, 36, "Enter Deposit Amount", "white",
                    {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 300)})
        self.make_textbox()
        self.make_enter_button()
        
    def make_enter_button(self):
        self.buttons = ButtonGroup()
        self.labels = []
        Button(((1278, 840), (88, 65)), self.buttons, bindings=[pg.K_RETURN])
        rect_pos = {"midright": (1251, 872)}           
        label = Label(self.font, 36, "Enter", "white", rect_pos, bg="blue2")
        self.labels.append(label)
    
    def make_textbox(self):
        rect = (self.screen_rect.centerx - 200, self.screen_rect.top + 600,
                   400, 200)    
        self.textbox = TextBox(rect, outline_color=pg.Color("white"),
                                          color=pg.Color("blue2"), 
                                          font=pg.font.Font(self.font, 36),
                                          font_color=pg.Color("white"))
        self.textbox.accepted = string.digits
        #update needed to set textbox.render_area
        self.textbox.update()
        self.dollar_sign = Label(self.font, 36, "$", "white",
                    {"midright": (rect[0] - 5, rect[1] + 100)})
        
    def leave_message(self, msg):
        self.make_textbox()
        self.persist["message"] = msg
        self.next = "MESSAGESCREEN"
        self.done = True
        
    def back_to_menu(self):
        self.beep()
        self.next = "MAINMENU"
        self.done = True
        
    def get_event(self, event, scale):
        self.textbox.get_event(event, tools.scaled_mouse_pos(scale))
        self.buttons.get_event(event)
        if event.type == pg.QUIT:
            self.back_to_menu()
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.back_to_menu()             
    
    def update(self, surface, keys, current, dt, scale, player):
        self.textbox.update()
        self.buttons.update(tools.scaled_mouse_pos(scale))
        if not self.textbox.active:
            self.beep()
            try:
                amount = int(self.textbox.final)
            except ValueError:
                amount = 0
            if player.cash >= amount:
                player.cash -= amount
                player.account.deposit(amount)
                msg = "${:.2f} Deposited".format(amount)
                self.leave_message(msg)
            else:
                self.leave_message("Insufficient Funds Deposited")
        text = "You have ${:.2f} available for deposit".format(player.cash)
        self.dyna_label = Label(self.font, 36, text, "white", 
                                          {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 80)})
        
        self.draw(surface)         
         
    def draw(self, surface):
        surface.fill(pg.Color("blue2"))
        self.title.draw(surface)
        self.dollar_sign.draw(surface)
        self.textbox.draw(surface)
        for label in self.labels:
            label.draw(surface)
        self.dyna_label.draw(surface)
        
class WithdrawalScreen(ATMState):
    def __init__(self):
        super(WithdrawalScreen, self).__init__()  
        self.title = Label(self.font, 36, "Enter Withdrawal Amount", "white",
                    {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 300)})
        
        self.make_textbox()
        self.make_enter_button()
        
    def make_enter_button(self):
        self.buttons = ButtonGroup()
        self.labels = []
        Button(((1278, 840), (88, 65)), self.buttons, bindings=[pg.K_RETURN])
        rect_pos = {"midright": (1251, 872)}           
        label = Label(self.font, 36, "Enter", "white", rect_pos, bg="blue2")
        self.labels.append(label)
        
    def make_textbox(self):
        rect = (self.screen_rect.centerx - 200,
                   self.screen_rect.top + 600, 400, 200)    
        self.textbox = TextBox(rect, outline_color=pg.Color("white"),
                                         color=pg.Color("blue2"), 
                                         font=pg.font.Font(self.font, 36), 
                                         font_color=pg.Color("white"))
        self.textbox.accepted = string.digits
        self.dollar_sign = Label(self.font, 36, "$", "white", 
                    {"midright": (rect[0] - 5, rect[1] + 100)})
        #update needed to set textbox.render_area
        self.textbox.update()

    def leave_message(self, msg):
        self.make_textbox()
        self.persist["message"] = msg
        self.next = "MESSAGESCREEN"
        self.done = True
        
    def back_to_menu(self):
        self.beep()
        self.next = "MAINMENU"
        self.done = True
        
    def get_event(self, event, scale):
        self.textbox.get_event(event, tools.scaled_mouse_pos(scale))
        self.buttons.get_event(event)
        if event.type == pg.QUIT:
            self.back_to_menu()
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.back_to_menu()
        
    def update(self, surface, keys, current, dt, scale, player):
        self.textbox.update()
        if not self.textbox.active:
            self.beep()
            try:
                amount = int(self.textbox.final)
            except ValueError:
                amount = 0
            if player.account.balance >= amount:
                player.account.withdrawal(amount)
                player.cash += amount
                self.leave_message("${:.2f} Withdrawn".format(amount))
            else:
                msg = "Insufficient Funds for Withdrawal"
                self.leave_message(msg)
        self.buttons.update(tools.scaled_mouse_pos(scale))
        text = "You have ${:.2f} available for withdrawal".format(player.account.balance)
        self.dyna_label = Label(self.font, 36, text, "white", 
                                          {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 80)})
        self.draw(surface)
        
    def draw(self, surface):
        surface.fill(pg.Color("blue2"))
        self.title.draw(surface)
        self.dollar_sign.draw(surface)
        self.textbox.draw(surface)
        for label in self.labels:
            label.draw(surface)
        self.dyna_label.draw(surface)
        

class AdvanceScreen(ATMState):
    def __init__(self):
        super(AdvanceScreen, self).__init__()
        self.make_textbox()
        self.title = Label(self.font, 36, "Enter Cash Advance Amount", "white",
                    {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 300)})
        self.make_enter_button()
    
    def make_dynamic_labels(self, player):
        text = "The maximum advance is ${:.2f}".format(player.account.max_advance)
        dyna1 = Label(self.font, 36, text, "white",
                             {"midtop": (self.screen_rect.centerx, self.screen_rect.top + 80)})
        fee_text = "A {}% fee will be added to the advance amount".format(player.account.lending_rate * 100)
        dyna2 = Label(self.font, 36, fee_text, "white", {"midtop": (self.screen_rect.centerx, dyna1.rect.bottom + 10)})
        self.dynamic_labels = [dyna1, dyna2]
        
    def make_enter_button(self):
        self.button_labels = []
        self.buttons = ButtonGroup()
        Button(((1278, 840), (88, 65)), self.buttons, bindings=[pg.K_RETURN])
        rect_pos = {"midright": (1251, 872)}           
        label = Label(self.font, 36, "Enter", "white", rect_pos, bg="blue2")
        self.button_labels.append(label)
        
    def make_textbox(self):
        rect = (self.screen_rect.centerx - 200,
                   self.screen_rect.top + 600, 400, 200)
        self.textbox = TextBox(rect, outline_color=pg.Color("white"),
                                          color=pg.Color("blue2"), 
                                          font=pg.font.Font(self.font, 36),
                                          font_color=pg.Color("white"))
        self.textbox.accepted = string.digits
        self.dollar_sign = Label(self.font, 36, "$", "white", 
                    {"midright": (rect[0] - 5, rect[1] + 100)})
        self.textbox.update()

    def leave_message(self, msg):
        self.make_textbox()
        self.beep()
        self.persist["message"] = msg
        self.next = "MESSAGESCREEN"
        self.done = True
        
    def back_to_menu(self):
        self.beep()
        self.next = "MAINMENU"
        self.done = True
        
    def get_event(self, event, scale):
        self.textbox.get_event(event, tools.scaled_mouse_pos(scale))
        self.buttons.get_event(event)
        if event.type == pg.QUIT:
            self.back_to_menu()
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.back_to_menu()               
        
    def update(self, surface, keys, current, dt, scale, player):
        self.textbox.update()
        if not self.textbox.active:
            self.beep()
            try:
                amount = int(self.textbox.final)
            except ValueError:
                amount = 0
            if amount > player.account.max_advance:
                amount = 0
                self.leave_message("You are not authorized for this amount")       
            else:
                player.account.cash_advance(amount)
                player.cash += amount
                msg = "${:.2f} Dispensed".format(amount)
                self.leave_message(msg)
        self.buttons.update(tools.scaled_mouse_pos(scale))
        self.make_dynamic_labels(player)
        self.draw(surface)

    def draw(self, surface):
        surface.fill(pg.Color("blue2"))
        self.title.draw(surface)
        self.dollar_sign.draw(surface)
        self.textbox.draw(surface)
        for label in self.dynamic_labels:
            label.draw(surface)
        for b_label in self.button_labels:
            b_label.draw(surface)        


class AccountScreen(ATMState):
    def __init__(self):
        super(AccountScreen, self).__init__()  
        self.buttons = ButtonGroup()
        Button(((1278, 840), (88, 65)), self.buttons,
                   call=self.back_to_menu)
        
    def back_to_menu(self, *args):
        self.beep()
        self.next = "MAINMENU"
        self.done = True
        
    def get_event(self, event, scale):
        self.buttons.get_event(event)
        if event.type == pg.QUIT:
            self.back_to_menu()
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.back_to_menu()
                
    def update(self, surface, keys, current, dt, scale, player):
        self.buttons.update(tools.scaled_mouse_pos(scale))
        self.labels = []
        
        balance = "Account Balance: ${:.2f}".format(player.account.balance)
        self.labels.append(Label(self.font, 48, balance, "white",
                                  {"topleft": (200, 150)}))
        self.labels.append(Label(self.font, 36, "Menu", "white",
                                  {"midright": (1278 - 27, 840 + 32)}))
        top = 300
        for transaction, amount in player.account.transactions[::-1]:
            label1 = Label(self.font, 36, transaction, "white",
                                 {"topleft": (200, top)})
            label2 = Label(self.font, 36, "${:.2f}".format(amount), "white",
                                 {"topright": (1220, top)})
            self.labels.extend([label1, label2])
            top += label1.rect.height
        self.draw(surface)  
    
    def draw(self, surface):
        surface.fill(pg.Color("blue2"))
        for label in self.labels:
            label.draw(surface)