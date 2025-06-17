from sqlalchemy import Column, String, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Profile information
    research_interests = Column(JSON)
    target_universities = Column(JSON)
    academic_background = Column(JSON)
    preferences = Column(JSON)
    
    # Relations
    applications = relationship("Application", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
