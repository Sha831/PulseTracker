import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import text

from app.auth.jwt_handler import create_token
from app.main import app
from app.db.session_redis import get_redis_client
from app.service.cache import build_analytics_cache_key


def get_active_org(db_session):
    return db_session.execute(
        text("""
            SELECT organization_id
            FROM organizations
            WHERE is_active = TRUE
            LIMIT 1
        """)
    ).scalar_one()


def get_test_bucket():
    now = datetime.now(timezone.utc)

    return now.replace(
        minute=0,
        second=0,
        microsecond=0
    ) - timedelta(hours=2)


def make_cache_key(org_id, bucket, event_type):
    return build_analytics_cache_key(
        from_=bucket,
        to_=bucket + timedelta(hours=1),
        event_type=event_type,
        org_id=org_id
    )


def make_request(client, org_id, bucket, event_type):
    token = create_token(org_id)

    return client.get(
        "/analytics",
        params={
            "from_": bucket.isoformat(),
            "to_": bucket.isoformat(),
            "event_type": event_type
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )


def insert_analytics(db_session, org_id, bucket, event_type, count):
    db_session.execute(
        text("""
            INSERT INTO hourly_event_analytics (
                organization_id,
                bucket_start,
                event_type,
                event_count
            )
            VALUES (
                :org_id,
                :bucket,
                :event_type,
                :count
            )
        """),
        {
            "org_id": org_id,
            "bucket": bucket,
            "event_type": event_type,
            "count": count
        }
    )

    db_session.commit()


def cleanup(db_session, org_id, event_type):
    db_session.execute(
        text("""
            DELETE FROM hourly_event_analytics
            WHERE organization_id = :org_id
            AND event_type = :event_type
        """),
        {
            "org_id": org_id,
            "event_type": event_type
        }
    )

    db_session.commit()


def test_cache_miss_queries_database_and_populates_cache(
    client, db_session
):
    org_id = get_active_org(db_session)
    bucket = get_test_bucket()
    event_type = f"pytest_miss_{uuid4().hex}"

    redis_client = client.app.state.redis_client
    cache_key = make_cache_key(org_id, bucket, event_type)

    try:
        insert_analytics(
            db_session, org_id, bucket, event_type, 25
        )

        redis_client.delete(cache_key)

        response = make_request(
            client, org_id, bucket, event_type
        )

        assert response.status_code == 200
        assert response.json()["analytics_result"]["event_count"] == 25

        # Verify PostgreSQL result was cached in Redis.
        cached_value = redis_client.get(cache_key)

        assert cached_value is not None
        assert json.loads(cached_value)["event_count"] == 25

    finally:
        redis_client.delete(cache_key)
        cleanup(db_session, org_id, event_type)


def test_cache_hit_returns_cached_response(client, db_session):

    org_id = get_active_org(db_session)
    bucket = get_test_bucket()
    event_type = f"pytest_hit_{uuid4().hex}"

    redis_client = client.app.state.redis_client
    cache_key = make_cache_key(org_id, bucket, event_type)

    cached_response = {
        "analytics": {"cached_test": {"00:00:00": {event_type: 99}}},
        "event_count": 99
    }

    try:
        # Intentionally cache a value different from PostgreSQL.
        redis_client.set(
            cache_key,
            json.dumps(cached_response),
            ex=30
        )

        response = make_request(
            client, org_id, bucket, event_type
        )

        assert response.status_code == 200

        data = response.json()["analytics_result"]

        # 99 proves the cached value was returned.
        assert data["event_count"] == 99

    finally:
        redis_client.delete(cache_key)


def test_redis_unavailable_falls_back_to_database(
    client, db_session
):
    org_id = get_active_org(db_session)
    bucket = get_test_bucket()
    event_type = f"pytest_fallback_{uuid4().hex}"

    class UnavailableRedis:
        def get(self, key):
            raise RedisConnectionError("Redis unavailable")

        def set(self, *args, **kwargs):
            raise RedisConnectionError("Redis unavailable")

    try:
        insert_analytics(
            db_session, org_id, bucket, event_type, 42
        )

        # Replace only the Redis dependency for this request.
        app.dependency_overrides[get_redis_client] = (
            lambda: UnavailableRedis()
        )

        response = make_request(
            client, org_id, bucket, event_type
        )

        assert response.status_code == 200
        assert response.json()["analytics_result"]["event_count"] == 42

    finally:
        app.dependency_overrides.pop(get_redis_client, None)
        cleanup(db_session, org_id, event_type)


def test_corrupted_cache_falls_back_to_database(
    client, db_session
):
    org_id = get_active_org(db_session)
    bucket = get_test_bucket()
    event_type = f"pytest_corrupt_{uuid4().hex}"

    redis_client = client.app.state.redis_client
    cache_key = make_cache_key(org_id, bucket, event_type)

    try:
        insert_analytics(
            db_session, org_id, bucket, event_type, 35
        )

        # Deliberately insert invalid JSON.
        redis_client.set(cache_key, "{invalid json", ex=30)

        response = make_request(
            client, org_id, bucket, event_type
        )

        assert response.status_code == 200
        assert response.json()["analytics_result"]["event_count"] == 35

        # The corrupted value should have been replaced.
        cached_value = redis_client.get(cache_key)

        assert cached_value is not None
        assert json.loads(cached_value)["event_count"] == 35

    finally:
        redis_client.delete(cache_key)
        cleanup(db_session, org_id, event_type)
