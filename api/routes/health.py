"""
Health check endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta

from api.dependencies import get_db
from models.api_models import HealthResponse
import logging

logger = logging.getLogger(__name__)

UTC_PLUS_1 = timezone(timedelta(hours=1))

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health and database connectivity",
    responses={
        200: {"description": "API is healthy"},
        503: {"description": "Service unavailable"}
    }
)
async def health_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns API status, database connectivity, and basic statistics.
    
    **No authentication required** - public endpoint for monitoring.
    """
    try:
        # Check database connectivity
        total_books = await db.books.count_documents({})
        total_changes = await db.changelogs.count_documents({})
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(UTC_PLUS_1),
            database="connected",
            total_books=total_books,
            total_changes=total_changes
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable - database connection failed"
        )