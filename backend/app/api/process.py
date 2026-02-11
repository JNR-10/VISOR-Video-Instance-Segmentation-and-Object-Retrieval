"""API endpoints for video processing."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List
import os
import json

from app.core.config import settings
from app.services.video_processor import VideoProcessor

router = APIRouter()
video_processor = VideoProcessor()

# In-memory storage for processing status (use Redis in production)
processing_status = {}

class ProcessRequest(BaseModel):
    video_id: str

class ProcessStatusResponse(BaseModel):
    video_id: str
    status: str  # "processing", "completed", "failed"
    progress: float
    message: str
    logs: List[str] = []

@router.post("/process")
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start background video processing."""
    
    # Find video file with any extension
    videos_dir = os.path.join(settings.STORAGE_PATH, "videos")
    video_path = None
    for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']:
        potential_path = os.path.join(videos_dir, f"{request.video_id}{ext}")
        if os.path.exists(potential_path):
            video_path = potential_path
            break
    
    if not video_path:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if already processing
    if request.video_id in processing_status:
        status = processing_status[request.video_id]
        if status["status"] == "processing":
            return {"message": "Video is already being processed", "status": status}
    
    # Initialize status
    processing_status[request.video_id] = {
        "status": "processing",
        "progress": 0.0,
        "message": "Starting video processing...",
        "logs": []
    }
    
    # Start background task
    background_tasks.add_task(process_video_task, request.video_id, video_path)
    
    return {
        "message": "Video processing started",
        "video_id": request.video_id
    }

@router.get("/process/status/{video_id}", response_model=ProcessStatusResponse)
async def get_processing_status(video_id: str):
    """Get processing status for a video."""
    
    if video_id not in processing_status:
        # Check if tracking file exists (already processed)
        tracking_path = os.path.join(settings.STORAGE_PATH, 'tracking', f'{video_id}_tracking.json')
        if os.path.exists(tracking_path):
            return ProcessStatusResponse(
                video_id=video_id,
                status="completed",
                progress=100.0,
                message="Video processing completed"
            )
        else:
            raise HTTPException(status_code=404, detail="Video not found or not processed")
    
    status = processing_status[video_id]
    return ProcessStatusResponse(
        video_id=video_id,
        status=status["status"],
        progress=status["progress"],
        message=status["message"],
        logs=status.get("logs", [])
    )

@router.get("/tracking/{video_id}")
async def get_tracking_data(video_id: str):
    """Get tracking data for a processed video."""
    
    tracking_path = os.path.join(settings.STORAGE_PATH, 'tracking', f'{video_id}_tracking.json')
    
    if not os.path.exists(tracking_path):
        raise HTTPException(status_code=404, detail="Tracking data not found. Video may not be processed yet.")
    
    with open(tracking_path, 'r') as f:
        data = json.load(f)
    
    return data

async def process_video_task(video_id: str, video_path: str):
    """Background task to process video."""
    try:
        # Initialize logs storage
        if "logs" not in processing_status[video_id]:
            processing_status[video_id]["logs"] = []
        
        async def update_progress(progress: float, message: str = None):
            processing_status[video_id]["progress"] = progress
            if message:
                processing_status[video_id]["message"] = message
            else:
                processing_status[video_id]["message"] = f"Processing... {progress:.1f}%"
        
        async def log_message(message: str):
            if "logs" not in processing_status[video_id]:
                processing_status[video_id]["logs"] = []
            processing_status[video_id]["logs"].append(message)
            # Keep only last 50 logs to avoid memory issues
            if len(processing_status[video_id]["logs"]) > 50:
                processing_status[video_id]["logs"] = processing_status[video_id]["logs"][-50:]
        
        # Process video
        await video_processor.process_video(video_id, video_path, update_progress, log_message)
        
        # Update status
        processing_status[video_id]["status"] = "completed"
        processing_status[video_id]["progress"] = 100.0
        processing_status[video_id]["message"] = "Video processing completed successfully"
        
    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        processing_status[video_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": f"Processing failed: {str(e)}",
            "logs": processing_status[video_id].get("logs", [])
        }
