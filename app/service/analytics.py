from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from uuid import UUID
from collections import defaultdict
from redis import Redis
from typing import Any

from app.service.cache import cache_analytics, get_cached_analytics, build_analytics_cache_key

"""
Analytics Services

Responsibilities:
-Event aggregation: Provides and executes the SQL query used to aggregate raw events into hourly analytics. This operation is triggered by the background aggregation scheduler.
-Analytics retrieval: Queries the pre-aggregated analytics data in PostgreSQL based on the requested time range, optional event-type filter, and authenticated organization ID.
-Response preparation: Structures the query results into the required API response format and calculates the total event count.
"""


def aggregate_previous_hr(session: Session):

    aggregate_event_sql = text("""
        WITH affected_buckets AS (
            SELECT DISTINCT
                organization_id,
                DATE_TRUNC('hour', occurred_at) AS bucket_start,
                event_type
            FROM raw_events
            WHERE received_at >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
              AND received_at < DATE_TRUNC('hour', NOW())
        ),

        recalculated_counts AS (
            SELECT
                ab.organization_id,
                ab.bucket_start,
                ab.event_type,
                COUNT(re.event_id) AS event_count
            FROM affected_buckets AS ab
            JOIN raw_events AS re
                ON re.organization_id = ab.organization_id
                AND re.event_type = ab.event_type
                AND re.occurred_at >= ab.bucket_start
                AND re.occurred_at < ab.bucket_start + INTERVAL '1 hour'
            GROUP BY
                ab.organization_id,
                ab.bucket_start,
                ab.event_type
        )

        INSERT INTO hourly_event_analytics (
            organization_id,
            bucket_start,
            event_type,
            event_count
        )
        SELECT
            organization_id,
            bucket_start,
            event_type,
            event_count
        FROM recalculated_counts

        ON CONFLICT (organization_id, bucket_start, event_type)
        DO UPDATE
        SET event_count = EXCLUDED.event_count;
    """)

    try:
        session.execute(aggregate_event_sql)
        session.commit()

    except Exception:
        session.rollback()
        raise


def get_analytics_result(session:Session, redis_connection:Redis, from_:datetime, to_:datetime, event_type:str|None, org_id: UUID) -> dict[str,Any]:

    cache_key = build_analytics_cache_key(from_=from_, to_=to_, event_type=event_type, org_id=org_id)
    cached_result = get_cached_analytics(client=redis_connection,cache_key=cache_key)
    if cached_result is not None:
        return cached_result

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
        day = date.date().isoformat()
        time = date.time().isoformat()

        response_result[day][time][event_type] = event_count
        total_event_count+=event_count

    response = {'analytics':response_result, 'event_count':total_event_count}
    
    cache_analytics(redis_connection,cache_key=cache_key,cache_analytics=response)
    
    return response



