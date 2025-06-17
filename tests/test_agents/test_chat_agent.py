import pytest
from app.agents.chat_agent import ChatAgent

@pytest.mark.asyncio
async def test_chat_agent_initialization():
    """Test ChatAgent initialization."""
    agent = ChatAgent()
    await agent.initialize()
    
    assert agent.llm is not None
    assert agent.embeddings is not None

@pytest.mark.asyncio
async def test_query_classification():
    """Test query classification."""
    agent = ChatAgent()
    await agent.initialize()
    
    # Test faculty search query
    result = await agent.classify_query("Find me CS professors at Stanford")
    assert "faculty" in result["classification"].lower()
    
    # Test program search query
    result = await agent.classify_query("What are the requirements for MIT PhD program?")
    assert "program" in result["classification"].lower()
    
    # Test general chat
    result = await agent.classify_query("Hello, how are you?")
    assert result["classification"] == "general_chat"

@pytest.mark.asyncio
async def test_response_generation():
    """Test response generation."""
    agent = ChatAgent()
    await agent.initialize()
    
    state = {
        "user_query": "Test query",
        "faculty_matches": [],
        "program_matches": [],
        "research_insights": [],
        "confidence_score": 0.8
    }
    
    result = await agent.generate_response(state)
    
    assert "response" in result
    assert "confidence_score" in result
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0