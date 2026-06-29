import redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

CACHE_EXPIRY = settings.CACHE_EXPIRY


def get_cached_url(short_code: str):
    return redis_client.get(short_code)


def cache_url(short_code: str, original_url: str):
    redis_client.setex(short_code, CACHE_EXPIRY, original_url)