"""
API Key service - business logic
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
import secrets
import hashlib
import logging
from repositories.api_key_repository import (
    save_api_key,
    get_api_key_by_hash,
    get_all_api_keys,
    deactivate_api_key
)
from models.api_key import APIKeyModel

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for API key operations"""
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure random API key
        
        Returns:
            API key string
        """
        random_part = secrets.token_urlsafe(32)
        return f"key_{random_part}"
    
    @staticmethod
    def hash_api_key(key: str) -> str:
        """
        Hash an API key using SHA256
        
        Args:
            key: Plain text API key
            
        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    async def create_api_key(db: AsyncIOMotorDatabase, name: str) -> dict:
        """
        Create a new API key
        
        Args:
            db: Database connection
            name: Name/description for the key
            
        Returns:
            Dictionary with key and metadata
        """
        try:
            # Generate key
            plain_key = APIKeyService.generate_api_key()
            key_hash = APIKeyService.hash_api_key(plain_key)
            
            # Create model
            api_key = APIKeyModel(
                key_hash=key_hash,
                name=name
            )
            
            # Save to database
            success = await save_api_key(db, api_key.model_dump())
            
            if not success:
                raise Exception("Failed to save API key")
            
            # Return key data (plain key only shown once!)
            return {
                'key': plain_key,
                'key_hash': key_hash,
                'name': api_key.name,
                'created_at': api_key.created_at,
                'is_active': api_key.is_active
            }
            
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            raise
    
    @staticmethod
    async def validate_api_key(db: AsyncIOMotorDatabase, key: str) -> bool:
        """
        Validate an API key (check if exists and is active)
        
        Args:
            db: Database connection
            key: Plain text API key
            
        Returns:
            True if valid and active
        """
        try:
            key_hash = APIKeyService.hash_api_key(key)
            api_key = await get_api_key_by_hash(db, key_hash)
            return api_key is not None
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False
    
    @staticmethod
    async def list_api_keys(db: AsyncIOMotorDatabase) -> List[dict]:
        """
        List all API keys
        
        Args:
            db: Database connection
            
        Returns:
            List of API key metadata (no plain keys)
        """
        return await get_all_api_keys(db)
    
    @staticmethod
    async def revoke_api_key(db: AsyncIOMotorDatabase, key_id: str) -> bool:
        """
        Revoke/deactivate an API key
        
        Args:
            db: Database connection
            key_id: MongoDB ObjectId as string
            
        Returns:
            True if successful
        """
        return await deactivate_api_key(db, key_id)