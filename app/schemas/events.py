from pydantic import BaseModel, Field, field_validator, StringConstraints
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Annotated
from uuid import UUID


class EventIn(BaseModel):
    event_type: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1)]
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
    recieved_at: datetime