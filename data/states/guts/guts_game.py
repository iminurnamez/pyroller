from random import randint
from ... import prepare
from ...components.cards import Deck
from ...components.labels import Label
from .guts_helpers import DealerButton

class GutsGame(object):
    def __init__(self, players, dealer_index, player, casino_player, bet, pot, free_ride):
        self.players = players 
        self.dealer_index = dealer_index
        self.dealer = self.players[self.dealer_index]
        self.dealer_button = DealerButton(self.dealer.dealer_button_topleft)
        self.player = player
        self.casino_player = casino_player
        self.bet = bet
        self.pot = pot
        self.deal_queue = self.make_deal_queue()
        self.deck = Deck((20,20))
        self.font = prepare.FONTS["Saniretro"]
        self.make_labels()
        self.free_ride = free_ride
        
    
    def make_deal_queue(self):
        left = self.players[self.dealer_index + 1:]
        right = self.players[:self.dealer_index + 1]
        return left + right
    
    def make_labels(self):
        color= "antiquewhite" if self.pot != 420 else "darkgreen"
        self.pot_label = Label(self.font, 48, "Pot: ${}".format(self.pot), color, {"center": (700, 525)})
        
    def compare_hands(self, player1, player2):
        h1 = []
        h2 = []
        for player, vals in [(player1, h1), (player2, h2)]:
            for card in player.cards:
                val = card.value if card.value != 1 else 14
                vals.append(val)
        h1.sort(reverse=True)
        h2.sort(reverse=True)
        if h1 == h2:
            return [player1, player2]
        elif h2[0] == h2[1]:
            if h1[0] == h1[1] and h1[0] > h2[0]:
                return [player1]                
            else:
                return [player2]
        else:
            if h1[0] > h2[0] or h1[0] == h1[1]:
                return [player1]            
            elif h1[0] == h2[0]:
                if h1[1] > h2[1]:
                    return [player1]
                else:
                    return [player2]
            else:
                return [player2]

    def get_winners(self):
        stayed = [x for x in self.players if x.stayed]
        best = []
        for stayer in stayed:
            if not best:
                best.append(stayer)
            else:
                new_best = []
                for b in best:
                    new_best.extend(self.compare_hands(b, stayer))
                best = new_best
        return best
                
            
    def draw(self, surface):
        self.pot_label.draw(surface)
        self.deck.draw(surface)
        self.dealer_button.draw(surface)