HAND_RANKS = {'ROYAL_FLUSH'     : 0,
              'STR_FLUSH'       : 1,
              '4_OF_A_KIND'     : 2,
              'FULL_HOUSE'      : 3,
              'FLUSH'           : 4,
              'STRAIGHT'        : 5,
              'THREE_OF_A_KIND' : 6,
              'TWO_PAIR'        : 7,
              'JACKS_OR_BETTER' : 8}
NO_HAND = 99
PAYTABLE = [
    (250, 50, 25, 8, 6, 4, 3, 2, 1),
    (500, 100, 50, 16, 12, 8, 6, 4, 2),
    (750, 150, 75, 24, 18, 12, 9, 6, 3),
    (1000, 200, 100, 32, 24, 16, 12, 8, 4),
    (4000, 250, 125, 40, 30, 20, 15, 10, 5),
]
RANKS = ('ROYAL FLUSH', 'STR. FLUSH', '4 OF A KIND', 'FULL HOUSE',
         'FLUSH', 'STRAIGHT', 'THREE OF A KIND', 'TWO PAIR', 'JACKS OR BETTER')