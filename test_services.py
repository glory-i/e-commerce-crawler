"""
Test services independently
"""
import asyncio
from config.database import get_async_db, db_config
from api.services.book_service import BookService
from api.services.change_service import ChangeService


async def test_book_service():
    """Test book service"""
    print("Testing BookService...\n")
    
    db = await get_async_db()
    
    # Test 1: Get all books (first page)
    result = await BookService.get_books(db, page=1, page_size=10)
    print(f"Total books: {result['total']}")
    print(f"Page 1 books: {len(result['data'])}")
    print(f"First book: {result['data'][0]['name'] if result['data'] else 'None'}\n")
    
    # Test 2: Filter by category
    result = await BookService.get_books(db, category="Fiction", page_size=5)
    print(f"Fiction books: {result['total']}")
    if result['data']:
        print(f"Sample: {result['data'][0]['name']}\n")
    
    # Test 3: Filter by price range
    result = await BookService.get_books(db, min_price=10.0, max_price=20.0, page_size=5)
    print(f"Books between £10-£20: {result['total']}")
    if result['data']:
        print(f"Sample: {result['data'][0]['name']} - £{result['data'][0]['price_incl_tax']}\n")
    
    # Test 4: Sort by price
    result = await BookService.get_books(db, sort_by="price", page_size=3)
    print("Cheapest books:")
    for book in result['data']:
        print(f"  - {book['name']}: £{book['price_incl_tax']}")
    print()
    
    # Test 5: Get categories
    categories = await BookService.get_all_categories(db)
    print(f"Total categories: {len(categories)}")
    print(f"Categories: {', '.join(categories[:5])}...\n")


async def test_change_service():
    """Test change service"""
    print("Testing ChangeService...\n")
    
    db = await get_async_db()
    
    # Test 1: Get all changes
    result = await ChangeService.get_changes(db, page=1, page_size=10)
    print(f"Total changes: {result['total']}")
    print(f"Page 1 changes: {len(result['data'])}")
    if result['data']:
        print(f"Latest change: {result['data'][0]['book_name']}\n")
    
    # Test 2: Filter by type
    result = await ChangeService.get_changes(db, change_type="added", page_size=5)
    print(f"Added books: {result['total']}\n")
    
    result = await ChangeService.get_changes(db, change_type="updated", page_size=5)
    print(f"Updated books: {result['total']}\n")
    
    # Test 3: Recent changes
    recent = await ChangeService.get_recent_changes(db, limit=5)
    print(f"5 most recent changes:")
    for change in recent:
        print(f"  - {change['book_name']} ({change['change_type']})")
    print()
    
    # Test 4: Statistics
    stats = await ChangeService.get_change_statistics(db)
    print(f"Change statistics:")
    print(f"  Total changes: {stats['total_changes']}")
    print(f"  Added: {stats['total_added']}")
    print(f"  Updated: {stats['total_updated']}")
    print(f"  Total runs: {stats['total_runs']}")
    print()


async def main():
    try:
        await test_book_service()
        await test_change_service()
    finally:
        await db_config.close_async()


if __name__ == "__main__":
    asyncio.run(main())