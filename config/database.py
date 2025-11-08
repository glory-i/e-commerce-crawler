# for database configuration 
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load db credentials from environment variables 
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")
        self.async_client = None
        self.sync_client = None
        
    async def connect_async(self):
        try:
            self.async_client = AsyncIOMotorClient(self.mongodb_uri)
            await self.async_client.admin.command('ping')
            logger.info(f"Connected to MongoDB (Async): {self.db_name}")
            return self.async_client[self.db_name]
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB (Async): {e}")
            raise
    
    def connect_sync(self):
        try:
            self.sync_client = MongoClient(self.mongodb_uri)
            self.sync_client.admin.command('ping')
            logger.info(f"Connected to MongoDB (Sync): {self.db_name}")
            return self.sync_client[self.db_name]
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB (Sync): {e}")
            raise
    
    async def close_async(self):
        if self.async_client:
            self.async_client.close()
            logger.info("Closed async MongoDB connection")
    
    def close_sync(self):
        if self.sync_client:
            self.sync_client.close()
            logger.info("Closed sync MongoDB connection")


# Global database config instance
db_config = DatabaseConfig()


async def get_async_db():
    return await db_config.connect_async()


def get_sync_db():
    return db_config.connect_sync()