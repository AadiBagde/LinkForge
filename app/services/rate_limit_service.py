import redis
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    decode_responses=True
)

MAX_REQUESTS = settings.MAX_REQUESTS_PER_MINUTE
WINDOW = settings.RATE_LIMIT_WINDOW


def check_rate_limit(ip: str) -> bool:
    """
    Check if IP has exceeded rate limit.
    
    Args:
        ip: Client IP address
        
    Returns:
        True if within limit, False otherwise
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    key = f"rate_limit:{ip}"

    try:
        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, WINDOW)

        if count > MAX_REQUESTS:
            logger.warning(
                f"Rate limit exceeded for IP {ip}: {count}/{MAX_REQUESTS}",
                extra={"ip": ip, "count": count, "limit": MAX_REQUESTS}
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {MAX_REQUESTS} requests per {WINDOW} seconds.",
                headers={"Retry-After": str(WINDOW)},
            )
        
        logger.debug(f"Rate limit check for {ip}: {count}/{MAX_REQUESTS}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit check error for {ip}: {str(e)}")
        # Fail open - allow request if Redis is down
        return True