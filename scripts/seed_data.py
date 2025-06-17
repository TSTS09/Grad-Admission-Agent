import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.db.models.university import University
from app.db.models.faculty import Faculty
from app.db.models.program import Program
from app.db.models.user import User
from app.core.security import get_password_hash
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Sample data
UNIVERSITIES_DATA = [
    {
        "name": "Stanford University",
        "short_name": "Stanford",
        "country": "USA",
        "state_province": "California", 
        "city": "Stanford",
        "cs_ranking": 1,
        "overall_ranking": 3,
        "acceptance_rate": 0.06,
        "website_url": "https://cs.stanford.edu",
        "admissions_email": "admissions@cs.stanford.edu"
    },
    {
        "name": "Massachusetts Institute of Technology",
        "short_name": "MIT",
        "country": "USA",
        "state_province": "Massachusetts",
        "city": "Cambridge", 
        "cs_ranking": 2,
        "overall_ranking": 1,
        "acceptance_rate": 0.08,
        "website_url": "https://www.csail.mit.edu",
        "admissions_email": "admissions@csail.mit.edu"
    },
    {
        "name": "Carnegie Mellon University",
        "short_name": "CMU",
        "country": "USA",
        "state_province": "Pennsylvania",
        "city": "Pittsburgh",
        "cs_ranking": 3,
        "overall_ranking": 25,
        "acceptance_rate": 0.11,
        "website_url": "https://csd.cmu.edu",
        "admissions_email": "admissions@cs.cmu.edu"
    },
    {
        "name": "University of California, Berkeley",
        "short_name": "UC Berkeley",
        "country": "USA",
        "state_province": "California",
        "city": "Berkeley",
        "cs_ranking": 4,
        "overall_ranking": 22,
        "acceptance_rate": 0.09,
        "website_url": "https://eecs.berkeley.edu",
        "admissions_email": "admissions@eecs.berkeley.edu"
    }
]

FACULTY_DATA = [
    {
        "name": "Dr. Andrew Ng",
        "email": "ang@cs.stanford.edu",
        "title": "Professor",
        "university_name": "Stanford University",
        "department": "Computer Science",
        "research_areas": ["Machine Learning", "Artificial Intelligence", "Deep Learning"],
        "hiring_status": "hiring",
        "hiring_probability": 0.85,
        "homepage_url": "https://www.andrewng.org",
        "h_index": 189,
        "citation_count": 250000
    },
    {
        "name": "Dr. Fei-Fei Li",
        "email": "feifeili@cs.stanford.edu", 
        "title": "Professor",
        "university_name": "Stanford University",
        "department": "Computer Science",
        "research_areas": ["Computer Vision", "Artificial Intelligence", "Machine Learning"],
        "hiring_status": "maybe",
        "hiring_probability": 0.65,
        "homepage_url": "https://profiles.stanford.edu/fei-fei-li",
        "h_index": 156,
        "citation_count": 180000
    },
    {
        "name": "Dr. Daphne Koller",
        "email": "daphne@cs.stanford.edu",
        "title": "Professor",
        "university_name": "Stanford University", 
        "department": "Computer Science",
        "research_areas": ["Machine Learning", "Probabilistic Models", "Computational Biology"],
        "hiring_status": "not_hiring",
        "hiring_probability": 0.25,
        "homepage_url": "https://cs.stanford.edu/people/koller",
        "h_index": 142,
        "citation_count": 150000
    },
    {
        "name": "Dr. Tommi Jaakkola",
        "email": "tommi@csail.mit.edu",
        "title": "Professor", 
        "university_name": "Massachusetts Institute of Technology",
        "department": "Electrical Engineering and Computer Science",
        "research_areas": ["Machine Learning", "Statistics", "Computational Biology"],
        "hiring_status": "hiring",
        "hiring_probability": 0.75,
        "homepage_url": "https://people.csail.mit.edu/tommi",
        "h_index": 98,
        "citation_count": 95000
    }
]

