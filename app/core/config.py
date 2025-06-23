# app/core/config.py - Updated for Real Scraping System

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """Enhanced settings for real-time scraping system"""
    
    # Basic app info
    APP_NAME: str = "Graduate Admissions Intelligence System"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Core AI API Keys (Required)
    GEMINI_API_KEY: Optional[str] = None
    
    # Web Scraping APIs (Recommended)
    SERPAPI_KEY: Optional[str] = None  # For Google search results
    
    # Social Media APIs (Optional but recommended)
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    
    # Firebase (Optional - for data persistence)
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    
    # Rate limiting and performance
    MAX_CONCURRENT_SCRAPES: int = 10
    SCRAPING_TIMEOUT_SECONDS: int = 30
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Caching
    CACHE_TTL_HOURS: int = 2  # How long to cache scraping results
    ENABLE_CACHING: bool = True
    
    # Intelligent update frequencies
    UPDATE_FREQUENCIES: Dict[str, int] = {
        "reddit_posts": 1,      # Daily
        "twitter_signals": 1,   # Daily  
        "university_pages": 7,  # Weekly
        "faculty_pages": 7,     # Weekly
        "program_pages": 30,    # Monthly
        "job_boards": 3         # Every 3 days
    }
    
    # Scraping priorities by source type
    SOURCE_PRIORITIES: Dict[str, float] = {
        "university_website": 0.9,
        "faculty_page": 0.9,
        "reddit": 0.7,
        "twitter": 0.6,
        "academic_forum": 0.8,
        "job_board": 0.8
    }
    
    # Content filtering
    MIN_CONTENT_LENGTH: int = 50
    MAX_CONTENT_LENGTH: int = 5000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("GEMINI_API_KEY")
    def validate_gemini_key(cls, v):
        if not v:
            raise ValueError("GEMINI_API_KEY is required for AI-powered synthesis")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def reddit_enabled(self) -> bool:
        return bool(self.REDDIT_CLIENT_ID and self.REDDIT_CLIENT_SECRET)
    
    @property
    def twitter_enabled(self) -> bool:
        return bool(self.TWITTER_BEARER_TOKEN)
    
    @property
    def google_search_enabled(self) -> bool:
        return bool(self.SERPAPI_KEY)
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration"""
        return {
            "max_concurrent": self.MAX_CONCURRENT_SCRAPES,
            "timeout": self.SCRAPING_TIMEOUT_SECONDS,
            "min_content_length": self.MIN_CONTENT_LENGTH,
            "max_content_length": self.MAX_CONTENT_LENGTH,
            "priorities": self.SOURCE_PRIORITIES,
            "update_frequencies": self.UPDATE_FREQUENCIES
        }

# Global settings instance
settings = Settings()

# Enhanced Firebase integration (optional)
def get_firebase():
    """Get Firebase manager if configured"""
    try:
        from app.core.firebase_config import FirebaseManager
        if settings.FIREBASE_PROJECT_ID:
            return FirebaseManager()
    except ImportError:
        pass
    return None

# API Key validation helper
def validate_api_setup() -> Dict[str, bool]:
    """Validate API key setup and return capabilities"""
    
    capabilities = {
        "core_ai": bool(settings.GEMINI_API_KEY),
        "google_search": settings.google_search_enabled,
        "reddit_scraping": settings.reddit_enabled,
        "twitter_scraping": settings.twitter_enabled,
        "firebase_storage": bool(settings.FIREBASE_PROJECT_ID)
    }
    
    return capabilities

# University domain detection
UNIVERSITY_DOMAINS = [
    ".edu",           # US universities
    ".ac.uk",         # UK universities  
    ".ox.ac.uk",      # Oxford
    ".cam.ac.uk",     # Cambridge
    ".ethz.ch",       # ETH Zurich
    ".epfl.ch",       # EPFL
    ".utoronto.ca",   # University of Toronto
    ".ubc.ca",        # UBC
    ".mcgill.ca",     # McGill
    ".mit.edu",       # MIT
    ".stanford.edu",  # Stanford
    ".berkeley.edu",  # UC Berkeley
    ".cmu.edu"        # Carnegie Mellon
]

# Target subreddits for graduate admissions intelligence
TARGET_SUBREDDITS = [
    "gradadmissions",
    "PhD", 
    "GradSchool",
    "MachineLearning",
    "compsci",
    "AskAcademia",
    "academia",
    "cscareerquestions",
    "EngineeringStudents",
    "gradschool",
    "ApplyingToCollege"
]

# Academic forums and job boards
ACADEMIC_FORUMS = [
    "thegradcafe.com",
    "academicjobsonline.org",
    "jobs.ac.uk",
    "vitae.ac.uk",
    "chronicleforums.com",
    "mathematicsjobs.org",
    "mathjobs.org"
]

# Common research areas for intelligent matching
RESEARCH_AREAS = [
    "Machine Learning",
    "Artificial Intelligence", 
    "Computer Vision",
    "Natural Language Processing",
    "Robotics",
    "Human-Computer Interaction",
    "Computer Systems",
    "Algorithms",
    "Database Systems",
    "Software Engineering",
    "Cybersecurity",
    "Data Science",
    "Deep Learning",
    "Reinforcement Learning",
    "Computer Graphics",
    "Bioinformatics",
    "Quantum Computing",
    "Distributed Systems",
    "Computer Networks",
    "Information Retrieval"
]

# STEM fields priority for scraping
STEM_PRIORITIES = {
    "Computer Science": 1.0,
    "Electrical Engineering": 0.9,
    "Mechanical Engineering": 0.8,
    "Chemical Engineering": 0.8,
    "Materials Science": 0.7,
    "Bioengineering": 0.7,
    "Applied Mathematics": 0.6,
    "Statistics": 0.6,
    "Physics": 0.5,
    "Chemistry": 0.5
}

# Export commonly used items
__all__ = [
    "settings",
    "get_firebase", 
    "validate_api_setup",
    "UNIVERSITY_DOMAINS",
    "TARGET_SUBREDDITS",
    "ACADEMIC_FORUMS", 
    "RESEARCH_AREAS",
    "STEM_PRIORITIES"
]