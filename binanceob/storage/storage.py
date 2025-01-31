from abc import ABC as Abstract, abstractmethod

from ..event import Event
from ..util import *

class Storage(Abstract):
    @abstractmethod
    def __init__(self): 
        pass

    @abstractmethod
    def start(self, symbol : str): 
        pass

    @abstractmethod
    def insert_event(self, event : Event) -> None: 
        '''
        Insert an event in database.
        '''
        pass

    @abstractmethod
    def close(self): 
        '''
        Close the storage instance properly.
        '''
        pass