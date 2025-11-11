"""
API key authentication - checks database first, then .env
"""
from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from config.api_config import default_api_config
from config.database import get_async_db  
from api.services.api_key_service import APIKeyService
import logging

logger = logging.getLogger(__name__)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, description="API key for authentication"),
    db: AsyncIOMotorDatabase = Depends(get_async_db)  
) -> str:
    """
    Verify API key - checks database first, then .env fallback
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database connection
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not x_api_key:
        logger.warning("Request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Check database first
    is_valid_in_db = await APIKeyService.validate_api_key(db, x_api_key)
    
    if is_valid_in_db:
        logger.debug(f"Valid API key from database: {x_api_key[:10]}...")
        return x_api_key
    
    # Fallback to .env
    if x_api_key in default_api_config.api_keys:
        logger.debug(f"Valid API key from .env: {x_api_key[:10]}...")
        return x_api_key
    
    # Not found in either
    logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"}
    )