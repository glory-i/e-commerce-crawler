import httpx
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime, UTC, timezone, timedelta


UTC_PLUS_1 = timezone(timedelta(hours=1))

def parse_rating(rating_class):
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


def clean_price(price_text):
    #Convert price text to float. Example: '£51.77' -> 51.77
    try:
        return float(price_text.replace('£', '').strip())
    except (ValueError, AttributeError):
        return 0.0


def generate_content_hash(book_data):
    # use the SHA 256 algorithm to generate a hash for the book.
    hash_string = f"{book_data['name']}|{book_data['price_incl_tax']}|{book_data['price_excl_tax']}|{book_data['availability']}|{book_data['rating']}"
    return hashlib.sha256(hash_string.encode()).hexdigest()



#Safely get attribute from tag, return default if missing or empty
def safe_get_attribute(tag, attribute, default=None):    
    if not tag:
        return default
    
    value = tag.get(attribute)
    
    if value and value.strip():
        return value.strip()
    
    return default


def scrape_book_detail(url):
    """
    Scrape a single book detail page.
    
    Args:
        url: Absolute URL of the book detail page
        
    Returns:
        dict: Book data including name, price, rating, etc.
        
    Raises:
        httpx.HTTPError: If request fails
        ValueError: If required fields are missing
    """
    print(f"\nFetching: {url}")
    #Fetch the HTML
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()  
    html = response.text
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract all fields
    
    # Name - from <h1> tag
    name = soup.find('h1').text.strip()
    
    # Category - from breadcrumb (3rd <li> item)
    category = "Unknown"
    breadcrumb = soup.find('ul', class_='breadcrumb')
    if breadcrumb:
        breadcrumb_items = breadcrumb.find_all('li')
        # Check if we have at least 3 items because the category is at index 2
        if len(breadcrumb_items) >= 3:
            category_link = breadcrumb_items[2].find('a')
            if category_link:
                category = category_link.text.strip()
    
    #extract product desciption
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
            # handle missing/empty 'src'
            src = safe_get_attribute(image_tag, 'src')
            if src:
                # Convert relative URL to absolute
                image_url = f"https://books.toscrape.com/{src.replace('../../', '')}"
    

    # Rating - from star-rating class
    rating = 0
    rating_p = soup.find('p', class_='star-rating')
    if rating_p:
        classes = rating_p.get('class', [])
        # Check if we have at least 2 items since the rating star is at the second index
        if len(classes) >= 2:
            rating = parse_rating(classes[1])
    

    # extract from Product Information Table
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
            
            # Skip if either is missing
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
    
    # Build book data dictionary
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


def get_book_urls_from_page(page_url):
    """
    Extract all book URLs from a catalog/list page
    
    Args:
        page_url: URL of the page containing book listings
        
    Returns:
        List of absolute book URLs
    """
    print(f"\nFetching book list from: {page_url}")
    
    # Fetch the page
    response = httpx.get(page_url, timeout=10.0)
    response.raise_for_status()
    html = response.text
    
    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # Find all book articles
    articles = soup.find_all('article', class_='product_pod')
    print(f"Found {len(articles)} books on this page")
    
    book_urls = []
    
    # Extract URL from each article
    for article in articles:
        # Find the <h3> tag  which contains the book link
        h3_tag = article.find('h3')
        if not h3_tag:
            continue
        
        # Find the <a> tag inside <h3>
        link_tag = h3_tag.find('a')
        if not link_tag:
            continue
        
        # Get the href attribute
        href = safe_get_attribute(link_tag, 'href')
        if not href:
            continue
        
        # Step 5: Convert relative URL to absolute URL
        # href looks like: "../../a-light-in-the-attic_1000/index.html"
        # or: "catalogue/a-light-in-the-attic_1000/index.html"
        
        # Remove leading "../" patterns
        href = href.replace('../', '')
        
        # Build absolute URL
        if href.startswith('catalogue/'):
            absolute_url = f"https://books.toscrape.com/{href}"
        else:
            # Already includes catalogue path
            absolute_url = f"https://books.toscrape.com/catalogue/{href}"
        
        book_urls.append(absolute_url)
    
    return book_urls


