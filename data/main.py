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
from .components import music_handler
import data.control


def main():
    args = (prepare.CAPTION, prepare.RENDER_SIZE, prepare.RESOLUTIONS)
    run_it = data.control.Control(*args)
    run_it.show_fps = prepare.ARGS["FPS"]
    run_it.max_iterations = prepare.ARGS["iterations"]
    run_it.music_handler = music_handler.MusicHandler()
    run_it.auto_discovery()

    # default state
    default_state = "SNAKESPLASH"

    straight = prepare.ARGS['straight']
    state = straight if straight else default_state
    run_it.start_state(state)

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
