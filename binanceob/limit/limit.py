class Limit(object):
    def __init__(self, price : float, quantity : int, limit_type : str):
        if isinstance(price, str): price = float(price)
        if isinstance(quantity, str): quantity = float(quantity)
        self.limit_type = limit_type
        self.price = price
        self.quantity = quantity

    def empty(self): return self.quantity == 0.0

    def __repr__(self):
        return f'{self.limit_type} Limit @ {self.price:.2f} of {self.quantity:.5f}'

class AskLimit(Limit):
    def __init__(self, price : float, quantity : int):
        super().__init__(price, quantity, 'ASK')

class BidLimit(Limit):
    def __init__(self, price : float, quantity : int):
        super().__init__(price, quantity, 'BID')