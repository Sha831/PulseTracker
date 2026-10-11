from fastapi import APIRouter, Depends, status, Header
from pydantic import StringConstraints
from typing import Annotated, Optional
from sqlalchemy.orm import Session

from app.db.sessions import get_db_session
from app.auth.dependencies import get_token_payload
from app.service.events import create_event 
from app.schemas.events import EventAccepted, EventIn
from app.schemas.auth import JWTPayload
"""
Event Ingestion API Endpoints

Responsibilities:
- accept vaild/authenticated event request
- store event in db log (event log is append only)
- return event_id for ingested events or
"""

router = APIRouter()

# protected endpoint , requires a valid JWT
@router.post("/events", status_code=status.HTTP_201_CREATED,response_model=EventAccepted)
def post_event(
    event: EventIn,
    # client shld provide idempotency key for safe retry / avoid duplicate events
    idempotency_key: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]] = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
    token_payload: JWTPayload = Depends(get_token_payload)
):
    event_id, recieved_at = create_event(
        session=session,
        organization_id=token_payload.sub,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        user_id=event.user_id,
        idempotency_key=idempotency_key,
        metadata=event.metadata,
    )

    return EventAccepted(event_id=event_id, recieved_at=recieved_at)
