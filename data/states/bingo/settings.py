"""Main settings for the bingo game"""

from ... import prepare


SQUARE_ROWS = [-2, -1, 0, 1, 2]
SQUARE_COLS = [-2, -1, 0, 1, 2]


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

    'square-label-font': prepare.FONTS["Saniretro"],
    'square-label-font-size': 32,
    'square-label-font-color': 'black',

    'card-square-rows': SQUARE_ROWS,
    'card-square-cols': SQUARE_COLS,
    'card-square-offset': 40,
    'card-square-scaled-offsets': [
        (x, y) for x in SQUARE_COLS for y in SQUARE_ROWS
    ],

    'card-numbers': {
        -2: range(1, 16),
        -1: range(16, 31),
        0: range(31, 46),
        1: range(46, 61),
        2: range(61, 76),
    },

    #
    # Player settings
    'player-cards-position': (prepare.RENDER_SIZE[0] / 2, prepare.RENDER_SIZE[1] - 400),
    'player-card-offsets': [
        # (-450, 0), (-150, 0), (150, 0), (450, 0),
        (-150, 0), (150, 0)
    ],

    #
    # Table settings
    'table-color': (0, 153, 51),

    #
    # Ball machine settings
    'machine-balls': range(1, 76),
    'machine-interval': 3,

    'machine-ball-position': (75, 75),
    'machine-ball-font': prepare.FONTS["Saniretro"],
    'machine-ball-font-size': 102,
    'machine-ball-font-color': 'white',

}
