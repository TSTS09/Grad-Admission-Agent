#!/usr/bin/env python3
"""
Seed initial data for STEM Graduate Admissions Assistant
Run this script after Firebase setup to populate the database with universities and sample faculty.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.firebase_config import init_firebase, get_firebase
from app.models.firebase_models import University, Faculty, Program
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Top universities for STEM programs
UNIVERSITIES_DATA = [
    {
        "name": "Stanford University",
        "short_name": "Stanford",
        "country": "USA",
        "state_province": "California",
        "city": "Stanford",
        "cs_ranking": 1,
        "overall_ranking": 3,
        "acceptance_rate": 0.04,
        "website_url": "https://stanford.edu",
        "admissions_email": "admission@stanford.edu",
        "is_active": True
    },
    {
        "name": "Massachusetts Institute of Technology",
        "short_name": "MIT",
        "country": "USA",
        "state_province": "Massachusetts",
        "city": "Cambridge",
        "cs_ranking": 2,
        "overall_ranking": 1,
        "acceptance_rate": 0.07,
        "website_url": "https://mit.edu",
        "admissions_email": "admissions@mit.edu",
        "is_active": True
    },
    {
        "name": "Carnegie Mellon University",
        "short_name": "CMU",
        "country": "USA",
        "state_province": "Pennsylvania",
        "city": "Pittsburgh",
        "cs_ranking": 3,
        "overall_ranking": 25,
        "acceptance_rate": 0.15,
        "website_url": "https://cmu.edu",
        "admissions_email": "admission@cmu.edu",
        "is_active": True
    },
    {
        "name": "University of California, Berkeley",
        "short_name": "UC Berkeley",
        "country": "USA",
        "state_province": "California",
        "city": "Berkeley",
        "cs_ranking": 4,
        "overall_ranking": 22,
        "acceptance_rate": 0.17,
        "website_url": "https://berkeley.edu",
        "admissions_email": "admissions@berkeley.edu",
        "is_active": True
    },
    {
        "name": "California Institute of Technology",
        "short_name": "Caltech",
        "country": "USA",
        "state_province": "California",
        "city": "Pasadena",
        "cs_ranking": 8,
        "overall_ranking": 9,
        "acceptance_rate": 0.06,
        "website_url": "https://caltech.edu",
        "admissions_email": "admissions@caltech.edu",
        "is_active": True
    },
    {
        "name": "Harvard University",
        "short_name": "Harvard",
        "country": "USA",
        "state_province": "Massachusetts",
        "city": "Cambridge",
        "cs_ranking": 12,
        "overall_ranking": 2,
        "acceptance_rate": 0.05,
        "website_url": "https://harvard.edu",
        "admissions_email": "college@harvard.edu",
        "is_active": True
    },
    {
        "name": "Princeton University",
        "short_name": "Princeton",
        "country": "USA",
        "state_province": "New Jersey",
        "city": "Princeton",
        "cs_ranking": 7,
        "overall_ranking": 1,
        "acceptance_rate": 0.06,
        "website_url": "https://princeton.edu",
        "admissions_email": "uaoffice@princeton.edu",
        "is_active": True
    },
    {
        "name": "University of Toronto",
        "short_name": "UofT",
        "country": "Canada",
        "state_province": "Ontario",
        "city": "Toronto",
        "cs_ranking": 15,
        "overall_ranking": 25,
        "acceptance_rate": 0.43,
        "website_url": "https://utoronto.ca",
        "admissions_email": "admissions@utoronto.ca",
        "is_active": True
    },
    {
        "name": "ETH Zurich",
        "short_name": "ETH",
        "country": "Switzerland",
        "state_province": "Zurich",
        "city": "Zurich",
        "cs_ranking": 8,
        "overall_ranking": 11,
        "acceptance_rate": 0.08,
        "website_url": "https://ethz.ch",
        "admissions_email": "admissions@ethz.ch",
        "is_active": True
    },
    {
        "name": "University of Oxford",
        "short_name": "Oxford",
        "country": "United Kingdom",
        "state_province": "England",
        "city": "Oxford",
        "cs_ranking": 5,
        "overall_ranking": 4,
        "acceptance_rate": 0.17,
        "website_url": "https://ox.ac.uk",
        "admissions_email": "admissions@ox.ac.uk",
        "is_active": True
    }
]

# Sample faculty data
SAMPLE_FACULTY = [
    {
        "name": "Dr. Andrew Ng",
        "email": "ang@cs.stanford.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Machine Learning", "Artificial Intelligence", "Deep Learning"],
        "hiring_status": "hiring",
        "hiring_probability": 0.8,
        "university_name": "Stanford University"
    },
    {
        "name": "Dr. Fei-Fei Li",
        "email": "feifeili@cs.stanford.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Computer Vision", "Artificial Intelligence", "Machine Learning"],
        "hiring_status": "maybe",
        "hiring_probability": 0.6,
        "university_name": "Stanford University"
    },
    {
        "name": "Dr. Hal Abelson",
        "email": "hal@mit.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Computer Science Education", "Software Engineering"],
        "hiring_status": "unknown",
        "hiring_probability": 0.3,
        "university_name": "Massachusetts Institute of Technology"
    },
    {
        "name": "Dr. Regina Barzilay",
        "email": "regina@csail.mit.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Natural Language Processing", "Machine Learning", "AI for Healthcare"],
        "hiring_status": "hiring",
        "hiring_probability": 0.9,
        "university_name": "Massachusetts Institute of Technology"
    },
    {
        "name": "Dr. Tom Mitchell",
        "email": "mitchell@cs.cmu.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Machine Learning", "Artificial Intelligence", "Cognitive Science"],
        "hiring_status": "not_hiring",
        "hiring_probability": 0.1,
        "university_name": "Carnegie Mellon University"
    },
    {
        "name": "Dr. Manuela Veloso",
        "email": "veloso@cs.cmu.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Robotics", "Artificial Intelligence", "Machine Learning"],
        "hiring_status": "hiring",
        "hiring_probability": 0.7,
        "university_name": "Carnegie Mellon University"
    },
    {
        "name": "Dr. Michael Jordan",
        "email": "jordan@berkeley.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Machine Learning", "Statistics", "Artificial Intelligence"],
        "hiring_status": "maybe",
        "hiring_probability": 0.5,
        "university_name": "University of California, Berkeley"
    },
    {
        "name": "Dr. Stuart Russell",
        "email": "russell@berkeley.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Artificial Intelligence", "Machine Learning", "Robotics"],
        "hiring_status": "hiring",
        "hiring_probability": 0.8,
        "university_name": "University of California, Berkeley"
    }
]

# Sample programs
SAMPLE_PROGRAMS = [
    {
        "name": "Computer Science PhD",
        "degree_type": "PhD",
        "department": "Computer Science",
        "application_deadline": "2024-12-15",
        "gre_required": True,
        "toefl_required": True,
        "min_gpa": 3.5,
        "duration_years": 5,
        "research_areas": ["Machine Learning", "Computer Vision", "NLP", "Systems"],
        "tuition_annual": 58080.0,
        "funding_available": True,
        "acceptance_rate": 0.06,
        "university_name": "Stanford University"
    },
    {
        "name": "Electrical Engineering and Computer Science PhD",
        "degree_type": "PhD",
        "department": "EECS",
        "application_deadline": "2024-12-15",
        "gre_required": False,
        "toefl_required": True,
        "min_gpa": 3.7,
        "duration_years": 5,
        "research_areas": ["AI", "Systems", "Theory", "Robotics"],
        "tuition_annual": 59750.0,
        "funding_available": True,
        "acceptance_rate": 0.08,
        "university_name": "Massachusetts Institute of Technology"
    },
    {
        "name": "Computer Science PhD",
        "degree_type": "PhD",
        "department": "School of Computer Science",
        "application_deadline": "2024-12-15",
        "gre_required": True,
        "toefl_required": True,
        "min_gpa": 3.5,
        "duration_years": 5,
        "research_areas": ["ML", "Robotics", "HCI", "Software Engineering"],
        "tuition_annual": 61344.0,
        "funding_available": True,
        "acceptance_rate": 0.05,
        "university_name": "Carnegie Mellon University"
    },
    {
        "name": "Computer Science MS",
        "degree_type": "MS",
        "department": "Computer Science",
        "application_deadline": "2024-12-15",
        "gre_required": True,
        "toefl_required": True,
        "min_gpa": 3.3,
        "duration_years": 2,
        "research_areas": ["AI", "Systems", "Theory", "Data Science"],
        "tuition_annual": 44066.0,
        "funding_available": False,
        "acceptance_rate": 0.17,
        "university_name": "University of California, Berkeley"
    }
]

class DataSeeder:
    """Handles seeding of initial data"""
    
    def __init__(self):
        self.firebase = None
        self.universities_created = {}
    
    async def initialize(self):
        """Initialize Firebase connection"""
        await init_firebase()
        self.firebase = get_firebase()
        logger.info("Firebase initialized for data seeding")
    
    async def seed_all_data(self):
        """Seed all initial data"""
        try:
            logger.info("Starting data seeding process...")
            
            # Seed universities first
            await self.seed_universities()
            
            # Seed faculty
            await self.seed_faculty()
            
            # Seed programs
            await self.seed_programs()
            
            logger.info("Data seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during data seeding: {e}")
            raise
    
    async def seed_universities(self):
        """Seed university data"""
        logger.info("Seeding universities...")
        
        for uni_data in UNIVERSITIES_DATA:
            try:
                # Check if university already exists
                existing = await self.firebase.query_collection(
                    'universities',
                    [('name', '==', uni_data['name'])],
                    limit=1
                )
                
                if existing:
                    logger.info(f"University {uni_data['name']} already exists, skipping...")
                    self.universities_created[uni_data['name']] = existing[0]['id']
                    continue
                
                # Create university
                university_id = await self.firebase.create_document('universities', data=uni_data)
                self.universities_created[uni_data['name']] = university_id
                
                logger.info(f"Created university: {uni_data['name']}")
                
            except Exception as e:
                logger.error(f"Error creating university {uni_data['name']}: {e}")
        
        logger.info(f"Seeded {len(self.universities_created)} universities")
    
    async def seed_faculty(self):
        """Seed faculty data"""
        logger.info("Seeding faculty...")
        
        faculty_created = 0
        
        for faculty_data in SAMPLE_FACULTY:
            try:
                # Get university ID
                university_name = faculty_data['university_name']
                if university_name not in self.universities_created:
                    logger.warning(f"University {university_name} not found for faculty {faculty_data['name']}")
                    continue
                
                faculty_data['university_id'] = self.universities_created[university_name]
                faculty_data['is_active'] = True
                
                # Check if faculty already exists
                existing = await self.firebase.query_collection(
                    'faculty',
                    [('name', '==', faculty_data['name']), ('university_name', '==', university_name)],
                    limit=1
                )
                
                if existing:
                    logger.info(f"Faculty {faculty_data['name']} already exists, skipping...")
                    continue
                
                # Create faculty
                await self.firebase.create_document('faculty', data=faculty_data)
                faculty_created += 1
                
                logger.info(f"Created faculty: {faculty_data['name']} at {university_name}")
                
            except Exception as e:
                logger.error(f"Error creating faculty {faculty_data['name']}: {e}")
        
        logger.info(f"Seeded {faculty_created} faculty members")
    
    async def seed_programs(self):
        """Seed program data"""
        logger.info("Seeding programs...")
        
        programs_created = 0
        
        for program_data in SAMPLE_PROGRAMS:
            try:
                # Get university ID
                university_name = program_data['university_name']
                if university_name not in self.universities_created:
                    logger.warning(f"University {university_name} not found for program {program_data['name']}")
                    continue
                
                program_data['university_id'] = self.universities_created[university_name]
                program_data['is_active'] = True
                
                # Check if program already exists
                existing = await self.firebase.query_collection(
                    'programs',
                    [('name', '==', program_data['name']), ('university_name', '==', university_name)],
                    limit=1
                )
                
                if existing:
                    logger.info(f"Program {program_data['name']} already exists, skipping...")
                    continue
                
                # Create program
                await self.firebase.create_document('programs', data=program_data)
                programs_created += 1
                
                logger.info(f"Created program: {program_data['name']} at {university_name}")
                
            except Exception as e:
                logger.error(f"Error creating program {program_data['name']}: {e}")
        
        logger.info(f"Seeded {programs_created} programs")
    
    async def verify_data(self):
        """Verify that data was seeded correctly"""
        logger.info("Verifying seeded data...")
        
        # Count universities
        universities = await self.firebase.query_collection('universities', [('is_active', '==', True)], limit=100)
        logger.info(f"Total universities in database: {len(universities)}")
        
        # Count faculty
        faculty = await self.firebase.query_collection('faculty', [('is_active', '==', True)], limit=100)
        logger.info(f"Total faculty in database: {len(faculty)}")
        
        # Count programs
        programs = await self.firebase.query_collection('programs', [('is_active', '==', True)], limit=100)
        logger.info(f"Total programs in database: {len(programs)}")
        
        # Count hiring faculty
        hiring_faculty = await self.firebase.query_collection('faculty', [('hiring_status', '==', 'hiring')], limit=100)
        logger.info(f"Faculty currently hiring: {len(hiring_faculty)}")
        
        logger.info("Data verification completed!")

async def main():
    """Main function to run data seeding"""
    try:
        seeder = DataSeeder()
        await seeder.initialize()
        await seeder.seed_all_data()
        await seeder.verify_data()
        
        print("\n✅ Data seeding completed successfully!")
        print("You can now start the application and see the seeded data.")
        
    except Exception as e:
        logger.error(f"Data seeding failed: {e}")
        print(f"\n❌ Data seeding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())