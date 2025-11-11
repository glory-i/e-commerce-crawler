"""
Change log endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from api.dependencies import get_db, get_current_api_key, limiter, get_rate_limit
from api.services.change_service import ChangeService
from models.api_models import ChangeListResponse, ErrorResponse
from config.api_config import default_api_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/changes", tags=["Changes"])


@router.get(
    "",
    response_model=ChangeListResponse,
    summary="Get change history",
    description="Get paginated list of book changes (additions and updates)",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        422: {"description": "Invalid query parameters"}
    }
)
@limiter.limit(get_rate_limit())
async def get_changes(
    request: Request,
    change_type: Optional[str] = Query(
        None,
        description="Filter by change type: 'added' or 'updated'"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Filter changes after this date (ISO format: 2025-11-08T00:00:00)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Filter changes before this date (ISO format: 2025-11-08T23:59:59)"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default_api_config.default_page_size,
        ge=1,
        le=default_api_config.max_page_size,
        description=f"Items per page (max {default_api_config.max_page_size})"
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
    api_key: str = Depends(get_current_api_key)
):
    """
    Get paginated list of change history with filtering options.
    
    Changes are always sorted by changed_at in descending order (newest first).
    
    **Query Parameters:**
    - **change_type**: Filter by type ('added' for new books, 'updated' for changed books)
    - **start_date**: Filter changes after this date
    - **end_date**: Filter changes before this date
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        # Validate change_type
        if change_type and change_type.lower() not in ['added', 'updated']:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="change_type must be 'added' or 'updated'"
            )
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="start_date cannot be after end_date"
            )
        
        # Call service
        result = await ChangeService.get_changes(
            db=db,
            change_type=change_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        logger.info(f"Changes endpoint: returned {len(result['data'])} changes (page {page})")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_changes endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/recent",
    response_model=list,
    summary="Get recent changes",
    description="Get most recent changes without pagination",
    responses={
        200: {"description": "List of recent changes"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"}
    }
)
@limiter.limit(get_rate_limit())
async def get_recent_changes(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of recent changes to return (max 50)"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    api_key: str = Depends(get_current_api_key)
):
    """
    Get most recent changes without pagination.
    
    Useful for dashboards or overview pages.
    
    **Query Parameters:**
    - **limit**: Number of changes to return (default: 10, max: 50)
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        changes = await ChangeService.get_recent_changes(db, limit=limit)
        logger.info(f"Recent changes endpoint: returned {len(changes)} changes")
        return changes
        
    except Exception as e:
        logger.error(f"Error in get_recent_changes endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/statistics",
    summary="Get change statistics",
    description="Get aggregate statistics about changes",
    responses={
        200: {"description": "Change statistics"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"}
    }
)
@limiter.limit(get_rate_limit())
async def get_change_statistics(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    api_key: str = Depends(get_current_api_key)
):
    """
    Get aggregate statistics about changes.
    
    Returns total changes, breakdowns by type, and latest change timestamp.
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        stats = await ChangeService.get_change_statistics(db)
        logger.info("Change statistics endpoint called")
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_change_statistics endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )