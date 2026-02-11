import subprocess
import os
from app.core.config import settings
from app.core.cache import cache

class FrameExtractor:
    def __init__(self):
        self.frames_dir = os.path.join(settings.STORAGE_PATH, "frames")
        os.makedirs(self.frames_dir, exist_ok=True)
    
    async def extract_frame(
        self,
        video_path: str,
        timestamp_ms: int,
        video_id: str
    ) -> str:
        timestamp_sec = timestamp_ms / 1000.0
        rounded_ts = int(timestamp_ms / 100) * 100
        
        frame_filename = f"{video_id}_{rounded_ts}.jpg"
        frame_path = os.path.join(self.frames_dir, frame_filename)
        
        cache_key = f"frame:{video_id}:{rounded_ts}"
        if await cache.exists(cache_key) and os.path.exists(frame_path):
            return frame_path
        
        if video_path.startswith('/static/'):
            video_path = os.path.join(settings.STORAGE_PATH, video_path.replace('/static/', ''))
        
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp_sec),
            '-i', video_path,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            frame_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        if os.path.exists(frame_path):
            await cache.set(cache_key, frame_path, expire=7200)
            return frame_path
        else:
            raise Exception(f"Failed to extract frame at {timestamp_ms}ms")
