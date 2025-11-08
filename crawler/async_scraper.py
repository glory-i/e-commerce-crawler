"""
Async web scraper for concurrent book crawling
"""
import httpx
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime, timezone, timedelta
import asyncio
from typing import List, Optional
from tenacity import (retry, stop_after_attempt, wait_exponential, retry_if_exception_type,before_sleep_log)

import logging


logger = logging.getLogger(__name__)

UTC_PLUS_1 = timezone(timedelta(hours=1))


def parse_rating(rating_class: str) -> int:
    """
    Convert rating class to number
    
    Args:
        rating_class: Rating text like 'Three', 'Five', etc.
        
    Returns:
        Rating number (1-5) or 0 if invalid
    """
    rating_map = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    
    if rating_class.strip() in rating_map:
        return rating_map[rating_class]
    
    return 0


def clean_price(price_text: str) -> float:
    """
    Convert price text to float
    
    Args:
        price_text: Price string like '£51.77'
        
    Returns:
        Float price value
    """
    try:
        return float(price_text.replace('£', '').strip())
    except (ValueError, AttributeError):
        return 0.0


def generate_content_hash(book_data: dict) -> str:
    """
    Generate SHA256 hash for change detection
    
    Args:
        book_data: Dictionary containing book data
        
    Returns:
        SHA256 hash string
    """
    hash_string = f"{book_data['name']}|{book_data['price_incl_tax']}|{book_data['price_excl_tax']}|{book_data['availability']}|{book_data['rating']}"
    return hashlib.sha256(hash_string.encode()).hexdigest()


def safe_get_attribute(tag, attribute: str, default=None):
    """
    Safely get attribute from tag, return default if missing or empty
    
    Args:
        tag: BeautifulSoup tag object
        attribute: Attribute name to get
        default: Default value if attribute missing
        
    Returns:
        Attribute value or default
    """
    if not tag:
        return default
    
    value = tag.get(attribute)
    if value and value.strip():
        return value.strip()
    
    return default


