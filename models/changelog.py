"""
Pydantic models for change log
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from enum import Enum

UTC_PLUS_1 = timezone(timedelta(hours=1))


class ChangeType(str, Enum):
    """Type of change detected"""
    ADDED = "added"      
    UPDATED = "updated"  


class FieldChange(BaseModel):
    """Represents a change to a single field"""
    old: Any = Field(..., description="Old value before change")
    new: Any = Field(..., description="New value after change")
    
    class Config:
        json_schema_extra = {
            "example": {
                "old": 51.77,
                "new": 45.00
            }
        }


class ChangeLog(BaseModel):
    """
    Change log entry for book changes
    One entry per book per detection run
    """
    book_id: str = Field(..., description="Book source URL (unique identifier)")
    book_name: str = Field(..., max_length=500, description="Book name for readability")
    change_type: ChangeType = Field(..., description="Type of change: added or updated")
    changes: Optional[dict[str, FieldChange]] = Field(
        None, 
        description="Dictionary of field changes. None for new books."
    )
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC_PLUS_1),
        description="When change was detected"
    )
    detection_run_id: str = Field(
        ..., 
        description="Unique ID for the scheduler run that detected this change"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "book_id": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "book_name": "A Light in the Attic",
                "change_type": "updated",
                "changes": {
                    "price_incl_tax": {
                        "old": 51.77,
                        "new": 45.00
                    },
                    "availability": {
                        "old": "In stock (22 available)",
                        "new": "In stock (18 available)"
                    }
                },
                "changed_at": "2025-11-08T15:30:00+01:00",
                "detection_run_id": "run_2025-11-08_02:00:00"
            }
        }


class ChangeLogCreate(BaseModel):
    """Model for creating a new changelog entry"""
    book_id: str
    book_name: str
    change_type: ChangeType
    changes: Optional[dict[str, FieldChange]] = None
    detection_run_id: str


class ChangeLogResponse(BaseModel):
    """Model for API responses """
    id: str
    book_id: str
    book_name: str
    change_type: str
    changes: Optional[dict[str, FieldChange]]
    changed_at: datetime
    detection_run_id: str


class SchedulerRunSummary(BaseModel):
    """Summary statistics for a scheduler run"""
    run_id: str
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    
    total_books_on_site: int
    total_books_in_db_before: int
    total_books_in_db_after: int
    
    new_books_added: int
    books_updated: int
    books_unchanged: int
    
    fields_changed: dict[str, int]  # e.g., {"price_incl_tax": 3, "availability": 2}
    
    errors: int
    error_details: Optional[list[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_2025-11-08_02:00:00",
                "started_at": "2025-11-08T02:00:00+01:00",
                "completed_at": "2025-11-08T02:03:45+01:00",
                "duration_seconds": 225.5,
                "total_books_on_site": 1000,
                "total_books_in_db_before": 995,
                "total_books_in_db_after": 1000,
                "new_books_added": 5,
                "books_updated": 3,
                "books_unchanged": 992,
                "fields_changed": {
                    "price_incl_tax": 2,
                    "availability": 1
                },
                "errors": 0,
                "error_details": None
            }
        }