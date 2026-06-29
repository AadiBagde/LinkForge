import redis
from fastapi import HTTPException
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    decode_responses=True
)

MAX_REQUESTS = settings.MAX_REQUESTS_PER_MINUTE
WINDOW = settings.RATE_LIMIT_WINDOW


def check_rate_limit(ip: str):
    key = f"rate_limit:{ip}"

    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key, WINDOW)

    if count > MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again later."
        )