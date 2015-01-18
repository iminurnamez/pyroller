import pygame as pg



    
class BlackjackBot(object):
    def __init__(self, game):
        self.game = game
        self.updates = {
                "Betting": self.betting,
                "Dealing": self.dealing,
                "Player Turn": self.player_turn,
                "Dealer Turn": self.dealer_turn,
                "End Round": self.end_round,
                "Show Results": self.show_results}
        self.break_points = {
                        1: 17,
                        2: 12,
                        3: 12,
                        4: 12,
                        5: 15,
                        6: 16,
                        7: 16,
                        8: 16,
                        9: 17,
                        10: 17,
                        11: 17,
                        12: 17,
                        13: 17}
        
        self.tick_count = 0
        self.tick_delay = 10
        self.active = True
        
    def betting(self):
        if not self.game.current_player_hand.bet.get_chip_total():
            chips = self.game.player.chip_pile.withdraw_chips(5)
            self.game.current_player_hand.bet.add_chips(chips)
        self.game.deal()
        
    def dealing(self):
        pass
        
    def player_turn(self):
        hand = self.game.current_player_hand
        best_score = hand.best_score()
        player_total = self.game.player.chip_pile.get_chip_total()
        bet_amount = self.game.current_player_hand.bet.get_chip_total()
        showing = sum([x.value for x in self.game.dealer.hand.cards if x.face_up])
        if len(self.game.moving_cards) < 1:
            
            if all([x.value == 1 for x in hand.cards]):
                if player_total >= bet_amount:
                    self.game.split_hand()
            if best_score == 11 and showing not in (10, 11, 12, 13, 1):
                if player_total >= bet_amount:
                    self.game.double_down()
                else:
                    self.game.hit_click()
            elif best_score < self.break_points[showing]:
                self.game.hit_click()
            else:
                self.game.stand()
        
    def dealer_turn(self):
        pass
        
    def show_results(self):
        self.game.quick_bet_click()
    
    def end_round(self):
        pass
        
    def update(self):
        if self.active:
            if not self.tick_count % self.tick_delay:
                self.updates[self.game.state]()
            
            self.tick_count += 1