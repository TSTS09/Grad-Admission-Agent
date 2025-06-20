"""
Security middleware and utilities for STEM Graduate Admissions Assistant
"""

import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from functools import wraps
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handler
security = HTTPBearer(auto_error=False)

class SecurityMiddleware:
    """Security middleware for rate limiting and request validation"""
    
    def __init__(self):
        self.rate_limits: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.api_keys: Dict[str, str] = {}
    
    async def __call__(self, request: Request, call_next):
        """Process request through security middleware"""
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP temporarily blocked due to excessive requests"
            )
        
        # Rate limiting
        if not self.check_rate_limit(client_ip, request.url.path):
            self.block_ip(client_ip, minutes=15)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Security headers
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add security headers
            response = self.add_security_headers(response)
            
            # Log request
            process_time = time.time() - start_time
            await self.log_request(request, response, process_time)
            
            return response
            
        except Exception as e:
            # Log security incidents
            await self.log_security_incident(request, str(e))
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, client_ip: str, path: str) -> bool:
        """Check if client is within rate limits"""
        if not settings.RATE_LIMIT_REQUESTS:
            return True
        
        current_time = time.time()
        window_start = current_time - settings.RATE_LIMIT_WINDOW
        
        # Initialize if first request
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
        
        # Remove old requests outside window
        self.rate_limits[client_ip] = [
            req_time for req_time in self.rate_limits[client_ip]
            if req_time > window_start
        ]
        
        # Check if within limit
        if len(self.rate_limits[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            return False
        
        # Add current request
        self.rate_limits[client_ip].append(current_time)
        return True
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked"""
        if client_ip not in self.blocked_ips:
            return False
        
        blocked_until = self.blocked_ips[client_ip]
        if datetime.utcnow() > blocked_until:
            del self.blocked_ips[client_ip]
            return False
        
        return True
    
    def block_ip(self, client_ip: str, minutes: int = 15):
        """Block IP for specified minutes"""
        self.blocked_ips[client_ip] = datetime.utcnow() + timedelta(minutes=minutes)
        logger.warning(f"Blocked IP {client_ip} for {minutes} minutes")
    
    def add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://apis.google.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;"
        
        return response
    
    async def log_request(self, request: Request, response: Response, process_time: float):
        """Log request for monitoring"""
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
            "client_ip": self.get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log slow requests
        if process_time > 5.0:
            logger.warning(f"Slow request: {log_data}")
        
        # Log errors
        if response.status_code >= 400:
            logger.warning(f"Error request: {log_data}")
    
    async def log_security_incident(self, request: Request, error: str):
        """Log security incidents"""
        incident_data = {
            "type": "security_incident",
            "method": request.method,
            "url": str(request.url),
            "client_ip": self.get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error(f"Security incident: {incident_data}")

class TokenManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode JWT token without verification (for debugging)"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError:
            return {}

class PasswordManager:
    """Password hashing and verification"""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """Generate secure random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

class APIKeyManager:
    """API key management for external integrations"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key

def require_auth(optional: bool = False):
    """Decorator to require authentication"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                if optional:
                    return await func(*args, **kwargs)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check for authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                if optional:
                    return await func(*args, **kwargs)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing"
                )
            
            # Verify token
            try:
                token = auth_header.split(" ")[1]  # Remove "Bearer "
                payload = TokenManager.verify_token(token)
                if not payload:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token"
                    )
                
                # Add user info to request
                request.state.user = payload
                
            except (IndexError, AttributeError):
                if optional:
                    return await func(*args, **kwargs)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_api_key(func):
    """Decorator to require API key"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from arguments
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        # Check for API key in headers or query params
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key missing"
            )
        
        # Verify API key (implement your logic here)
        if not verify_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return await func(*args, **kwargs)
    return wrapper

def verify_api_key(api_key: str) -> bool:
    """Verify API key (implement your logic)"""
    # For demo purposes, accept any key starting with "demo_"
    if settings.is_development:
        return api_key.startswith("demo_")
    
    # In production, implement proper API key verification
    # This would check against your database of valid API keys
    return False

class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not input_str:
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in input_str if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit length
        return sanitized[:max_length]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_research_area(area: str) -> bool:
        """Validate research area"""
        from app.core.config import Constants
        return area in Constants.RESEARCH_AREAS
    
    @staticmethod
    def validate_university_name(name: str) -> bool:
        """Validate university name"""
        if not name or len(name) < 2 or len(name) > 200:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        name_lower = name.lower()
        
        return not any(pattern in name_lower for pattern in suspicious_patterns)

# CSRF Protection
class CSRFProtection:
    """CSRF protection utilities"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, expected: str) -> bool:
        """Verify CSRF token"""
        return secrets.compare_digest(token, expected)

# Security utilities
def get_current_user_optional(credentials: HTTPAuthorizationCredentials = security):
    """Get current user (optional authentication)"""
    if not credentials:
        return None
    
    payload = TokenManager.verify_token(credentials.credentials)
    if not payload:
        return None
    
    return payload

def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    """Get current user (required authentication)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = TokenManager.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

# Initialize security middleware
security_middleware = SecurityMiddleware()

# Export commonly used items
__all__ = [
    "SecurityMiddleware",
    "TokenManager", 
    "PasswordManager",
    "APIKeyManager",
    "InputValidator",
    "CSRFProtection",
    "require_auth",
    "require_api_key",
    "get_current_user",
    "get_current_user_optional",
    "security_middleware"
]