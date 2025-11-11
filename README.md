#  Web Crawler & API System

A Python web scraping and monitoring system for [books.toscrape.com](https://books.toscrape.com) - featuring async concurrent crawling, intelligent change detection, and a secure REST API with comprehensive test coverage.

---

## 🎯 Project Overview

This project demonstrates enterprise-level Python development practices through a complete data pipeline solution:

1. **Async Web Crawler** - High-performance scraper that collects and stores book data in MongoDB
2. **Intelligent Scheduler** - Daily monitoring system with hash-based change detection and automated email reports
3. **Production REST API** - FastAPI service with authentication, rate limiting, and comprehensive filtering capabilities


---

## 🚀 Setup Instructions

Follow these steps to set up and run the project on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.12.6** (or compatible 3.12.x version)
- **MongoDB** (local installation, Docker, or MongoDB Atlas account)
- **Git** (for cloning the repository)
- A **Gmail account** (for email notifications)

---

### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd ECommerceCrawler
```

---

### Step 2: Create Python Virtual Environment

Create and activate a virtual environment to isolate project dependencies:

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` prefix in your terminal, indicating the virtual environment is active.

---

### Step 3: Install Dependencies

Install all required Python packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

This will install all libraries with their specific versions as used in development.

---

### Step 4: Set Up MongoDB

Choose **one** of the following three approaches:

#### **Option A: Local MongoDB Installation** (Recommended for development)

1. **Download and install MongoDB Community Server:**
   - Visit: https://www.mongodb.com/try/download/community
   - Follow installation instructions for your operating system

2. **Start MongoDB service:**
   
   **Windows:**
```bash
   net start MongoDB
```
   
   **macOS (using Homebrew):**
```bash
   brew services start mongodb-community
```
   
   **Linux:**
```bash
   sudo systemctl start mongod
```

3. **Verify MongoDB is running:**
```bash
   mongosh
   # Should connect to mongodb://localhost:27017
```

4. **Your connection string will be:**
```
   MONGO_URI=mongodb://localhost:27017
```

#### **Option B: MongoDB Atlas** (Cloud-hosted, free tier available)

1. **Create a free account:**
   - Visit: https://www.mongodb.com/cloud/atlas/register
   - Sign up for a free account

2. **Create a cluster:**
   - Choose the free tier (M0)
   - Select a cloud provider and region closest to you

3. **Set up database access:**
   - Go to "Database Access" → Create a database user
   - Set username and password (save these!)
   - Grant "Read and write to any database" permissions

4. **Configure network access:**
   - Go to "Network Access" → Add IP Address
   - For development, you can use `0.0.0.0/0` (allow from anywhere)
   - **Note:** Restrict this in production!

5. **Get your connection string:**
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (looks like: `mongodb+srv://username:password@cluster.xxxxx.mongodb.net/`)
   - Replace `<password>` with your database user password

6. **Your connection string will be:**
```
   MONGO_URI=mongodb+srv://username:password@cluster.xxxxx.mongodb.net/ecommerce_crawler?retryWrites=true&w=majority
```

#### **Option C: MongoDB with Docker** (Containerized approach)

1. **Install Docker Desktop:**
   - Visit: https://www.docker.com/products/docker-desktop

2. **Run MongoDB container:**
```bash
   docker run -d \
     --name mongodb \
     -p 27017:27017 \
     -e MONGO_INITDB_ROOT_USERNAME=admin \
     -e MONGO_INITDB_ROOT_PASSWORD=password123 \
     mongo:latest
```

3. **Verify container is running:**
```bash
   docker ps
   # Should show mongodb container running
```

4. **Your connection string will be:**
```
   MONGO_URI=mongodb://admin:password123@localhost:27017/ecommerce_crawler?authSource=admin
```

5. **To stop MongoDB later:**
```bash
   docker stop mongodb
```

6. **To start MongoDB again:**
```bash
   docker start mongodb
```

---

### Step 5: Configure Environment Variables

1. **Copy the example environment file:**
```bash
   cp .env.example .env
```

2. **Open `.env` file in your text editor and configure the following:**

#### MongoDB Configuration
```env
# Use the connection string from your chosen MongoDB setup (Step 4)
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=ecommerce_crawler
```

#### Email Configuration (for scheduler notifications)

You'll need a Gmail account and an **App Password** (not your regular Gmail password):

**Generate Gmail App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Under "Select app", choose "Mail"
4. Under "Select device", choose "Other" and enter "ECommerceCrawler"
5. Click "Generate"
6. Copy the 16-character password (spaces don't matter)

**Add to `.env`:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient-email@gmail.com
```



---

### Step 6: Generate API Keys

The API requires authentication via API keys. Generate them using the provided script:
```bash
python generate_api_keys.py
```

**Output example:**
```
Generated API Keys (copy these to your .env file):
key_EMGt8*****,key_EMGt9*****
```

**Add to `.env`:**
```env
# Comma-separated list of API keys
API_KEYS=key_EMGt8*****,key_EMGt9*****
```

**Important:** Keep these keys secret! Never commit them to Git.

---

### Step 7: Verify Setup

Your `.env` file should now look similar to this:
```env
# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=ecommerce_crawler

# Email (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com



# API Keys
API_KEYS=key_EMGt8*****,key_EMGt9*****
```

---

## 🧪 Running the Application

Now that setup is complete, you can run the different components:

### 1. Run the Web Crawler

Crawl all books from books.toscrape.com and store them in MongoDB:
```bash
python -m crawler.main
```

**Expected output:**
```
INFO - Starting async crawl...
INFO - Found 1000 books to crawl
INFO - Processing batch 1/20 (50 books)
...
INFO - ASYNC CRAWL COMPLETE
INFO - Total books processed: 1000
INFO - Duration: 215.43 seconds (3.59 minutes)
```

**What happens:**
- Discovers all 1000 books across 50 pages
- Crawls concurrently (10 books at a time)
- Stores data in MongoDB `books` collection
- Creates indexes for efficient querying

---

### 2. Run the Scheduler (Manual Test)

Before setting up the daily scheduler, test it manually:
```bash
python -m scheduler.runner
```

**Expected output:**
```
INFO - Starting scheduled crawl...
INFO - Detecting changes...
INFO - Found 0 new books, 0 updates
INFO - Generating reports...
INFO - Sending email notification...
INFO - Crawl complete!
```

**What happens:**
- Re-crawls the website
- Detects new books or changes
- Generates JSON and CSV reports in `reports/output/`
- Sends email with reports attached

**Tip:** To test change detection, first run the command below to simulate price changes:
```bash
python test_with_changes.py
```

This script creates fake price updates in MongoDB. Then run the scheduler again:
```bash
python -m scheduler.runner
```

You should now see changes detected and receive an email with the change report!

---

### 3. Run the FastAPI Server

Start the REST API server:
```bash
python -m api.main
```

**Expected output:**
```
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8000
```

**Access the API:**
- **Swagger UI (Interactive Docs):** http://localhost:8000/docs
- **ReDoc (Alternative Docs):** http://localhost:8000/redoc
- **OpenAPI JSON Schema:** http://localhost:8000/openapi.json

---

### 4. Test API Endpoints

#### Using Swagger UI (Recommended for beginners)

1. **Open browser:** http://localhost:8000/docs
2. **Authorize with API Key:**
   - Click the "Authorize" button (🔒 icon at top right)
   - Enter one of your API keys (from `.env`)
   - Click "Authorize"

3. **Try the endpoints:**
   - `GET /books` - List all books with filters
   - `GET /books/{book_id}` - Get specific book details
   - `GET /changes` - View changelog history

#### Using cURL (Command line)
```bash
# Get all books (first page)
curl -X GET "http://localhost:8000/books?page=1&page_size=10" \
  -H "X-API-Key: your-api-key-here"

# Filter books by category and price
curl -X GET "http://localhost:8000/books?category=Fiction&min_price=10&max_price=30" \
  -H "X-API-Key: your-api-key-here"

# Get specific book by ID
curl -X GET "http://localhost:8000/books/{book_id}" \
  -H "X-API-Key: your-api-key-here"

# Get recent changes
curl -X GET "http://localhost:8000/changes?page=1&page_size=20" \
  -H "X-API-Key: your-api-key-here"
```

---

## 🧪 Running Tests

Execute the test suite to verify everything works:
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api_endpoints.py

# Run with coverage report
pytest --cov=crawler --cov=scheduler --cov=api
```

---

## 📅 Setting Up Daily Scheduler (Production)

The scheduler is configured to run automatically at 2:00 AM daily. To enable continuous operation:

### Option 1: Keep Script Running
```bash
# Run in foreground
python -m scheduler.runner

# Or run in background (Linux/macOS)
nohup python -m scheduler.runner &
```

The script will keep running and execute the crawl at the scheduled time daily.

### Option 2: System Service (Linux)

Create a systemd service for automatic startup and better process management.

### Option 3: Docker Container

Run the scheduler as a long-lived Docker container for isolation and easy deployment.

---

## 🔍 Verification Checklist

Ensure everything is working:

- [ ] Virtual environment activated (`.venv`)
- [ ] All dependencies installed (`pip list` shows required packages)
- [ ] MongoDB running and accessible
- [ ] `.env` file configured with all required variables
- [ ] API keys generated and added to `.env`
- [ ] Gmail app password configured correctly
- [ ] Crawler completes successfully (1000 books in ~3-4 minutes)
- [ ] MongoDB contains `books` collection with data
- [ ] Scheduler runs without errors
- [ ] Email notification received (after scheduler run)
- [ ] FastAPI server starts successfully
- [ ] Swagger UI accessible at http://localhost:8000/docs
- [ ] API endpoints return data with valid API key

---

## 🚨 Common Issues & Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:** Ensure virtual environment is activated and dependencies installed:
```bash
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: "Failed to connect to MongoDB"
**Solution:** 
- Verify MongoDB is running: `mongosh` (should connect successfully)
- Check `MONGO_URI` in `.env` matches your MongoDB setup
- For Atlas: Ensure IP address is whitelisted in Network Access

### Issue: "Email not sending"
**Solution:**
- Verify you're using Gmail App Password, not regular password
- Check SMTP settings in `.env`
- Ensure "Less secure app access" is NOT enabled (use App Password instead)

### Issue: "API returns 401 Unauthorized"
**Solution:**
- Check API key is in `.env` under `API_KEYS`
- Ensure you're sending the key in header: `X-API-Key: your-key-here`
- Verify API server is reading `.env` correctly

### Issue: "Crawler is slow"
**Solution:**
- Check `max_concurrent_requests` in `config/crawler_config.py`
- Increase if your network can handle it (try 15-20)
- Verify network connection is stable



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
| **APScheduler** | Task scheduling | Pythonic cron-like scheduling, supports async jobs |
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
├── generate_api_keys.py         # Utility to generate API keys
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
│
├── scheduler/
│   ├── __init__.py
│   ├── runner.py                
│   ├── main.py                  
│   ├── change_detector.py       # Change detection logic
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
│   ├── test_api_endpoints.py    # Api endpoints unit tests
│
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

