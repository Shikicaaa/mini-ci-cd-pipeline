import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_host = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')


def get_redis_connection():
    try:
        redis_client = redis.from_url(redis_host, decode_responses=True)
        redis_client.ping()
        print("Super")
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}")
        redis_client = None


if __name__ == "__main__":
    get_redis_connection()
