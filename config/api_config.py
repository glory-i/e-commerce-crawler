"""
API configuration settings
"""
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class APIConfig:
    """Configuration for FastAPI application"""
    
    # API Info
    title: str = "ECommerce Crawler API"
    description: str = "API for querying book data and change logs history"
    version: str = "1.0.0"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allow_origins: List[str] = None
    allow_credentials: bool = True
    allow_methods: List[str] = None
    allow_headers: List[str] = None
    
    # Rate Limiting
    rate_limit: str = "100/hour"  
    
    # API Keys
    api_keys: List[str] = None
    
    # Pagination
    default_page_size: int = 50
    max_page_size: int = 100
    
    def __post_init__(self):
        """Load API keys from environment"""
        if self.api_keys is None:
            keys_str = os.getenv("API_KEYS", "")
            self.api_keys = [key.strip() for key in keys_str.split(",") if key.strip()]
        
        if self.allow_origins is None:
            self.allow_origins = ["*"]  # Allow all origins (for development)
        
        if self.allow_methods is None:
            self.allow_methods = ["*"]
        
        if self.allow_headers is None:
            self.allow_headers = ["*"]


# Default configuration instance
default_api_config = APIConfig()