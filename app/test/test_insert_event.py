from sqlalchemy import text
from db.sessions import get_db_session
import uuid
from datetime import datetime, timezone
from psycopg2.extras import Json

def insert_event():
    gen = get_db_session()
    session = next(gen)

    try:
        event_id = uuid.uuid4()

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
                "organization_id": "org_1",
                "event_type": "user_login",
                "occurred_at": datetime.now(timezone.utc),
                "user_id": "user_456",
                "metadata": Json({"source": "api", "device": "mobile"})
            }
        )

        session.commit()
        print("Event inserted:", event_id)

    except Exception as e:
        session.rollback()
        raise

    finally:
        gen.close()

if __name__ == "__main__":
    insert_event()
