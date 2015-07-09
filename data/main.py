"""
The main function is defined here. It simply creates an instance of
tools.Control and adds the game states to its dictionary using
tools.setup_states.  There should be no need (theoretically) to edit
the tools.Control class.  All modifications should occur in this module
and in the prepare module.
"""

import cProfile
import pstats

from . import prepare, tools
from .states import title_screen, lobby_screen, stats_menu
from .states import stats_screen, snake_splash
from .states import credits_screen
from .states import atm_screen
from .components import music_handler


def main():
    args = (prepare.CAPTION, prepare.RENDER_SIZE, prepare.RESOLUTIONS)
    run_it = tools.Control(*args)
    run_it.show_fps = prepare.ARGS["FPS"]
    run_it.max_iterations = prepare.ARGS["iterations"]
    run_it.music_handler = music_handler.MusicHandler()
    state_dict = {"SNAKESPLASH"   : snake_splash.SnakeSplash(),
                  "TITLESCREEN"   : title_screen.TitleScreen(),
                  "LOBBYSCREEN"   : lobby_screen.LobbyScreen(),
                  "STATSMENU"     : stats_menu.StatsMenu(),
                  "STATSSCREEN"   : stats_screen.StatsScreen(),
                  "CREDITSSCREEN" : credits_screen.CreditsScreen(),
                  "ATMSCREEN"     : atm_screen.ATMScreen()}
    if prepare.ARGS['straight']:
        run_it.setup_states(state_dict, "TITLESCREEN")
    else:
        run_it.setup_states(state_dict, "SNAKESPLASH")
    #
    # Start the main state
    if not prepare.ARGS['profile']:
        run_it.main()
    else:
        #
        # Run with profiling turned on - produces a 'profile' file
        # with stats and then dumps this to the screen
        cProfile.runctx('run_it.main()', globals(), locals(), 'profile')
        p = pstats.Stats('profile')
        print(p.sort_stats('cumulative').print_stats(100))
