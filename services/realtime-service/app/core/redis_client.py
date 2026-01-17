import redis
from app.core.config import settings

# Redis connection
redis_conn = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=False  # Keep bytes for compatibility
)


def decode_val(v):
    """Decode Redis bytes to string."""
    return v.decode() if isinstance(v, bytes) else v


def decode_dict(d):
    """Decode all values in a Redis hash dict."""
    return {decode_val(k): decode_val(v) for k, v in d.items()}
