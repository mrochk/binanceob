import sys
from binanceob import BinanceOrderbook

if __name__ == '__main__': 
    symbol = sys.argv[1] if len(sys.argv) > 1 else None
    BinanceOrderbook(symbol, 20).start()
