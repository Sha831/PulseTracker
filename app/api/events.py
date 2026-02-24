from fastapi import APIRouter, Depends, status, Header
from pydantic import BaseModel, Field, constr, field_validator
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.sessions import get_db_session
from app.service.events import create_event

router = APIRouter()

class EventIn(BaseModel):
    organization_id: constr(strip_whitespace=True, min_length=1)
    event_type: constr(strip_whitespace=True, min_length=1)
    occurred_at: datetime
    user_id: Optional[str] = None
    metadata: Dict[str,Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    def occurred_at_cannot_be_future(cls, value: datetime):
        now = datetime.now(timezone.utc)

        if value.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")

        if value > now:
            raise ValueError("occurred_at cannot be in the future")
        
        if now - value>timedelta(days=5):
            raise ValueError("occurred_at shld be within the past 5 days from today")

        return value



class EventAccepted(BaseModel):
    event_id: UUID



@router.post("/events", status_code=status.HTTP_202_ACCEPTED,response_model=EventAccepted)
def post_event(
    event: EventIn,
    idempotency_key: Optional[constr(strip_whitespace=True, min_length=1)] = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
):
    event_id = create_event(
        session=session,
        organization_id=event.organization_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        user_id=event.user_id,
        idempotency_key=idempotency_key,
        metadata=event.metadata,
    )

    return EventAccepted(event_id=event_id)
