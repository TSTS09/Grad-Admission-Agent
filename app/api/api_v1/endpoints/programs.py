from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_active_user
from app.schemas.program import Program, ProgramSearch, ProgramMatch
from app.schemas.user import User
from app.services.program import get_programs, get_program_by_id, search_programs, match_programs_for_user

router = APIRouter()

@router.get("/", response_model=List[Program])
async def read_programs(
    skip: int = 0,
    limit: int = 100,
    degree_type: Optional[str] = Query(None),
    university_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get programs with optional filters"""
    return await get_programs(
        db,
        skip=skip,
        limit=limit,
        degree_type=degree_type,
        university_id=university_id
    )

@router.get("/{program_id}", response_model=Program)
async def read_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get program by ID"""
    program = await get_program_by_id(db, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program

@router.post("/search", response_model=List[Program])
async def search_programs_endpoint(
    search: ProgramSearch,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search programs based on criteria"""
    return await search_programs(db, search)

@router.get("/match/recommendations", response_model=List[ProgramMatch])
async def get_program_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized program recommendations for user"""
    return await match_programs_for_user(db, current_user.id)
