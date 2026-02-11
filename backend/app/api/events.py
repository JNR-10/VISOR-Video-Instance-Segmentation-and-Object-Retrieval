from fastapi import APIRouter
from datetime import datetime
import uuid

from app.core.config import settings
from app.schemas.event import EventRequest, EventResponse

router = APIRouter()

@router.post("/events", response_model=EventResponse)
async def log_event(request: EventRequest):
    # Analytics disabled in stateless mode - just return success
    # In production, send to analytics service (e.g., Google Analytics, Mixpanel)
    return EventResponse(
        event_id=str(uuid.uuid4()),
        created_at=datetime.utcnow()
    )
