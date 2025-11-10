"""
APScheduler setup - runs change detection daily
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler.runner import run_change_detection
from config.crawler_config import CrawlerConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def scheduled_change_detection():
    """
    Wrapper function for scheduled runs
    """
    logger.info("Scheduled change detection triggered")
    
    try:
        config = CrawlerConfig()
        summary = await run_change_detection(config)
        
        logger.info("Scheduled change detection completed successfully")
        return summary
    
    except Exception as e:
        logger.error(f"Error in scheduled change detection: {e}")
        raise


def start_scheduler():
    """
    Start the APScheduler
    """
    logger.info("Starting scheduler...")
    
    scheduler = AsyncIOScheduler()
    
    # Schedule daily at 2:00 AM
    scheduler.add_job(
        scheduled_change_detection,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_change_detection',
        name='Daily Change Detection',
        replace_existing=True
    )
    
    logger.info("Scheduler configured to run daily at 02:00 AM")
    
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    return scheduler


async def main():
    """
    Main entry point - starts scheduler and keeps it running
    """
    logger.info("="*60)
    logger.info("ECOMMERCE CRAWLER SCHEDULER")
    logger.info("="*60)
    
    scheduler = start_scheduler()
    
    logger.info("Scheduler is running. Press Ctrl+C to exit.")
    logger.info("Next run scheduled for: 02:00 AM daily")
    
    try:
        # Keep the program running
        while True:
            await asyncio.sleep(60)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())