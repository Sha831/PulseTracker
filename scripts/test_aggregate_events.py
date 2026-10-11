from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.sessions import SessionLocal

"""
Disclamer : 
-Please dont refer these test scripts for general testing as these were made during specific cases/time during designing backend
"""

def aggregate_previous_hr(session:Session):

    aggregate_event_sql = text("""
                INSERT INTO hourly_event_analytics
                    (organization_id, bucket_start, event_type, event_count)
                SELECT
                    re.organization_id,
                    DATE_TRUNC('hour', re.occurred_at),
                    re.event_type,
                    COUNT(*)
                FROM raw_events AS re
                WHERE re.received_at >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
                AND re.received_at < DATE_TRUNC('hour', NOW())
                GROUP BY
                    re.organization_id,
                    re.event_type,
                    DATE_TRUNC('hour', re.occurred_at)
                ON CONFLICT (organization_id, bucket_start, event_type)
                DO UPDATE
                SET event_count = EXCLUDED.event_count;
            """)

    try :

        session.execute(aggregate_event_sql)
        session.commit()

    except Exception as e:
        session.rollback()
        raise


if __name__ == "__main__":

    session = SessionLocal()

    aggregate_previous_hr(session=session)