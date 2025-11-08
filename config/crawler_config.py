"""
Crawler configuration settings
"""
from dataclasses import dataclass


@dataclass
class CrawlerConfig:
    """Configuration for web crawler"""
    
    # Concurrency settings
    max_concurrent_requests: int = 10
    batch_size: int = 50
    
    # Retry settings
    max_retry_attempts: int = 3
    retry_min_wait: int = 1  # seconds
    retry_max_wait: int = 10  # seconds
    retry_multiplier: int = 1  # exponential multiplier
    
    request_timeout: float = 10.0  # seconds
    user_agent: str = "EcommerceCrawler/1.0"
    
    request_delay: float = 0.1  # seconds between requests
    
    base_url: str = "https://books.toscrape.com/"
    
    db_batch_size: int = 50  

    skip_existing: bool = True    


# Default configuration instance
default_config = CrawlerConfig()