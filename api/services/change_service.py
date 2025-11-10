"""
Change service - business logic for changelog operations
"""
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging
from math import ceil

logger = logging.getLogger(__name__)


class ChangeService:
    """Service for changelog-related operations"""
    
    @staticmethod
    def build_change_filters(
        change_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Build MongoDB filter query for changelogs
        
        Args:
            change_type: Filter by change type ("added" or "updated")
            start_date: Filter changes after this date
            end_date: Filter changes before this date
            
        Returns:
            MongoDB filter dictionary
        """
        filters = {}
        
        if change_type:
            filters['change_type'] = change_type.lower()
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            filters['changed_at'] = date_filter
        
        return filters
    
    @staticmethod
    async def get_changes(
        db: AsyncIOMotorDatabase,
        change_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get paginated and filtered changes
        
        Args:
            db: Database connection
            change_type: Filter by type
            start_date: Filter from date
            end_date: Filter to date
            page: Page number
            page_size: Items per page
            
        Returns:
            Dictionary with pagination info and change data
        """
        try:
            # Build filters
            filters = ChangeService.build_change_filters(change_type, start_date, end_date)
            
            # Get total count
            total = await db.changelogs.count_documents(filters)
            
            # Calculate pagination
            total_pages = ceil(total / page_size) if total > 0 else 1
            skip = (page - 1) * page_size
            
            # Query database (sort by changed_at descending - newest first)
            cursor = db.changelogs.find(filters).sort('changed_at', -1).skip(skip).limit(page_size)
            changes = await cursor.to_list(length=page_size)
            
            # Remove MongoDB _id field
            for change in changes:
                change.pop('_id', None)
            
            logger.info(f"Retrieved {len(changes)} changes (page {page}/{total_pages}, total: {total})")
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'data': changes
            }
            
        except Exception as e:
            logger.error(f"Error fetching changes: {e}")
            raise
    
    @staticmethod
    async def get_recent_changes(db: AsyncIOMotorDatabase, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent changes (no pagination)
        
        Args:
            db: Database connection
            limit: Maximum number of changes to return
            
        Returns:
            List of recent changes
        """
        try:
            cursor = db.changelogs.find().sort('changed_at', -1).limit(limit)
            changes = await cursor.to_list(length=limit)
            
            for change in changes:
                change.pop('_id', None)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error fetching recent changes: {e}")
            raise
    
    @staticmethod
    async def get_change_statistics(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """
        Get statistics about changes
        
        Args:
            db: Database connection
            
        Returns:
            Dictionary with change statistics
        """
        try:
            total_changes = await db.changelogs.count_documents({})
            total_added = await db.changelogs.count_documents({'change_type': 'added'})
            total_updated = await db.changelogs.count_documents({'change_type': 'updated'})
            
            # Get latest change
            latest_change = await db.changelogs.find_one({}, sort=[('changed_at', -1)])
            
            # Get unique run IDs (number of scheduler runs)
            run_ids = await db.changelogs.distinct('detection_run_id')
            
            return {
                'total_changes': total_changes,
                'total_added': total_added,
                'total_updated': total_updated,
                'latest_change': latest_change.get('changed_at') if latest_change else None,
                'total_runs': len(run_ids)
            }
            
        except Exception as e:
            logger.error(f"Error fetching change statistics: {e}")
            raise