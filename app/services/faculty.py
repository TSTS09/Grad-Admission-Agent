from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.models.faculty import Faculty
from app.db.models.university import University
from app.schemas.faculty import FacultyCreate, FacultyUpdate, FacultySearch

async def get_faculty(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    university_id: Optional[int] = None,
    research_area: Optional[str] = None,
    hiring_status: Optional[str] = None
) -> List[Faculty]:
    """Get faculty members with filters"""
    query = select(Faculty).where(Faculty.is_active == True)
    
    if university_id:
        query = query.where(Faculty.university_id == university_id)
    
    if research_area:
        query = query.where(Faculty.research_areas.contains([research_area]))
    
    if hiring_status:
        query = query.where(Faculty.hiring_status == hiring_status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_faculty_by_id(db: AsyncSession, faculty_id: int) -> Optional[Faculty]:
    """Get faculty member by ID"""
    result = await db.execute(
        select(Faculty).where(Faculty.id == faculty_id)
    )
    return result.scalar_one_or_none()

async def search_faculty(db: AsyncSession, search: FacultySearch) -> List[Faculty]:
    """Search faculty based on criteria"""
    query = select(Faculty).where(Faculty.is_active == True)
    
    # Research areas filter
    if search.research_areas:
        research_conditions = []
        for area in search.research_areas:
            research_conditions.append(Faculty.research_areas.contains([area]))
        query = query.where(or_(*research_conditions))
    
    # Universities filter
    if search.universities:
        query = query.where(Faculty.university_id.in_(search.universities))
    
    # Hiring status filter
    if search.hiring_status:
        query = query.where(Faculty.hiring_status.in_(search.hiring_status))
    
    # Hiring probability filter
    if search.min_hiring_probability:
        query = query.where(Faculty.hiring_probability >= search.min_hiring_probability)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_faculty_by_research_area(
    db: AsyncSession,
    research_area: str,
    hiring_only: bool = False,
    limit: int = 50
) -> List[Faculty]:
    """Get faculty by research area"""
    query = select(Faculty).where(
        and_(
            Faculty.is_active == True,
            Faculty.research_areas.contains([research_area])
        )
    )
    
    if hiring_only:
        query = query.where(Faculty.hiring_status == "hiring")
    
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()