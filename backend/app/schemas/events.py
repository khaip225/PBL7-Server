from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from shared.types import EventSeverity


class EventResponse(BaseModel):
    id: UUID
    job_id: UUID | None = None
    event_type: str
    severity: EventSeverity
    payload: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    offset: int
    limit: int
