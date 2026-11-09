from redis import Redis, exceptions
from datetime import datetime
from uuid import UUID
import json
import logging


logger = logging.getLogger(__name__)

def build_analytics_cache_key(from_:datetime, to_:datetime, event_type:str|None, org_id: UUID) -> str:

    event_type = event_type if event_type is not None else "all"
    cache_key = f'analytics:{org_id}:{event_type}:{from_}:{to_}'
    return cache_key


def cache_analytics(client:Redis,cache_key:str,cache_analytics:dict):

    try:
        client.set(cache_key,json.dumps(cache_analytics),ex=30)

    except TypeError:
        logger.exception("Failed to serialize analytics response")
        
    except exceptions.RedisError:
        logger.warning("Redis cache write failed", exc_info=True)


def get_cached_analytics(client:Redis,cache_key:str):

    try:
        cached_response = client.get(cache_key)
        if cached_response is None:
            return None  # Cache miss
        
        response = json.loads(cached_response)
        return response
    
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in analytics cache", exc_info=True)
        try:
            client.delete(cache_key)
        except exceptions.RedisError:
            logger.warning("Failed to delete corrupted cache entry", exc_info=True)
        return None

    except (exceptions.RedisError,):
        #logger to catch redis/json errors only
        logger.warning("Redis read failed; falling back to PostgreSQL", exc_info=True)
        return None
