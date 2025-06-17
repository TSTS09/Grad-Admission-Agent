import pytest
from httpx import AsyncClient
from app.db.models.user import User

@pytest.mark.asyncio
async def test_chat_query_unauthorized(client: AsyncClient):
    """Test chat query without authentication."""
    response = await client.post(
        "/api/v1/chat/query",
        json={"message": "Hello"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_chat_query_success(client: AsyncClient, db, sample_user_data):
    """Test successful chat query."""
    # Create a test user first
    from app.core.security import get_password_hash
    
    user = User(
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"]),
        full_name=sample_user_data["full_name"],
        research_interests=sample_user_data["research_interests"]
    )
    db.add(user)
    await db.commit()
    
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Test chat query
    response = await client.post(
        "/api/v1/chat/query",
        json={"message": "Find me CS professors at Stanford"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert isinstance(data["faculty_matches"], list)

@pytest.mark.asyncio
async def test_chat_empty_message(client: AsyncClient, db, sample_user_data):
    """Test chat with empty message."""
    # Setup user and get token (similar to above)
    from app.core.security import get_password_hash
    
    user = User(
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"]),
        full_name=sample_user_data["full_name"]
    )
    db.add(user)
    await db.commit()
    
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Test empty message
    response = await client.post(
        "/api/v1/chat/query",
        json={"message": ""},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422  # Validation error
