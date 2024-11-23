from ..event import Event
from ..limit import BidLimit, AskLimit
from ..util import *

class Orderbook(object):
    def __init__(self, snapshot : dict):
        self.midprice = self.volume = self.spread = 0

        self.bids_limit = []
        self.asks_limit = []

        self.price2asks = dict()
        self.price2bids = dict()

        bids = snapshot['bids']
        asks = snapshot['asks']

        self.__initialize(bids, asks)

        assert len(self.asks_limit) == len(self.bids_limit)
        self.depth = len(self.asks_limit)

        self.__remove_empty()
        self.__sort()

    def update(self, event : Event): 
        updated = 0
        added = 0

        for up in event.asks_update:
            price, qty = list(map(float, up))

            if price in self.price2asks.keys():
                self.price2asks[price].quantity = qty 
                updated += 1
            elif qty > 0.0: 
                new_limit =  AskLimit(price, qty)
                self.price2asks[price] = new_limit
                self.asks_limit.append(new_limit)
                added += 1

        for up in event.bids_update:
            price, qty = list(map(float, up))

            if price in self.price2bids.keys():
                self.price2bids[price].quantity = qty 
                updated += 1
            elif qty > 0.0: 
                new_limit = BidLimit(price, qty)
                self.price2bids[price] = new_limit
                self.bids_limit.append(new_limit)
                added += 1

        print(f'added {added} limits and updated {updated} limits')

        self.__remove_empty()
        self.__sort()

        self.midprice = self.__get_midprice()
        self.spread   = self.__get_spread()

    def display(self, nlimits=10):
        self.__sort()

        s = f'Orderbook ({len(self.bids_limit)} bids, {len(self.asks_limit)} asks):\n'

        for i in range(nlimits-1, -1, -1): s += f'{self.asks_limit[i]}\n'

        s += ('-' * len(f'{self.asks_limit[0]}')) + '--\n'
        s += f'MidPrice: {self.midprice:.3f}, Spread: {self.spread:.2f}\n'
        s += ('-' * len(f'{self.asks_limit[0]}')) + '--\n'

        for i in range(nlimits): s += f'{self.bids_limit[i]}\n'

        print(s, flush=True)

    def __initialize(self, bids : list, asks : list):
        for e in bids:
            price, qty = list(map(float, e))
            limit = BidLimit(price, qty)
            self.bids_limit.append(limit)
            self.price2bids[price] = limit

        for e in asks:
            price, qty = list(map(float, e))
            limit = AskLimit(price, qty)
            self.asks_limit.append(limit)
            self.price2asks[price] = limit

    def __sort(self):
        by_price = lambda limit: limit.price
        self.bids_limit = sorted(self.bids_limit, key=by_price, reverse=True)
        self.asks_limit = sorted(self.asks_limit, key=by_price)

    def __remove_limit(self, limit):
        if isinstance(limit, AskLimit):
            try:
                self.asks_limit.remove(limit)
                self.price2asks.pop(limit.price)
            except ValueError:
                printerr(ValueError, f'when trying to remove {limit}')
                exit(1)
            except KeyError:
                printerr(KeyError, f'when trying to remove {limit}')
                exit(1)
        elif isinstance(limit, BidLimit):
            try:
                self.bids_limit.remove(limit)
                self.price2bids.pop(limit.price)
            except ValueError:
                printerr(ValueError, f'when trying to remove {limit}')
                exit(1)
            except KeyError:
                printerr(KeyError, f'when trying to remove {limit}')
                exit(1)
        else: 
            printerr(f'<remove_limit> error: limit is neither bid or ask: {limit}')
            exit(1)

    def __remove_empty(self):
        def emptylimit(limit : AskLimit | BidLimit): return limit.empty()

        toremove = list(filter(emptylimit, self.asks_limit))
        for limit in toremove: self.__remove_limit(limit)

        toremove = list(filter(emptylimit, self.bids_limit))
        for limit in toremove: self.__remove_limit(limit)

    def __get_midprice(self):
        bestask = self.asks_limit[0]
        bestbid = self.bids_limit[0]
        return (bestask.price + bestbid.price) / 2

    def __get_spread(self):
        return self.asks_limit[0].price - self.bids_limit[0].price