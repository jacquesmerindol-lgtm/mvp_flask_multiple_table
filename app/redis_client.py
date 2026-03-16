# redis_client.py
from redis import Redis
from config import get_settings

settings = get_settings()

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True  # Retourne des str au lieu de bytes
)
