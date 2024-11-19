import sys
import time
from typing import Dict
from binance import Client, ThreadedWebsocketManager

from queue import Queue

class DepthDiffEvent(object):
    def __init__(self, stream_msg : dict):
        assert 'e' in stream_msg.keys() and 'depthUpdate' == stream_msg['e'], \
            'can not instantiate OrderBookDepthMessage from that stream message'

        self.symbol          = stream_msg['s']
        self.timestamp       = stream_msg['E']
        self.asks_update     = stream_msg['a']
        self.bids_update     = stream_msg['b']
        self.first_update_id = stream_msg['U']
        self.last_update_id  = stream_msg['u']

    def get_n_bids_update(self): return len(self.bids_update)

    def get_n_asks_update(self): return len(self.asks_update)

    def __repr__(self):
        s =  f'Depth Diff @ {self.timestamp}'
        s += f' [Bids: {self.get_n_bids_update()} | '
        s += f'Asks: {self.get_n_asks_update()}]'
        return s

class Orderbook(object):
    def __init__(self, snapshot):
        self.midprice = self.volume = self.spread = 0

        self.bids_limit : list[self.Limit] = []
        self.asks_limit : list[self.Limit] = []

        self.price2asks : Dict[float, self.Limit] = dict()
        self.price2bids : Dict[float, self.Limit] = dict()

        bids = snapshot['bids']
        asks = snapshot['asks']

        self.__initialize(bids, asks)

        assert len(self.asks_limit) == len(self.bids_limit)
        self.depth = len(self.asks_limit)

        self.__remove_empty()
        self.__sort()

    def __initialize(self, bids, asks):
        for e in bids:
            price, qty = list(map(float, e))
            limit = self.Limit(price, qty, 'BID')
            self.bids_limit.append(limit)
            self.price2bids[price] = limit

        for e in asks:
            price, qty = list(map(float, e))
            limit = self.Limit(price, qty, 'ASK')
            self.asks_limit.append(limit)
            self.price2asks[price] = limit

    def __sort(self):
        by_price = lambda limit: limit.price
        self.bids_limit = sorted(self.bids_limit, key=by_price, reverse=True)
        self.asks_limit = sorted(self.asks_limit, key=by_price)

    def __remove_empty(self):
        i = 0
        for limit in self.asks_limit:
            if limit.quantity == 0.0:
                try:
                    self.asks_limit.remove(limit)
                    self.price2asks.pop(limit.price)
                    i += 1
                except ValueError:
                    printerr(ValueError, f'when trying to remove {limit}')
                except KeyError:
                    printerr(KeyError, f'when trying to remove {limit}')

        for limit in self.bids_limit:
            if limit.quantity == 0.0:
                try:
                    self.bids_limit.remove(limit)
                    self.price2bids.pop(limit.price)
                    i += 1
                except ValueError:
                    printerr(ValueError, f'when trying to remove {limit}')
                except KeyError:
                    printerr(KeyError, f'when trying to remove {limit}')

        print(f'<remove empty> removed {i} limits')

    def __get_midprice(self):
        bestask = self.asks_limit[0]
        bestbid = self.bids_limit[0]
        return (bestask.price + bestbid.price) / 2

    def __get_spread(self):
        return self.asks_limit[0].price - self.bids_limit[0].price

    def update(self, event : DepthDiffEvent): 
        updated = 0
        added = 0

        for up in event.asks_update:
            price, qty = list(map(float, up))

            if price in self.price2asks.keys():
                self.price2asks[price].quantity = qty 
                updated += 1
            else: 
                if qty == 0: continue
                new_limit =  self.Limit(price, qty, 'ASK')
                self.price2asks[price] = new_limit
                self.asks_limit.append(new_limit)
                added += 1

        for up in event.bids_update:
            price, qty = list(map(float, up))

            if price in self.price2bids.keys():
                self.price2bids[price].quantity = qty 
                updated += 1
            else: 
                if qty == 0: continue
                new_limit = self.Limit(price, qty, 'BID')
                self.price2bids[price] = new_limit
                self.bids_limit.append(new_limit)
                added += 1

        print(f'<update> added {added} limits and updated {updated} limits')

        self.__remove_empty()
        self.__sort()
        self.__remove_empty()

        self.midprice = self.__get_midprice()
        self.spread   = self.__get_spread()

    def display(self, nlimits=10):
        self.__sort()

        s = f'Orderbook (depth={self.depth}):\n'

        for i in range(nlimits-1, -1, -1): s += f'{self.asks_limit[i]}\n'

        s += ('-' * len(f'{self.asks_limit[0]}')) + '\n'
        s += f'MidPrice: {self.midprice:.2f}, Spread: {self.spread:.4f}\n'
        s += ('-' * len(f'{self.asks_limit[0]}')) + '\n'

        for i in range(nlimits): s += f'{self.bids_limit[i]}\n'

        print(s, flush=True)

    class Limit(object):
        def __init__(self, price, quantity, limit_type):
            if isinstance(price, str): price = float(price)
            if isinstance(quantity, str): quantity = float(quantity)
            self.limit_type = limit_type
            self.price = price
            self.quantity = quantity

        def __repr__(self):
            return f'{self.limit_type} Limit @ {self.price:.2f} of {self.quantity:.5f}'

BASE_SYMBOL = 'BTCUSDT'

def printerr(msg): sys.stderr.write(msg)

def get_symbol(): 
    return sys.argv[1] if len(sys.argv) > 1 else BASE_SYMBOL 

def get_snapshot(symbol, limit=1000):
    return Client().get_order_book(symbol=symbol, limit=limit)

def open_depth_stream(twm : ThreadedWebsocketManager, callback, symbol, interval=100):
    assert interval is None or interval == 100, 'interval must be None for 1s, or 100 for 100ms'
    print(f'starting wss depth stream for symbol <{symbol}>...')
    try:
        socket_name = twm.start_depth_socket(callback, symbol, interval=interval)
        print(f'depth stream ({socket_name}) started successfully for symbol <{symbol}>')
        return socket_name
    except: printerr('an error occured when trying to start <twm.start_depth_socket>')

def is_first_event(last_update_id, event):
    U, u = event['U'], event['u']
    return U <= last_update_id+1 and last_update_id+1 <= u

def prune_buffer(last_update_id, buffer : list):
    before = len(buffer)
    while not is_first_event(last_update_id, buffer[0]): buffer.pop(0)
    print(f'<prune buffer> removed {before - len(buffer)} events')

def main():
    symbol = get_symbol()

    print(f'starting orderbook for symbol <{symbol}>...')

    twm = ThreadedWebsocketManager()
    twm.start()

    buffer = list()
    u = None

    def callback_buffer(msg): 
        nonlocal u, buffer

        buffer.append(msg)

        if u is not None: assert msg['U'] == u+1
        u = msg['u']

        n_asks, n_bids, n_events = len(msg['a']), len(msg['b']), len(buffer)
        print(f'<callback> message received [{n_bids} bids, {n_asks} asks],', 
              f'buffer size is now {n_events}')

    def wait_for_first_event():
        while True:
            condition_list = [is_first_event(last_update_id, event) for event in buffer]
            if any(condition_list): return
            time.sleep(1)

    socket_name = open_depth_stream(twm, callback_buffer, symbol, 100); time.sleep(1)
    
    snapshot = get_snapshot(symbol)
    last_update_id = snapshot['lastUpdateId']

    orderbook = Orderbook(snapshot)

    wait_for_first_event()

    prune_buffer(last_update_id, buffer)

    time.sleep(20)

    twm.stop_socket(socket_name)
    twm.stop()

    while True:
        if buffer:
            msg = buffer.pop(0)
            event = DepthDiffEvent(msg)
            orderbook.update(event)
            time.sleep(2)
            print()
            print()
            orderbook.display(5)

    

if __name__ == '__main__': main()