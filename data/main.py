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
from .states import stats_screen, blackjack, craps, bingo, keno, video_poker
from .states import credits_screen, snake_splash, pachinko
from .components import music_handler
from .states import credits_screen, snake_splash, pachinko, baccarat


def main():
    args = (prepare.CAPTION, prepare.RENDER_SIZE, prepare.RESOLUTIONS)
    run_it = tools.Control(*args)
    run_it.show_fps = prepare.ARGS["FPS"]
    run_it.music_handler = music_handler.MusicHandler()
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
                  "VIDEOPOKER"  : video_poker.VideoPoker(),
                  "PACHINKO"    : pachinko.Pachinko(),
                  "BACCARAT"    : baccarat.Baccarat(),
    }
    if prepare.ARGS['straight']:
        run_it.setup_states(state_dict, "TITLESCREEN")
    else:
        run_it.setup_states(state_dict, "BACCARAT")
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
