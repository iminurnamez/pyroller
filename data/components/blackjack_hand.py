from ..components.chips import BetPile

class Hand(object):
    card_values = {i: i for i in range(2, 11)}
    face_values = {i: 10 for i in range(11, 14)}
    card_values.update(face_values)
    card_values[1] = "Ace"
    
    def __init__(self, topleft, cards=None, bet_chips=None):
        self.tl = topleft
        self.cards = cards if cards is not None else []
        self.final = False
        self.busted = False
        self.winner = False
        self.loser = False
        self.push = False
        self.blackjack = False
        self.bet = BetPile((self.tl[0], self.tl[1] - 20), (48, 30), bet_chips)
        
    def get_scores(self):
        scores = []
        scores.append([])
        cards = self.cards
        for card in cards:
            if card.value == 1:
                new_scores = []
                for score in scores:
                    new_scores.append(score + [1])
                    new_scores.append(score + [11])
                    scores = new_scores
            else:
                for score in scores:
                    score.append(self.card_values[card.value])
        return [sum(score) for score in scores]
        
    def best_score(self):
        scores = self.get_scores()
        best = None
        for score in scores:
            if score <= 21:
                if best is None:
                    best = score
                elif best < score:
                    best = score
        if best:
            return best
        else:
            return None