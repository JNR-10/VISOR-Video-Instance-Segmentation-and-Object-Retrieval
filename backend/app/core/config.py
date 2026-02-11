from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from typing import List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )
    
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = True
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/visor"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./data"
    
    MODEL_CACHE_DIR: str = "../data/models"
    DEVICE: str = "mps"
    SAM_MODEL: str = "mobile_sam"
    CLIP_MODEL: str = "openai/clip-vit-base-patch32"
    
    PRODUCT_SEARCH_PROVIDER: str = "internal"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://localhost:3001"
    
    ENABLE_ANALYTICS: bool = True
    
    DETECTION_FPS: int = 10
    TRACKING_MAX_AGE: int = 30
    MAX_OVERLAYS: int = 3
    
    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(',') if origin.strip()]

settings = Settings()
