import os

class Settings:
    """Application settings"""
    
    # Basic app info
    APP_NAME = "Intelligent Grad Admissions Assistant"
    VERSION = "1.0.0"
    
    # Server
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
    
    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Database
    DATABASE_PATH = "admissions_search.db"

# Global settings instance
settings = Settings()