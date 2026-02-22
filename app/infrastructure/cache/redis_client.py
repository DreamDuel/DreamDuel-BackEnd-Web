"""Redis client for caching and session management"""

from typing import Optional, Any
import json
import redis
from redis import Redis

from app.core.config import settings


class RedisClient:
    """Redis client wrapper"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
    
    def connect(self):
        """Connect to Redis"""
        self.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            self.client.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.client:
            return None
        
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in Redis with expiration (in seconds)"""
        if not self.client:
            return False
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return self.client.setex(key, expire, value)
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.client:
            return False
        
        return bool(self.client.delete(key))
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.client:
            return False
        
        return bool(self.client.exists(key))
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        if not self.client:
            return 0
        
        return self.client.incrby(key, amount)
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key"""
        if not self.client:
            return False
        
        return bool(self.client.expire(key, seconds))
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self.client:
            return -1
        
        return self.client.ttl(key)


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Get Redis client instance"""
    return redis_client
