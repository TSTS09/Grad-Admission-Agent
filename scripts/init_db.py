import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.db.base import Base
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def init_database():
    """Initialize the database with all tables"""
    logger.info("Initializing database...")
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialization completed")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_database())
