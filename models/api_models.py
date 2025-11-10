"""
API response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class APIBookResponse(BaseModel):
    """Response model for book data"""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    price_incl_tax: float
    price_excl_tax: float
    availability: str
    number_of_reviews: int
    rating: int
    image_url: Optional[str] = None
    source_url: str
    crawled_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "A Light in the Attic",
                "description": "It's hard to imagine a world without A Light in the Attic...",
                "category": "Poetry",
                "price_incl_tax": 51.77,
                "price_excl_tax": 51.77,
                "availability": "In stock (22 available)",
                "number_of_reviews": 0,
                "rating": 3,
                "image_url": "https://books.toscrape.com/media/cache/...",
                "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "crawled_at": "2025-11-08T14:30:00+01:00"
            }
        }


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    data: List[Any] = Field(..., description="Array of items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 1000,
                "page": 1,
                "page_size": 50,
                "total_pages": 20,
                "data": []
            }
        }


class BookListResponse(BaseModel):
    """Response for GET /books"""
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[APIBookResponse]


class APIChangeResponse(BaseModel):
    """Response model for change log entry"""
    book_id: str
    book_name: str
    change_type: str
    changes: Optional[dict] = None
    changed_at: datetime
    detection_run_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "book_id": "https://books.toscrape.com/catalogue/book_123/index.html",
                "book_name": "A Light in the Attic",
                "change_type": "updated",
                "changes": {
                    "price_incl_tax": {
                        "old": 51.77,
                        "new": 45.00
                    }
                },
                "changed_at": "2025-11-08T14:30:00+01:00",
                "detection_run_id": "run_2025-11-08_02:00:00"
            }
        }


class ChangeListResponse(BaseModel):
    """Response for GET /changes"""
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[APIChangeResponse]


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid API key"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    total_books: int
    total_changes: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-08T14:30:00+01:00",
                "database": "connected",
                "total_books": 1000,
                "total_changes": 25
            }
        }