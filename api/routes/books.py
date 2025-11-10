"""
Book endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from urllib.parse import unquote

from api.dependencies import get_db, get_current_api_key, limiter, get_rate_limit
from api.services.book_service import BookService
from models.api_models import BookListResponse, APIBookResponse, ErrorResponse
from config.api_config import default_api_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["Books"])


@router.get(
    "",
    response_model=BookListResponse,
    summary="Get all books",
    description="Get paginated list of books with optional filtering and sorting",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        422: {"description": "Invalid query parameters"}
    }
)
@limiter.limit(get_rate_limit())
async def get_books(
    request: Request,

    category: Optional[str] = Query(None, description="Filter by category (case-insensitive)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price (inclusive)"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price (inclusive)"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating (1-5)"),
    sort_by: Optional[str] = Query(None, description="Sort by field: rating, price, reviews, name"),
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
    Get paginated list of books with filtering and sorting options.
    
    **Query Parameters:**
    - **category**: Filter by book category
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **rating**: Filter by rating (1-5 stars)
    - **sort_by**: Sort field (rating, price, reviews, name)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        # Validate price range
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_price cannot be greater than max_price"
            )
        
        # Call service
        result = await BookService.get_books(
            db=db,
            category=category,
            min_price=min_price,
            max_price=max_price,
            rating=rating,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
        
        logger.info(f"Books endpoint: returned {len(result['data'])} books (page {page})")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_books endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/get-by-source-url/{book_source_url:path}",
    response_model=APIBookResponse,
    summary="Get book by source url",
    description="Get detailed information about a specific book using its book url",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Book not found"}
    }
)
@limiter.limit(get_rate_limit())
async def get_book_by_source_url(
    request: Request,
    book_source_url: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    api_key: str = Depends(get_current_api_key)
):
    """
    Get detailed information about a specific book by its ID (source URL).
    
    **Path Parameters:**
    - **book_id**: Book identifier (source URL, URL-encoded)
    
    **Example:**
```
    GET /books/https%3A%2F%2Fbooks.toscrape.com%2Fcatalogue%2Fa-light-in-the-attic_1000%2Findex.html
```
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        # Decode URL-encoded book_source_url
        decoded_book_source_url = unquote(book_source_url)
        
        # Call service
        book = await BookService.get_book_by_source_url(db, decoded_book_source_url)
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book not found: {decoded_book_source_url}"
            )
        
        logger.info(f"Book detail endpoint: returned book {book.get('name', 'Unknown')}")
        
        return book
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_book_by_source_url endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{book_id}",
    response_model=APIBookResponse,
    summary="Get book by ID",
    description="Get detailed information about a specific book by its ID",
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Book not found"},
        422: {"model": ErrorResponse, "description": "Invalid book ID format"}
    }
)
@limiter.limit(get_rate_limit())
async def get_book_by_id(
    request: Request,
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    api_key: str = Depends(get_current_api_key)
):
    """
    Get detailed information about a specific book by its book ID.
    
    **Path Parameters:**
    - **book_id**: book id (24-character hexadecimal string)
    
    **Example:**
```
    GET /books/507f1f77bcf86cd799439011
```
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        # Call service
        book = await BookService.get_book_by_book_id(db, book_id)
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book not found with ID: {book_id}"
            )
        
        logger.info(f"Book by ID endpoint: returned book {book.get('name', 'Unknown')}")
        
        return book
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_book_by_id endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/categories/list",
    response_model=list[str],
    summary="Get all categories",
    description="Get list of all unique book categories",
    responses={
        200: {"description": "List of categories"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"}
    }
)
@limiter.limit(get_rate_limit())
async def get_categories(
    request: Request,

    db: AsyncIOMotorDatabase = Depends(get_db),
    api_key: str = Depends(get_current_api_key)
):
    """
    Get list of all unique book categories.
    
    Useful for building filter dropdowns in frontend applications.
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Rate Limit:**
    - 100 requests per hour
    """
    try:
        categories = await BookService.get_all_categories(db)
        logger.info(f"Categories endpoint: returned {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"Error in get_categories endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )