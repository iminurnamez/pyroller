"""Main settings for the bingo game"""

from ... import prepare


SQUARE_ROWS = [-2, -1, 0, 1, 2]
SQUARE_COLS = [-2, -1, 0, 1, 2]


SETTINGS = {

    'button-font': prepare.FONTS["Saniretro"],
    'button-font-size': 64,
    'button-font-color': 'gold3',
    'button-size': (360, 90),

    'small-button-font': prepare.FONTS["Saniretro"],
    'small-button-font-size': 32,
    'small-button-font-color': 'gold3',
    'small-button-size': (180, 45),
    'small-button-scale': 0.6,

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

    'card-remaining-label-font': prepare.FONTS["Saniretro"],
    'card-remaining-label-font-size': 18,
    'card-remaining-label-font-color': 'black',
    'card-remaining-label-offset': (0, 110),

    'card-value-label-font': prepare.FONTS["Saniretro"],
    'card-value-label-font-size': 22,
    'card-value-label-font-color': 'yellow',
    'card-value-label-offset': (0, -160),
    'card-initial-value': 5,

    'card-double-down-button-font': prepare.FONTS["Saniretro"],
    'card-double-down-button-font-size': 18,
    'card-double-down-button-font-color': 'black',
    'card-double-down-button-offset': (0, 160),

    #
    # Player settings
    'player-cards-position': (prepare.RENDER_SIZE[0] / 2, prepare.RENDER_SIZE[1] - 400),
    'player-card-offsets': [
        (-450, 0), (-150, 0), (150, 0), (450, 0),
        # (-150, 0), (150, 0)
    ],

    #
    # Table settings
    'table-color': (0, 153, 51),

    #
    # Ball machine settings
    'machine-balls': range(1, 76),
    'machine-interval': 1,

    'machine-ball-position': (75, 75),
    'machine-ball-font': prepare.FONTS["Saniretro"],
    'machine-ball-font-size': 102,
    'machine-ball-font-color': 'white',

    'called-balls-position': (180, 40),
    'called-balls-offsets': (20, 20),
    'called-balls-size': (15, 5),
    'called-ball-number-font': prepare.FONTS["Saniretro"],
    'called-ball-number-font-size': 16,
    'called-ball-number-font-color': 'black',
    'called-ball-number-called-font-color': 'white',

    'machine-speeds': [
        ('Slow', 10), ('Medium', 5), ('Fast', 1),
    ],

    #
    # Debug settings
    'debug-auto-pick': True,
    'debug-auto-pick-position': (1250, 40),
    'debug-restart-position': (1250, 120),
}
