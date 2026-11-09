from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.auth.jwt_handler import create_token


def get_active_organizations(db_session, limit=2):
    result = db_session.execute(
        text("""
            SELECT organization_id
            FROM organizations
            WHERE is_active = TRUE
            LIMIT :limit
        """),
        {"limit": limit}
    )

    return result.scalars().all()


def get_test_bucket():
    # Two hours ago, rounded down to the hour.
    now = datetime.now(timezone.utc)
    return now.replace(
        minute=0,
        second=0,
        microsecond=0
    ) - timedelta(hours=2)


def insert_analytics_row(db_session, org_id, bucket, event_type, count):
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
                :event_count
            )
        """),
        {
            "org_id": org_id,
            "bucket": bucket,
            "event_type": event_type,
            "event_count": count
        }
    )

    db_session.commit()


def cleanup_analytics(db_session, org_id, event_types):
    db_session.execute(
        text("""
            DELETE FROM hourly_event_analytics
            WHERE organization_id = :org_id
            AND event_type IN :event_types
        """).bindparams(
            __import__("sqlalchemy").bindparam(
                "event_types",
                expanding=True
            )
        ),
        {
            "org_id": org_id,
            "event_types": event_types
        }
    )

    db_session.commit()


def make_analytics_request(client, org_id, bucket, event_type=None):
    token = create_token(org_id)

    params = {
        "from_": bucket.isoformat(),
        "to_": bucket.isoformat()
    }

    if event_type is not None:
        params["event_type"] = event_type

    return client.get(
        "/analytics",
        params=params,
        headers={
            "Authorization": f"Bearer {token}"
        }
    )


def test_analytics_returns_correct_event_count(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]

    bucket = get_test_bucket()
    event_type = f"pytest_{uuid4().hex}"

    try:
        insert_analytics_row(
            db_session, org_id, bucket, event_type, 25
        )

        response = make_analytics_request(
            client, org_id, bucket, event_type
        )

        assert response.status_code == 200

        data = response.json()["analytics_result"]

        assert data["event_count"] == 25

    finally:
        cleanup_analytics(db_session, org_id, [event_type])


def test_analytics_event_type_filter(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]

    bucket = get_test_bucket()

    event_type_1 = f"pytest_view_{uuid4().hex}"
    event_type_2 = f"pytest_buy_{uuid4().hex}"

    try:
        insert_analytics_row(
            db_session, org_id, bucket, event_type_1, 10
        )

        insert_analytics_row(
            db_session, org_id, bucket, event_type_2, 20
        )

        response = make_analytics_request(
            client, org_id, bucket, event_type_1
        )

        assert response.status_code == 200

        data = response.json()["analytics_result"]

        assert data["event_count"] == 10

    finally:
        cleanup_analytics(
            db_session, org_id, [event_type_1, event_type_2]
        )


def test_analytics_time_range_filter(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]

    bucket = get_test_bucket()
    next_bucket = bucket + timedelta(hours=1)

    event_type = f"pytest_range_{uuid4().hex}"

    try:
        insert_analytics_row(
            db_session, org_id, bucket, event_type, 15
        )

        insert_analytics_row(
            db_session, org_id, next_bucket, event_type, 30
        )

        response = make_analytics_request(
            client, org_id, bucket, event_type
        )

        assert response.status_code == 200

        data = response.json()["analytics_result"]

        # Only the first hourly bucket should be included.
        assert data["event_count"] == 15

    finally:
        cleanup_analytics(db_session, org_id, [event_type])


def test_analytics_organization_isolation(client, db_session):

    organizations = get_active_organizations(
        db_session, limit=2
    )

    if len(organizations) < 2:
        pytest.skip("Requires two active organizations")

    org1, org2 = organizations

    bucket = get_test_bucket()
    event_type = f"pytest_isolation_{uuid4().hex}"

    try:
        insert_analytics_row(
            db_session, org1, bucket, event_type, 10
        )

        insert_analytics_row(
            db_session, org2, bucket, event_type, 50
        )

        response = make_analytics_request(
            client, org1, bucket, event_type
        )

        assert response.status_code == 200

        data = response.json()["analytics_result"]

        # Organization 1 must not see organization 2's count.
        assert data["event_count"] == 10

    finally:
        cleanup_analytics(db_session, org1, [event_type])
        cleanup_analytics(db_session, org2, [event_type])


def test_analytics_empty_result(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]

    bucket = get_test_bucket()
    event_type = f"pytest_empty_{uuid4().hex}"

    response = make_analytics_request(
        client, org_id, bucket, event_type
    )

    assert response.status_code == 200

    data = response.json()["analytics_result"]

    assert data["event_count"] == 0
    assert data["analytics"] == {}
