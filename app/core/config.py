import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, validator
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Firebase
    FIREBASE_PROJECT_ID: str = "stem-grad-assistant"
    FIREBASE_STORAGE_BUCKET: str = "stem-grad-assistant.appspot.com"
    FIREBASE_CONFIG: Optional[str] = None  # JSON string for credentials
    
    # External APIs
    OPENAI_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # Scraping
    ENABLE_BACKGROUND_SCRAPING: bool = False
    SCRAPING_DELAY: float = 1.0
    SCRAPING_USER_AGENT: str = "STEM-Admissions-Assistant/2.0 (Educational Research)"
    SCRAPING_MAX_CONCURRENT: int = 5
    SCRAPING_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # AI Configuration
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.3
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hour
    
    # Monitoring
    ENABLE_METRICS: bool = True
    HEALTH_CHECK_TIMEOUT: int = 30
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DEBUG", pre=True)
    def set_debug_from_environment(cls, v, values):
        if values.get("ENVIRONMENT") == "development":
            return True
        return v
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Configuration for different environments
class DevelopmentConfig(Settings):
    """Development environment configuration"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_BACKGROUND_SCRAPING: bool = False

class ProductionConfig(Settings):
    """Production environment configuration"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_BACKGROUND_SCRAPING: bool = True
    WORKERS: int = 2

class TestingConfig(Settings):
    """Testing environment configuration"""
    ENVIRONMENT: str = "testing"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    ENABLE_BACKGROUND_SCRAPING: bool = False

# Factory function to get appropriate config
def get_config() -> Settings:
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Global settings instance
settings = get_settings()

# Constants
class Constants:
    """Application constants"""
    
    # University rankings (top CS schools)
    TOP_CS_UNIVERSITIES = [
        "Stanford University",
        "Massachusetts Institute of Technology",
        "Carnegie Mellon University",
        "University of California, Berkeley",
        "California Institute of Technology",
        "Harvard University",
        "Princeton University",
        "University of Toronto",
        "ETH Zurich",
        "University of Oxford"
    ]
    
    # Research areas
    RESEARCH_AREAS = [
        "Machine Learning",
        "Artificial Intelligence",
        "Computer Vision",
        "Natural Language Processing",
        "Robotics",
        "Systems",
        "Algorithms",
        "Theory",
        "Human Computer Interaction",
        "Software Engineering",
        "Cybersecurity",
        "Data Science",
        "Bioinformatics",
        "Quantum Computing",
        "Computer Graphics",
        "Database Systems",
        "Distributed Systems",
        "Programming Languages"
    ]
    
    # Degree types
    DEGREE_TYPES = ["PhD", "MS", "MEng", "MCS", "MS/PhD"]
    
    # Hiring statuses
    HIRING_STATUSES = ["hiring", "maybe", "not_hiring", "unknown"]
    
    # Scraping priorities
    SCRAPING_PRIORITIES = ["critical", "high", "medium", "low"]
    
    # Social media sources
    SOCIAL_MEDIA_SOURCES = ["reddit", "twitter", "linkedin"]
    
    # Application deadlines (typical months)
    APPLICATION_DEADLINE_MONTHS = [
        "December", "January", "February", "March"
    ]
    
    # Countries
    COUNTRIES = ["USA", "Canada", "United Kingdom", "Switzerland", "Germany", "Netherlands", "France", "Australia"]

# Validation functions
def validate_api_keys():
    """Validate that required API keys are present"""
    required_keys = []
    
    if not settings.OPENAI_API_KEY:
        required_keys.append("OPENAI_API_KEY")
    
    if settings.ENABLE_BACKGROUND_SCRAPING:
        if not settings.REDDIT_CLIENT_ID:
            required_keys.append("REDDIT_CLIENT_ID")
        if not settings.REDDIT_CLIENT_SECRET:
            required_keys.append("REDDIT_CLIENT_SECRET")
    
    if required_keys and settings.is_production:
        raise ValueError(f"Missing required API keys in production: {required_keys}")
    
    return len(required_keys) == 0

def get_database_url() -> str:
    """Get Firebase project URL"""
    return f"https://{settings.FIREBASE_PROJECT_ID}-default-rtdb.firebaseio.com/"

def get_storage_url() -> str:
    """Get Firebase Storage URL"""
    return f"gs://{settings.FIREBASE_STORAGE_BUCKET}"

# Utility functions
def get_cors_origins() -> List[str]:
    """Get CORS origins for current environment"""
    if settings.is_production:
        return [
            f"https://{settings.FIREBASE_PROJECT_ID}.web.app",
            f"https://{settings.FIREBASE_PROJECT_ID}.firebaseapp.com"
        ]
    else:
        return settings.ALLOWED_ORIGINS

def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI configuration"""
    return {
        "api_key": settings.OPENAI_API_KEY,
        "model": settings.OPENAI_MODEL,
        "max_tokens": settings.OPENAI_MAX_TOKENS,
        "temperature": settings.OPENAI_TEMPERATURE
    }

def get_scraping_config() -> Dict[str, Any]:
    """Get scraping configuration"""
    return {
        "enabled": settings.ENABLE_BACKGROUND_SCRAPING,
        "delay": settings.SCRAPING_DELAY,
        "user_agent": settings.SCRAPING_USER_AGENT,
        "max_concurrent": settings.SCRAPING_MAX_CONCURRENT,
        "timeout": settings.SCRAPING_TIMEOUT
    }

# Feature flags
class FeatureFlags:
    """Feature flags for enabling/disabling features"""
    
    ENABLE_CHAT = True
    ENABLE_FACULTY_SEARCH = True
    ENABLE_PROGRAM_SEARCH = True
    ENABLE_SOCIAL_MEDIA_SCRAPING = settings.ENABLE_BACKGROUND_SCRAPING
    ENABLE_UNIVERSITY_SCRAPING = settings.ENABLE_BACKGROUND_SCRAPING
    ENABLE_USER_AUTHENTICATION = False  # Disable for now
    ENABLE_RATE_LIMITING = settings.is_production
    ENABLE_CACHING = True
    ENABLE_ANALYTICS = settings.is_production
    ENABLE_ERROR_REPORTING = settings.is_production

# Version info
VERSION = "2.0.0"
API_VERSION = "v1"
BUILD_DATE = "2024-01-15"

# Export commonly used items
__all__ = [
    "settings",
    "Constants",
    "FeatureFlags",
    "get_settings",
    "get_config",
    "validate_api_keys",
    "get_cors_origins",
    "get_openai_config",
    "get_scraping_config",
    "VERSION",
    "API_VERSION"
]