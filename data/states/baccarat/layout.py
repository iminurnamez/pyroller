import pygame
import json
import os.path
from operator import itemgetter
from .ui import *


def get_rect(data):
    x, y, w, h = itemgetter('x', 'y', 'width', 'height')(data)
    return pygame.Rect(x, y, w, h)


def load_layout(state, filename):
    def handle_player_hand(data):
        deck = Deck(get_rect(data), stacking=(12, 200))
        state.player_hand = deck
        state.groups.append(deck)

    def handle_dealer_hand(data):
        deck = Deck(get_rect(data), stacking=(12, 200))
        state.dealer_hand = deck
        state.groups.append(deck)

    def handle_player_bet(data):
        pass

    def handle_dealer_bet(data):
        pass

    def handle_tie_bet(data):
        pass

    def handle_shoe(data):
        shoe = Deck(get_rect(data), decks=state.options['decks'])
        state.shoe = shoe
        state.groups.append(shoe)

    def handle_player_chips(data):
        chips = ChipPile(get_rect(data))
        state.player_chips = chips
        state.groups.append(chips)

    def handle_imagelayer(layer):
        fn = os.path.splitext(os.path.basename(layer['image']))[0]
        state.background_filename = fn

    def handle_objectgroup(layer):
        for thing in layer['objects']:
            f = get_handler('handle_{}'.format(thing['type']))
            f(thing)

    get_handler = lambda name: handlers.get(name, lambda name: name)
    handlers = {k: v for k, v in locals().items() if k.startswith('handle_')}
    with open(filename) as fp:
        all_data = json.load(fp)

    for layer in all_data['layers']:
        f = get_handler('handle_{}'.format(layer['type']))
        f(layer)
