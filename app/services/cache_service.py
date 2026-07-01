import redis
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

CACHE_EXPIRY = settings.CACHE_EXPIRY


def get_cached_url(short_code: str) -> str | None:
    """
    Get cached URL by short code.
    
    Args:
        short_code: Short code to look up
        
    Returns:
        Original URL if cached, None otherwise
    """
    try:
        result = redis_client.get(short_code)
        if result:
            logger.debug(f"Cache hit for {short_code}")
            return result
        logger.debug(f"Cache miss for {short_code}")
        return None
    except Exception as e:
        logger.error(f"Cache get error: {str(e)}")
        return None


def cache_url(short_code: str, original_url: str) -> bool:
    """
    Cache a URL mapping.
    
    Args:
        short_code: Short code
        original_url: Original URL to cache
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client.setex(short_code, CACHE_EXPIRY, original_url)
        logger.debug(f"Cached {short_code} for {CACHE_EXPIRY}s")
        return True
    except Exception as e:
        logger.error(f"Cache set error: {str(e)}")
        return False


def invalidate_cache(short_code: str) -> bool:
    """
    Remove a URL from cache.
    
    Args:
        short_code: Short code to invalidate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client.delete(short_code)
        logger.debug(f"Invalidated cache for {short_code}")
        return True
    except Exception as e:
        logger.error(f"Cache invalidation error: {str(e)}")
        return False