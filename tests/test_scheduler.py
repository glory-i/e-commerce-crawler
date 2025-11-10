"""
Tests for scheduler and change detection
"""
import pytest
from scheduler.change_detector import (
    detect_changes,
    compare_content_hashes,
    categorize_books,
    generate_run_id
)


def test_detect_no_changes():
    """Test when nothing changed"""
    old_book = {
        'name': 'Test Book',
        'price_incl_tax': 10.99,
        'availability': 'In stock'
    }
    
    new_book = {
        'name': 'Test Book',
        'price_incl_tax': 10.99,
        'availability': 'In stock'
    }
    
    changes = detect_changes(old_book, new_book)
    assert changes is None


def test_detect_price_change():
    """Test price change detection"""
    old_book = {
        'name': 'Test Book',
        'price_incl_tax': 10.99,
        'price_excl_tax': 10.99
    }
    
    new_book = {
        'name': 'Test Book',
        'price_incl_tax': 15.99,
        'price_excl_tax': 15.99
    }
    
    changes = detect_changes(old_book, new_book)
    
    assert changes is not None
    assert 'price_incl_tax' in changes
    assert changes['price_incl_tax']['old'] == 10.99
    assert changes['price_incl_tax']['new'] == 15.99


def test_compare_same_hashes():
    """Test comparing identical content hashes"""
    old_book = {'content_hash': 'abc123'}
    new_book = {'content_hash': 'abc123'}
    
    result = compare_content_hashes(old_book, new_book)
    assert result is False  # No change


def test_compare_different_hashes():
    """Test comparing different content hashes"""
    old_book = {'content_hash': 'abc123'}
    new_book = {'content_hash': 'xyz789'}
    
    result = compare_content_hashes(old_book, new_book)
    assert result is True  # Changed


def test_categorize_books():
    """Test book categorization"""
    site_urls = ['book1', 'book2', 'book3', 'book4']
    db_urls = {'book1', 'book2'}
    
    new_books, existing_books = categorize_books(site_urls, db_urls)
    
    assert len(new_books) == 2
    assert len(existing_books) == 2
    assert 'book3' in new_books
    assert 'book4' in new_books
    assert 'book1' in existing_books
    assert 'book2' in existing_books


def test_generate_run_id():
    """Test run ID generation"""
    run_id = generate_run_id()
    
    assert run_id.startswith('run_')
    assert len(run_id) > 10