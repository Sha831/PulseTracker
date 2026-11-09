from datetime import datetime, timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

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


def make_event_payload(user_id):
    return {
        "event_type": "product_viewed",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "metadata": {
            "source": "pytest"
        }
    }


def cleanup_event(db_session, org_id, idempotency_key, user_id):
    # Delete idempotency record first in case it references raw_events
    db_session.execute(
        text("""
            DELETE FROM idempotency_keys
            WHERE organization_id = :org_id
            AND idempotency_key = :idempotency_key
        """),
        {
            "org_id": org_id,
            "idempotency_key": idempotency_key
        }
    )

    db_session.execute(
        text("""
            DELETE FROM raw_events
            WHERE organization_id = :org_id
            AND user_id = :user_id
        """),
        {
            "org_id": org_id,
            "user_id": user_id
        }
    )

    db_session.commit()


def test_same_org_same_key_returns_original_event(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]
    token = create_token(org_id)

    key = str(uuid4())
    user_id = f"pytest-{key}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key
    }

    payload = make_event_payload(user_id)

    try:
        # First request
        response1 = client.post(
            "/events",
            json=payload,
            headers=headers
        )

        # Retry with the same key
        response2 = client.post(
            "/events",
            json=payload,
            headers=headers
        )

        assert response1.status_code == 201
        assert response2.status_code == 201

        event_id1 = response1.json()["event_id"]
        event_id2 = response2.json()["event_id"]

        assert event_id1 == event_id2

        count = db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM raw_events
                WHERE organization_id = :org_id
                AND user_id = :user_id
            """),
            {"org_id": org_id, "user_id": user_id}
        ).scalar_one()

        assert count == 1

    finally:
        cleanup_event(db_session, org_id, key, user_id)


def test_same_org_different_keys_create_new_events(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]
    token = create_token(org_id)

    key1 = str(uuid4())
    key2 = str(uuid4())
    user_id = f"pytest-{uuid4()}"

    payload = make_event_payload(user_id)

    headers1 = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key1
    }

    headers2 = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key2
    }

    try:
        response1 = client.post("/events", json=payload, headers=headers1)
        response2 = client.post("/events", json=payload, headers=headers2)

        assert response1.status_code == 201
        assert response2.status_code == 201

        assert response1.json()["event_id"] != response2.json()["event_id"]

    finally:
        cleanup_event(db_session, org_id, key1, user_id)
        cleanup_event(db_session, org_id, key2, user_id)


def test_different_orgs_same_key_create_separate_events(client, db_session):

    organizations = get_active_organizations(db_session, limit=2)

    if len(organizations) < 2:
        pytest.skip("This test requires two active organizations")

    org1, org2 = organizations

    token1 = create_token(org1)
    token2 = create_token(org2)

    key = str(uuid4())
    user_id = f"pytest-{uuid4()}"

    payload = make_event_payload(user_id)

    headers1 = {
        "Authorization": f"Bearer {token1}",
        "Idempotency-Key": key
    }

    headers2 = {
        "Authorization": f"Bearer {token2}",
        "Idempotency-Key": key
    }

    try:
        response1 = client.post("/events", json=payload, headers=headers1)
        response2 = client.post("/events", json=payload, headers=headers2)

        assert response1.status_code == 201
        assert response2.status_code == 201

        assert response1.json()["event_id"] != response2.json()["event_id"]

    finally:
        cleanup_event(db_session, org1, key, user_id)
        cleanup_event(db_session, org2, key, user_id)


def test_concurrent_duplicate_requests_create_one_event(client, db_session):

    org_id = get_active_organizations(db_session, limit=1)[0]
    token = create_token(org_id)

    key = str(uuid4())
    user_id = f"pytest-{key}"

    payload = make_event_payload(user_id)

    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key
    }

    def send_request():
        return client.post(
            "/events",
            json=payload,
            headers=headers
        )

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(
                executor.map(lambda _: send_request(), range(5))
            )

        for response in responses:
            assert response.status_code == 201

        event_ids = {
            response.json()["event_id"]
            for response in responses
        }

        assert len(event_ids) == 1

        count = db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM raw_events
                WHERE organization_id = :org_id
                AND user_id = :user_id
            """),
            {"org_id": org_id, "user_id": user_id}
        ).scalar_one()

        assert count == 1

    finally:
        cleanup_event(db_session, org_id, key, user_id)
