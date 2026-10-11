from app.db.sessions import SessionLocal
from app.service.analytics import aggregate_previous_hr

"""
Background Aggregation Scheduler

Responsibilities:
- Schedule hourly aggregation of raw events.
- Trigger the analytics service to update pre-aggregated data in PostgreSQL.
- Keep analytics data ready for faster API responses.
"""

def aggregate_job():
    session = SessionLocal()

    try:
        aggregate_previous_hr(session=session)
    finally:
        session.close()

