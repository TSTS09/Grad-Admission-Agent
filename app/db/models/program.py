from sqlalchemy import Column, String, Integer, Float, JSON, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

# Association table for many-to-many relationship
program_faculty = Table(
    'program_faculty',
    BaseModel.metadata,
    Column('program_id', Integer, ForeignKey('programs.id')),
    Column('faculty_id', Integer, ForeignKey('faculty.id'))
)

class Program(BaseModel):
    __tablename__ = "programs"
    
    name = Column(String, nullable=False)
    degree_type = Column(String, nullable=False)  # PhD, MS, etc.
    department = Column(String)
    
    # University relationship
    university_id = Column(Integer, ForeignKey("universities.id"))
    university = relationship("University", back_populates="programs")
    
    # Application information
    application_deadline = Column(String)
    application_requirements = Column(JSON)
    gre_required = Column(Boolean)
    toefl_required = Column(Boolean)
    min_gpa = Column(Float)
    
    # Program details
    duration_years = Column(Integer)
    research_areas = Column(JSON)
    specializations = Column(JSON)
    
    # Financial information
    tuition_annual = Column(Float)
    funding_available = Column(Boolean)
    average_funding_amount = Column(Float)
    funding_details = Column(JSON)
    
    # Statistics
    acceptance_rate = Column(Float)
    enrollment_size = Column(Integer)
    international_student_percentage = Column(Float)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    last_updated = Column(String)
    
    # Relations
    faculty = relationship("Faculty", secondary="program_faculty", back_populates="programs")
    applications = relationship("Application", back_populates="program")
