from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Annotated
from redis import Redis

from app.db.sessions_postgres import get_db_session
from app.auth.dependencies import get_token_payload 
from app.schemas.analytics import GetAnalytics,AnalyticsResponse
from app.schemas.auth import JWTPayload
from app.service.analytics import get_analytics_result
from app.db.session_redis import get_redis_client

"""
Analytics API Endpoints

Responsibilities:
- accept vaild/authenticated analytics request
- extract analytics query parameters from request
- return response for analytics query
"""

router = APIRouter()

@router.get("/analytics", status_code=status.HTTP_200_OK, response_model=AnalyticsResponse)
def get_analytics(
            req_analytics: Annotated[GetAnalytics, Query()],
            session: Session = Depends(get_db_session),
            redis_connection: Redis = Depends(get_redis_client),
            token_payload: JWTPayload = Depends(get_token_payload)
):

    
    analytics = get_analytics_result(session=session,
                                    redis_connection=redis_connection,
                                    from_=req_analytics.from_,
                                    to_=req_analytics.to_,
                                    event_type=req_analytics.event_type,
                                    org_id=token_payload.sub)


    return AnalyticsResponse(analytics_result=analytics)