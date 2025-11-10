"""
API key authentication
"""
from fastapi import Header, HTTPException, status
from typing import Optional
from config.api_config import default_api_config
import logging

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: Optional[str] = Header(None, description="API key for authentication")) -> str:
    """
    Verify API key from request header
    
    Args:
        x_api_key: API key from X-API-Key header
        
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
    
    if x_api_key not in default_api_config.api_keys:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    logger.debug(f"Valid API key: {x_api_key[:10]}...")
    return x_api_key