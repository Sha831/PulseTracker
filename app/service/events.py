from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, timezone
from psycopg2.extras import Json

"""
Event Ingestion Service

Responsibilities:
- Ingest validated events into the event log.
- Handle idempotent event creation when an Idempotency-Key is provided.
- Return the identifier of the ingested event.
"""

def create_event(
    session: Session,
    organization_id: UUID,
    event_type: str,
    occurred_at: datetime,
    user_id: str | None,
    idempotency_key: str | UUID | None,
    metadata: dict,
) -> tuple[UUID, datetime]:
    
    received_at = datetime.now(timezone.utc)

    if idempotency_key:
        lookup_sql = text("""
            SELECT event_id
            FROM idempotency_keys
            WHERE idempotency_key = :idempotency_key
        """)

        result = session.execute(
            lookup_sql,
            {"idempotency_key": idempotency_key}
        )

        row = result.fetchone()

        if row is not None:
            return row.event_id, row.received_at

    try:
        event_id = uuid4()

        insert_event_sql = text("""
            INSERT INTO raw_events (
                event_id,
                organization_id,
                event_type,
                occurred_at,
                user_id,
                metadata,
                received_at
            ) VALUES (
                :event_id,
                :organization_id,
                :event_type,
                :occurred_at,
                :user_id,
                :metadata,
                :received_at
            )
        """)

        session.execute(
            insert_event_sql,
            {
                "event_id": event_id,
                "organization_id": organization_id,
                "event_type": event_type,
                "occurred_at": occurred_at,
                "user_id": user_id,
                "metadata": Json(metadata),
                "received_at": received_at,
            }
        )

        if idempotency_key:
            insert_key_sql = text("""
                INSERT INTO idempotency_keys (
                    idempotency_key,
                    event_id,
                    received_at
                ) VALUES (
                    :idempotency_key,
                    :event_id,
                    :received_at
                )
            """)

            session.execute(
                insert_key_sql,
                {
                    "idempotency_key": idempotency_key,
                    "event_id": event_id,
                    "received_at": received_at,
                }
            )

        session.commit()
        return event_id , received_at

    except IntegrityError as e:
        session.rollback()

        # Another request already processed this idempotency key
        if getattr(e.orig, "pgcode", None) == "23505" and idempotency_key:
            result = session.execute(
                lookup_sql,
                {"idempotency_key": idempotency_key}
            )
            row = result.fetchone()
            if row:
                return row.event_id, row.received_at

        # handle other Unexpected database integrity error.
        raise

    except Exception:
        session.rollback()
        raise
