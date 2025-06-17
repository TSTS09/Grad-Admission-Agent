import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.worker.celery_app import celery_app
from app.scrapers.university_spider import UniversitySpider
from app.scrapers.social_media import RedditMonitor, TwitterMonitor
from app.database import AsyncSessionLocal
from app.db.models.faculty import Faculty
from app.db.models.university import University
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def scrape_university_faculty(self, universities: List[str] = None):
    """Celery task to scrape university faculty"""
    try:
        return asyncio.run(_scrape_university_faculty_async(universities))
    except Exception as e:
        logger.error(f"Error in scrape_university_faculty task: {e}")
        raise self.retry(countdown=60, exc=e)

async def _scrape_university_faculty_async(universities: List[str] = None):
    """Async implementation of faculty scraping"""
    universities = universities or ['stanford', 'mit', 'cmu', 'berkeley']
    
    async with UniversitySpider() as spider:
        faculty_data = await spider.scrape(universities=universities)
    
    # Save to database
    async with AsyncSessionLocal() as db:
        saved_count = 0
        
        for faculty_info in faculty_data:
            try:
                await _save_faculty_to_db(db, faculty_info)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving faculty {faculty_info.get('name')}: {e}")
        
        await db.commit()
    
    logger.info(f"Faculty scraping completed: {saved_count}/{len(faculty_data)} saved")
    return {"scraped": len(faculty_data), "saved": saved_count}

@celery_app.task(bind=True, max_retries=3)
def monitor_social_media(self):
    """Celery task to monitor social media for hiring announcements"""
    try:
        return asyncio.run(_monitor_social_media_async())
    except Exception as e:
        logger.error(f"Error in monitor_social_media task: {e}")
        raise self.retry(countdown=300, exc=e)

async def _monitor_social_media_async():
    """Async implementation of social media monitoring"""
    reddit_posts = []
    twitter_tweets = []
    
    # Monitor Reddit
    try:
        async with RedditMonitor() as reddit:
            reddit_posts = await reddit.scrape(limit=200)
    except Exception as e:
        logger.error(f"Error monitoring Reddit: {e}")
    
    # Monitor Twitter
    try:
        async with TwitterMonitor() as twitter:
            twitter_tweets = await twitter.scrape(limit=100)
    except Exception as e:
        logger.error(f"Error monitoring Twitter: {e}")
    
    # Process and analyze posts/tweets for hiring signals
    total_signals = len(reddit_posts) + len(twitter_tweets)
    
    # Here you would typically:
    # 1. Analyze posts for faculty names and universities
    # 2. Update faculty hiring status based on signals
    # 3. Save relevant posts to database for reference
    
    logger.info(f"Social media monitoring completed: {total_signals} signals found")
    return {"reddit_posts": len(reddit_posts), "twitter_tweets": len(twitter_tweets)}

@celery_app.task(bind=True, max_retries=3)
def update_program_requirements(self):
    """Celery task to update program requirements"""
    try:
        return asyncio.run(_update_program_requirements_async())
    except Exception as e:
        logger.error(f"Error in update_program_requirements task: {e}")
        raise self.retry(countdown=1800, exc=e)

async def _update_program_requirements_async():
    """Async implementation of program requirements update"""
    # This would scrape program websites for updated requirements
    # For now, return a placeholder
    
    logger.info("Program requirements update completed")
    return {"updated": 0}

async def _save_faculty_to_db(db: AsyncSession, faculty_info: Dict[str, Any]):
    """Save faculty information to database"""
    # This is a simplified version - you'd want more robust handling
    
    from sqlalchemy import select
    
    # Check if faculty already exists
    result = await db.execute(
        select(Faculty).where(
            Faculty.name == faculty_info['name'],
            Faculty.university.has(University.name.ilike(f"%{faculty_info['university']}%"))
        )
    )
    
    existing_faculty = result.scalar_one_or_none()
    
    if existing_faculty:
        # Update existing faculty
        existing_faculty.hiring_status = faculty_info.get('hiring_status')
        existing_faculty.hiring_probability = faculty_info.get('hiring_probability', 0.0)
        existing_faculty.research_areas = faculty_info.get('research_areas', [])
        existing_faculty.homepage_url = faculty_info.get('homepage_url')
        existing_faculty.email = faculty_info.get('email')
    else:
        # Create new faculty
        # You'd need to get or create the university first
        new_faculty = Faculty(
            name=faculty_info['name'],
            title=faculty_info.get('title'),
            email=faculty_info.get('email'),
            department=faculty_info.get('department'),
            research_areas=faculty_info.get('research_areas', []),
            hiring_status=faculty_info.get('hiring_status', 'unknown'),
            hiring_probability=faculty_info.get('hiring_probability', 0.0),
            homepage_url=faculty_info.get('homepage_url'),
            # university_id would be set after finding/creating university
        )
        
        db.add(new_faculty)