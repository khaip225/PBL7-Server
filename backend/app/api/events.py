from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..database import get_db
from ..models.event_log import EventLog
from ..schemas.events import EventResponse, EventListResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    job_id: str | None = Query(None),
    event_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = select(EventLog)
    if job_id:
        q = q.where(EventLog.job_id == job_id)
    if event_type:
        q = q.where(EventLog.event_type == event_type)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(EventLog.created_at.desc()).offset(offset).limit(limit)
    events = list((await db.execute(q)).scalars().all())

    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in events],
        total=total, offset=offset, limit=limit
    )
