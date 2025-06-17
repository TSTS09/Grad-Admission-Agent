from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.user import User
import uuid

async def create_chat_session(db: AsyncSession, user_id: int) -> ChatSession:
    """Create a new chat session"""
    session = ChatSession(
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        title="New Conversation"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def add_message_to_session(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    agent_type: Optional[str] = None,
    confidence_score: Optional[float] = None,
    sources: Optional[List] = None
) -> ChatMessage:
    """Add a message to a chat session"""
    # Get session
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    message = ChatMessage(
        session_id=session.id,
        role=role,
        content=content,
        agent_type=agent_type,
        confidence_score=confidence_score,
        sources=sources or []
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

async def get_user_sessions(db: AsyncSession, user_id: int) -> List[ChatSession]:
    """Get all chat sessions for a user"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .where(ChatSession.is_active == True)
        .order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()