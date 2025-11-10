"""
API Key repository - database operations
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)


async def save_api_key(db: AsyncIOMotorDatabase, api_key_data: dict) -> bool:
    """
    Save an API key to database
    
    Args:
        db: Database connection
        api_key_data: API key data dictionary
        
    Returns:
        True if successful
    """
    try:
        result = await db.api_keys.insert_one(api_key_data)
        logger.info(f"Created API key: {api_key_data['name']}")
        return True
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        return False


async def get_api_key_by_hash(db: AsyncIOMotorDatabase, key_hash: str) -> Optional[dict]:
    """
    Get an API key by its hash
    
    Args:
        db: Database connection
        key_hash: SHA256 hash of the key
        
    Returns:
        API key document or None
    """
    try:
        api_key = await db.api_keys.find_one({'key_hash': key_hash, 'is_active': True})
        return api_key
    except Exception as e:
        logger.error(f"Error getting API key: {e}")
        return None


async def get_all_api_keys(db: AsyncIOMotorDatabase) -> List[dict]:
    """
    Get all API keys
    
    Args:
        db: Database connection
        
    Returns:
        List of API key documents
    """
    try:
        cursor = db.api_keys.find()
        api_keys = await cursor.to_list(length=None)
        
        # Convert _id to string
        for key in api_keys:
            key['id'] = str(key.pop('_id'))
        
        return api_keys
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return []


async def deactivate_api_key(db: AsyncIOMotorDatabase, key_id: str) -> bool:
    """
    Deactivate an API key by ID
    
    Args:
        db: Database connection
        key_id: MongoDB ObjectId as string
        
    Returns:
        True if successful
    """
    try:
        object_id = ObjectId(key_id)
        result = await db.api_keys.update_one(
            {'_id': object_id},
            {'$set': {'is_active': False}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Deactivated API key: {key_id}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error deactivating API key: {e}")
        return False


async def create_api_key_indexes(db: AsyncIOMotorDatabase):
    """
    Create indexes for api_keys collection
    
    Args:
        db: Database connection
    """
    try:
        await db.api_keys.create_index('key_hash', unique=True)
        await db.api_keys.create_index('is_active')
        logger.info("Created API key indexes")
    except Exception as e:
        logger.error(f"Error creating API key indexes: {e}")