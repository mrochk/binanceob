from time    import time
from ..event import Event
from ..limit import BidLimit, AskLimit
from ..util  import *

class Orderbook(object):
    def __init__(self, snapshot : dict, symbol : str, max_limits : int = 1000):
        self.symbol   = symbol
        self.midprice = self.volume = self.spread = 0

        self.max_limits = max_limits

        self.bids = []
        self.asks = []

        self.price2asks = dict()
        self.price2bids = dict()

        bids = snapshot['bids']
        asks = snapshot['asks']

        self.__initialize(bids, asks)

        assert len(self.asks) == len(self.bids)
        self.depth = len(self.asks)

        self.__remove_empty_limits()
        self.__sort_limits()

    def update(self, event : Event): 
        addedA, updatedA = self.update_asks(event.asks_update)
        addedB, updatedB = self.update_bids(event.bids_update)

        added   = addedA   + addedB
        updated = updatedA + updatedB

        print(f'<{self.symbol}> added {added} limits and updated {updated} limits')

        self.__remove_empty_limits()
        self.__sort_limits()

        # remove if too many limits in ob
        if len(self.asks) > self.max_limits: self.asks = self.asks[:self.max_limits]
        if len(self.bids) > self.max_limits: self.bids = self.bids[:self.max_limits]

        self.midprice = self.__get_midprice()
        self.spread   = self.__get_spread()

    def update_asks(self, updates):
        added = updated = 0
        for up in updates:
            price, qty = list(map(float, up))

            if price in self.price2asks.keys():
                self.price2asks[price].quantity = qty 
                updated += 1
            elif qty > 0.0: 
                new_limit =  AskLimit(price, qty)
                self.price2asks[price] = new_limit
                self.asks.append(new_limit)
                added += 1
        return added, updated

    def update_bids(self, updates):
        added = updated = 0
        for up in updates:
            price, qty = list(map(float, up))

            if price in self.price2bids.keys():
                self.price2bids[price].quantity = qty 
                updated += 1
            elif qty > 0.0: 
                new_limit = BidLimit(price, qty)
                self.price2bids[price] = new_limit
                self.bids.append(new_limit)
                added += 1
        return added, updated

    def as_dict(self, depth=10):
        return {
            'timestamp': time(),
            'bids': [l.as_dict() for l in self.bids[:depth]],
            'asks': [l.as_dict() for l in self.asks[:depth]],
        }

    def display(self, nlimits=10):
        self.__sort_limits()

        s = f'Orderbook ({len(self.bids)} bids, {len(self.asks)} asks):\n'

        for i in range(nlimits-1, -1, -1): s += f'{self.asks[i]}\n'

        s += ('-' * len(f'{self.asks[0]}')) + '--\n'
        s += f'MidPrice: {self.midprice:.3f}, Spread: {self.spread:.2f}\n'
        s += ('-' * len(f'{self.asks[0]}')) + '--\n'

        for i in range(nlimits): s += f'{self.bids[i]}\n'

        print(s, flush=True)

    def __initialize(self, bids : list, asks : list):
        for e in bids:
            price, qty = list(map(float, e))
            limit = BidLimit(price, qty)
            self.bids.append(limit)
            self.price2bids[price] = limit

        for e in asks:
            price, qty = list(map(float, e))
            limit = AskLimit(price, qty)
            self.asks.append(limit)
            self.price2asks[price] = limit

    def __sort_limits(self):
        by_price = lambda limit: limit.price
        self.bids = sorted(self.bids, key=by_price, reverse=True)
        self.asks = sorted(self.asks, key=by_price)

    def __remove_limit(self, limit):
        if isinstance(limit, AskLimit):
            try:
                self.asks.remove(limit)
                self.price2asks.pop(limit.price)
            except ValueError:
                print_error(ValueError, f'when trying to remove {limit}')
                exit(1)
            except KeyError:
                print_error(KeyError, f'when trying to remove {limit}')
                exit(1)
        elif isinstance(limit, BidLimit):
            try:
                self.bids.remove(limit)
                self.price2bids.pop(limit.price)
            except ValueError:
                print_error(ValueError, f'when trying to remove {limit}')
                exit(1)
            except KeyError:
                print_error(KeyError, f'when trying to remove {limit}')
                exit(1)
        else: 
            print_error(f'<remove_limit> error: limit is neither bid or ask: {limit}')
            exit(1)

    def __remove_empty_limits(self):
        def emptylimit(limit : AskLimit | BidLimit): return limit.empty()

        toremove = list(filter(emptylimit, self.asks))
        for limit in toremove: self.__remove_limit(limit)

        toremove = list(filter(emptylimit, self.bids))
        for limit in toremove: self.__remove_limit(limit)

    def __get_midprice(self):
        bestask = self.asks[0]
        bestbid = self.bids[0]
        return (bestask.price + bestbid.price) / 2

    def __get_spread(self):
        return self.asks[0].price - self.bids[0].price
