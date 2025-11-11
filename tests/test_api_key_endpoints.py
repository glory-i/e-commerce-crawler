"""
Tests for API key management endpoints
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_create_api_key(client):
    """Test creating a new API key"""
    response = client.post(
        "/admin/api-keys",
        json={"name": "Test Application"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'key' in data
    assert 'key_hash' in data
    assert data['name'] == "Test Application"
    assert data['is_active'] is True
    assert data['key'].startswith('key_')


def test_create_api_key_and_use_it(client):
    """Test creating API key and using it for authentication"""
    # Create key
    response = client.post(
        "/admin/api-keys",
        json={"name": "Test Key"}
    )
    
    assert response.status_code == 200
    key_data = response.json()
    new_key = key_data['key']
    
    # Use the new key to access protected endpoint
    response = client.get(
        "/books?page_size=5",
        headers={"X-API-Key": new_key}
    )
    
    assert response.status_code == 200


def test_list_api_keys(client):
    """Test listing all API keys"""
    response = client.get("/admin/api-keys")
    
    assert response.status_code == 200
    keys = response.json()
    assert isinstance(keys, list)


def test_revoke_api_key(client):
    """Test revoking an API key"""
    # First create a key
    response = client.post(
        "/admin/api-keys",
        json={"name": "Key to Revoke"}
    )
    
    assert response.status_code == 200
    key_data = response.json()
    
    # List keys to get the ID
    response = client.get("/admin/api-keys")
    keys = response.json()
    
    if keys:
        key_id = keys[-1]['id']  # Get last created key
        
        # Revoke it
        response = client.delete(f"/admin/api-keys/{key_id}")
        assert response.status_code == 200


def test_revoke_nonexistent_key(client):
    """Test revoking a key that doesn't exist"""
    response = client.delete("/admin/api-keys/507f1f77bcf86cd799439011")
    assert response.status_code == 404


def test_create_multiple_keys(client):
    """Test creating multiple API keys"""
    names = ["App 1", "App 2", "App 3"]
    created_keys = []
    
    for name in names:
        response = client.post(
            "/admin/api-keys",
            json={"name": name}
        )
        assert response.status_code == 200
        created_keys.append(response.json()['key'])
    
    assert len(created_keys) == 3
    assert len(set(created_keys)) == 3  # All unique


def test_api_key_invalid_format(client):
    """Test using API key with invalid format"""
    response = client.get(
        "/books",
        headers={"X-API-Key": "invalid_key"}
    )
    
    assert response.status_code == 401