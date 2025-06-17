import pytest
from httpx import AsyncClient
from app.db.models.university import University
from app.db.models.faculty import Faculty

@pytest.mark.asyncio
async def test_get_faculty_list(client: AsyncClient, db, sample_university_data, sample_faculty_data):
    """Test getting faculty list."""
    # Create university
    university = University(**sample_university_data)
    db.add(university)
    await db.commit()
    await db.refresh(university)
    
    # Create faculty
    faculty_data = sample_faculty_data.copy()
    faculty_data["university_id"] = university.id
    faculty = Faculty(**faculty_data)
    db.add(faculty)
    await db.commit()
    
    # Test API
    response = await client.get("/api/v1/faculty/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == sample_faculty_data["name"]

@pytest.mark.asyncio
async def test_get_faculty_by_id(client: AsyncClient, db, sample_university_data, sample_faculty_data):
    """Test getting faculty by ID."""
    # Create university and faculty
    university = University(**sample_university_data)
    db.add(university)
    await db.commit()
    await db.refresh(university)
    
    faculty_data = sample_faculty_data.copy()
    faculty_data["university_id"] = university.id
    faculty = Faculty(**faculty_data)
    db.add(faculty)
    await db.commit()
    await db.refresh(faculty)
    
    # Test API
    response = await client.get(f"/api/v1/faculty/{faculty.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == sample_faculty_data["name"]
    assert data["email"] == sample_faculty_data["email"]

@pytest.mark.asyncio
async def test_get_faculty_not_found(client: AsyncClient):
    """Test getting non-existent faculty."""
    response = await client.get("/api/v1/faculty/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_search_faculty_by_research_area(client: AsyncClient, db, sample_university_data, sample_faculty_data):
    """Test searching faculty by research area."""
    # Create university and faculty
    university = University(**sample_university_data)
    db.add(university)
    await db.commit()
    await db.refresh(university)
    
    faculty_data = sample_faculty_data.copy()
    faculty_data["university_id"] = university.id
    faculty = Faculty(**faculty_data)
    db.add(faculty)
    await db.commit()
    
    # Test search
    response = await client.get("/api/v1/faculty/research/Machine Learning")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1