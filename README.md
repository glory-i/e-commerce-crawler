#  Web Crawler & API System

A production-grade Python web scraping and monitoring system for [books.toscrape.com](https://books.toscrape.com) - featuring async concurrent crawling, intelligent change detection, and a secure REST API with comprehensive test coverage.

---

## 🎯 Project Overview

This project demonstrates enterprise-level Python development practices through a complete data pipeline solution:

1. **Async Web Crawler** - High-performance scraper that collects and stores book data in MongoDB
2. **Intelligent Scheduler** - Daily monitoring system with hash-based change detection and automated email reports
3. **Production REST API** - FastAPI service with authentication, rate limiting, and comprehensive filtering capabilities


---

##  Architecture & Technical Approach

### Part 1: Robust Web Crawler

The crawler implements web scraping with enterprise patterns:

#### Performance Optimization
- **Async Concurrency**: Uses `httpx` with `asyncio.Semaphore` to process 10-20 books simultaneously
- **Batch Processing**: Configurable batch sizes (default: 50 books) for memory efficiency and progress tracking
- **Resume Capability**: Intelligent skip logic that queries existing URLs from MongoDB to avoid redundant crawling
- **Connection Pooling**: Maintains persistent HTTP client across requests for optimal network utilization


#### Robustness & Reliability
- **Exponential Backoff Retry Logic**: Uses `tenacity` library for intelligent retry handling with exponential delays
- **Graceful Error Handling**: Comprehensive exception catching prevents single-book failures from crashing entire crawl
- **HTML Snapshots**: Stores raw HTML as fallback for re-parsing if site structure changes
- **Transient Error Recovery**: Distinguishes between retryable network errors and permanent failures

#### Data Quality & Integrity
- **SHA256 Content Hashing**: Generates unique fingerprints for efficient change detection (O(1) comparison vs O(n) field-by-field)
- **Pydantic Validation**: Ensures data type safety and structure consistency before database insertion
- **Deduplication**: MongoDB unique indexes on `source_url` prevent duplicate entries
- **Comprehensive Metadata**: Tracks crawl timestamps, status codes, and source URLs for audit trails

**MongoDB Schema Design**:
```python
{
    "name": str,
    "description": str,
    "category": str,
    "price_excl_tax": float,
    "price_incl_tax": float,
    "availability": str,
    "num_reviews": int,
    "image_url": str,
    "rating": int,
    "source_url": str (unique indexed),
    "crawled_at": datetime,
    "content_hash": str (indexed),
    "raw_html_snapshot": str
}
```

**Optimized Indexes**:
- `source_url` (unique) - Deduplication and resume capability
- `category` - Category filtering in API
- `price_incl_tax` - Price range queries
- `rating` - Rating-based filtering
- `content_hash` - Fast change detection (O(1) hash comparison)
- `crawled_at` (descending) - Temporal queries

---

### Part 2: Scheduler & Change Detection

Implements sophisticated monitoring with automated reporting:

#### Intelligent Change Detection
- **Hash-Based Comparison**: SHA256 content hashes enable instant change detection without field-by-field comparison
- **Field-Level Tracking**: Records exactly which fields changed (price, availability, description, etc.)
- **New Book Detection**: Identifies newly added books by comparing current site inventory with database
- **Update vs Insert Logic**: Smart handling that updates existing records and inserts new ones

**Performance Optimization**:
```python
# Traditional approach: O(n * m) where n = fields, m = books
for field in ['price', 'availability', 'description', ...]:
    if old[field] != new[field]:
        changes.append(field)

# Hash-based approach: O(1) per book
if old_hash != new_hash:
    # Only then check individual fields
```

#### Scheduling & Automation
- **APScheduler Integration**: Cron-based scheduling (default: 2:00 AM daily)
- **Graceful Shutdown**: Proper cleanup of database connections and async resources
- **Configurable Frequency**: Easy modification of schedule without code changes
- **Missed Execution Handling**: Built-in coalescing to prevent duplicate runs

#### Reporting & Notifications
- **Dual Format Reports**: Generates both JSON and CSV  formats
- **Email Integration**: SMTP-based notifications with report attachments (JSON + CSV)
- **Change History Logging**: Maintains complete audit trail in MongoDB `changelogs` collection
- **Statistical Summaries**: Comprehensive metrics (books crawled, changes detected, errors encountered)



---

### Part 3: Secure REST API

Production-grade FastAPI application with enterprise security patterns:

#### API Architecture
- **Clean Architecture**: Three-layer separation (Routes → Services → Database)
- **Services Layer**: Business logic isolated from HTTP concerns for reusability and testability
- **Dependency Injection**: FastAPI dependencies for database connections and authentication
- **Response Models**: Pydantic schemas for type-safe API responses

**Folder Structure**:
```
api/
├── main.py              # FastAPI app initialization
├── routes/              # HTTP endpoint controllers
│   ├── books.py         # Book querying endpoints
│   ├── changes.py       # Changelog endpoints
│   └── api_keys.py      # API key management
├── services/            # Business logic layer
│   ├── book_service.py
│   └── change_service.py
└── auth.py              # Authentication middleware
```

#### Security Implementation
- **API Key Authentication**: Header-based authentication (`X-API-Key`) with database validation
- **Rate Limiting**: `SlowAPI` integration (100 requests/hour per API key)
- **Environment-Based Secrets**: API keys stored in `.env` with fallback to database
- **Key Management Endpoints**: CRUD operations for API key administration

####  Query Capabilities
**GET `/books`** - Comprehensive filtering and pagination:
- **Category Filtering**: `?category=Fiction`
- **Price Range**: `?min_price=10&max_price=50`
- **Rating Filter**: `?rating=4` (4 stars and above)
- **Multi-Sort Support**: `?sort_by=price,rating` with ascending/descending
- **Pagination**: `?page=2&page_size=20` (configurable limits)
- **Full-Text Search**: `?search=python` (searches name and description)

**GET `/books/{book_id}`** - Detailed book view with change history

**GET `/changes`** - Audit trail with filters:
- Date range filtering
- Change type filtering (new_book, update, deleted)
- Pagination support

**POST `/api-keys`** - Generate new API keys (authenticated)

#### API Documentation
- **OpenAPI/Swagger UI**: Auto-generated interactive documentation at `/docs`
- **ReDoc**: Alternative documentation view at `/redoc`
- **Schema Export**: `/openapi.json` for client generation

---

## 🛠️ Technologies & Design Decisions

### Core Libraries

| Technology | Purpose | Why This Choice |
|-----------|---------|-----------------|
| **httpx** | Async HTTP client | Modern async/await support, connection pooling, better than `requests` for concurrent operations |
| **BeautifulSoup4** | HTML parsing | Robust parsing for static HTML, simpler than Scrapy for this use case, no JavaScript rendering needed |
| **MongoDB + Motor** | NoSQL database | Flexible schema for varying book data, Motor provides async database operations matching our async crawler |
| **Pydantic** | Data validation | Type safety, automatic validation, clear error messages, perfect for API contracts and database schemas |
| **tenacity** | Retry logic | Declarative retry policies with exponential backoff, cleaner than manual retry loops |
| **APScheduler** | Task scheduling | Pythonic cron-like scheduling, supports async jobs, easier than Celery for single-machine deployments |
| **FastAPI** | REST API framework | Automatic OpenAPI docs, async support, dependency injection, fast performance |
| **SlowAPI** | Rate limiting | Simple integration with FastAPI, flexible rate limit strategies |
| **pytest + pytest-asyncio** | Testing | Async test support, fixture-based testing, comprehensive assertion library |

### Key Async Patterns
```python
# Semaphore for concurrency control
semaphore = asyncio.Semaphore(max_concurrent)
async with semaphore:
    response = await client.get(url)

# Batch processing with asyncio.gather
batches = [urls[i:i+batch_size] for i in range(0, len(urls), batch_size)]
for batch in batches:
    results = await asyncio.gather(*[scrape_book(url) for url in batch])
```

### Design Patterns Applied
- **Repository Pattern**: Database access abstracted through helper functions
- **Service Layer Pattern**: Business logic separated from HTTP handling
- **Decorator Pattern**: Retry logic implemented via `@retry` decorators
- **Dependency Injection**: FastAPI dependencies for database and auth

---

## 📊 Project Structure
```
ECommerceCrawler/
├── .env.example                 # Environment configuration template
├── requirements.txt             # Python dependencies with versions
├── generate-api-keys.py         # Utility to generate API keys
│
├── config/
│   ├── __init__.py
│   ├── database.py              # MongoDB connection management
│   ├── settings.py              # Environment variable loading
│   └── crawler_config.py        # Crawler behavior configuration
│
├── models/
│   ├── __init__.py
│   ├── book.py                  # Book Pydantic schema
│   ├── changelog.py             # Changelog Pydantic schema
│   └── api_key.py               # API Key schema
│
├── crawler/
│   ├── __init__.py
│   ├── main.py                  # Entry point for crawler execution
│   ├── async_scraper.py         # Async book scraping logic
│   ├── url_extractor.py         # Pagination and URL collection
│   └── utils/
│       ├── db_helpers.py        # Database operations (insert, update, dedup)
│       └── html_helpers.py      # HTML parsing utilities
│
├── scheduler/
│   ├── __init__.py
│   ├── runner.py                # APScheduler job runner
│   ├── change_detector.py       # Change detection logic
│   ├── report_generator.py      # JSON/CSV report creation
│   └── email_notifier.py        # SMTP email sending
│
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── auth.py                  # API key authentication
│   ├── routes/
│   │   ├── books.py             # Book endpoints
│   │   ├── changes.py           # Changelog endpoints
│   │   └── api_keys.py          # Key management endpoints
│   └── services/
│       ├── book_service.py      # Book business logic
│       └── change_service.py    # Changelog business logic
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_crawler.py          # Crawler unit tests
│   ├── test_scheduler.py        # Scheduler tests
│   └── test_api.py              # API endpoint tests
│
├── reports/
│   └── output/                  # Generated daily reports (JSON/CSV)
│
└── submission/
    ├── document_structure/      # Sample MongoDB documents
    ├── screenshots/             # Crawl logs and execution screenshots
    └── sample_reports/          # Example daily change reports
```

---

## 📝 Sample Documents & Reports

### MongoDB Book Document
See `submission/document_structure/book.json`

### MongoDB Changelog Document
See `submission/document_structure/change_log.json`


### Execution Screenshots
- Successful crawl logs: `submission/screenshots/`

---

## 🔧 Configuration

The system is highly configurable through environment variables and configuration files:

### Crawler Configuration (`config/crawler_config.py`)
- `skip_existing`: Resume from last crawl (default: `True`)
- `max_concurrent_requests`: Concurrent async requests (default: `10`)
- `batch_size`: Books per processing batch (default: `50`)
- `max_retries`: Retry attempts for failed requests (default: `3`)

### Environment Variables (`.env`)
See `.env.example` for required configuration:
- MongoDB connection strings
- SMTP email settings
- API key configuration

---

## 🚀 Python Version

**Python 3.12.6**

All dependencies and versions are specified in `requirements.txt`.

---

