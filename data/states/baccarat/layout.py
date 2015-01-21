import pygame
import json
import os.path
from operator import itemgetter
from .ui import *


def get_rect(data):
    return pygame.Rect(*itemgetter('x', 'y', 'width', 'height')(data))


def load_layout(state, filename):
    def handle_player_hand(data):
        rect = get_rect(data).move(120, 0)
        deck = Deck(rect, stacking=(140, 500))
        deck.auto_arrange = False
        state.player_hand = deck
        state.groups.append(deck)

    def handle_dealer_hand(data):
        rect = get_rect(data).move(120, 0)
        deck = Deck(rect, stacking=(140, 500))
        deck.auto_arrange = False
        state.dealer_hand = deck
        state.groups.append(deck)

    def handle_player_bet(data):
        state.betting_areas['player'] = get_rect(data)

    def handle_dealer_bet(data):
        state.betting_areas['dealer'] = get_rect(data)

    def handle_tie_bet(data):
        state.betting_areas['tie'] = get_rect(data)

    def handle_shoe(data):
        shoe = Deck(get_rect(data), decks=state.options['decks'])
        state.shoe = shoe
        state.groups.append(shoe)

    def handle_player_chips(data):
        chips = ChipPile(get_rect(data))
        state.player_chips = chips
        state.groups.append(chips)

    def handle_house_chips(data):
        chips = ChipRack(get_rect(data))
        state.house_chips = chips
        state.groups.append(chips)

    def handle_imagelayer(layer):
        fn = os.path.splitext(os.path.basename(layer['image']))[0]
        state.background_filename = fn

    def handle_objectgroup(layer):
        for thing in layer['objects']:
            get_handler('handle_{}'.format(thing['type']))(thing)

    get_handler = lambda name: handlers.get(name, lambda name: name)
    handlers = {k: v for k, v in locals().items() if k.startswith('handle_')}
    with open(filename) as fp:
        all_data = json.load(fp)

    for layer in all_data['layers']:
        get_handler('handle_{}'.format(layer['type']))(layer)