def get_all_pagination_urls(base_url: str = "https://books.toscrape.com/") -> list:
    """
    Get all pagination page URLs by parsing 'Page X of Y' text
    
    Args:
        base_url: Base URL of the website
        
    Returns:
        List of all page URLs to crawl
    """
    print(f"\nChecking pagination at: {base_url}")
    
    # Fetch homepage to find total pages
    response = httpx.get(base_url, timeout=10.0)
    response.raise_for_status()
    html = response.text
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Find the pagination section
    pagination = soup.find('ul', class_='pager')
    
    if not pagination:
        # No pagination found, only one page
        print("No pagination found - single page only")
        return [base_url]
    
    # Find the "current" page element with text like "Page 3 of 50"
    current_page_li = pagination.find('li', class_='current')
    
    if not current_page_li:
        # No current page indicator, assume single page
        print("No current page indicator found - single page only")
        return [base_url]
    
    # Extract text: "Page 3 of 50" or just "Page 1 of 50"
    page_text = current_page_li.text.strip()
    print(f"Found pagination text: '{page_text}'")
    
    # Parse the text to extract total pages
    # Expected format: "Page 3 of 50" or "Page 1 of 50"
    try:
        # Split by "of" and get the last part
        parts = page_text.split('of')
        if len(parts) != 2:
            print("Could not parse pagination format - single page only")
            return [base_url]
        
        # Get total pages number
        total_pages = int(parts[1].strip())
        print(f"Found {total_pages} total pages")
        
    except (ValueError, IndexError) as e:
        print(f"Error parsing pagination: {e} - single page only")
        return [base_url]
    
    # Build list of all page URLs
    page_urls = [base_url]  # Page 1
    
    for page_num in range(2, total_pages + 1):
        page_url = f"{base_url}catalogue/page-{page_num}.html"
        page_urls.append(page_url)
    
    return page_urls



def get_all_book_urls(base_url: str = "https://books.toscrape.com/") -> list:
    """
    Get all book URLs from all pages
    
    Args:
        base_url: Base URL of the website
        
    Returns:
        List of all book URLs across all pages
    """
    # Get all page URLs
    page_urls = get_all_pagination_urls(base_url)
    
    all_book_urls = []
    
    # Extract book URLs from each page
    for page_index, page_url in enumerate(page_urls, 1):
        print(f"\nProcessing page {page_index}/{len(page_urls)}")
        
        try:
            book_urls = get_book_urls_from_page(page_url)
            all_book_urls.extend(book_urls)
            print(f"Extracted {len(book_urls)} books from page {page_index}")
            
        except Exception as e:
            print(f"Error processing page {page_url}: {e}")
            continue
    
    print(f"\nTotal books found: {len(all_book_urls)}")
    return all_book_urls



#for testing
if __name__ == "__main__":
    print("="*10)
    print("TESTING WEB SCRAPER")
    print("="*10)
    
    # Test 1: Extract book URLs from homepage
    print("\n[TEST 1] Extracting book URLs from homepage...")
    homepage_url = "https://books.toscrape.com/"
    
    try:
        book_urls = get_book_urls_from_page(homepage_url)
        
        print(f"\nSuccessfully extracted {len(book_urls)} book URLs")
        print("\nFirst 5 URLs:")
        for i, url in enumerate(book_urls[:5], 1):
            print(f"  {i}. {url}")
        
    except Exception as e:
        print(f"Error extracting URLs: {e}")
        exit(1)
    
    # Test 2: Scrape details from first book
    print("\n" + "="*60)
    print("[TEST 2] Scraping details from first book...")
    print("="*60)
    
    if book_urls:
        first_book_url = book_urls[0]
        
        try:
            book = scrape_book_detail(first_book_url)
            
            print("\nBOOK DATA EXTRACTED:")
            print("-"*60)
            
            # Print all fields (except raw HTML)
            for key, value in book.items():
                if key != 'raw_html_snapshot':
                    print(f"{key}: {value}")
            
            print(f"\nraw_html_snapshot: [Stored - {len(book['raw_html_snapshot'])} characters]")
            
        except Exception as e:
            print(f"Error scraping book: {e}")
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)
    # Test with ONE book
    test_url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    
    try:
        book = scrape_book_detail(test_url)
        
        print("\n" + "="*50)
        print("BOOK DATA EXTRACTED:")
        print("="*50)
        
        # Print all fields (except raw HTML)
        for key, value in book.items():
            if key != 'raw_html_snapshot':  # Don't print HTML (too long)
                print(f"{key}: {value}")
        
        print(f"\nraw_html_snapshot: [Stored - {len(book['raw_html_snapshot'])} characters]")
        
    except Exception as e:
        print(f"Error: {e}")