"""
Book service - business logic for book operations
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from math import ceil
from bson import ObjectId

logger = logging.getLogger(__name__)


class BookService:
    """Service for book-related operations"""
    
    @staticmethod
    def build_book_filters(
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build MongoDB filter query from parameters
        
        Args:
            category: Filter by category
            min_price: Minimum price (inclusive)
            max_price: Maximum price (inclusive)
            rating: Filter by rating
            
        Returns:
            MongoDB filter dictionary
        """
        filters = {}
        
        if category:
            # Case-insensitive category search
            filters['category'] = {'$regex': f'^{category}$', '$options': 'i'}
        
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter['$gte'] = min_price
            if max_price is not None:
                price_filter['$lte'] = max_price
            filters['price_incl_tax'] = price_filter
        
        if rating is not None:
            filters['rating'] = rating
        
        return filters
    
    @staticmethod
    def build_sort_criteria(sort_by: Optional[str] = None) -> List[tuple]:
        """
        Build MongoDB sort criteria
        
        Args:
            sort_by: Field to sort by (rating, price, reviews)
            
        Returns:
            List of (field, direction) tuples for MongoDB sort
        """
        sort_map = {
            'rating': [('rating', -1)],  # Highest rating first
            'price': [('price_incl_tax', 1)],  # Lowest price first
            'reviews': [('number_of_reviews', -1)],  # Most reviews first
            'name': [('name', 1)],  # Alphabetical
        }
        
        if sort_by and sort_by.lower() in sort_map:
            return sort_map[sort_by.lower()]
        
        # Default sort by crawled_at (newest first)
        return [('crawled_at', -1)]
    
    @staticmethod
    async def get_books(
        db: AsyncIOMotorDatabase,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        rating: Optional[int] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get paginated, filtered, and sorted books
        
        Args:
            db: Database connection
            category: Filter by category
            min_price: Minimum price
            max_price: Maximum price
            rating: Filter by rating
            sort_by: Sort field
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Dictionary with pagination info and book data
        """
        try:
            # Build filters
            filters = BookService.build_book_filters(category, min_price, max_price, rating)
            
            # Get total count
            total = await db.books.count_documents(filters)
            
            # Calculate pagination
            total_pages = ceil(total / page_size) if total > 0 else 1
            skip = (page - 1) * page_size
            
            # Build sort criteria
            sort_criteria = BookService.build_sort_criteria(sort_by)
            
            # Query database
            cursor = db.books.find(filters).sort(sort_criteria).skip(skip).limit(page_size)
            books = await cursor.to_list(length=page_size)
            
            for book in books:
                book['id'] = str(book.pop('_id'))
                book.pop('raw_html_snapshot', None)  # Don't send HTML in API
                book.pop('content_hash', None)  # Internal field
            
            logger.info(f"Retrieved {len(books)} books (page {page}/{total_pages}, total: {total})")
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'data': books
            }
            
        except Exception as e:
            logger.error(f"Error fetching books: {e}")
            raise
    

    @staticmethod
    async def get_book_by_book_id(db: AsyncIOMotorDatabase, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single book by bookid
        
        Args:
            db: Database connection
            book_id: book id
            
        Returns:
            Book document or None if not found
        """
        try:
            # Convert string to ObjectId
            try:
                object_id = ObjectId(book_id)
            except Exception:
                # Invalid ObjectId format
                logger.warning(f"Invalid MongoDB ObjectId format: {book_id}")
                return None
            
            # Query by _id
            book = await db.books.find_one({'_id': object_id})
            
            if book:
                # Convert _id to string for JSON serialization
                book['id'] = str(book.pop('_id'))
                book.pop('raw_html_snapshot', None)
                book.pop('content_hash', None)
                logger.info(f"Retrieved book by ID: {book.get('name', 'Unknown')}")
            else:
                logger.warning(f"Book not found with ID: {book_id}")
            
            return book
            
        except Exception as e:
            logger.error(f"Error fetching book by MongoDB ID: {e}")
            raise

    @staticmethod
    async def get_book_by_source_url(db: AsyncIOMotorDatabase, book_source_url: str) -> Optional[Dict[str, Any]]:
        """
        Get a single book by ID (source_url)
        
        Args:
            db: Database connection
            book_source_url: Book source URL
            
        Returns:
            Book document or None if not found
        """
        try:
            book = await db.books.find_one({'source_url': book_source_url})
            
            if book:
                book['id'] = str(book.pop('_id'))
                book.pop('raw_html_snapshot', None)
                book.pop('content_hash', None)
                logger.info(f"Retrieved book: {book.get('name', 'Unknown')}")
            else:
                logger.warning(f"Book not found: {book_source_url}")
            
            return book
            
        except Exception as e:
            logger.error(f"Error fetching book by ID: {e}")
            raise
    
    @staticmethod
    async def get_all_categories(db: AsyncIOMotorDatabase) -> List[str]:
        """
        Get list of all unique categories
        
        Args:
            db: Database connection
            
        Returns:
            List of category names
        """
        try:
            categories = await db.books.distinct('category')
            return sorted(categories)
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise