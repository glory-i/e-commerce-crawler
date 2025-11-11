"""
Test scheduler with immediate execution
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scheduler.runner import run_change_detection
from config.crawler_config import CrawlerConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_immediate_run():
    """Test change detection without scheduler"""
    logger.info("Running change detection immediately...")
    
    config = CrawlerConfig()
    summary = await run_change_detection(config)
    
    logger.info("Test complete!")
    return summary


async def test_scheduler_every_minute():
    """Test scheduler that runs every minute (for testing)"""
    logger.info("Starting test scheduler (runs every minute)...")
    
    scheduler = AsyncIOScheduler()
    
    # Run every minute for testing
    scheduler.add_job(
        run_change_detection,
        'cron',
        # minute='*/2',  # Every 2 minutes
        minute='*',  # Every minute
        id='test_change_detection',
        name='Test Change Detection'
    )
    
    scheduler.start()
    logger.info("Scheduler started. Will run every minute. Press Ctrl+C to stop.")
    
    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    # Test immediate run
    #asyncio.run(test_immediate_run())
    
    # Or test scheduler (uncomment to test)
    asyncio.run(test_scheduler_every_minute())