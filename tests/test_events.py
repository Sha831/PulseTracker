from datetime import datetime, timezone
from sqlalchemy import text

from app.auth.jwt_handler import create_token


def test_create_event_success(client, db_session):

    # ARRANGE: Get an existing active organization
    result = db_session.execute(
        text("""
            SELECT organization_id
            FROM organizations
            WHERE is_active = TRUE
            LIMIT 1
        """)
    )

    org_id = result.scalar_one_or_none()

    assert org_id is not None, "Test database needs an active organization"

    # Generate a real JWT
    token = create_token(org_id)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    event_payload = {
        "event_type": "product_viewed",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "user_id": "test_user_001",
        "metadata": {
            "product_id": "product_123",
            "source": "pytest"
        }
    }

    # ACT: Call the actual endpoint
    response = client.post(
        "/events",
        json=event_payload,
        headers=headers
    )

    # ASSERT: Verify API response
    assert response.status_code == 201

    response_data = response.json()

    assert "event_id" in response_data
    assert "recieved_at" in response_data

    # ASSERT: Verify database persistence
    event_id = response_data["event_id"]

    stored_event = db_session.execute(
        text("""
            SELECT event_id, organization_id, event_type, user_id
            FROM raw_events
            WHERE event_id = :event_id
        """),
        {"event_id": event_id}
    ).mappings().one_or_none()

    assert stored_event is not None
    assert str(stored_event["organization_id"]) == str(org_id)
    assert stored_event["event_type"] == "product_viewed"
    assert stored_event["user_id"] == "test_user_001"

    # CLEANUP
    db_session.execute(
        text("DELETE FROM raw_events WHERE event_id = :event_id"),
        {"event_id": event_id}
    )
    db_session.commit()


def test_event_rejects_invalid_jwt(client):

    response = client.post(
        "/events",
        json={
            "event_type": "product_viewed",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "user_id": "test_user"
        },
        headers={
            "Authorization": "Bearer invalid_token"
        }
    )

    assert response.status_code == 401


def test_event_rejects_invalid_payload(client, db_session):

    org_id = db_session.execute(
        text("""
            SELECT organization_id
            FROM organizations
            WHERE is_active = TRUE
            LIMIT 1
        """)
    ).scalar_one()

    token = create_token(org_id)

    response = client.post(
        "/events",
        json={
            "event_type": "product_viewed",
            "occurred_at": "invalid_timestamp",
            "user_id": "test_user"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 422


