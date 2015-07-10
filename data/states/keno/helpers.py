import random

#http://casinogamblingtips.info/tag/pay-table
PAYTABLE = [
    [(0, 0)], #0
    [(1, 3)], #1
    [(2, 12)], #2
    [(2, 1), (3, 40)], #3
    [(2, 1), (3, 2), (4, 120)], #4
    [(3, 1), (4, 18), (5, 800)], #5
    [(3, 1), (4, 3), (5, 80), (6, 1500)], #6
    [(4, 1), (5, 18), (6, 360), (7, 5000)], #7
    [(5, 10), (6, 75), (7, 1000), (8, 15000)], #8
    [(5, 4), (6, 35), (7, 250), (8, 3000), (9, 20000)], #9
    [(5, 2), (6, 15), (7, 100), (8, 1500), (9, 8000), (10, 25000)], #10
]

def pick_numbers(spot):
    numbers = []
    while len(numbers) < spot:
        number = random.randint(0, 79)
        if number not in numbers:
            numbers.append(number)
    return numbers

def is_winner(spot, hit):
    paytable = PAYTABLE[spot]
    for entry in paytable:
        if entry[0] == hit:
            return True
    return False
