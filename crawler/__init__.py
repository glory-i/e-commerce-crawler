from .simple_scraper import get_all_book_urls, scrape_book_detail
from .async_scraper import get_all_book_urls_async, scrape_multiple_books

__all__ = [
    'get_all_book_urls', 
    'scrape_book_detail',
    'get_all_book_urls_async',
    'scrape_multiple_books'
]