from pymongo import MongoClient
from config.settings import settings
import logging

class DatabaseConnection:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                self._client = MongoClient(settings.MONGODB_URI)
                self._db = self._client[settings.MONGODB_DATABASE]
                self._client.admin.command('ping')
                logging.info("Connected to MongoDB successfully")
            except Exception as e:
                logging.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    @property
    def db(self):
        return self._db
    
    def close_connection(self):
        if self._client:
            self._client.close()

db_connection = DatabaseConnection()