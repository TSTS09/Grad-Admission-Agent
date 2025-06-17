import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.db.base import Base
from app.core.config import settings

# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestingSessionLocal() as session:
        yield session
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    
    async def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_university_data():
    """Sample university data for testing."""
    return {
        "name": "Test University",
        "short_name": "TU",
        "country": "USA",
        "state_province": "California",
        "city": "Test City",
        "cs_ranking": 10,
        "website_url": "https://test.edu"
    }

@pytest.fixture
def sample_faculty_data():
    """Sample faculty data for testing."""
    return {
        "name": "Dr. Test Professor",
        "email": "test@test.edu",
        "title": "Professor",
        "department": "Computer Science",
        "research_areas": ["Machine Learning", "AI"],
        "hiring_status": "hiring",
        "hiring_probability": 0.8
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "research_interests": ["Machine Learning"],
        "target_universities": [1],
        "academic_background": {
            "degree": "BS",
            "major": "Computer Science",
            "gpa": 3.8
        }
    }
