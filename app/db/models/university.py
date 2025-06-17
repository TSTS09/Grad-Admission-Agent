from sqlalchemy import Column, String, Integer, Float, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class University(BaseModel):
    __tablename__ = "universities"
    
    name = Column(String, nullable=False, index=True)
    short_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    state_province = Column(String)
    city = Column(String)
    
    # Rankings and metrics
    cs_ranking = Column(Integer)
    overall_ranking = Column(Integer)
    acceptance_rate = Column(Float)
    
    # Contact and web information
    website_url = Column(String)
    admissions_email = Column(String)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    scraping_config = Column(JSON)
    
    # Relations
    programs = relationship("Program", back_populates="university")
    faculty = relationship("Faculty", back_populates="university")
