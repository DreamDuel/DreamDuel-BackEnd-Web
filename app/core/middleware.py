"""Rate limiting middleware"""

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.infrastructure.cache.redis_client import redis_client
from app.core.config import settings
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Create rate limit key
        key = f"rate_limit:{client_ip}:{int(time.time() / self.window)}"
        
        try:
            # Increment request count
            current_requests = redis_client.get(key)
            
            if current_requests is None:
                redis_client.setex(key, self.window, 1)
            else:
                current_requests = int(current_requests)
                
                if current_requests >= self.requests_per_minute:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again later."
                    )
                
                redis_client.incr(key)
            
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                self.requests_per_minute - int(current_requests or 0)
            )
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time()) + self.window
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            # If Redis is down, allow the request through
            # but log the error
            print(f"Rate limiting error: {e}")
            return await call_next(request)
