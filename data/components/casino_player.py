import inspect
import os
from collections import OrderedDict
from .. import prepare
from . import loggable


class CasinoPlayer(loggable.Loggable):
    """Class to represent the player/user. A new
    CasinoPlayer will be instantiated each time the
    program launches. Passing a stats dict to __init__
    allows persistence of player statistics between
    sessions."""

    def __init__(self, stats=None):
        self.addLogger()
        self._stats = OrderedDict([("cash", prepare.MONEY),
                                             ("Blackjack", OrderedDict(
                                                    [("games played", 0),
                                                    ("hands played", 0),
                                                    ("hands won", 0),
                                                    ("hands lost", 0),
                                                    ("blackjacks", 0),
                                                    ("pushes", 0),
                                                    ("busts", 0),
                                                    ("total bets", 0),
                                                    ("total winnings", 0)])),
                                             ("Craps", OrderedDict(
                                                    [('times as shooter', 0),
                                                     ('bets placed', 0),
                                                     ('bets won', 0),
                                                     ('bets lost', 0),
                                                     ('total bets', 0),
                                                     ('total winnings', 0)])),
                                             ("Bingo", OrderedDict(
                                                    [("games played", 0),
                                                    ("cards won", 0),
                                                    ("cards lost", 0),
                                                    ("total bets", 0),
                                                    ("total winnings", 0),
                                                    ("time played", 0),
                                                    ("_last squares", [])])),
                                             ("Keno", OrderedDict(
                                                    [("games played", 0)])),
                                             ("Video Poker", OrderedDict(
                                                    [("games played", 0)])),
                                             ("Pachinko", OrderedDict(
                                                    [('games played', 0),
                                                    ('total winnings', 0),
                                                    ('earned', 0),
                                                    ('jackpots', 0),
                                                    ('gutters', 0),
                                                    ]))
                                            ])

        if stats is not None:
            self.stats["cash"] = stats["cash"]
            for game in self.stats:
                if game != "cash":
                    for stat, default in self.stats[game].items():
                        self.stats[game][stat] = stats[game].get(stat, default)

    @property
    def stats(self):
        """Access stats directly - left here for backwards compatibility"""
        #
        # The following trickery is just to make the deprecation warning a bit
        # more helpful for the developers of the games
        frame, full_filename, line_number, function_name, lines, index = inspect.stack()[1]
        filename = os.path.split(full_filename)[1]
        component = os.path.split(os.path.split(full_filename)[0])[1]
        self.log.warn(
            'Direct access to stats is deprecated - please use helper methods: game {0}, file {1}:{3} - {2}'.format(
                component, filename, function_name, line_number))
        #
        return self._stats

    @property
    def cash(self):
        """The current cash for the player"""
        return self._stats['cash']

    @cash.setter
    def cash(self, value):
        """Set the cash value"""
        self._stats['cash'] = value
