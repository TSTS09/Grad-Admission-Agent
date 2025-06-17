from sqlalchemy import Column, String, Integer, Float, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Faculty(BaseModel):
    __tablename__ = "faculty"
    
    name = Column(String, nullable=False, index=True)
    email = Column(String)
    title = Column(String)  # Professor, Associate Professor, etc.
    
    # University relationship
    university_id = Column(Integer, ForeignKey("universities.id"))
    university = relationship("University", back_populates="faculty")
    department = Column(String)
    
    # Research information
    research_areas = Column(JSON)  # List of research keywords
    research_statement = Column(Text)
    homepage_url = Column(String)
    google_scholar_url = Column(String)
    
    # Hiring status
    hiring_status = Column(String)  # "hiring", "maybe", "not_hiring", "unknown"
    hiring_probability = Column(Float, default=0.0)
    last_hiring_update = Column(String)  # Source of last update
    
    # Publications and metrics
    h_index = Column(Integer)
    citation_count = Column(Integer)
    recent_publications = Column(JSON)
    
    # Contact and social
    office_location = Column(String)
    phone = Column(String)
    twitter_handle = Column(String)
    linkedin_url = Column(String)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    last_scraped = Column(String)
    scraping_sources = Column(JSON)
    
    # Relations
    programs = relationship("Program", secondary="program_faculty", back_populates="faculty")
