from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class FacultyBase(BaseModel):
    name: str
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    research_areas: Optional[List[str]] = None
    research_statement: Optional[str] = None
    homepage_url: Optional[str] = None

class FacultyCreate(FacultyBase):
    university_id: int

class FacultyUpdate(FacultyBase):
    name: Optional[str] = None

class Faculty(FacultyBase):
    id: int
    university_id: int
    hiring_status: Optional[str] = None
    hiring_probability: float = 0.0
    h_index: Optional[int] = None
    citation_count: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class FacultySearch(BaseModel):
    research_areas: List[str]
    universities: Optional[List[int]] = None
    hiring_status: Optional[List[str]] = None
    min_hiring_probability: Optional[float] = None
    degree_types: Optional[List[str]] = None

class FacultyMatch(BaseModel):
    faculty: Faculty
    match_score: float
    matching_areas: List[str]
    university_name: str