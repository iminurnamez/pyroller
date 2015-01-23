class InsufficientFundsException(Exception):
    pass

class Pot(object):
    '''
    Current money in whole dollars at stake.
    '''
    def __init__(self, wallet):
        '''
        Initialize a pot with a provided wallet.
        '''
        self.wallet     = wallet
        self._balance   = 0         #running total put into pot
        self.paid       = False     #has this round been purchased?
        self.won        = 0         #what has been won prior to a clear
        
    def change_bet(self, amount):
        '''
        Increase current balance by given int(amount)
        '''
        self._balance += amount
        self.make_bet(amount)
        
    def repeat_bet(self):
        self.make_bet(self._balance)
        
    def make_bet(self, amount):
        '''
        Deduct from wallet if able and set paid=True
        '''
        try:
            self.wallet.decrease(int(amount))
            self.paid = True
        except InsufficientFundsException:
            raise
        
    def clear_bet(self):
        '''
        Execute payout(1) so whatever is in pot goes back to player. Set balance to zero
        Also set won to zero (ensure after calling payout so that player receives money back)
        '''
        self.payout(1)
        self._balance = 0
        self.won = 0
        
    def payout(self, amount):
        '''
        Increase wallet balance by current pot balance * amount
        '''
        money = self._balance * int(amount)
        self.won += money
        self.wallet.increase(money)
        self.paid = False

class Wallet(object):
    '''
    Available money in whole dollars.
    
    increase(amount): increase balance by given amount
    decrease(amount): decrease balance by given amount. If allow_negative, balance can be negative.
    
    set balance(amount): will set balance to amount. If allow_negative, balance can be negative.
    get balance: returns balance 
    '''
    def __init__(self, balance=0, allow_negative=False):
        '''
        Initialize a wallet with provided int(balance) where default=0
        Set allow_negative to True if negative balance is permitted
        '''
        self.allow_negative  = allow_negative
        self._balance        = int(balance)
        
    @property
    def balance(self):
        return self._balance
        
    @balance.setter
    def balance(self, amount):
        if not self.allow_negative and amount < 0:
            raise ValueError("Must allow_negative=True if using negative amount")
        else:
            self._balance = int(amount)
        
    def increase(self, amount):
        '''
        Increase balance by provided int(amount).
        '''
        self._balance += int(amount)
        
    def decrease(self, amount):
        '''
        Decrease balance by provided int(amount).
        Throws InsufficientFundsException if allow_negative is False(default)
        '''
        if self.allow_negative:
            self._balance -= int(amount)
        else:
            remaining = self._balance - int(amount)
            if remaining >= 0:
                self._balance = remaining
            else:
                raise InsufficientFundsException()

def print_balance(wallet):
    print("wallet balance={0}".format(wallet.balance))
    
def print_pot(pot):
    print("pot balance={0}".format(pot._balance))
    
def print_can_play(pot):
    print("can play(bought)={0}".format(pot.bought))

if __name__ == '__main__':
    wallet = Wallet(100)
    wallet.allow_negative = True
    pot    = Pot(wallet)
    print_can_play(pot)
    
    print("bet 75")
    pot.make_bet(75)
    print_pot(pot)
    print_balance(wallet)
    print_can_play(pot)
    
    print("won base 100")
    pot.payout(100)
    print_pot(pot)
    print_balance(wallet)
    print_can_play(pot)
