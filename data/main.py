"""
The main function is defined here. It simply creates an instance of
tools.Control and adds the game states to its dictionary using
tools.setup_states.  There should be no need (theoretically) to edit
the tools.Control class.  All modifications should occur in this module
and in the prepare module.
"""

from . import prepare, tools
from .states import title_screen, lobby_screen, stats_menu, stats_screen, blackjack


def main():
    """Add states to control here."""
    run_it = tools.Control(prepare.ORIGINAL_CAPTION)
    state_dict = {"SPLASH" : splash.Splash(),
                  "INTRO"  : intro.Intro(),
                  "GAME"   : game.Game()}
    run_it.setup_states(state_dict, "SPLASH")
    run_it.main()

def main():
    run_it = tools.Control(prepare.ORIGINAL_CAPTION)
    state_dict = {"TITLESCREEN": title_screen.TitleScreen(),
                        "LOBBYSCREEN": lobby_screen.LobbyScreen(),
                        "STATSMENU": stats_menu.StatsMenu(),
                        "STATSSCREEN": stats_screen.StatsScreen(),
                        "BLACKJACK": blackjack.Blackjack()}
    run_it.setup_states(state_dict, "TITLESCREEN")
    run_it.main()
