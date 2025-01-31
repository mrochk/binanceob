import json
from pymongo            import MongoClient
from pymongo.database   import Database
from pymongo.collection import Collection

from ..storage import Storage, Event, print_error

HOST = 'mongodb://localhost:27017/'

class Mongo(Storage):
    client     : MongoClient
    db         : Database
    collection : Collection

    def __init__(self):
        self.client = MongoClient(HOST)
        self.db = self.client['database']

    def start(self, symbol : str):
        self.collection = self.db[symbol]

    def insert_event(self, event : Event):
        try:
            message = event.asdict()
            self.collection.insert_one(message)
        except Exception as e:
            print(e)
            print_error('<mongo> error when trying to insert msg')

    def close(self): 
        print('<mongo> closing database')
        self.client.close()
        print('<mongo> database closed')