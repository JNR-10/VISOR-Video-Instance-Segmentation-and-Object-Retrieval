from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api import videos, events, health, process

app = FastAPI(
    title="VISOR API",
    description="Video Instance Segmentation & Object Retrieval",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.STORAGE_PATH, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_PATH, "videos"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_PATH, "frames"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_PATH, "crops"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_PATH, "tracking"), exist_ok=True)

app.mount("/static", StaticFiles(directory=settings.STORAGE_PATH), name="static")

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(videos.router, prefix="/api", tags=["videos"])
app.include_router(events.router, prefix="/api", tags=["analytics"])
app.include_router(process.router, prefix="/api", tags=["processing"])

@app.on_event("startup")
async def startup_event():
    # Database disabled for demo - running in stateless mode
    # All data stored in files (videos, masks, tracking JSON)
    print("Running in stateless mode - no database required")
    # try:
    #     from app.core.database import init_db
    #     await init_db()
    #     print("Database initialized successfully")
    # except Exception as e:
    #     print(f"Warning: Database initialization failed: {e}")
    #     print("Running without database - using stateless mode")
    
@app.get("/")
async def root():
    return {
        "message": "VISOR API",
        "version": "1.0.0",
        "docs": "/docs"
    }
