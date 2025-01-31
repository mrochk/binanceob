from binanceob       import BinanceOrderbook
from binanceob.util  import BASE_SYMBOL

def parse_symbols(arg:str):
    if arg is None: return [BASE_SYMBOL]
    if ',' in arg:  return list(filter(lambda s: len(s)>0, arg.split(',')))
    return [arg.replace(',', '')]

def parse_yes_no(arg:str):
    assert arg in ['yes', 'no']
    return True if arg == 'yes' else False

if __name__ == '__main__': 
    ob = BinanceOrderbook(symbol=BASE_SYMBOL)
    ob.start()