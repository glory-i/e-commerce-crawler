#Pydantic model for Book 
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional
from datetime import datetime,  UTC, timezone, timedelta
from enum import Enum

UTC_PLUS_1 = timezone(timedelta(hours=1))

class BookStatus(str, Enum):
    ACTIVE = "active"
    UNAVAILABLE = "unavailable"
    DELETED = "deleted"


class BookRating(int, Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class BookModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: str = Field(..., min_length=1, max_length=100)
    price_incl_tax: float = Field(..., gt=0)
    price_excl_tax: float = Field(..., gt=0)
    availability: str = Field(..., max_length=100)
    number_of_reviews: int = Field(default=0, ge=0)
    image_url: str = Field(...)
    rating: int = Field(..., ge=1, le=5)
    
    # Metadata
    source_url: str = Field(...)
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(UTC_PLUS_1))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC_PLUS_1))
    status: BookStatus = Field(default=BookStatus.ACTIVE)
    content_hash: str = Field(..., min_length=32, max_length=64)
    raw_html_snapshot: Optional[str] = Field(None)
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "name": "A Light in the Attic",
                "description": "It's hard to imagine a world without A Light in the Attic...",
                "category": "Poetry",
                "price_incl_tax": 51.77,
                "price_excl_tax": 51.77,
                "availability": "In stock (22 available)",
                "number_of_reviews": 0,
                "image_url": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
                "rating": 3,
                "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "crawled_at": "2025-11-07T10:30:00Z",
                "updated_at": "2025-11-07T10:30:00Z",
                "status": "active",
                "content_hash": "a1b2c3d4e5f6...",
                "raw_html_snapshot": "<html>...</html>"
            }
        }


class BookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price_incl_tax: float
    price_excl_tax: float
    availability: str
    number_of_reviews: int = 0
    image_url: str
    rating: int
    source_url: str


class BookUpdate(BaseModel):
    price_incl_tax: Optional[float] = None
    price_excl_tax: Optional[float] = None
    availability: Optional[str] = None
    number_of_reviews: Optional[int] = None
    status: Optional[BookStatus] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BookResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    price_incl_tax: float
    price_excl_tax: float
    availability: str
    number_of_reviews: int
    image_url: str
    rating: int
    source_url: str
    crawled_at: datetime
    updated_at: datetime
    status: str