from pymongo import MongoClient 

from binanceob.util import * 

if __name__ == '__main__':
    client = MongoClient(MONGODB_HOST)

    db = client.get_database(MONGODB_DBNAME)

    collections = db.list_collections()

    print('Collections:')
    for c in collections: print(c)

    btcusdt = db[BASE_SYMBOL]

    n_messages = len(list(btcusdt.find()))
    print(f'\nn_messages in {BASE_SYMBOL} = {n_messages}')

