class Event(object):
    """
    Wrapper around the Binance 'Depth Diff.' event.
    https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#diff-depth-stream
    """
    def __init__(self, stream_msg : dict):
        Event.__msg_sanity_check(stream_msg)

        self.symbol          = stream_msg['s']
        self.timestamp       = stream_msg['E']
        self.asks_update     = stream_msg['a']
        self.bids_update     = stream_msg['b']
        self.first_update_id = stream_msg['U']
        self.last_update_id  = stream_msg['u']

    @staticmethod
    def __msg_sanity_check(msg : dict):
        errmsg = 'can not instantiate Event from that stream message'
        assert 'e' in msg.keys() and 'depthUpdate' == msg['e'], errmsg

    def get_n_bids_update(self): return len(self.bids_update)

    def get_n_asks_update(self): return len(self.asks_update)

    def __repr__(self):
        s =  f'Depth Diff @ {self.timestamp}'
        s += f' [Bids: {self.get_n_bids_update()} | '
        s += f'Asks: {self.get_n_asks_update()}]'
        return s