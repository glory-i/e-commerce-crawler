"""
Test scheduler with fake changes (modify some books manually)
"""
import asyncio
from config.database import get_async_db, db_config
from repositories.book_repository import get_all_book_urls
from datetime import datetime, timezone, timedelta

UTC_PLUS_1 = timezone(timedelta(hours=1))


async def create_fake_changes():
    """Modify 3 books to simulate changes"""
    print("Creating fake changes in database...")
    
    db = await get_async_db()
    
    # Get first 3 books
    all_urls = await get_all_book_urls(db)
    urls_to_modify = list(all_urls)[:3]
    
    for url in urls_to_modify:
        # Update price to a different value
        await db.books.update_one(
            {'source_url': url},
            {
                '$set': {
                    'price_incl_tax': 99.99,
                    'price_excl_tax': 99.99,
                    'content_hash': 'fake_hash_to_trigger_change'
                }
            }
        )
        print(f"Modified: {url}")
    
    await db_config.close_async()
    
    print(f"\nModified {len(urls_to_modify)} books.")
    print("Now run: python -m scheduler.runner")
    print("The scheduler will detect these as changes!")


if __name__ == "__main__":
    asyncio.run(create_fake_changes())