from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ProgramBase(BaseModel):
    name: str
    degree_type: str
    department: Optional[str] = None
    research_areas: Optional[List[str]] = None
    application_deadline: Optional[str] = None
    gre_required: Optional[bool] = None
    toefl_required: Optional[bool] = None

class ProgramCreate(ProgramBase):
    university_id: int

class ProgramUpdate(ProgramBase):
    name: Optional[str] = None
    degree_type: Optional[str] = None

class Program(ProgramBase):
    id: int
    university_id: int
    acceptance_rate: Optional[float] = None
    tuition_annual: Optional[float] = None
    funding_available: Optional[bool] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProgramSearch(BaseModel):
    degree_types: List[str]
    research_areas: Optional[List[str]] = None
    universities: Optional[List[int]] = None
    max_tuition: Optional[float] = None
    funding_required: Optional[bool] = None
    gre_required: Optional[bool] = None

class ProgramMatch(BaseModel):
    program: Program
    match_score: float
    university_name: str
    faculty_matches: List[Dict[str, Any]] = []