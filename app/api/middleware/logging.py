import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host,
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            logger.error(
                "Request failed",
                request_id=request_id,
                error=str(e),
                processing_time=time.time() - start_time,
            )
            raise
        
        # Log response
        processing_time = time.time() - start_time
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            processing_time=processing_time,
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response