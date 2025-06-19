import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.scrapers.university_scraper import UniversitySpider
from app.scrapers.social_media import RedditMonitor, TwitterMonitor
from app.database import AsyncSessionLocal
from app.services.faculty import create_or_update_faculty
from app.core.config import settings
from app.core.logging import get_logger
from app.worker.celery_app import celery_app

logger = get_logger(__name__)

class ScrapingPriority(Enum):
    CRITICAL = 1    # Faculty hiring, deadlines
    HIGH = 2        # Program requirements  
    MEDIUM = 3      # Faculty research updates
    LOW = 4         # General program info

class DataUpdateScheduler:
    """Scheduler for managing data scraping and updates"""
    
    def __init__(self):
        self.update_intervals = {
            ScrapingPriority.CRITICAL: timedelta(hours=6),    # 4 times daily
            ScrapingPriority.HIGH: timedelta(hours=12),       # Twice daily
            ScrapingPriority.MEDIUM: timedelta(days=1),       # Daily
            ScrapingPriority.LOW: timedelta(days=7)           # Weekly
        }
        
        # Adjust for application season
        self.is_application_season = self._is_application_season()
        if self.is_application_season:
            self.update_intervals[ScrapingPriority.CRITICAL] = timedelta(hours=3)
            self.update_intervals[ScrapingPriority.HIGH] = timedelta(hours=6)
    
    def _is_application_season(self) -> bool:
        """Check if it's currently application season (Sep-Jan)"""
        current_month = datetime.now().month
        return current_month in [9, 10, 11, 12, 1]
    
    async def schedule_all_updates(self):
        """Schedule all data update tasks"""
        logger.info("Scheduling data update tasks")
        
        # Schedule university faculty scraping (HIGH priority)
        celery_app.send_task(
            'app.worker.tasks.scrape_university_faculty',
            countdown=300  # Start in 5 minutes
        )
        
        # Schedule social media monitoring (CRITICAL priority)
        celery_app.send_task(
            'app.worker.tasks.monitor_social_media',
            countdown=60   # Start in 1 minute
        )
        
        # Schedule program requirements update (MEDIUM priority)
        celery_app.send_task(
            'app.worker.tasks.update_program_requirements',
            countdown=3600  # Start in 1 hour
        )
        
        logger.info("All update tasks scheduled")