PROGRAMS_DATA = [
    {
        "name": "Computer Science PhD",
        "degree_type": "PhD",
        "university_name": "Stanford University",
        "department": "Computer Science",
        "application_deadline": "2024-12-01",
        "application_requirements": {
            "gre": "recommended",
            "toefl": "required_for_international",
            "letters": 3,
            "statement": "required",
            "transcripts": "required"
        },
        "gre_required": False,
        "toefl_required": True,
        "min_gpa": 3.5,
        "duration_years": 5,
        "research_areas": ["AI", "ML", "Systems", "Theory", "HCI"],
        "tuition_annual": 58416.0,
        "funding_available": True,
        "acceptance_rate": 0.06
    },
    {
        "name": "Electrical Engineering and Computer Science PhD",
        "degree_type": "PhD", 
        "university_name": "Massachusetts Institute of Technology",
        "department": "EECS",
        "application_deadline": "2024-12-15",
        "application_requirements": {
            "gre": "required",
            "toefl": "required_for_international", 
            "letters": 3,
            "statement": "required",
            "transcripts": "required"
        },
        "gre_required": True,
        "toefl_required": True,
        "min_gpa": 3.7,
        "duration_years": 5,
        "research_areas": ["AI", "Robotics", "Systems", "Theory"],
        "tuition_annual": 59750.0,
        "funding_available": True,
        "acceptance_rate": 0.08
    }
]

async def seed_universities(db: AsyncSession):
    """Seed universities data"""
    logger.info("Seeding universities...")
    
    for uni_data in UNIVERSITIES_DATA:
        university = University(**uni_data)
        db.add(university)
    
    await db.commit()
    logger.info(f"Seeded {len(UNIVERSITIES_DATA)} universities")

async def seed_faculty(db: AsyncSession):
    """Seed faculty data"""
    logger.info("Seeding faculty...")
    
    # Get universities for mapping
    from sqlalchemy import select
    universities = {}
    result = await db.execute(select(University))
    for uni in result.scalars().all():
        universities[uni.name] = uni.id
    
    for faculty_data in FACULTY_DATA:
        uni_name = faculty_data.pop("university_name")
        faculty_data["university_id"] = universities[uni_name]
        
        faculty = Faculty(**faculty_data)
        db.add(faculty)
    
    await db.commit()
    logger.info(f"Seeded {len(FACULTY_DATA)} faculty members")

async def seed_programs(db: AsyncSession):
    """Seed programs data"""
    logger.info("Seeding programs...")
    
    # Get universities for mapping
    from sqlalchemy import select
    universities = {}
    result = await db.execute(select(University))
    for uni in result.scalars().all():
        universities[uni.name] = uni.id
    
    for program_data in PROGRAMS_DATA:
        uni_name = program_data.pop("university_name")
        program_data["university_id"] = universities[uni_name]
        
        program = Program(**program_data)
        db.add(program)
    
    await db.commit() 
    logger.info(f"Seeded {len(PROGRAMS_DATA)} programs")

async def seed_demo_user(db: AsyncSession):
    """Create a demo user"""
    logger.info("Creating demo user...")
    
    demo_user = User(
        email="demo@stemgradassistant.com",
        hashed_password=get_password_hash("demo123"),
        full_name="Demo User",
        research_interests=["Machine Learning", "Computer Vision", "Robotics"],
        target_universities=[1, 2, 3],  # Stanford, MIT, CMU
        academic_background={
            "degree": "Bachelor of Science",
            "major": "Computer Science", 
            "university": "State University",
            "gpa": 3.8,
            "graduation_year": 2023
        },
        preferences={
            "degree_type": "PhD",
            "preferred_locations": ["California", "Massachusetts"],
            "funding_required": True,
            "research_focus": "AI/ML"
        }
    )
    
    db.add(demo_user)
    await db.commit()
    logger.info("Demo user created with email: demo@stemgradassistant.com")

async def main():
    """Main seeding function"""
    logger.info("Starting database seeding...")
    
    async with AsyncSessionLocal() as db:
        await seed_universities(db)
        await seed_faculty(db)
        await seed_programs(db)
        await seed_demo_user(db)
    
    logger.info("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())