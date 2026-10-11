from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from uuid import UUID
from collections import defaultdict

"""
Analytics Services

Responsibilities:
-Event aggregation: Provides and executes the SQL query used to aggregate raw events into hourly analytics. This operation is triggered by the background aggregation scheduler.
-Analytics retrieval: Queries the pre-aggregated analytics data in PostgreSQL based on the requested time range, optional event-type filter, and authenticated organization ID.
-Response preparation: Structures the query results into the required API response format and calculates the total event count.
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


def get_analytics_result(session:Session, from_:datetime, to_:datetime, event_type:str|None, org_id: UUID) -> tuple[dict,int]:

    get_analytics_data = text("""
                                SELECT
                                    bucket_start,
                                    event_type,
                                    event_count
                                FROM hourly_event_analytics
                                WHERE organization_id = :organization_id
                                AND bucket_start >= :from_
                                AND bucket_start < :to_
                                AND (:event_type IS NULL OR event_type = :event_type)
                                ORDER BY bucket_start, event_type
                            """)

    result = session.execute(
            get_analytics_data,
            {
                "organization_id": org_id,
                "from_": from_,
                "to_": to_,
                "event_type": event_type,
            }
                            )


    rows = result.fetchall()

    response_result = defaultdict(
        lambda: defaultdict(dict)
    )
    total_event_count = 0

    for date, event_type, event_count in rows:
        day = date.date()
        time = date.time()

        response_result[day][time][event_type] = event_count

        total_event_count+=event_count

    return response_result, total_event_count



