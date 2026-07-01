from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.db import models
from app.api import urls, auth, advanced_analytics, url_management
from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import setup_error_handlers


# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Link Management & Analytics Platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
)

# Setup error handling and logging middleware
setup_error_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(urls.router)
app.include_router(auth.router)
app.include_router(advanced_analytics.router)
app.include_router(url_management.router)

logger.info(f"{settings.APP_NAME} API started - v{settings.APP_VERSION}")


@app.get("/", tags=["Health"])
def root():
    """Root endpoint - API is running"""
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Favicon endpoint"""
    return Response(status_code=204)