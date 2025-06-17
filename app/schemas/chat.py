from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    faculty_matches: List[Dict[str, Any]] = []
    program_matches: List[Dict[str, Any]] = []
    confidence_score: float = 0.0
    sources: List[Dict[str, Any]] = []

class ChatMessage(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    agent_type: Optional[str] = None
    confidence_score: Optional[float] = None
    sources: Optional[List[Dict[str, Any]]] = None

class ChatSession(BaseModel):
    id: int
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    messages: List[ChatMessage] = []