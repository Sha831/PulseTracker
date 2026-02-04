from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, constr
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.sessions import get_db_session
from app.service.events import create_event

router = APIRouter()

class EventIn(BaseModel):
    organization_id: constr(strip_whitespace=True, min_length=1)
    event_type: constr(strip_whitespace=True, min_length=1)
    occurred_at: datetime
    user_id: Optional[str] = None
    metadata: Dict[str,Any] = Field(default_factory=dict)



@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
def post_event(
    event: EventIn,
    session: Session = Depends(get_db_session),
):
    event_id = create_event(
        session=session,
        organization_id=event.organization_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        user_id=event.user_id,
        metadata=event.metadata,
    )

    return {"event_id": event_id}
