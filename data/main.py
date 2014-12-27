"""
The main function is defined here. It simply creates an instance of
tools.Control and adds the game states to its dictionary using
tools.setup_states.  There should be no need (theoretically) to edit
the tools.Control class.  All modifications should occur in this module
and in the prepare module.
"""

from . import prepare, tools
from .states import title_screen, lobby_screen, stats_menu
from .states import stats_screen, blackjack, craps, bingo, keno
from .states import credits_screen, snake_splash

def main():
    args = (prepare.ORIGINAL_CAPTION, prepare.RENDER_SIZE, prepare.RESOLUTIONS)
    run_it = tools.Control(*args)
    state_dict = {"SNAKESPLASH": snake_splash.SnakeSplash(),
                  "TITLESCREEN" : title_screen.TitleScreen(),
                  "LOBBYSCREEN" : lobby_screen.LobbyScreen(),
                  "STATSMENU"   : stats_menu.StatsMenu(),
                  "STATSSCREEN" : stats_screen.StatsScreen(),
                  "CREDITSSCREEN": credits_screen.CreditsScreen(),
                  "BLACKJACK"   : blackjack.Blackjack(),
                  "CRAPS"       : craps.Craps(),
                  "BINGO"       : bingo.Bingo(),
                  "KENO"        : keno.Keno(),
    }
    if prepare.ARGS['straight']:
        run_it.setup_states(state_dict, "TITLESCREEN")
    else:
        run_it.setup_states(state_dict, "SNAKESPLASH")
    run_it.main()
