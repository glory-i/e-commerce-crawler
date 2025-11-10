"""
FastAPI application setup
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging

from api.routes import books_router, changes_router, health_router
from api.dependencies import limiter
from config.api_config import default_api_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("="*60)
    logger.info(f"Starting {default_api_config.title}")
    logger.info(f"Version: {default_api_config.version}")
    logger.info(f"Documentation: http://{default_api_config.host}:{default_api_config.port}/docs")
    logger.info("="*60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app with lifespan
app = FastAPI(
    title=default_api_config.title,
    description=default_api_config.description,
    version=default_api_config.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=default_api_config.allow_origins,
    allow_credentials=default_api_config.allow_credentials,
    allow_methods=default_api_config.allow_methods,
    allow_headers=default_api_config.allow_headers,
)

# Include routers
app.include_router(health_router)
app.include_router(books_router)
app.include_router(changes_router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "ECommerce Crawler API",
        "version": default_api_config.version,
        "documentation": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=default_api_config.host,
        port=default_api_config.port,
        reload=True
    )