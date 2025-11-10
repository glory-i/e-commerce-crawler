"""
Tests for BookService
"""
import pytest
from api.services.book_service import BookService


@pytest.mark.asyncio
async def test_get_all_books(db):
    """Test getting all books with pagination"""
    result = await BookService.get_books(db, page=1, page_size=10)
    
    assert result['total'] > 0
    assert result['page'] == 1
    assert result['page_size'] == 10
    assert len(result['data']) <= 10
    assert 'id' in result['data'][0]


@pytest.mark.asyncio
async def test_filter_by_category(db):
    """Test filtering books by category"""
    result = await BookService.get_books(db, category="Fiction", page_size=5)
    
    assert result['total'] >= 0
    
    if result['data']:
        # If books found, verify they're Fiction
        for book in result['data']:
            assert book['category'].lower() == 'fiction'


@pytest.mark.asyncio
async def test_filter_by_price_range(db):
    """Test filtering books by price range"""
    result = await BookService.get_books(
        db, 
        min_price=10.0, 
        max_price=20.0, 
        page_size=10
    )
    
    if result['data']:
        for book in result['data']:
            assert 10.0 <= book['price_incl_tax'] <= 20.0


@pytest.mark.asyncio
async def test_sort_by_price(db):
    """Test sorting books by price"""
    result = await BookService.get_books(db, sort_by="price", page_size=5)
    
    if len(result['data']) > 1:
        prices = [book['price_incl_tax'] for book in result['data']]
        # Check prices are in ascending order
        assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_get_categories(db):
    """Test getting all categories"""
    categories = await BookService.get_all_categories(db)
    
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert all(isinstance(cat, str) for cat in categories)


@pytest.mark.asyncio
async def test_get_book_by_invalid_id(db):
    """Test getting book with invalid MongoDB ID"""
    book = await BookService.get_book_by_book_id(db, "invalid_id")
    
    assert book is None


@pytest.mark.asyncio
async def test_pagination_total_pages(db):
    """Test pagination calculates total pages correctly"""
    result = await BookService.get_books(db, page=1, page_size=50)
    
    expected_pages = (result['total'] + 49) // 50  # Ceiling division
    assert result['total_pages'] == expected_pages