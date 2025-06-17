import time
from typing import Dict
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.utils.cache import get_redis

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc"] or request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Create rate limit key
        key = f"rate_limit:{client_ip}"
        
        # Check rate limit
        redis_client = await get_redis()
        if redis_client:
            current_requests = await redis_client.get(key)
            
            if current_requests is None:
                # First request from this IP in the window
                await redis_client.set(key, 1, ex=settings.RATE_LIMIT_WINDOW)
            else:
                current_requests = int(current_requests)
                if current_requests >= settings.RATE_LIMIT_REQUESTS:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                else:
                    await redis_client.incr(key)
        
        # Process request
        response = await call_next(request)
        return response