@retry(
    stop=stop_after_attempt(3),  
    wait=wait_exponential(multiplier=1, min=1, max=10),  
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)  
)
async def fetch_html(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """
    Fetch HTML content from URL asynchronously
    
    Args:
        client: Async HTTP client
        url: URL to fetch
        
    Returns:
        HTML content as string, or None if failed
    """
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.text
    except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
        logger.warning(f"Attempt failed for {url}: {e}")
        raise  # to trigger retry
    except Exception as e:
        logger.error(f"Non-retryable error fetching {url}: {e}")
        return None


def parse_book_html(html: str, url: str) -> Optional[dict]:
    """
    Parse book HTML and extract all fields
    
    Args:
        html: HTML content of book page
        url: Source URL of the book
        
    Returns:
        Dictionary with book data, or None if parsing failed
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract all fields
                
        # Name
        name_tag = soup.find('h1')
        name = name_tag.text.strip() if name_tag else "Unknown"
        
        # Category
        category = "Unknown"
        breadcrumb = soup.find('ul', class_='breadcrumb')
        if breadcrumb:
            breadcrumb_items = breadcrumb.find_all('li')
            if len(breadcrumb_items) >= 3:
                category_link = breadcrumb_items[2].find('a')
                if category_link:
                    category = category_link.text.strip()
        
        # Description
        description = None
        description_div = soup.find('div', id='product_description')
        if description_div:
            description_p = description_div.find_next_sibling('p')
            if description_p:
                description = description_p.text.strip()
        
        # Image URL
        image_url = None
        image_div = soup.find('div', class_='item active')
        if image_div:
            image_tag = image_div.find('img')
            if image_tag:
                src = safe_get_attribute(image_tag, 'src')
                if src:
                    image_url = f"https://books.toscrape.com/{src.replace('../../', '')}"
        
        # Rating
        rating = 0
        rating_p = soup.find('p', class_='star-rating')
        if rating_p:
            classes = rating_p.get('class', [])
            if len(classes) >= 2:
                rating = parse_rating(classes[1])
        
        # Product Information Table
        price_incl_tax = 0.0
        price_excl_tax = 0.0
        availability = "Unknown"
        number_of_reviews = 0
        
        table = soup.find('table', class_='table-striped')
        if table:
            rows = table.find_all('tr')
            
            for row in rows:
                header_tag = row.find('th')
                value_tag = row.find('td')
                
                if not header_tag or not value_tag:
                    continue
                
                header = header_tag.text.strip()
                value = value_tag.text.strip()
                
                if header == 'Price (incl. tax)':
                    price_incl_tax = clean_price(value)
                elif header == 'Price (excl. tax)':
                    price_excl_tax = clean_price(value)
                elif header == 'Availability':
                    availability = value
                elif header == 'Number of reviews':
                    try:
                        number_of_reviews = int(value)
                    except ValueError:
                        number_of_reviews = 0
        
        # Build book data dictionary - ensure limits are not exceeded so that pydantic model validation passes.
        book_data = {
            'name': name[:500] if name else "Unknown",  
            'description': description[:5000] if description else None,  
            'category': category[:100] if category else "Unknown",  
            'price_incl_tax': price_incl_tax,
            'price_excl_tax': price_excl_tax,
            'availability': availability[:100] if availability else "Unknown",  
            'number_of_reviews': number_of_reviews,
            'image_url': image_url,
            'rating': rating,
            'source_url': url,
            'crawled_at': datetime.now(UTC_PLUS_1),
            'raw_html_snapshot': html
        }
        
        # Generate content hash
        book_data['content_hash'] = generate_content_hash(book_data)
        
        return book_data
        
    except Exception as e:
        print(f"Error parsing book HTML from {url}: {e}")
        return None


async def scrape_book_async(client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore) -> Optional[dict]:
    """
    Scrape a single book asynchronously with concurrency control and retry logic
    
    Args:
        client: Async HTTP client
        url: Book URL to scrape
        semaphore: Semaphore to limit concurrent requests
        
    Returns:
        Book data dictionary or None if failed after all retries
    """
    async with semaphore:
        try:
            # Fetch HTML 
            html = await fetch_html(client, url)
            
            if not html:
                return None
            
            # Parse HTML
            book_data = parse_book_html(html, url)
            
            return book_data
            
        except Exception as e:
            # All retries exhausted
            logger.error(f"Failed to scrape {url} after all retry attempts: {e}")
            return None

async def scrape_multiple_books(book_urls: List[str], max_concurrent: int = 10) -> List[dict]:
    """
    Scrape multiple books concurrently
    
    Args:
        book_urls: List of book URLs to scrape
        max_concurrent: Maximum number of concurrent requests
        
    Returns:
        List of book data dictionaries (successful scrapes only)
    """
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create async HTTP client
    async with httpx.AsyncClient() as client:
        # Create tasks for all books
        tasks = [
            scrape_book_async(client, url, semaphore)
            for url in book_urls
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
    
    # Filter out None values (failed scrapes)
    successful_results = [book for book in results if book is not None]
    
    return successful_results


async def get_book_urls_from_page_async(client: httpx.AsyncClient, page_url: str) -> List[str]:
    """
    Extract all book URLs from a catalog page asynchronously
    
    Args:
        client: Async HTTP client
        page_url: URL of the catalog page
        
    Returns:
        List of book URLs
    """
    html = await fetch_html(client, page_url)
    
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    articles = soup.find_all('article', class_='product_pod')
    
    book_urls = []
    
    for article in articles:
        h3_tag = article.find('h3')
        if not h3_tag:
            continue
        
        link_tag = h3_tag.find('a')
        if not link_tag:
            continue
        
        href = safe_get_attribute(link_tag, 'href')
        if not href:
            continue
        
        # Convert relative URL to absolute
        href = href.replace('../', '')
        
        if href.startswith('catalogue/'):
            absolute_url = f"https://books.toscrape.com/{href}"
        else:
            absolute_url = f"https://books.toscrape.com/catalogue/{href}"
        
        book_urls.append(absolute_url)
    
    return book_urls


async def get_all_book_urls_async(base_url: str = "https://books.toscrape.com/") -> List[str]:
    """
    Get all book URLs from all pages asynchronously
    
    Args:
        base_url: Base URL of the website
        
    Returns:
        List of all book URLs
    """
    print(f"\nFetching all book URLs from {base_url}")
    
    async with httpx.AsyncClient() as client:
        # Get pagination info from homepage
        html = await fetch_html(client, base_url)
        
        if not html:
            print("Failed to fetch homepage")
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        pagination = soup.find('ul', class_='pager')
        
        total_pages = 1
        
        if pagination:
            current_page_li = pagination.find('li', class_='current')
            if current_page_li:
                page_text = current_page_li.text.strip()
                try:
                    parts = page_text.split('of')
                    if len(parts) == 2:
                        total_pages = int(parts[1].strip())
                        print(f"Found {total_pages} pages")
                except (ValueError, IndexError):
                    pass
        
        # Build all page URLs
        page_urls = [base_url]
        for page_num in range(2, total_pages + 1):
            page_url = f"{base_url}catalogue/page-{page_num}.html"
            page_urls.append(page_url)
        
        print(f"Extracting book URLs from {len(page_urls)} pages...")
        
        # Fetch book URLs from all pages concurrently
        tasks = [
            get_book_urls_from_page_async(client, page_url)
            for page_url in page_urls
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Flatten list of lists
        all_book_urls = []
        for book_urls in results:
            all_book_urls.extend(book_urls)
        
        print(f"Total book URLs extracted: {len(all_book_urls)}")
        
        return all_book_urls