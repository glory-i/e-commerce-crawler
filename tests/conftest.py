"""
Pytest configuration and fixtures
"""
import pytest
import pytest_asyncio
from config.database import get_async_db



@pytest_asyncio.fixture(scope="function")  
async def db():
    """
    Database fixture - fresh connection per test
    """
    database = await get_async_db()
    yield database
    # Connection managed by get_async_db


@pytest.fixture
def sample_book_data():
    """Sample book data for testing"""
    return {
        "name": "Test Book",
        "description": "A test book description",
        "category": "Fiction",
        "price_incl_tax": 19.99,
        "price_excl_tax": 19.99,
        "availability": "In stock (5 available)",
        "number_of_reviews": 0,
        "rating": 4,
        "image_url": "https://example.com/image.jpg",
        "source_url": "https://books.toscrape.com/test",
        "content_hash": "test_hash_123"
    }


@pytest.fixture
def api_key():
    """Valid API key for testing"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    keys = os.getenv("API_KEYS", "").split(",")
    
    if keys and keys[0]:
        return keys[0].strip()
    
    return "test_key_123"