"""
Shared dependencies for API routes
"""
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from config.database import get_async_db
from api.auth import verify_api_key
from slowapi import Limiter
from slowapi.util import get_remote_address
from config.api_config import default_api_config


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


async def get_db() -> AsyncIOMotorDatabase:
    """Get database connection"""
    return await get_async_db()


def get_current_api_key(api_key: str = Depends(verify_api_key)) -> str:
    """Get current authenticated API key"""
    return api_key


def get_rate_limit() -> str:
    """Get rate limit configuration"""
    return default_api_config.rate_limit
