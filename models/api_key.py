"""
API Key models
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone, timedelta
from typing import Optional

UTC_PLUS_1 = timezone(timedelta(hours=1))


class APIKeyModel(BaseModel):
    """Database model for API key"""
    key_hash: str = Field(..., description="SHA256 hash of the API key")
    name: str = Field(..., max_length=200, description="Name/description of the key")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC_PLUS_1))
    is_active: bool = Field(default=True, description="Whether the key is active")


class APIKeyCreate(BaseModel):
    """Model for creating a new API key"""
    name: str = Field(..., max_length=200, description="Name/description for this key")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My Application"
            }
        }
    )


class APIKeyResponse(BaseModel):
    """Response when creating a new API key"""
    key: str = Field(..., description="The actual API key - save this, it won't be shown again!")
    key_hash: str = Field(..., description="Hash of the key (stored in database)")
    name: str
    created_at: datetime
    is_active: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "key_abc123def456...",
                "key_hash": "sha256_hash_here",
                "name": "My Application",
                "created_at": "2025-11-08T14:30:00+01:00",
                "is_active": True
            }
        }
    )


class APIKeyListItem(BaseModel):
    """Model for listing API keys (without revealing the actual key)"""
    id: str
    name: str
    key_hash: str
    created_at: datetime
    is_active: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "My Application",
                "key_hash": "sha256_hash_here",
                "created_at": "2025-11-08T14:30:00+01:00",
                "is_active": True
            }
        }
    )