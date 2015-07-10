from collections import OrderedDict

import pygame as pg

from data import prepare
import data.state
from .guts_player import GutsPlayer
from .guts_ai_player import AIPlayer
from .guts_game import GutsGame
from .guts_substates import Dealing, PlayerTurn, ShowCards, Tutorial
from .guts_substates import ShowResults, Betting, StartGame, BankruptScreen


class Guts(data.state.State):
    show_in_lobby = True
    name = 'Guts'

    def __init__(self):
        super(Guts, self).__init__()
        self.screen_rect = pg.Rect((0,0), prepare.RENDER_SIZE)
        self.bet_amount = 10
        self.next = "LOBBYSCREEN"
        self.font = prepare.FONTS["Saniretro"]

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([("games played", 0),
                            ("hands played", 0),
                            ("hands won", 0),
                            ("hands lost", 0),
                            ("stays", 0),
                            ("passes", 0),
                            ("total bets", 0),
                            ("total losses", 0),
                            ("total winnings", 0)])
        return stats

    def startup(self, now, persistent):
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = self.name
        player_cash = self.casino_player.cash
        player_chips = None

        self.player = GutsPlayer(player_cash, player_chips)
        self.ai_players = [AIPlayer("Player 1", "left", (160, 580)),
                                  AIPlayer("Player 2", "left", (160, 230)),
                                  AIPlayer("Player 3", "top", (455, 5)),
                                  AIPlayer("Player 4", "top", (755, 5)),
                                  AIPlayer("Player 5", "right", (1130, 230)),
                                  AIPlayer("Player 6", "right", (1130, 580))
                                  ]
        self.players = self.ai_players
        self.players.append(self.player)
        self.dealer_index = 2
        self.states = {"Start Game": StartGame(),
                             "Tutorial": Tutorial(),
                             "Betting": Betting(),
                             "Dealing": Dealing(),
                             "Player Turn": PlayerTurn(),
                             "Show Cards": ShowCards(),
                             "Show Results": ShowResults(),
                             "Bankrupt Screen": BankruptScreen()}
        self.state_name = "Start Game"
        self.state = self.states[self.state_name]
        self.new_game()
        self.state.startup(self.game)

    def next_dealer(self):
        self.dealer_index += 1
        if self.dealer_index > len(self.players) - 1:
            self.dealer_index = 0

    def new_game(self, pot=0):
        free_ride = True if pot else False
        pot = pot

        self.next_dealer()
        for player in self.players:
            player.cards = []
            player.stayed = False
            player.passed = False
            player.label = None
            player.won = 0
            player.lost = 0
        self.game = GutsGame(self.players, self.dealer_index, self.player,
                                         self.casino_player, self.bet_amount, pot, free_ride)

    def update_stats(self):
        self.casino_player.increase("total losses", self.game.player.lost)
        self.casino_player.increase("total winnings", self.game.player.won)
        if self.game.player.won:
            self.casino_player.increase("hands won")
        if self.game.player.lost:
            self.casino_player.increase("hands lost")

    def back_to_lobby(self, *args):
        self.persist["casino_player"].cash = self.player.cash
        self.next = "LOBBYSCREEN"
        self.done = True

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.state.back_to_lobby()
        self.state.get_event(event)

    def flip_state(self):
        previous_state, next_state = self.state_name, self.state.next
        self.state_name = next_state
        self.state.done = False
        self.state = self.states[self.state_name]
        if self.game.game_over:
            self.update_stats()
            pot = sum([x.lost for x in self.players])
            self.new_game(pot)
        self.state.startup(self.game)

    def update(self, surface, keys, current_time, dt, scale):
        if self.state.quit:
            self.state.done = False
            self.state.quit = False
            self.back_to_lobby()
        elif self.state.done:
            self.flip_state()
        self.state.update(dt, scale)
        self.state.draw(surface)

