from pydantic import BaseModel
from typing import List, Optional, Tuple

class SegmentRequest(BaseModel):
    video_id: str
    timestamp_ms: int
    x: float
    y: float
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class SegmentResponse(BaseModel):
    object_id: str
    mask_url: str
    crop_url: str
    bbox: BoundingBox
    confidence: float
    timestamp_ms: int
    category: Optional[str] = None
