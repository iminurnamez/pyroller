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

    'tiny-button-font': prepare.FONTS["Saniretro"],
    'tiny-button-font-size': 16,
    'tiny-button-font-color': 'gold3',
    'tiny-button-size': (30, 45),
    'tiny-button-scale': 0.4,

    #
    # Settings for a single Bingo Card
    'square-number-font': prepare.FONTS["Saniretro"],
    'square-number-font-size': 32,
    'square-number-font-color': 'white',
    'square-number-scale': 1.0,

    'player-square-label-font': prepare.FONTS["Saniretro"],
    'player-square-label-font-size': 32,
    'player-square-label-font-color': 'black',
    'player-square-label-scale': 1.0,

    'dealer-square-label-font': prepare.FONTS["Saniretro"],
    'dealer-square-label-font-size': 32,
    'dealer-square-label-font-color': 'black',
    'dealer-square-label-scale': 0.4,

    'card-square-rows': SQUARE_ROWS,
    'card-square-cols': SQUARE_COLS,
    'card-square-scaled-offsets': [
        (x, y) for x in SQUARE_COLS for y in SQUARE_ROWS
    ],
    'player-card-square-offset': 48,
    'dealer-card-square-offset': 20,
    'card-square-header-offset': (0, -6),

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

    'player-card-square-remaining-label-offset': (0, 110),
    'player-card-square-max-chars': 20,
    'dealer-card-square-remaining-label-offset': (0, 57),
    'dealer-card-square-max-chars': 20,

    'card-value-label-font': prepare.FONTS["Saniretro"],
    'card-value-label-font-size': 72,
    'card-value-label-font-color': 'white',
    'card-value-label-offset': (60, 240),
    'card-initial-value': 5,

    'card-double-down-button-font': prepare.FONTS["Saniretro"],
    'card-double-down-button-font-size': 42,
    'card-double-down-button-font-color': 'white',
    'card-double-down-button-offset': (0, 150),
    'card-double-down-delay': 2,

    'card-focus-flash-timing': [
        (True, 0.5),
        (False, 0.1),
    ],

    'card-winning-flash-timing': [
        (True, 0.05),
        (False, 0.01),
        (True, 0.05),
        (False, 0.01),
        (True, 0.05),
        (False, 0.01),
        (True, 0.05),
        (False, 0.01),
        (True, 0.05),
        (False, 0.01),
    ],

    #
    # Player settings
    'player-cards-position': (prepare.RENDER_SIZE[0] / 2, prepare.RENDER_SIZE[1] - 600),
    'player-card-offsets': {
        1: [(0, 0)],
        2: [(-150, 0), (150, 0)],
        3: [(-300, 0), (0, 0), (300, 0)],
        4: [(-450, 0), (-150, 0), (150, 0), (450, 0)],
        5: [(-560, 0), (-280, 0), (0, 0), (280, 0), (560, 0)],
    },
    'dealer-card-offset': (-58, 240),

    #
    # Table settings
    'table-color': (0, 153, 51),

    #
    # Ball machine settings
    'machine-balls': range(1, 76),

    'machine-background-position': (780, 120),
    'machine-ball-position': (75, -50),
    'machine-ball-font': prepare.FONTS["Saniretro"],
    'machine-ball-font-size': 76,
    'machine-ball-font-color': 'white',
    'machine-ball-sprite-scale': 2.0,
    'machine-ball-angle-range': (-20, 20),
    'machine-ball-drop-initial-speed': 30,
    'machine-ball-drop-acceleration': 1,

    'spout-position': (30, 180),
    'spout-number': 6,

    'called-balls-position': (180, 80),
    'called-ball-number-font': prepare.FONTS["Saniretro"],
    'called-ball-number-font-size': 16,
    'called-ball-number-font-color': 'black',
    'called-ball-font-colors': ['black', 'white', 'grey'],
    'called-ball-sprite-lookup': {
        -2: (0, 0),
        -1: (0, 3),
        0: (0, 2),
        1: (0, 1),
        2: (0, 4),
    },
    'called-ball-font-color': {
        -2: 'white',
        -1: 'white',
        0: 'white',
        1: 'white',
        2: 'black',
    },

    #
    # Conveyor
    'conveyor-position': (-50, 240),
    'conveyor-speed': 450,
    'conveyor-repeat': 43,
    'conveyor-ball-position': 90,
    'conveyor-ball-drop-off': 1400,

    #
    # Cog wheel
    'machine-cog-position': (1360, 170),
    'machine-cog-speed': 450 / 600 * 500,
    'machine-speeds': [
        # Text, interval (s), balls to increase
        ('0', 11, 0),
        ('1', 10, 5),
        ('2', 9, 10),
        ('3', 8, 15),
        ('4', 7, 20),
        ('5', 6, 25),
        ('6', 5, 30),
        ('7', 4, 35),
        ('8', 3, 40),
    ],

    # Player picking
    'player-pick-sounds': [
        'bingo-pick-1',
        'bingo-pick-2',
        'bingo-pick-3',
        'bingo-pick-4',
    ],
    'player-pick-interval': 1.0,

    #
    # Card selection
    'card-selection-default': 2,
    'card-selection': [
        ('One', 1, (-70, -70)),
        ('Two', 2, (+70, -70)),
        ('Three', 3, (-70, 0)),
        ('Four', 4, (+70, 0)),
        ('Five', 5, (-70, 70)),
        ('Random', None, (+70, 70)),
    ],
    'card-selection-position': (170, 920),
    'card-selection-offsets': (0, 40),
    'card-selection-font': prepare.FONTS["Saniretro"],
    'card-selection-font-size': 32,
    'card-selection-font-color': 'white',
    'card-selection-size': (30, 45),
    'card-selection-scale': 0.6,

    #
    # Winning pattern display
    'winning-pattern-position': (520, 920),
    'winning-pattern-buttons': {
        'Lines': (-85, -70),
        'Stamp': (+85, -70),
        'Corners': (-85, 0),
        'Center': (+85, 0),
        'Coverall': (-85, 70),
        'Random': (+85, 70),
    },
    'winning-pattern-font': prepare.FONTS["Saniretro"],
    'winning-pattern-font-size': 32,
    'winning-pattern-font-color': 'white',
    'winning-pattern-scale': 1,
    'winning-pattern-logo-scale': 0.4,
    'winning-pattern-logo-offset': 55,
    'winning-pattern-label-width': 30,

    #
    # Money display
    'money-num-digits': 5,
    'money-digit-font': prepare.FONTS["Saniretro"],
    'money-digit-font-size': 60,
    'money-digit-font-color': 'black',
    'money-position': (580, 20),
    'money-offsets': (50, 0),
    'money-hide-offsets': (0, -16),
    'money-hide-repeats': 5,

    #
    # Flashing patterns
    'label-flash-delay-on': 0.1,
    'label-flash-states': [
        'BINGO', '', 'BINGO', '', 'BINGO', '',
        'B', 'I', 'N', 'G', 'O', '',
        'O', 'G', 'N', 'I', 'B', '',
        'BO', 'IG', 'N', '',
        'N', 'IG', 'BO',
        'BNO', 'IG', 'BNO', 'IG', 'BNO', 'IG',
        'BNO', 'IG', 'BNO', 'IG', 'BNO', 'IG',
    ],

    #
    # Randomized button display
    'randomize-button-number': 20,
    'randomize-button-delay': 25,
    'randomize-button-speed-up': 1.1,

    #
    # Next chip
    'next-chip-font': prepare.FONTS["Saniretro"],
    'next-chip-font-size': 34,
    'next-chip-font-color': 'black',
    'next-chip-size': (180, 45),
    'next-chip-scale': 1.7,
    'next-chip-position': (1260, 930),
    'next-chip-delay': 1,

    #
    # Menu bar
    'menu-bar-position': (1400 / 2, 50),
    'menu-bar-scale': 1.55,

    #
    # Debug settings
    'debug-auto-pick': False,
    'debug-restart-position': (1250, 120),
    'debug-next-ball-position': (1250, 200),
    'debug-new-cards-position': (1250, 280),
    'debug-auto-pick-position': (1250, 360),
}
