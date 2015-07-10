import os
from collections import OrderedDict

import pygame as pg

from data import tools, prepare
from data.components.loggable import getLogger
from data.components.warning_window import NoticeWindow
from data.components.labels import Label, ButtonGroup, NeonButton
import data.state
from .keno_card import KenoCard
from .pay_table import PayTable
from .round_history import RoundHistory
from .action import Action
from .model import Wallet, Pot, InsufficientFundsException
from .helpers import pick_numbers, PAYTABLE
from .keno_advisor import KenoAdvisor


# Utilize the logger along with the following functions to print to console instead of prints.
log = getLogger("KENO")
#log.debug("testing debug log")
#log.info("testing info log")
#log.error("testing error log")

class Keno(data.state.State):
    """Class to represent a casino game."""
    show_in_lobby = True
    name = 'Keno'

    def __init__(self):
        super(Keno, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.game_started = False
        self.font = prepare.FONTS["Saniretro"]
        self.advisor = KenoAdvisor()
        self.mock_label = Label(self.font, 64, 'KENO [WIP]', 'gold3', {'center':(672,102)})

        b_width = 360
        b_height = 90
        side_margin = 10
        w = self.screen_rect.right - (b_width + side_margin)
        h = self.screen_rect.bottom - (b_height+15)
        self.buttons = ButtonGroup()
        NeonButton((w, h), "Lobby", self.back_to_lobby, None, self.buttons)

        self.turns = 16
        self.play_max_active = False

        ball_path = os.path.join('resources', 'keno', 'balls', '64x64', 'sheet.png')
        ball_sheet = pg.image.load(ball_path).convert_alpha()
        self.balls = tools.strip_from_sheet(ball_sheet, (0,0), (64,64), 10, 8)

        self.keno_card = KenoCard(self.balls)
        #self.keno_card = KenoCard() -- no ball graphics

        self.prev_spot_count = 0

        self.pay_table = PayTable(self.keno_card)
        self.pay_table.update(0)

        self.round_history = RoundHistory(self.keno_card)

        self.alert = None


        self.quick_picking = Action(pg.Rect(370, 760, 150, 75),
                                    Label(self.font, 32, 'QUICK PICK', 'gold3', {'center':(0,0)}),
                                    self.activate_quick_pick)


        self.betting = Action(pg.Rect(682, 760, 150, 75),
                              Label(self.font, 32, 'BET 1', 'gold3', {'center':(0,0)}),
                              self.activate_bet)

        self.clearing = Action(pg.Rect(526, 760, 150, 75),
                               Label(self.font, 32, 'CLEAR', 'gold3', {'center':(0,0)}),
                               self.activate_clear)

        self.playing = Action(pg.Rect(838, 760, 156, 75),
                              Label(self.font, 32, 'PLAY', 'gold3', {'center':(0,0)}),
                              self.activate_play)

        self.playing_max = Action(pg.Rect(838, 840, 156, 75),
                                  Label(self.font, 32, 'PLAY MAX', 'gold3', {'center':(0,0)}),
                                  self.activate_playmax)

        self.actions = {
            'quick pick'    : self.quick_picking,
            'betting'       : self.betting,
            'clearing'      : self.clearing,
            'playing'       : self.playing,
            'playing max'   : self.playing_max,
        }

        self.gui_widgets = {
            'title'         : self.mock_label,
            'card'          : self.keno_card,
            'quick_pick'    : self.quick_picking,
            'play'          : self.playing,
            'play_max'      : self.playing_max,
            'pay_table'     : self.pay_table,
            'round_history' : self.round_history,
            'balance'       : None,
            'bet_action'    : None,
            'clear'         : None,
            'bet'           : None,
            'won'           : None,
            'spot'          : None,
        }

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([("games played", 0)])
        return stats

    def activate_quick_pick(self):
        self.keno_card.reset()
        numbers = pick_numbers(10)

        for number in numbers:
            self.keno_card.toggle_owned(number)

    def activate_bet(self):
        log.debug("betting activated")

        try:
            self.make_bet(1)
        except InsufficientFundsException:
            self.handle_insufficient_funds()

        spot_count = self.keno_card.spot_count
        self.pay_table.update(spot_count, self.pot._balance)

    def activate_clear(self):
        log.debug("clear activated")
        self.keno_card.ready_play(clear_all=True)
        self.clear_bet()
        self.round_history.clear()

    def validate_configuration(self):
        if not self.pot.paid and self.pot._balance > 0:

            try:
                self.pot.repeat_bet()
                return True
            except InsufficientFundsException:
                self.handle_insufficient_funds()
                return False

        elif not self.pot.paid:
            self.alert = NoticeWindow(self.screen_rect.center, "Please place your bet.")
            return False

        spot_count = self.keno_card.spot_count
        if spot_count <= 0:
            self.alert = NoticeWindow(self.screen_rect.center, "Please pick your spots.")
            return False

        return True

    def handle_insufficient_funds(self):
        self.pot.clear_bet(with_payout=False)
        self.play_max_active = False
        self.turns = 0
        self.alert_insufficient_funds()

    def alert_insufficient_funds(self):
        self.alert = NoticeWindow(self.screen_rect.center, "You cannot afford that bet.")

    def activate_play(self):

        if not self.validate_configuration():
            return

        numbers = pick_numbers(20)
        log.debug("pick: {}".format(numbers))

        self.keno_card.ready_play()
        self.keno_card.current_pick = numbers
        for number in numbers:
            self.keno_card.toggle_hit(number)

        self.play_game()

    def activate_playmax(self):
        self.round_history.clear()

        if not self.validate_configuration():
            return

        self.continue_playmax()
        self.play_game()

    def continue_playmax(self):
        log.debug("turns={0}".format(self.turns))

        try:
            self.pot.repeat_bet()
            self.play_max_active = True
            numbers = pick_numbers(20)

            self.keno_card.ready_play()
            self.keno_card.current_pick = numbers
            for number in numbers:
                self.keno_card.toggle_hit(number)

            self.turns -= 1
            if self.turns <= 0:
                self.play_max_active = False
                self.turns = 16

        except InsufficientFundsException:
            self.turns = 0
            self.handle_insufficient_funds()
            self.play_max_active = False

    def make_bet(self, amount):
        try:
            self.pot.change_bet(amount)
        except InsufficientFundsException:
            self.handle_insufficient_funds()

    def clear_bet(self):
        self.pot.clear_bet()

    def result(self, spot, hit):

        paytable = PAYTABLE[spot]
        payment = 0.0
        for entry in paytable:
            if entry[0] == hit:
                payment = entry[1]

            if payment > 0.0:
                break

        self.pot.payout(payment)
        self.casino_player.cash = self.wallet.balance

    def back_to_lobby(self, *args):
        self.game_started = False
        self.done = True
        self.next = "LOBBYSCREEN"

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = self.name
        self.gui_widgets['bet_action'] = self.betting
        self.gui_widgets['clear'] = self.clearing

        self.wallet = Wallet(self.casino_player.cash)
        self.pot    = Pot(self.wallet)

        self.casino_player.increase("games played", 1)

    def play_game(self):
        spot_count = self.keno_card.spot_count
        hit_count = self.keno_card.hit_count
        self.result(spot_count, hit_count)
        self.round_history.update(spot_count, hit_count)

    def get_event(self, event, scale=(1,1)):
        """This method will be called for each event in the event queue
        while the state is active.
        """
        if event.type == pg.QUIT and not self.alert:
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN and not self.alert:
            #Use tools.scaled_mouse_pos(scale, event.pos) for correct mouse
            #position relative to the pygame window size.
            event_pos = tools.scaled_mouse_pos(scale, event.pos)
            log.info(event_pos) #[for debugging positional items]

            for action in self.actions.values():
                action.execute(event_pos)

            self.keno_card.update(event_pos)

            spot_count = self.keno_card.spot_count
            if spot_count != self.prev_spot_count:
                self.pay_table.update(spot_count, self.pot._balance)
                self.prev_spot_count = spot_count

        if not self.alert:
            self.buttons.get_event(event)
        self.alert and self.alert.get_event(event)

    def draw(self, surface):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(prepare.FELT_GREEN)

        self.buttons.draw(surface)
        self.advisor.draw(surface)
        for widget in self.gui_widgets.values():
            if widget:
                widget.draw(surface)

        if self.alert and not self.alert.done:
            self.alert.draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        """
        This method will be called once each frame while the state is active.
        Surface is a reference to the rendering surface which will be scaled
        to pygame's display surface, keys is the return value of the last call
        to pygame.key.get_pressed. current_time is the number of milliseconds
        since pygame was initialized. dt is the number of milliseconds since
        the last frame.
        """

        self.advisor.update(dt)

        if self.play_max_active:
            self.continue_playmax()
            self.play_game()

        total_text = "Balance:  ${}".format(self.wallet.balance)

        self.gui_widgets['balance'] = Label(self.font, 48, total_text, "gold3",
                               {"topleft": (24, 760)})

        bet_text = "Bet: ${}".format(self.pot._balance)
        self.gui_widgets['bet'] = Label(self.font, 48, bet_text, "gold3",
                               {"topleft": (24, 760+48)})

        won_text = "Won: ${}".format(self.pot.won)
        self.gui_widgets['won'] = Label(self.font, 48, won_text, "gold3",
                               {"topleft": (24, 760+48+48)})

        spot_count = self.keno_card.spot_count
        spot_text = "Spot: {}".format(spot_count)
        self.gui_widgets['spot'] = Label(self.font, 48, spot_text, "gold3",
                               {"topleft": (1036, 760)})

        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        if self.alert:
            self.alert.update(mouse_pos)
            if self.alert.done:
                self.alert = None

        self.draw(surface)
