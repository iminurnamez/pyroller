from collections import OrderedDict

class CasinoPlayer(object):
    """Class to represent the player/user. A new 
    CasinoPlayer will be instantiated each time the
    program launches. Passing a stats dict to __init__
    allows persistence of player statistics between
    sessions."""

    def __init__(self, stats=None):
        self.stats = OrderedDict([("cash", 999),
                                             ("Blackjack", OrderedDict(
                                                    [("games played", 0),
                                                    ("hands played", 0),
                                                    ("hands won", 0),
                                                    ("hands lost", 0),
                                                    ("blackjacks", 0),
                                                    ("pushes", 0),
                                                    ("busts", 0),
                                                    ("total bets", 0),
                                                    ("total winnings", 0)])) ])
                    
        if stats is not None:
            self.stats["cash"] = stats["cash"]
            for game in stats:
                if game != "cash":
                    #
                    # Make sure we have a place holder for the game
                    if game not in self.stats:
                        self.stats[game] = OrderedDict()
                    #
                    # Update stats
                    for stat in stats[game]:
                        self.stats[game][stat] = stats[game][stat]
                    
                
        