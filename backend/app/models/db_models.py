from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Video(Base):
    __tablename__ = "videos"
    
    video_id = Column(String, primary_key=True, default=generate_uuid)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SegmentedObject(Base):
    __tablename__ = "segmented_objects"
    
    object_id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, nullable=False)
    timestamp_ms = Column(Integer, nullable=False)
    click_x = Column(Float, nullable=False)
    click_y = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)
    mask_url = Column(String, nullable=False)
    crop_url = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    embedding = Column(Vector(512), nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductMatch(Base):
    __tablename__ = "product_matches"
    
    match_id = Column(String, primary_key=True, default=generate_uuid)
    object_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    image_url = Column(String, nullable=False)
    buy_url = Column(String, nullable=False)
    category = Column(String, nullable=True)
    embedding = Column(Vector(512), nullable=True)
    product_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    event_id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String, nullable=False)
    video_id = Column(String, nullable=True)
    object_id = Column(String, nullable=True)
    product_id = Column(String, nullable=True)
    timestamp_ms = Column(Integer, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrackedObject(Base):
    __tablename__ = "tracked_objects"
    
    track_id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, nullable=False)
    object_class = Column(String, nullable=False)
    first_seen_ms = Column(Integer, nullable=False)
    last_seen_ms = Column(Integer, nullable=False)
    bbox_history = Column(JSON, nullable=False)
    mask_url = Column(String, nullable=True)
    crop_url = Column(String, nullable=True)
    embedding = Column(Vector(512), nullable=True)
    product_id = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
