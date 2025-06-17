from sqlalchemy import Column, String, Integer, Float, JSON, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Application(BaseModel):
    __tablename__ = "applications"
    
    # User and program relationship
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="applications")
    
    program_id = Column(Integer, ForeignKey("programs.id"))
    program = relationship("Program", back_populates="applications")
    
    # Application status
    status = Column(String, default="planning")  # planning, submitted, accepted, rejected, waitlisted
    submitted_date = Column(DateTime)
    decision_date = Column(DateTime)
    
    # Application materials
    documents = Column(JSON)  # List of uploaded documents
    statement_of_purpose = Column(Text)
    research_statement = Column(Text)
    
    # Scores and metrics
    gre_verbal = Column(Integer)
    gre_quantitative = Column(Integer)
    gre_writing = Column(Float)
    toefl_score = Column(Integer)
    ielts_score = Column(Float)
    gpa = Column(Float)
    
    # AI assistance
    match_score = Column(Float)  # AI-calculated match score
    ai_recommendations = Column(JSON)
    document_feedback = Column(JSON)
    
    # Notes and tracking
    notes = Column(Text)
    deadlines = Column(JSON)
    reminders = Column(JSON)
 