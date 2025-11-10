"""
API Key management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.dependencies import get_db, limiter, get_rate_limit
from api.services.api_key_service import APIKeyService
from models.api_key import APIKeyCreate, APIKeyResponse, APIKeyListItem
from models.api_models import ErrorResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/api-keys", tags=["API Keys"])


@router.post(
    "",
    response_model=APIKeyResponse,
    summary="Generate new API key",
    description="Generate a new API key. Save the key - it won't be shown again!",
    responses={
        201: {"description": "API key created"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
@limiter.limit(get_rate_limit())
async def create_api_key(
    request: Request,
    key_data: APIKeyCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate a new API key.
    
    **IMPORTANT:** Save the returned key immediately - it will never be shown again!
    
    **No authentication required** - allows initial key generation.
    """
    try:
        result = await APIKeyService.create_api_key(db, key_data.name)
        logger.info(f"Created new API key: {key_data.name}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get(
    "",
    response_model=list[APIKeyListItem],
    summary="List all API keys",
    description="Get list of all API keys (hashes only, not the actual keys)",
    responses={
        200: {"description": "List of API keys"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
@limiter.limit(get_rate_limit())
async def list_api_keys(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    List all API keys.
    
    Returns key metadata (name, hash, created_at) but NOT the actual keys.
    
    **No authentication required** for simplicity.
    """
    try:
        keys = await APIKeyService.list_api_keys(db)
        logger.info(f"Listed {len(keys)} API keys")
        return keys
        
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete(
    "/{key_id}",
    summary="Revoke API key",
    description="Deactivate an API key by ID",
    responses={
        200: {"description": "API key revoked"},
        404: {"model": ErrorResponse, "description": "API key not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
@limiter.limit(get_rate_limit())
async def revoke_api_key(
    request: Request,
    key_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Revoke/deactivate an API key.
    
    The key will immediately stop working for authentication.
    
    **No authentication required** for simplicity.
    """
    try:
        success = await APIKeyService.revoke_api_key(db, key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {key_id}"
            )
        
        logger.info(f"Revoked API key: {key_id}")
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )