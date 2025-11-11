"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint(client):
    """Test health check endpoint (no auth required)"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'total_books' in data


def test_books_without_auth(client):
    """Test that books endpoint requires authentication"""
    response = client.get("/books")
    
    assert response.status_code == 401
    assert "API key" in response.json()['detail']


def test_books_with_auth(client, api_key):
    """Test books endpoint with valid API key"""
    response = client.get(
        "/books?page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'total' in data
    assert 'data' in data
    assert len(data['data']) <= 5


def test_books_with_filters(client, api_key):
    """Test books endpoint with filters"""
    response = client.get(
        "/books?category=Fiction&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data['data']:
        for book in data['data']:
            assert book['category'].lower() == 'fiction'





def test_invalid_api_key(client):
    """Test with invalid API key"""
    response = client.get(
        "/books",
        headers={"X-API-Key": "invalid_key_12345"}
    )
    
    assert response.status_code == 401


def test_get_book_by_id_invalid_format(client, api_key):
    """Test get book by ID with invalid format"""
    response = client.get(
        "/books/invalid_id_format",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 404


def test_get_book_by_id_not_found(client, api_key):
    """Test get book by ID that doesn't exist"""
    response = client.get(
        "/books/555f1f77bcf86cd799439022",  # Valid format but book doesn't exist
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 404


def test_get_categories_endpoint(client, api_key):
    """Test get all categories endpoint"""
    response = client.get(
        "/books/categories/list",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)


def test_books_with_price_filter(client, api_key):
    """Test books with min and max price filters"""
    response = client.get(
        "/books?min_price=10&max_price=20&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data['data']:
        for book in data['data']:
            assert 10 <= book['price_incl_tax'] <= 20


def test_books_with_rating_filter(client, api_key):
    """Test books with rating filter"""
    response = client.get(
        "/books?rating=4&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data['data']:
        for book in data['data']:
            assert book['rating'] == 4


def test_books_with_sorting(client, api_key):
    """Test books with different sort options"""
    # Sort by price
    response = client.get(
        "/books?sort_by=price&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if len(data['data']) > 1:
        prices = [book['price_incl_tax'] for book in data['data']]
        assert prices == sorted(prices)


def test_books_pagination_last_page(client, api_key):
    """Test accessing last page of books"""
    # Get total pages first
    response = client.get(
        "/books?page_size=50",
        headers={"X-API-Key": api_key}
    )
    
    data = response.json()
    last_page = data['total_pages']
    
    # Request last page
    response = client.get(
        f"/books?page={last_page}&page_size=50",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200


def test_books_invalid_price_range(client, api_key):
    """Test books with invalid price range (min > max)"""
    response = client.get(
        "/books?min_price=50&max_price=10",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 422


def test_books_multiple_filters(client, api_key):
    """Test books with multiple filters combined"""
    response = client.get(
        "/books?category=Fiction&min_price=10&rating=4&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data['data']:
        for book in data['data']:
            assert book['category'].lower() == 'fiction'
            assert book['price_incl_tax'] >= 10
            assert book['rating'] == 4