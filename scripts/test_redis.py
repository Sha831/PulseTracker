import redis

from app.core.config import REDIS_URL

"""
Disclamer : 
-Please dont refer these test scripts for general testing as these were made during specific cases/time during designing backend
"""

r = redis.from_url(REDIS_URL,decode_responses=True)

r.set("city","blore",ex=5)


print(r.get('city'))