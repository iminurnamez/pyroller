from collections import OrderedDict

from .blackjack_game import BlackjackGame
from .blackjack_states import Betting, Dealing, PlayerTurn, DealerTurn, ShowResults, EndRound
import data.state


class Blackjack(data.state.State):
    """
    State to represent a blackjack game. Player cash
    will be converted to chips for the game and converted
    back into cash before returning to the lobby.
    """
    show_in_lobby = True
    name = 'Blackjack'

    def __init__(self):
        super(Blackjack, self).__init__()
        self.states = {
                    "Betting": Betting(),
                    "Dealing": Dealing(),
                    "Player Turn": PlayerTurn(),
                    "Dealer Turn": DealerTurn(),
                    "Show Results": ShowResults(),
                    "End Round": EndRound()
                    }

    @staticmethod
    def initialize_stats():
        """Return OrderedDict suitable for use in game stats

        :return: collections.OrderedDict
        """
        stats = OrderedDict([("games played", 0),
                             ("hands played", 0),
                             ("hands won", 0),
                             ("hands lost", 0),
                             ("blackjacks", 0),
                             ("pushes", 0),
                             ("busts", 0),
                             ("total bets", 0),
                             ("total winnings", 0)])
        return stats

    def startup(self, current_time, persistent):
        """Get state ready to resume."""
        self.persist = persistent
        self.casino_player = self.persist["casino_player"]
        self.casino_player.current_game = self.name
        self.game = BlackjackGame(self.casino_player, self.casino_player.cash)
        self.state_name = "Betting"
        self.state = self.states[self.state_name]
        self.state.startup(self.game)

    def new_game(self, player_cash, chips=None, chip_pile=None):
        """Start a new round of blackjack."""
        self.game = BlackjackGame(self.casino_player, player_cash, chips, chip_pile)

    def cash_out_player(self):
        """Convert player's chips to cash and update stats."""
        self.casino_player.cash = self.game.player.chip_pile.get_chip_total()

    def leave_state(self):
        """Prepare to exit game and return to lobby screen."""
        self.cash_out_player()
        self.done = True
        self.next = "LOBBYSCREEN"

    def get_event(self, event, scale):
        self.state.get_event(event, scale)

    def update(self, surface, keys, current_time, dt, scale):
        if self.state.quit:
            self.state.done = False
            self.state.quit = False
            self.leave_state()
        elif self.state.done:
            previous_state, next_state = self.state_name, self.state.next
            self.state_name = next_state
            self.state.done = False
            self.state = self.states[self.state_name]
            if self.state_name == "Betting":
                chips = self.game.player.chip_pile.all_chips()
                chip_pile = self.game.player.chip_pile
                quick_bet = self.game.quick_bet
                self.new_game(0, chips, chip_pile)
                self.game.quick_bet = quick_bet
            self.state.startup(self.game)
        self.state.update(surface, keys, current_time, dt, scale)
        self.draw(surface)

    def draw(self, surface):
        self.state.draw(surface)

