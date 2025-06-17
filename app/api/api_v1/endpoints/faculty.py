from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_active_user
from app.schemas.faculty import Faculty, FacultyCreate, FacultyUpdate, FacultySearch
from app.schemas.user import User
from app.services.faculty import (
    get_faculty, get_faculty_by_id, create_faculty, update_faculty,
    search_faculty, get_faculty_by_research_area
)

router = APIRouter()

@router.get("/", response_model=List[Faculty])
async def read_faculty(
    skip: int = 0,
    limit: int = 100,
    university_id: Optional[int] = Query(None),
    research_area: Optional[str] = Query(None),
    hiring_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get faculty members with optional filters"""
    return await get_faculty(
        db,
        skip=skip,
        limit=limit,
        university_id=university_id,
        research_area=research_area,
        hiring_status=hiring_status
    )

@router.get("/{faculty_id}", response_model=Faculty)
async def read_faculty_by_id(
    faculty_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get faculty member by ID"""
    faculty = await get_faculty_by_id(db, faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    return faculty

@router.post("/search", response_model=List[Faculty])
async def search_faculty_members(
    search: FacultySearch,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search faculty members based on research interests and criteria"""
    return await search_faculty(db, search)

@router.get("/research/{research_area}", response_model=List[Faculty])
async def get_faculty_by_research(
    research_area: str,
    hiring_only: bool = Query(False),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    """Get faculty members by research area"""
    return await get_faculty_by_research_area(
        db, research_area, hiring_only=hiring_only, limit=limit
    )
