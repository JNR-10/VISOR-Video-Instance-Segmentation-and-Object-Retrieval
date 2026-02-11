from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class EventRequest(BaseModel):
    event_type: str
    video_id: Optional[str] = None
    object_id: Optional[str] = None
    product_id: Optional[str] = None
    timestamp_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class EventResponse(BaseModel):
    event_id: str
    created_at: datetime
