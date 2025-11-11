"""
Tests for change endpoints
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from datetime import datetime, timedelta


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_get_changes_no_auth(client):
    """Test changes endpoint requires authentication"""
    response = client.get("/changes")
    assert response.status_code == 401


def test_get_changes_with_auth(client, api_key):
    """Test get all changes"""
    response = client.get(
        "/changes?page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'total' in data
    assert 'data' in data


def test_get_changes_filter_by_type_added(client, api_key):
    """Test filter changes by type 'added'"""
    response = client.get(
        "/changes?change_type=added&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data['data']:
        for change in data['data']:
            assert change['change_type'] == 'added'


def test_get_changes_filter_by_type_updated(client, api_key):
    """Test filter changes by type 'updated'"""
    response = client.get(
        "/changes?change_type=updated&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data['data']:
        for change in data['data']:
            assert change['change_type'] == 'updated'


def test_get_changes_invalid_type(client, api_key):
    """Test changes with invalid type"""
    response = client.get(
        "/changes?change_type=invalid",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 422


def test_get_changes_with_date_range(client, api_key):
    """Test changes with date range filter"""
    start_date = (datetime.now() - timedelta(days=7)).isoformat()
    end_date = datetime.now().isoformat()
    
    response = client.get(
        f"/changes?start_date={start_date}&end_date={end_date}&page_size=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200


def test_get_changes_invalid_date_range(client, api_key):
    """Test changes with invalid date range (start > end)"""
    start_date = datetime.now().isoformat()
    end_date = (datetime.now() - timedelta(days=7)).isoformat()
    
    response = client.get(
        f"/changes?start_date={start_date}&end_date={end_date}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 422


def test_get_recent_changes(client, api_key):
    """Test get recent changes endpoint"""
    response = client.get(
        "/changes/recent?limit=5",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    changes = response.json()
    assert isinstance(changes, list)
    assert len(changes) <= 5


def test_get_recent_changes_with_limit(client, api_key):
    """Test recent changes with different limits"""
    response = client.get(
        "/changes/recent?limit=10",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    changes = response.json()
    assert len(changes) <= 10


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

def test_get_change_statistics(client, api_key):
    """Test get change statistics endpoint"""
    response = client.get(
        "/changes/statistics",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    stats = response.json()
    assert 'total_changes' in stats
    assert 'total_added' in stats
    assert 'total_updated' in stats


def test_changes_pagination(client, api_key):
    """Test changes pagination"""
    response = client.get(
        "/changes?page=1&page_size=10",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['page_size'] == 10