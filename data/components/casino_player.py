import inspect
import os
import datetime
from collections import OrderedDict
from .. import prepare
from . import loggable


class NoGameSet(Exception):
    """There is no current game defined for the player"""


class GameNotFound(Exception):
    """The game was not defined in the stats collection"""


class CasinoPlayer(loggable.Loggable):
    """Class to represent the player/user. A new
    CasinoPlayer will be instantiated each time the
    program launches. Passing a stats dict to __init__
    allows persistence of player statistics between
    sessions."""

    # Game states for which no statistics are collected
    no_stats_stats = [
        'LOBBYSCREEN', 'STATSMENU', 'STATSSCREEN',
    ]

    def __init__(self, stats=None):
        self.addLogger()
        self._current_game = None
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
                                                    ("total lost", 0),
                                                    ("total won", 0),
                                                    ("time played", 0),
                                                    ("_time played seconds", 0),
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
        self.warnOnce(
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

    @property
    def current_game(self):
        """The current game for storing stats"""
        return self._current_game

    @current_game.setter
    def current_game(self, value):
        """Set the current game"""
        if value in self.no_stats_stats:
            self._current_game = None
        else:
            #
            # The case of the the current game is not handled very consistently so
            # the following code makes sure this works whatever the case is
            # TODO: remove case inconsistencies and then remove this code
            for name in self._stats:
                if name.lower() == value.lower():
                    self._current_game = name
                    break
            else:
                raise GameNotFound('There was no game called "{0}" in the stats collection'.format(value))

    def increase(self, name, amount=1):
        """Increase the value of a stat"""
        self.set(name, self.get(name) + amount)

    def decrease(self, name, amount=1):
        """Decrease the value of a stat"""
        self.increase(name, -amount)

    def increase_time(self, name, seconds):
        """Increase a value, interpreted as a time"""
        initial_text = self.get(name, '00:00:00')
        dt = datetime.datetime.strptime(initial_text, '%H:%M:%S')
        new = dt + datetime.timedelta(seconds=seconds)
        self.set(name, new.strftime('%H:%M:%S'))

    def decrease_time(self, name, seconds):
        """Decrease a value, interpreted as a time"""
        self.increase(name, -seconds)

    def set(self, name, value):
        """Set the value of a stat"""
        if self.current_game is None:
            raise NoGameSet('No current game has been set (when trying to access stat "{0}")'.format(name))
        #
        self._stats[self.current_game][name] = value

    def get(self, name, default=0):
        """Return the value of a stat"""
        if self.current_game is None:
            raise NoGameSet('No current game has been set (when trying to access stat "{0}")'.format(name))
        #
        return self._stats[self.current_game].get(name, default)