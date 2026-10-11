from pydantic import BaseModel, field_validator, model_validator, StringConstraints
from datetime import datetime, timezone, timedelta
from typing import Optional, Annotated


class GetAnalytics(BaseModel):
    from_:datetime
    to_: datetime
    event_type: Optional[Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1)]] = None


    @field_validator("from_")
    def analytics_range_min(cls, value: datetime):
        now = datetime.now(timezone.utc)
        allowed = now - timedelta(days=60)
        oldest_allowed = allowed.replace(hour=0, minute=0, second=0, microsecond=0)
        normalized_value = value.replace(minute=0, second=0, microsecond=0)

        if normalized_value.tzinfo is None:
            raise ValueError("from_ must be timezone-aware")
        
        if normalized_value < oldest_allowed:
            raise ValueError(f"Analytics are available for last 60 days only. Please enter a date&time from {oldest_allowed}")

        return normalized_value


    @field_validator("to_")
    def analytics_range_max(cls, value: datetime):
        now = datetime.now(timezone.utc)
        newest_allowed = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        normalized_value = value.replace(minute=0, second=0, microsecond=0)

        if normalized_value.tzinfo is None:
            raise ValueError("to_ must be timezone-aware")
        
        if normalized_value > newest_allowed:
            raise ValueError(f"Analytics are available only up to the latest completed hour. Please enter a date&time upto {newest_allowed}")

        return normalized_value + timedelta(hours=1)


    @model_validator(mode="after")
    def validate_time_range(self):
        if self.from_ > self.to_:
            raise ValueError("Invalid time range given")
        
        return self



class AnalyticsResponse(BaseModel):
    analytics_result : dict
    total_event_count:int