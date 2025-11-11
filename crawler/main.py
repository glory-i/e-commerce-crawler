"""
Main crawler script 
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Set

from crawler.async_scraper import get_all_book_urls_async, scrape_multiple_books
from config.database import get_async_db, db_config
from config.crawler_config import CrawlerConfig, default_config

# from utilities.db_helpers import (
#     save_book_to_db, 
#     create_indexes, 
#     get_all_crawled_urls,
#     get_crawl_statistics
# )

from repositories.book_repository import (
    save_book_to_db, 
    create_indexes, 
    get_all_crawled_urls,
    get_crawl_statistics)

UTC_PLUS_1 = timezone(timedelta(hours=1))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def save_books_batch(db, books: List[dict]) -> dict:
    """
    Save a batch of books to database
    
    Args:
        db: MongoDB database instance
        books: List of book data dictionaries
        
    Returns:
        Dictionary with success/failure counts
    """
    results = {
        'success': 0,
        'failed': 0
    }
    
    for book in books:
        try:
            success = await save_book_to_db(db, book)
            if success:
                results['success'] += 1
                logger.debug(f"Saved: {book.get('name', 'Unknown')}")
            else:
                results['failed'] += 1
                logger.warning(f"Failed to save: {book.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error saving book {book.get('name', 'Unknown')}: {e}")
            results['failed'] += 1
    
    return results


def filter_new_books(all_urls: List[str], existing_urls: Set[str]) -> List[str]:
    """
    Filter out already-crawled books
    
    Args:
        all_urls: List of all book URLs found
        existing_urls: Set of URLs already in database
        
    Returns:
        List of URLs that need to be crawled
    """
    # Use set for O(1) lookup
    new_urls = [url for url in all_urls if url not in existing_urls]
    return new_urls


async def crawl_all_books_async(config: CrawlerConfig = None):
    """
    Main async crawler function 
    
    Args:
        config: Crawler configuration (uses default if None)
    """
    if config is None:
        config = default_config
    
    start_time = datetime.now(UTC_PLUS_1)
    logger.info(f"Starting async crawl at {start_time.isoformat()}")
    logger.info(f"Configuration:")
    logger.info(f"  - Concurrency: {config.max_concurrent_requests} requests")
    logger.info(f"  - Batch size: {config.batch_size} books")
    logger.info(f"  - Retry attempts: {config.max_retry_attempts}")
    logger.info(f"  - Request timeout: {config.request_timeout}s")
    logger.info(f"  - Skip existing: {config.skip_existing}")
    
    # Connect to database
    db = await get_async_db()
    
    # Create indexes
    await create_indexes(db)
    
    # Get database statistics
    stats = await get_crawl_statistics(db)
    logger.info(f"Database contains {stats.get('total_books', 0)} books")
    
    try:
        # Get all book URLs
        logger.info(f"Fetching book URLs from {config.base_url}")
        all_book_urls = await get_all_book_urls_async(config.base_url)
        total_found = len(all_book_urls)
        logger.info(f"Found {total_found} books on website")
        
        if total_found == 0:
            logger.warning("No books found to crawl")
            return
        
        # filter out already-crawled books
        if config.skip_existing:
            logger.info("Checking for already-crawled books...")
            existing_urls = await get_all_crawled_urls(db)
            book_urls = filter_new_books(all_book_urls, existing_urls)
            
            skipped_count = total_found - len(book_urls)
            logger.info(f"Skipping {skipped_count} already-crawled books")
            logger.info(f"Will crawl {len(book_urls)} new/missing books")
        else:
            book_urls = all_book_urls
            logger.info("Skip existing disabled- will process all books")
        
        total_books = len(book_urls)
        
        if total_books == 0:
            logger.info("No new books to crawl - all books already in database")
            return
        
        # Process books in batches
        results = {
            'success': 0,
            'failed': 0,
            'scrape_errors': 0
        }
        
        # Split book URLs into batches
        for batch_start in range(0, total_books, config.batch_size):
            batch_end = min(batch_start + config.batch_size, total_books)
            batch_urls = book_urls[batch_start:batch_end]
            
            batch_num = (batch_start // config.batch_size) + 1
            total_batches = (total_books + config.batch_size - 1) // config.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_urls)} books)")
            
            # Scrape batch concurrently with retry logic
            scraped_books = await scrape_multiple_books(
                batch_urls, 
                config.max_concurrent_requests
            )
            
            # Count scraping failures
            scrape_errors = len(batch_urls) - len(scraped_books)
            results['scrape_errors'] += scrape_errors
            
            if scrape_errors > 0:
                logger.warning(f"Failed to scrape {scrape_errors} books in this batch (after retries)")
            
            # Save batch to database
            if scraped_books:
                batch_results = await save_books_batch(db, scraped_books)
                results['success'] += batch_results['success']
                results['failed'] += batch_results['failed']
                
                logger.info(f"Batch complete: {batch_results['success']} saved, {batch_results['failed']} failed")
        
        # Print final summary
        end_time = datetime.now(UTC_PLUS_1)
        duration = (end_time - start_time).total_seconds()
        
        logger.info("="*60)
        logger.info("ASYNC CRAWL COMPLETE")
        logger.info("="*60)
        logger.info(f"Total books found on website: {total_found}")
        
        if config.skip_existing:
            logger.info(f"Already in database (skipped): {total_found - total_books}")
        
        logger.info(f"Books processed in this run: {total_books}")
        logger.info(f"Successfully scraped: {total_books - results['scrape_errors']}")
        logger.info(f"Scraping errors (after retries): {results['scrape_errors']}")
        logger.info(f"Successfully saved to DB: {results['success']}")
        logger.info(f"Failed to save to DB: {results['failed']}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        if total_books > 0:
            logger.info(f"Average time per book: {duration/total_books:.2f} seconds")
            logger.info(f"Books per minute: {(total_books/duration)*60:.1f}")
        
        # Get updated statistics
        final_stats = await get_crawl_statistics(db)
        logger.info(f"Total books now in database: {final_stats.get('total_books', 0)}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Fatal error during async crawl: {e}")
        raise
    finally:
        # Close database connection
        await db_config.close_async()


if __name__ == "__main__":
    # Run the async crawler with default configuration
    
    # skip existing books by default
    asyncio.run(crawl_all_books_async())
    