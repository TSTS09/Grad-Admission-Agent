from sqlalchemy import Column, String, Integer, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="chat_sessions")
    
    session_id = Column(String, unique=True, index=True)
    title = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relations
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    session = relationship("ChatSession", back_populates="messages")
    
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # AI context
    agent_type = Column(String)  # which agent generated this
    confidence_score = Column(Float)
    sources = Column(JSON)  # Sources used for the response
    
    # Metadata
    tokens_used = Column(Integer)
    processing_time = Column(Float)