from redis import Redis
from fastapi import Request


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis_client