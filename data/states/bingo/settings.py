"""Main settings for the bingo game"""

from ... import prepare


SETTINGS = {

    'button-font': prepare.FONTS["Saniretro"],
    'button-font-size': 64,
    'button-font-color': 'gold3',
    'button-size': (360, 90),


    #
    # Settings for a single Bingo Card

    'square-number-font': prepare.FONTS["Saniretro"],
    'square-number-font-size': 32,
    'square-number-font-color': 'white',

    'card-square-offset': 40,
    'card-square-scaled-offsets': [
        (x, y) for x in [-2, -1, 0, 1, 2] for y in [-2, -1, 0, 1, 2]
    ],

    #
    # Player settings
    'player-cards-position': (prepare.RENDER_SIZE[0] / 2, prepare.RENDER_SIZE[1] - 400),
    'player-card-offsets': [
        (-450, 0), (-150, 0), (150, 0), (450, 0),
    ],

}
