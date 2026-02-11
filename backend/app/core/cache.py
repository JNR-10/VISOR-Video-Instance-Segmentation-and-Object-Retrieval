import redis.asyncio as redis
from app.core.config import settings
import json
from typing import Optional, Any

class CacheManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            await self.connect()
        value = await self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        if not self.redis_client:
            await self.connect()
        await self.redis_client.set(
            key,
            json.dumps(value),
            ex=expire
        )
    
    async def delete(self, key: str):
        if not self.redis_client:
            await self.connect()
        await self.redis_client.delete(key)
    
    async def exists(self, key: str) -> bool:
        if not self.redis_client:
            await self.connect()
        return await self.redis_client.exists(key) > 0

cache = CacheManager()
