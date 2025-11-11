"""
Main scheduler runner - coordinates change detection process
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

from crawler.async_scraper import get_all_book_urls_async, scrape_multiple_books
from config.database import get_async_db, db_config
from config.crawler_config import CrawlerConfig
from repositories.book_repository import save_book_to_db, get_book_by_url, create_indexes, get_all_book_urls, count_books
from repositories.changelog_repository import save_changelog, get_changelogs_by_run_id, create_changelog_indexes
from scheduler.change_detector import detect_changes, compare_content_hashes, build_changelog_entry, categorize_books, calculate_field_statistics, generate_run_id
from models.changelog import ChangeType, SchedulerRunSummary
from reports.json_reporter import generate_json_report
from reports.csv_reporter import generate_csv_report
from notifications.email_notifier import send_email_alert

UTC_PLUS_1 = timezone(timedelta(hours=1))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_new_books(
    db,
    new_book_urls: List[str],
    run_id: str,
    config: CrawlerConfig
) -> Tuple[int, int]:
    """
    Process and save new books that don't exist in database
    
    Args:
        db: MongoDB database instance
        new_book_urls: List of URLs for new books
        run_id: Scheduler run ID
        config: Crawler configuration
        
    Returns:
        Tuple of (successfully_added, failed)
    """
    if not new_book_urls:
        logger.info("No new books to process")
        return 0, 0
    
    logger.info(f"Processing {len(new_book_urls)} new books")
    
    successfully_added = 0
    failed = 0
    
    scraped_books = await scrape_multiple_books(new_book_urls, config.max_concurrent_requests)
    
    for book_data in scraped_books:
        try:
            # Save book to database
            success = await save_book_to_db(db, book_data)
            
            if success:
                # Create changelog entry for new book
                changelog = build_changelog_entry(
                    book_source_url=book_data['source_url'],
                    book_name=book_data['name'],
                    change_type=ChangeType.ADDED,
                    changes=None,
                    detection_run_id=run_id
                )
                
                await save_changelog(db, changelog)
                successfully_added += 1
                logger.info(f"Added new book: {book_data['name']}")
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Error processing new book {book_data.get('source_url', 'unknown')}: {e}")
            failed += 1
    
    scrape_failed = len(new_book_urls) - len(scraped_books)
    failed += scrape_failed
    
    logger.info(f"New books summary: {successfully_added} added, {failed} failed")
    
    return successfully_added, failed


async def process_existing_books(
    db,
    existing_book_urls: List[str],
    run_id: str,
    config: CrawlerConfig
) -> Tuple[int, int, List[dict]]:
    """
    Check existing books for changes
    
    Args:
        db: MongoDB database instance
        existing_book_urls: List of URLs for existing books
        run_id: Scheduler run ID
        config: Crawler configuration
        
    Returns:
        Tuple of (books_updated, books_unchanged, list_of_changelogs)
    """
    if not existing_book_urls:
        logger.info("No existing books to check")
        return 0, 0, []
    
    logger.info(f"Checking {len(existing_book_urls)} existing books for changes")
    
    books_updated = 0
    books_unchanged = 0
    all_changelogs = []
    
    scraped_books = await scrape_multiple_books(existing_book_urls, config.max_concurrent_requests)
    
    scraped_books_dict = {book['source_url']: book for book in scraped_books}
    
    for url in existing_book_urls:
        try:
            # Get new book data
            new_book_data = scraped_books_dict.get(url)
            
            if not new_book_data:
                logger.warning(f"Failed to scrape {url}, skipping change detection")
                continue
            
            # Get old book from database
            old_book = await get_book_by_url(db, url)
            
            if not old_book:
                logger.warning(f"Book {url} not found in database, skipping")
                continue
            
            # Quick hash check
            if compare_content_hashes(old_book, new_book_data):
                # Hashes differ - something changed, find out what
                changes = detect_changes(old_book, new_book_data)
                
                if changes:
                    # Update book in database
                    await save_book_to_db(db, new_book_data)
                    
                    # Create changelog entry
                    changelog = build_changelog_entry(
                        book_source_url=url,
                        book_name=new_book_data['name'],
                        change_type=ChangeType.UPDATED,
                        changes=changes,
                        detection_run_id=run_id
                    )
                    
                    await save_changelog(db, changelog)
                    all_changelogs.append(changelog)
                    
                    books_updated += 1
                    
                    changed_fields = ', '.join(changes.keys())
                    logger.info(f"Updated book: {new_book_data['name']} (changed: {changed_fields})")
                else:
                    books_unchanged += 1
            else:
                books_unchanged += 1
                
        except Exception as e:
            logger.error(f"Error processing book {url}: {e}")
            continue
    
    logger.info(f"Existing books summary: {books_updated} updated, {books_unchanged} unchanged")
    
    return books_updated, books_unchanged, all_changelogs


async def run_change_detection(config: CrawlerConfig = None):
    """
    Main change detection function - run by scheduler
    
    Args:
        config: Crawler configuration
    """
    if config is None:
        config = CrawlerConfig()
    
    run_id = generate_run_id()
    started_at = datetime.now(UTC_PLUS_1)
    
    logger.info("="*60)
    logger.info(f"STARTING CHANGE DETECTION: {run_id}")
    logger.info("="*60)
    
    db = await get_async_db()
    
    await create_indexes(db)
    await create_changelog_indexes(db)
    
    try:
        # Get initial book count
        books_in_db_before = await count_books(db)
        logger.info(f"Books in database before: {books_in_db_before}")
        
        # Get all book URLs from website
        logger.info("Fetching book URLs from website...")
        site_urls = await get_all_book_urls_async(config.base_url)
        total_books_on_site = len(site_urls)
        logger.info(f"Found {total_books_on_site} books on website")
        
        # Get all book URLs from database
        logger.info("Fetching book URLs from database...")
        db_urls = await get_all_book_urls(db)
        logger.info(f"Found {len(db_urls)} books in database")
        
        # Categorize books
        new_book_urls, existing_book_urls = categorize_books(site_urls, db_urls)
        
        # Process new books
        new_books_added, new_books_failed = await process_new_books(
            db, new_book_urls, run_id, config
        )
        
        # Process existing books
        books_updated, books_unchanged, changelogs = await process_existing_books(
            db, existing_book_urls, run_id, config
        )
        
        # Calculate field statistics
        field_stats = calculate_field_statistics(changelogs)
        
        # Get final book count
        books_in_db_after = await count_books(db)
        
        # Calculate duration
        completed_at = datetime.now(UTC_PLUS_1)
        duration = (completed_at - started_at).total_seconds()
        
        # Create summary
        summary = SchedulerRunSummary(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            total_books_on_site=total_books_on_site,
            total_books_in_db_before=books_in_db_before,
            total_books_in_db_after=books_in_db_after,
            new_books_added=new_books_added,
            books_updated=books_updated,
            books_unchanged=books_unchanged,
            fields_changed=field_stats,
            errors=new_books_failed,
            error_details=None
        )
        
        # Log summary
        logger.info("="*60)
        logger.info("CHANGE DETECTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Run ID: {run_id}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        logger.info(f"Books on website: {total_books_on_site}")
        logger.info(f"Books in DB (before): {books_in_db_before}")
        logger.info(f"Books in DB (after): {books_in_db_after}")
        logger.info(f"New books added: {new_books_added}")
        logger.info(f"Books updated: {books_updated}")
        logger.info(f"Books unchanged: {books_unchanged}")
        logger.info(f"Errors: {new_books_failed}")
        
        if field_stats:
            logger.info("Field changes:")
            for field, count in field_stats.items():
                logger.info(f"  - {field}: {count} changes")
        
        logger.info("="*60)
        

        logger.info("Generating reports...")
        
        try:
            # Get all changelogs for this run
            all_changelogs = await get_changelogs_by_run_id(db, run_id)
            
            # Generate JSON report
            json_report_path = generate_json_report(summary, all_changelogs)
            logger.info(f"JSON report: {json_report_path}")
            
            # Generate CSV report
            csv_report_path = generate_csv_report(summary, all_changelogs)
            logger.info(f"CSV report: {csv_report_path}")
            
            # Send email alert with reports attached
            logger.info("Sending email alert...")
            email_sent = send_email_alert(
                summary,
                report_files=[json_report_path, csv_report_path],
                force_send=False  # Only send if changes detected
            )
            
            if email_sent:
                logger.info("Email alert sent successfully")
            else:
                logger.info("Email alert skipped (no changes or not configured)")
            
        except Exception as e:
            logger.error(f"Error generating reports or sending email: {e}")
        
        logger.info("="*60)

        return summary
        
    except Exception as e:
        logger.error(f"Fatal error during change detection: {e}")
        raise
    finally:
        await db_config.close_async()


if __name__ == "__main__":
    # Run change detection manually
    asyncio.run(run_change_detection())