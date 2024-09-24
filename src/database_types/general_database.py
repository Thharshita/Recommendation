from abc import ABC, abstractmethod

class Database(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def insert(self):
        pass
    
    @abstractmethod
    async def query(self):
        pass

    @abstractmethod
    async def delete(self):
        pass

    @abstractmethod
    async def check_and_delete_project_id(self):
        pass

    @abstractmethod
    async def store_raw_corpus(self):
        pass

