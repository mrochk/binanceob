from binanceob       import BinanceOrderbook
from multiprocessing import Process
import argparse

BASE_SYMBOL = 'BTCUSDT'

def parse_symbols(arg:str):
    if arg is None: return [BASE_SYMBOL]
    if ',' in arg:  return list(filter(lambda s: len(s)>0, arg.split(',')))
    return [arg.replace(',', '')]

def parse_yes_no(arg:str):
    assert arg in ['yes', 'no']
    return True if arg == 'yes' else False

if __name__ == '__main__': 
    argparser = argparse.ArgumentParser(
        prog='Binance Orderbook',
        description="""Minimal Python project allowing one to run a 
                       Binance order book locally (for data collection purposes).""",
    )

    argparser.add_argument('-i', '--interval',  required=False, default='1s',        type=str, help='interval at which we update the order book, can be one of "1s" or "100ms"')
    argparser.add_argument('-s', '--symbols',   required=False, default=BASE_SYMBOL, type=str, help='list of symbols, comma separated; if not provided, defaults to "BTCUSDT"')
    argparser.add_argument('-w', '--writedata', required=False, default='yes',       type=str, help='write the collected data on interrupt')
    argparser.add_argument('--display',         required=False, default='yes',       type=str, help='display the order book in terminal, only the first symbol')
    argparser.add_argument('--depth',           required=False, default=10,          type=int, help='display the order book in terminal, only the first symbol')

    # get args
    args      = argparser.parse_args()
    symbols   = parse_symbols(args.symbols)
    writedata = parse_yes_no(args.writedata)
    display   = parse_yes_no(args.display)
    depth     = args.depth
    interval  = args.interval; assert interval in ['1s', '100ms'], 'interval must be "1s" or "100ms"'

    if len(symbols) == 1:
        symbol = symbols[0]
        ob = BinanceOrderbook(
            symbol=symbol, interval=interval, write_data=writedata, 
            display=display, depth=depth,
        )
        ob.start()
        exit(0)

    # if more than one symbol
    processes = list()
    for symbol in symbols:
        ob = BinanceOrderbook(
            symbol=symbol, 
            interval=interval, 
            write_data=writedata,             
            depth=depth,
            display=False,
        )
        process = Process(target=ob.start)
        processes.append(process)
    [process.start() for process in processes]
    try: [process.join()  for process in processes]
    except KeyboardInterrupt: exit(0)
