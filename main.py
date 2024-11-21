import sys, time
from binanceob import Orderbook, Event
from binance import Client, ThreadedWebsocketManager

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

def stop_stream(twm : ThreadedWebsocketManager, stream_name):
    try:
        twm.stop_socket(stream_name)
        time.sleep(0.1)
        print(f'stream <{stream_name}> stopped successfully')
    except: printerr('error when trying to stop wss stream')

def stop_twm(twm : ThreadedWebsocketManager):
    try:  twm.stop(); time.sleep(0.1); print(f'twm stopped successfully')
    except: printerr('error when trying to stop twm')

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

    socket_name = open_depth_stream(twm, callback_buffer, symbol, None); time.sleep(1)
    
    snapshot = get_snapshot(symbol)
    last_update_id = snapshot['lastUpdateId']

    orderbook = Orderbook(snapshot)

    wait_for_first_event()

    prune_buffer(last_update_id, buffer)

    time.sleep(2)

    try:
        while True:
            if not buffer: continue
            msg = buffer.pop(0)
            event = Event(msg)
            orderbook.update(event)
            print()
            print()
            orderbook.display(20)
    except KeyboardInterrupt:
        print(f'\nshutting down...')
        stop_stream(twm, socket_name)
        stop_twm(twm)
        time.sleep(0.1)
        print('orderbook stopped successfully')
        exit(0)


if __name__ == '__main__': main()