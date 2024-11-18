import sys
import time
from binance import Client, ThreadedWebsocketManager

BASE_SYMBOL = 'BTCUSDT'

def printerr(msg): sys.stderr.write(msg)

def get_symbol(): 
    return sys.argv[1] if len(sys.argv) > 1 else BASE_SYMBOL 

def get_snapshot(symbol, limit=1000):
    return Client().get_order_book(symbol=symbol, limit=limit)

def open_depth_stream(twm : ThreadedWebsocketManager, callback, symbol, interval=100):
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

    socket_name = open_depth_stream(twm, callback_buffer, symbol); time.sleep(1)
    
    orderbook = get_snapshot(symbol)
    last_update_id = orderbook['lastUpdateId']

    wait_for_first_event()

    prune_buffer(last_update_id, buffer)

    time.sleep(20)

    twm.stop_socket(socket_name)
    twm.stop()

if __name__ == '__main__': main()