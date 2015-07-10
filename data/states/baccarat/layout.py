import json
import os.path
from operator import itemgetter

import pygame

from .table import BettingArea
from .cards import *
from .chips import *
from .ui import *

__all__ = ('load_layout', )


def get_rect(data):
    return pygame.Rect(*itemgetter('x', 'y', 'width', 'height')(data))


def load_layout(state, filename):
    def handle_player_hand(data):
        rect = get_rect(data).move(120, 0)
        deck = Deck(rect, stacking=(140, 500))
        state.player_hand = deck
        state.metagroup.add(deck)

    def handle_dealer_hand(data):
        rect = get_rect(data).move(120, 0)
        deck = Deck(rect, stacking=(140, 500))
        state.dealer_hand = deck
        state.metagroup.add(deck)

    def add_betting_area(name, rect):
        area = BettingArea(name, rect)
        area.drop_rect = rect.copy()
        state.betting_areas[name] = area

    def handle_player_bet(data):
        add_betting_area('player', get_rect(data))

    def handle_dealer_bet(data):
        add_betting_area('dealer', get_rect(data))

    def handle_tie_bet(data):
        add_betting_area('tie', get_rect(data))

    def handle_shoe(data):
        shoe = Deck(get_rect(data), decks=state.options['decks'])
        state.shoe = shoe
        state.metagroup.add(shoe)

    def handle_player_chips(data):
        chips = ChipPile(get_rect(data))
        chips.drop_rect = chips.rect.copy()
        state.player_chips = chips
        state.metagroup.add(chips, index=0)

    def handle_house_chips(data):
        chips = ChipRack(get_rect(data))
        state.house_chips = chips
        state.metagroup.add(chips, index=0)

    def handle_confirm_button(data):
        state.confirm_button_rect = get_rect(data)

    def handle_money_display(data):
        def update_text(*args):
            text.text = str(state.player_chips.value)

        state.interested_events.append(
            ('CHIPS_VALUE_CHANGE', update_text))

        text = TextSprite('', state.font)
        text.rect = get_rect(data)
        state.hud.add(text, layer=1)

    def handle_imagelayer(layer):
        fn = os.path.splitext(os.path.basename(layer['image']))[0]
        state.background_filename = fn

    def handle_objectgroup(layer):
        for thing in layer['objects']:
            get_handler('handle_{}'.format(thing['name']))(thing)

    get_handler = lambda name: handlers.get(name, lambda name: name)
    handlers = {k: v for k, v in locals().items() if k.startswith('handle_')}
    with open(filename) as fp:
        all_data = json.load(fp)

    for layer in all_data['layers']:
        get_handler('handle_{}'.format(layer['type']))(layer)
