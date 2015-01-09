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
        state.shoe.rect = get_rect(data)
        pass

    def handle_player_chips(data):
        pass

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
