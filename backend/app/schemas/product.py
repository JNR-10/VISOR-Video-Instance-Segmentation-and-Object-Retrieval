from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Product(BaseModel):
    product_id: str
    title: str
    brand: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    image_url: HttpUrl
    buy_url: HttpUrl
    category: Optional[str]
    confidence: float

class RetrieveRequest(BaseModel):
    object_id: str
    category: Optional[str] = "product"

class RetrieveResponse(BaseModel):
    object_id: str
    products: List[Product]
    processing_time_ms: float
