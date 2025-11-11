"""
Tests for ChangeService
"""
import pytest
from api.services.change_service import ChangeService


@pytest.mark.asyncio
async def test_get_all_changes(db):
    """Test getting all changes with pagination"""
    result = await ChangeService.get_changes(db, page=1, page_size=10)
    
    assert 'total' in result
    assert result['page'] == 1
    assert result['page_size'] == 10
    assert len(result['data']) <= 10


@pytest.mark.asyncio
async def test_filter_by_change_type(db):
    """Test filtering changes by type"""
    # Test 'added' filter
    result_added = await ChangeService.get_changes(
        db, 
        change_type="added", 
        page_size=5
    )
    
    if result_added['data']:
        for change in result_added['data']:
            assert change['change_type'] == 'added'
    
    # Test 'updated' filter
    result_updated = await ChangeService.get_changes(
        db, 
        change_type="updated", 
        page_size=5
    )
    
    if result_updated['data']:
        for change in result_updated['data']:
            assert change['change_type'] == 'updated'


@pytest.mark.asyncio
async def test_get_recent_changes(db):
    """Test getting recent changes"""
    changes = await ChangeService.get_recent_changes(db, limit=5)
    
    assert isinstance(changes, list)
    assert len(changes) <= 5


@pytest.mark.asyncio
async def test_get_change_statistics(db):
    """Test getting change statistics"""
    stats = await ChangeService.get_change_statistics(db)
    
    assert 'total_changes' in stats
    assert 'total_added' in stats
    assert 'total_updated' in stats
    assert isinstance(stats['total_changes'], int)