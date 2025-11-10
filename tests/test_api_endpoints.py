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


def test_changes_endpoint(client, api_key):
    """Test changes endpoint"""
    response = client.get(
        "/changes?page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'total' in data
    assert 'data' in data


def test_invalid_api_key(client):
    """Test with invalid API key"""
    response = client.get(
        "/books",
        headers={"X-API-Key": "invalid_key_12345"}
    )
    
    assert response.status_code == 401