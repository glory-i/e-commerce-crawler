# """
# Database helper functions for book operations
# """
# from motor.motor_asyncio import AsyncIOMotorDatabase
# from models.book import BookModel
# from typing import Optional, List, Set
# import logging


# logger = logging.getLogger(__name__)


# async def save_book_to_db(db: AsyncIOMotorDatabase, book_data: dict) -> bool:
#     """
#     Save a book to MongoDB with upsert (insert or update)
    
#     Args:
#         db: MongoDB database instance
#         book_data: Book data dictionary
        
#     Returns:
#         True if successful, False otherwise
#     """
#     try:
#         # Validate data with Pydantic model
#         book = BookModel(**book_data)
        
#         # Convert to dict for MongoDB
#         book_dict = book.model_dump()
        
#         # Upsert: Update if exists, insert if new
#         result = await db.books.update_one(
#             {'source_url': book_dict['source_url']},
#             {'$set': book_dict},
#             upsert=True
#         )
        
#         if result.upserted_id:
#             logger.info(f"Inserted new book: {book_dict['name']}")
#         elif result.modified_count > 0:
#             logger.info(f"Updated existing book: {book_dict['name']}")
#         else:
#             logger.debug(f"No changes for book: {book_dict['name']}")
        
#         return True
        
#     except Exception as e:
#         logger.error(f"Error saving book to database: {e}")
#         return False


# async def get_book_by_url(db: AsyncIOMotorDatabase, source_url: str) -> Optional[dict]:
#     """
#     Retrieve a book from database by source URL
    
#     Args:
#         db: MongoDB database instance
#         source_url: Book's source URL
        
#     Returns:
#         Book document if found, None otherwise
#     """
#     try:
#         book = await db.books.find_one({'source_url': source_url})
#         return book
#     except Exception as e:
#         logger.error(f"Error retrieving book: {e}")
#         return None


# async def get_all_crawled_urls(db: AsyncIOMotorDatabase) -> Set[str]:
#     """
#     Get set of all source URLs already in database 
    
#     Args:
#         db: MongoDB database instance
        
#     Returns:
#         Set of source URLs (set allows O(1) lookup)
#     """
#     try:
#         # Only fetch the source_url field 
#         cursor = db.books.find({}, {'source_url': 1, '_id': 0})
        
#         # Use set for O(1) lookup performance
#         urls = {doc['source_url'] async for doc in cursor}
        
#         logger.info(f"Found {len(urls)} books already in database")
#         return urls
        
#     except Exception as e:
#         logger.error(f"Error getting crawled URLs: {e}")
#         return set()


# async def get_crawl_statistics(db: AsyncIOMotorDatabase) -> dict:
#     """
#     Get statistics about crawled books
    
#     Args:
#         db: MongoDB database instance
        
#     Returns:
#         Dictionary with statistics
#     """
#     try:
#         total_books = await db.books.count_documents({})
        
#         # Get category distribution
#         pipeline = [
#             {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
#             {'$sort': {'count': -1}},
#             {'$limit': 10}
#         ]
#         top_categories = await db.books.aggregate(pipeline).to_list(length=10)
        
#         # Get latest crawl time
#         latest = await db.books.find_one(
#             {},
#             sort=[('crawled_at', -1)]
#         )
        
#         return {
#             'total_books': total_books,
#             'top_categories': top_categories,
#             'latest_crawl': latest['crawled_at'] if latest else None
#         }
        
#     except Exception as e:
#         logger.error(f"Error getting statistics: {e}")
#         return {}


# async def create_indexes(db: AsyncIOMotorDatabase):
#     """
#     Create database indexes for efficient querying
    
#     Args:
#         db: MongoDB database instance
#     """
#     try:
#         # Unique index on source_url (prevents duplicates)
#         await db.books.create_index('source_url', unique=True)
#         logger.info("Created unique index on source_url")
        
#         # Indexes for common queries
#         await db.books.create_index('category')
#         await db.books.create_index('price_incl_tax')
#         await db.books.create_index('rating')
#         await db.books.create_index([('crawled_at', -1)])
        
#         # Compound index for filtering
#         await db.books.create_index([('category', 1), ('price_incl_tax', 1)])
        
#         logger.info("Created all database indexes")
        
#     except Exception as e:
#         logger.error(f"Error creating indexes: {e}")