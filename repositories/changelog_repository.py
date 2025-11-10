"""
ChangeLog repository - handles all changelog database operations
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.changelog import ChangeLog, ChangeLogCreate
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

UTC_PLUS_1 = timezone(timedelta(hours=1))


async def save_changelog(db: AsyncIOMotorDatabase, changelog_data: dict) -> bool:
    """
    Save a changelog entry to database
    
    Args:
        db: MongoDB database instance
        changelog_data: ChangeLog data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        changelog = ChangeLog(**changelog_data)
        changelog_dict = changelog.model_dump()
        
        result = await db.changelogs.insert_one(changelog_dict)
        
        logger.info(f"Inserted changelog for book: {changelog_dict['book_name']} ({changelog_dict['change_type']})")
        return True
        
    except Exception as e:
        logger.error(f"Error saving changelog to database: {e}")
        return False


async def get_changelogs_by_run_id(db: AsyncIOMotorDatabase, run_id: str) -> List[dict]:
    """
    Get all changelogs for a specific scheduler run
    
    Args:
        db: MongoDB database instance
        run_id: Scheduler run ID
        
    Returns:
        List of changelog documents
    """
    try:
        cursor = db.changelogs.find({'detection_run_id': run_id})
        changelogs = await cursor.to_list(length=None)
        return changelogs
    except Exception as e:
        logger.error(f"Error getting changelogs for run {run_id}: {e}")
        return []


async def get_recent_changelogs(db: AsyncIOMotorDatabase, limit: int = 100) -> List[dict]:
    """
    Get most recent changelog entries
    
    Args:
        db: MongoDB database instance
        limit: Maximum number of entries to return
        
    Returns:
        List of changelog documents, sorted by changed_at descending
    """
    try:
        cursor = db.changelogs.find().sort('changed_at', -1).limit(limit)
        changelogs = await cursor.to_list(length=limit)
        return changelogs
    except Exception as e:
        logger.error(f"Error getting recent changelogs: {e}")
        return []


async def get_changelogs_by_change_type(db: AsyncIOMotorDatabase, change_type: str, limit: int = 100) -> List[dict]:
    """
    Get changelogs filtered by change type
    
    Args:
        db: MongoDB database instance
        change_type: "added" or "updated"
        limit: Maximum number of entries to return
        
    Returns:
        List of changelog documents
    """
    try:
        cursor = db.changelogs.find({'change_type': change_type}).sort('changed_at', -1).limit(limit)
        changelogs = await cursor.to_list(length=limit)
        return changelogs
    except Exception as e:
        logger.error(f"Error getting changelogs by type {change_type}: {e}")
        return []


async def get_changelogs_by_date_range(
    db: AsyncIOMotorDatabase,
    start_date: datetime,
    end_date: datetime
) -> List[dict]:
    """
    Get changelogs within a date range
    
    Args:
        db: MongoDB database instance
        start_date: Start datetime (inclusive)
        end_date: End datetime (inclusive)
        
    Returns:
        List of changelog documents
    """
    try:
        cursor = db.changelogs.find({
            'changed_at': {
                '$gte': start_date,
                '$lte': end_date
            }
        }).sort('changed_at', -1)
        
        changelogs = await cursor.to_list(length=None)
        return changelogs
    except Exception as e:
        logger.error(f"Error getting changelogs by date range: {e}")
        return []


async def count_changelogs_by_run_id(db: AsyncIOMotorDatabase, run_id: str) -> dict:
    """
    Count changelogs by type for a specific run
    
    Args:
        db: MongoDB database instance
        run_id: Scheduler run ID
        
    Returns:
        Dictionary with counts: {"added": 5, "updated": 3}
    """
    try:
        pipeline = [
            {'$match': {'detection_run_id': run_id}},
            {'$group': {'_id': '$change_type', 'count': {'$sum': 1}}}
        ]
        
        results = await db.changelogs.aggregate(pipeline).to_list(length=10)
        
        counts = {result['_id']: result['count'] for result in results}
        return counts
        
    except Exception as e:
        logger.error(f"Error counting changelogs for run {run_id}: {e}")
        return {}


async def get_field_change_statistics(db: AsyncIOMotorDatabase, run_id: str) -> dict:
    """
    Get statistics on which fields changed in a run
    
    Args:
        db: MongoDB database instance
        run_id: Scheduler run ID
        
    Returns:
        Dictionary with field counts: {"price_incl_tax": 3, "availability": 2}
    """
    try:
        changelogs = await get_changelogs_by_run_id(db, run_id)
        
        field_counts = {}
        
        for changelog in changelogs:
            if changelog.get('changes'):
                for field_name in changelog['changes'].keys():
                    field_counts[field_name] = field_counts.get(field_name, 0) + 1
        
        return field_counts
        
    except Exception as e:
        logger.error(f"Error getting field statistics for run {run_id}: {e}")
        return {}


async def create_changelog_indexes(db: AsyncIOMotorDatabase):
    """
    Create indexes for changelogs collection
    
    Args:
        db: MongoDB database instance
    """
    try:
        await db.changelogs.create_index('detection_run_id')
        await db.changelogs.create_index('change_type')
        await db.changelogs.create_index([('changed_at', -1)])
        # await db.changelogs.create_index('book_id')
        await db.changelogs.create_index('book_source_url')
        await db.changelogs.create_index([('detection_run_id', 1), ('change_type', 1)])
        
        logger.info("Created changelog indexes")
    except Exception as e:
        logger.error(f"Error creating changelog indexes: {e}")