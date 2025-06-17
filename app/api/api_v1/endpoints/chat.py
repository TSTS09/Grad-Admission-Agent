from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_active_user
from app.schemas.chat import ChatRequest, ChatResponse, ChatSession
from app.schemas.user import User
from app.agents.workflow import get_workflow
from app.services.chat import create_chat_session, add_message_to_session, get_user_sessions
import uuid
import json

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle chat query from user"""
    try:
        # Get workflow instance
        workflow = get_workflow()
        if not workflow:
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        
        # Create or get chat session
        if not request.session_id:
            session = await create_chat_session(db, current_user.id)
            session_id = session.session_id
        else:
            session_id = request.session_id
        
        # Add user message
        await add_message_to_session(db, session_id, "user", request.message)
        
        # Process with AI workflow
        response = await workflow.process_query(
            query=request.message,
            user_id=current_user.id,
            session_id=session_id,
            context=request.context or {}
        )
        
        # Add AI response
        await add_message_to_session(
            db, session_id, "assistant", response["response"],
            agent_type=response.get("agent_type"),
            confidence_score=response.get("confidence_score"),
            sources=response.get("sources")
        )
        
        return ChatResponse(
            response=response["response"],
            session_id=session_id,
            faculty_matches=response.get("faculty_matches", []),
            program_matches=response.get("program_matches", []),
            confidence_score=response.get("confidence_score", 0.0),
            sources=response.get("sources", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's chat sessions"""
    return await get_user_sessions(db, current_user.id)

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message (simplified - you'd want proper auth here)
            workflow = get_workflow()
            response = await workflow.process_query(
                query=message_data["message"],
                user_id=message_data.get("user_id"),
                session_id=session_id
            )
            
            # Send response back
            await websocket.send_text(json.dumps({
                "type": "response",
                "data": response
            }))
            
    except WebSocketDisconnect:
        pass
