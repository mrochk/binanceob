from binance import Client, ThreadedWebsocketManager
from time import sleep
from ..orderbook import Orderbook
from ..event import Event
from ..util import *

class BinanceOrderbook(object):
    def __init__(self, symbol='BTCUSDT', display_depth=10):
        self.symbol = symbol if symbol is not None else BASE_SYMBOL
        self.display_depth = display_depth
        self.buffer = list()
        self.twm = ThreadedWebsocketManager() 

        self.twm.start()

    def start(self):
        u = None

        def callback(msg): 
            nonlocal u

            # sanity check
            if u is not None: assert msg['U'] == u+1
            u = msg['u']

            # append message
            self.buffer.append(msg)

            # log
            n_asks, n_bids = len(msg['a']), len(msg['b'])
            print(f'event received ({n_bids} bids, {n_asks} asks)')

        socket_name = self.__open_depth_stream(callback)
        snapshot = self.__get_snapshot()
        last_update_id = snapshot['lastUpdateId']
        orderbook = Orderbook(snapshot)
        self.__wait_first_event(last_update_id)
        self.__prune_buffer(last_update_id)

        try:
            while True: self.__loop(orderbook)
        except KeyboardInterrupt:
            print(f'\nshutting down...')
            self.__stop_stream(socket_name)
            self.__stop_twm()
            sleep(0.1)
            print('orderbook stopped successfully')
            return

    def __wait_first_event(self, luid):
        while True:
            for event in self.buffer:
                if self.__is_first_event(luid, event): return
            sleep(0.5)

    def __loop(self, orderbook):
        if not self.buffer: return
        msg = self.buffer.pop(0)
        event = Event(msg)
        orderbook.update(event)
        print()
        orderbook.display(self.display_depth) 

    def __get_snapshot(self, limit=1000):
        return Client().get_order_book(symbol=self.symbol, limit=limit)

    def __open_depth_stream(self, callback, interval=None):
        assert interval is None or interval in [100], 'interval must be None for 1000ms, 100 for 100ms'
        print(f'starting wss depth stream for symbol <{self.symbol}>...')
        try:
            socket_name = self.twm.start_depth_socket(callback, self.symbol, interval=None)
            print(f'depth stream ({socket_name}) started successfully for symbol <{self.symbol}>')
            sleep(1)
            return socket_name
        except: 
            printerr('an error occured when trying to start <twm.start_depth_socket>')
            raise Exception()

    @staticmethod
    def __is_first_event(last_update_id, event):
        U, u = event['U'], event['u']
        return U <= last_update_id+1 and last_update_id+1 <= u

    def __prune_buffer(self, last_update_id):
        before = len(self.buffer)
        while not self.__is_first_event(last_update_id, self.buffer[0]): self.buffer.pop(0)
        print(f'<prune buffer> removed {before - len(self.buffer)} events')
        sleep(1)

    def __stop_stream(self, stream_name):
        try:
            self.twm.stop_socket(stream_name)
            sleep(0.1)
            print(f'stream <{stream_name}> stopped successfully')
        except: printerr('error when trying to stop wss stream')

    def __stop_twm(self):
        try:  self.twm.stop(); sleep(0.1); print(f'twm stopped successfully')
        except: printerr('error when trying to stop twm')

    
