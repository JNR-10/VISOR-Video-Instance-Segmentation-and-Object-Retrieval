from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
import uuid
import aiofiles

from app.core.config import settings
from app.schemas.video import VideoUploadRequest, VideoResponse
from app.services.video_processor import VideoProcessor

router = APIRouter()
video_processor = VideoProcessor()

@router.post("/videos", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(None),
    url: str = None,
    title: str = None,
    description: str = None
):
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file or url must be provided")
    
    video_id = str(uuid.uuid4())
    
    if file:
        file_ext = os.path.splitext(file.filename)[1]
        file_path = os.path.join(settings.STORAGE_PATH, "videos", f"{video_id}{file_ext}")
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        video_url = f"/static/videos/{video_id}{file_ext}"
    else:
        file_path = None
        video_url = url
    
    metadata = await video_processor.extract_metadata(file_path if file_path else url)
    
    # Return video info without database (stateless mode)
    return VideoResponse(
        video_id=video_id,
        url=video_url,
        title=title or f"Video {video_id[:8]}",
        description=description,
        duration=metadata.get("duration"),
        width=metadata.get("width"),
        height=metadata.get("height"),
        fps=metadata.get("fps"),
        created_at=datetime.utcnow()
    )

# get_video endpoint removed - not needed in stateless mode
# Video info is stored in tracking JSON files
