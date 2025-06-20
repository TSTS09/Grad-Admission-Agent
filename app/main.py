# app/main.py - Firebase-integrated FastAPI application
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from app.core.config import init_firebase, get_firebase
from app.agents.cost_effective_agents import ChatOrchestrator
from app.scrapers.real_university_scraper import ScrapingOrchestrator
from app.models.firebase_models import ChatSession, ChatMessage, Faculty, Program
from app.core.logging import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global instances
chat_orchestrator = None
scraping_orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting STEM Graduate Admissions Assistant (Firebase Edition)")
    
    # Initialize Firebase
    await init_firebase()
    
    # Initialize AI agents
    global chat_orchestrator, scraping_orchestrator
    chat_orchestrator = ChatOrchestrator()
    scraping_orchestrator = ScrapingOrchestrator()
    
    # Start background scraping if enabled
    if os.getenv('ENABLE_BACKGROUND_SCRAPING', 'false').lower() == 'true':
        asyncio.create_task(background_scraping_task())
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="STEM Graduate Admissions Assistant",
    version="2.0.0",
    description="AI-powered STEM graduate admissions assistant with real-time data",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency for optional authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication - returns None if no token provided"""
    if not credentials:
        return None
    # Add your auth logic here if needed
    return {"user_id": "demo_user"}

# API Routes

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    try:
        with open("static/dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Dashboard coming soon!</h1>")

@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    """Serve the chat interface"""
    try:
        with open("static/chat.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Chat interface coming soon!</h1>")

@app.post("/api/v1/chat/query")
async def chat_query(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Handle chat query"""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        session_id = request.get("session_id")
        context = request.get("context", {})
        
        # Create or get session
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            await ChatSession.create(
                session_id=session_id,
                user_id=current_user.get("user_id") if current_user else None,
                title=message[:50] + "..." if len(message) > 50 else message
            )
        
        # Save user message
        await ChatMessage.create(
            session_id=session_id,
            role="user",
            content=message
        )
        
        # Process with AI
        response_data = await chat_orchestrator.process_query(message, context)
        
        # Save AI response
        await ChatMessage.create(
            session_id=session_id,
            role="assistant",
            content=response_data["response"],
            confidence_score=response_data["confidence_score"],
            sources=response_data["sources"]
        )
        
        # Return response
        return {
            "response": response_data["response"],
            "session_id": session_id,
            "faculty_matches": response_data["faculty_matches"],
            "program_matches": response_data["program_matches"],
            "confidence_score": response_data["confidence_score"],
            "sources": response_data["sources"]
        }
        
    except Exception as e:
        logger.error(f"Chat query error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/faculty/search")
async def search_faculty(
    q: str = "",
    research_area: str = None,
    university: str = None,
    hiring_only: bool = False,
    limit: int = 20
):
    """Search faculty members"""
    try:
        firebase = get_firebase()
        
        # Build filters
        filters = [('is_active', '==', True)]
        
        if hiring_only:
            filters.append(('hiring_status', '==', 'hiring'))
        
        if university:
            filters.append(('university_name', '==', university))
        
        # Query Firebase
        results = await firebase.query_collection('faculty', filters, limit=limit)
        
        # Filter by research area if specified
        if research_area:
            filtered_results = []
            for result in results:
                if research_area.lower() in [area.lower() for area in result.get('research_areas', [])]:
                    filtered_results.append(result)
            results = filtered_results
        
        # Filter by query string if provided
        if q:
            q_lower = q.lower()
            filtered_results = []
            for result in results:
                if (q_lower in result.get('name', '').lower() or
                    any(q_lower in area.lower() for area in result.get('research_areas', []))):
                    filtered_results.append(result)
            results = filtered_results
        
        return {"faculty": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Faculty search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/v1/programs/search")
async def search_programs(
    q: str = "",
    degree_type: str = None,
    university: str = None,
    funding_only: bool = False,
    limit: int = 20
):
    """Search academic programs"""
    try:
        firebase = get_firebase()
        
        # Build filters
        filters = [('is_active', '==', True)]
        
        if degree_type:
            filters.append(('degree_type', '==', degree_type))
        
        if university:
            filters.append(('university_name', '==', university))
        
        if funding_only:
            filters.append(('funding_available', '==', True))
        
        # Query Firebase
        results = await firebase.query_collection('programs', filters, limit=limit)
        
        # Filter by query string if provided
        if q:
            q_lower = q.lower()
            filtered_results = []
            for result in results:
                if (q_lower in result.get('name', '').lower() or
                    q_lower in result.get('department', '').lower()):
                    filtered_results.append(result)
            results = filtered_results
        
        return {"programs": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Program search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/v1/universities")
async def get_universities(limit: int = 50):
    """Get list of universities"""
    try:
        firebase = get_firebase()
        filters = [('is_active', '==', True)]
        results = await firebase.query_collection('universities', filters, limit=limit)
        return {"universities": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Universities error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch universities")

@app.post("/api/v1/admin/scrape")
async def trigger_scraping(current_user: dict = Depends(get_current_user)):
    """Trigger manual scraping (admin only)"""
    try:
        # In production, add proper admin authentication
        asyncio.create_task(scraping_orchestrator.run_daily_scraping())
        return {"message": "Scraping started", "status": "success"}
    except Exception as e:
        logger.error(f"Scraping trigger error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraping")

@app.get("/api/v1/stats")
async def get_stats():
    """Get application statistics"""
    try:
        firebase = get_firebase()
        
        # Count documents in collections
        faculty_count = len(await firebase.query_collection('faculty', [('is_active', '==', True)], limit=1000))
        program_count = len(await firebase.query_collection('programs', [('is_active', '==', True)], limit=1000))
        university_count = len(await firebase.query_collection('universities', [('is_active', '==', True)], limit=1000))
        hiring_count = len(await firebase.query_collection('faculty', [('hiring_status', '==', 'hiring')], limit=1000))
        
        return {
            "faculty_count": faculty_count,
            "program_count": program_count,
            "university_count": university_count,
            "hiring_faculty_count": hiring_count,
            "last_updated": "2024-01-15T10:00:00Z"  # You can make this dynamic
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "faculty_count": 0,
            "program_count": 0,
            "university_count": 0,
            "hiring_faculty_count": 0,
            "last_updated": None
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Firebase connection
        firebase = get_firebase()
        await firebase.query_collection('universities', [], limit=1)
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "firebase": "connected",
            "timestamp": "2024-01-15T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Background tasks
async def background_scraping_task():
    """Background task for periodic scraping"""
    while True:
        try:
            logger.info("Starting background scraping")
            await scraping_orchestrator.run_daily_scraping()
            logger.info("Background scraping completed")
            
            # Wait 24 hours before next scraping
            await asyncio.sleep(24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Background scraping error: {e}")
            # Wait 1 hour before retrying on error
            await asyncio.sleep(60 * 60)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )

