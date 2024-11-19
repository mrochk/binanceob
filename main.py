import sys
import time
from binance import Client, ThreadedWebsocketManager

from enum import Enum

class Orderbook(object):
    def __init__(self, snapshot, n_limits_display=3):
        print(snapshot.keys())

        self.n_limits_display = n_limits_display

        bids = snapshot['bids']
        asks = snapshot['asks']

        self.bids_limit = []
        self.asks_limit = []

        for e in bids:
            price, qty = e
            limit = self.Limit(price, qty, 'BID')
            self.bids_limit.append(limit)

        for e in asks:
            price, qty = e
            limit = self.Limit(price, qty, 'ASK')
            self.asks_limit.append(limit)

        self.bids_limit = sorted(self.bids_limit, key=lambda limit: limit.price, reverse=True)
        self.asks_limit = sorted(self.asks_limit, key=lambda limit: limit.price)

    def __repr__(self):
        s = f'Orderbook:\n'
        for i in range(self.n_limits_display-1, -1, -1): 
            s += f'{self.asks_limit[i]}\n'
        s += ('-' * len(f'{self.asks_limit[-i]}')) + '\n'
        for i in range(self.n_limits_display): s += f'{self.bids_limit[i]}\n'
        return s

    class Limit(object):
        def __init__(self, price, quantity, limit_type):
            if isinstance(price, str): price = float(price)
            if isinstance(quantity, str): quantity = float(quantity)
            self.limit_type = limit_type
            self.price = price
            self.quantity = quantity

        def __repr__(self):
            return f'{self.limit_type} Limit @ {self.price:.2f} of {self.quantity:.5f}'

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

    buffer = []
    u = None

    def callback_buffer(msg): 
        nonlocal u

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

    socket_name = open_depth_stream(twm, callback_buffer, symbol, None); time.sleep(1)
    
    orderbook = get_snapshot(symbol)
    last_update_id = orderbook['lastUpdateId']

    ob = Orderbook(orderbook, 10)
    print(ob)

    wait_for_first_event()

    prune_buffer(last_update_id, buffer)

    time.sleep(5)

    twm.stop_socket(socket_name)
    twm.stop()

    event = buffer[0]
    obmsg = DepthDiffEvent(event)
    print(obmsg)

if __name__ == '__main__': main()