"""
Change detection logic - compares old and new book data
"""
from typing import Optional, Tuple, List
from models.book import BookModel
from models.changelog import FieldChange, ChangeType
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

UTC_PLUS_1 = timezone(timedelta(hours=1))


# Fields to monitor for changes
MONITORED_FIELDS = [
    'name',
    'price_incl_tax',
    'price_excl_tax',
    'availability',
    'rating',
    'number_of_reviews'
]


def detect_changes(old_book: dict, new_book_data: dict) -> Optional[dict]:
    """
    Compare old and new book data, detect changes
    
    Args:
        old_book: Book document from database
        new_book_data: Newly scraped book data
        
    Returns:
        Dictionary of changes {field_name: FieldChange}, or None if no changes
    """
    changes = {}
    
    for field in MONITORED_FIELDS:
        old_value = old_book.get(field)
        new_value = new_book_data.get(field)
        
        # Compare values
        if old_value != new_value:
            
            changes[field] = {
                'old': old_value,
                'new': new_value
            }
            
            logger.debug(f"Change detected in '{field}': {old_value} -> {new_value}")
    
    # Return changes dict or None if no changes
    return changes if changes else None


def compare_content_hashes(old_book: dict, new_book_data: dict) -> bool:
    """
    Quick check: compare content hashes to see if anything changed
    
    Args:
        old_book: Book document from database
        new_book_data: Newly scraped book data
        
    Returns:
        True if hashes are different (something changed), False if same
    """
    old_hash = old_book.get('content_hash', '')
    new_hash = new_book_data.get('content_hash', '')
    
    return old_hash != new_hash


def build_changelog_entry(
    book_source_url: str,
    book_name: str,
    change_type: ChangeType,
    changes: Optional[dict],
    detection_run_id: str
) -> dict:
    """
    Build a changelog entry dictionary ready for database insertion
    
    Args:
        book_source_url: Book source URL
        book_name: Book name
        change_type: "added" or "updated"
        changes: Dictionary of field changes, or None for new books
        detection_run_id: Unique ID for this scheduler run
        
    Returns:
        Changelog entry dictionary
    """
    changelog_entry = {
        'book_source_url': book_source_url,
        'book_name': book_name,
        'change_type': change_type.value if isinstance(change_type, ChangeType) else change_type,
        'changes': changes,
        'changed_at': datetime.now(UTC_PLUS_1),
        'detection_run_id': detection_run_id
    }
    
    return changelog_entry


def categorize_books(
    site_urls: List[str],
    db_urls: set
) -> Tuple[List[str], List[str]]:
    """
    Categorize books into new and existing
    
    Args:
        site_urls: List of book URLs found on website
        db_urls: Set of book URLs in database
        
    Returns:
        Tuple of (new_book_urls, existing_book_urls)
    """
    new_books = []
    existing_books = []
    
    for url in site_urls:
        if url in db_urls:
            existing_books.append(url)
        else:
            new_books.append(url)
    
    logger.info(f"Categorized books: {len(new_books)} new, {len(existing_books)} existing")
    
    return new_books, existing_books


def calculate_field_statistics(changelogs: List[dict]) -> dict:
    """
    Calculate statistics on which fields changed
    
    Args:
        changelogs: List of changelog entries
        
    Returns:
        Dictionary with field change counts
    """
    field_stats = {}
    
    for changelog in changelogs:
        if changelog.get('changes'):
            for field_name in changelog['changes'].keys():
                field_stats[field_name] = field_stats.get(field_name, 0) + 1
    
    return field_stats


def generate_run_id() -> str:
    """
    Generate a unique ID for this scheduler run
    
    Returns:
        Run ID string like "run_2025-11-08_14:30:00"
    """
    now = datetime.now(UTC_PLUS_1)
    run_id = f"run_{now.strftime('%Y-%m-%d_%H:%M:%S')}"
    return run_id