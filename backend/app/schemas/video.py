from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class VideoUploadRequest(BaseModel):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    description: Optional[str] = None

class VideoResponse(BaseModel):
    video_id: str
    url: str
    title: Optional[str]
    description: Optional[str]
    duration: Optional[float]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True
