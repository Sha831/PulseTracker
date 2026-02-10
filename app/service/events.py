from sqlalchemy import text
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, timezone
from psycopg2.extras import Json


def create_event(
    session: Session,
    organization_id: str,
    event_type: str,
    occurred_at: datetime,
    user_id: str | None,
    idempotency_key: str | UUID | None,
    metadata: dict,
) -> UUID:
    #Creates a raw event and Returns the generated event_id on success.
    if idempotency_key:
        get_idempotency_key = text("""
            SELECT event_id
            FROM idempotency_keys
            WHERE idempotency_key = 'abc-123';
            """)
    try:
        event_id = uuid4()

        insert_sql = text("""
            INSERT INTO raw_events (
                event_id,
                organization_id,
                event_type,
                occurred_at,
                user_id,
                metadata
            ) VALUES (
                :event_id,
                :organization_id,
                :event_type,
                :occurred_at,
                :user_id,
                :metadata
            )
        """)

        session.execute(
            insert_sql,
            {
                "event_id": event_id,
                "organization_id": organization_id,
                "event_type": event_type,
                "occurred_at": occurred_at,
                "user_id": user_id,
                "metadata": Json(metadata),
            }
        )

        session.commit()
        return event_id

    except Exception:
        session.rollback()
        raise
