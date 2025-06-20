# app/main.py - Real-time online data FastAPI application
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from app.agents.realtime_agents import RealTimeDataOrchestrator
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global instances
data_orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting STEM Graduate Admissions Assistant (Real-Time Edition)")
    
    # Initialize real-time data orchestrator
    global data_orchestrator
    data_orchestrator = RealTimeDataOrchestrator()
    
    logger.info("Application startup complete - ready to fetch real-time data!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="STEM Graduate Admissions Assistant",
    version="2.0.0",
    description="AI-powered STEM graduate admissions assistant with real-time online data",
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
    return {"user_id": "demo_user"}

# API Routes

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    try:
        with open("static/dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <h1>🎓 STEM Graduate Admissions Assistant</h1>
        <p>Real-time PhD admissions data and AI assistance</p>
        <a href="/chat">Start Chat</a>
        """)

@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    """Serve the chat interface"""
    try:
        with open("static/chat.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <h1>💬 AI Chat Assistant</h1>
        <p>Ask me about PhD programs, faculty, and admissions!</p>
        <textarea placeholder="Ask: 'Find ML professors at Stanford hiring for 2026'"></textarea>
        """)

@app.post("/api/v1/chat/query")
async def chat_query(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Handle chat query with real-time data fetching"""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        context = request.get("context", {})
        
        logger.info(f"Processing real-time query: {message}")
        
        # Process with real-time data orchestrator
        response_data = await data_orchestrator.process_query(message, context)
        
        # Add session ID for frontend
        import uuid
        session_id = str(uuid.uuid4())
        
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
    """Search faculty members in real-time"""
    try:
        # Build search query
        search_parts = []
        
        if q:
            search_parts.append(q)
        
        if university:
            search_parts.append(f"university: {university}")
        
        if research_area:
            search_parts.append(f"research: {research_area}")
        
        if hiring_only:
            search_parts.append("hiring PhD students")
        
        search_query = " ".join(search_parts) + " computer science faculty"
        
        # Create query info for the orchestrator
        query_info = {
            "intent": "faculty_search",
            "universities": [university] if university else [],
            "research_areas": [research_area] if research_area else [],
            "hiring_focus": hiring_only,
            "search_terms": search_parts
        }
        
        # Fetch real-time data
        response_data = await data_orchestrator._fetch_real_time_data(query_info)
        
        # Filter results based on limit
        faculty_results = response_data.get("faculty_matches", [])[:limit]
        
        return {
            "faculty": faculty_results,
            "total": len(faculty_results),
            "sources": response_data.get("sources", []),
            "timestamp": "real-time"
        }
        
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
    """Search academic programs in real-time"""
    try:
        # Build search query
        search_parts = []
        
        if q:
            search_parts.append(q)
        
        if university:
            search_parts.append(university)
        
        if degree_type:
            search_parts.append(degree_type)
        
        if funding_only:
            search_parts.append("funding available")
        
        search_query = " ".join(search_parts) + " computer science program requirements"
        
        # Create query info
        query_info = {
            "intent": "program_search",
            "universities": [university] if university else [],
            "degree_types": [degree_type] if degree_type else [],
            "search_terms": search_parts
        }
        
        # Fetch real-time data
        response_data = await data_orchestrator._fetch_real_time_data(query_info)
        
        # Filter results
        program_results = response_data.get("program_matches", [])[:limit]
        
        return {
            "programs": program_results,
            "total": len(program_results),
            "sources": response_data.get("sources", []),
            "timestamp": "real-time"
        }
        
    except Exception as e:
        logger.error(f"Program search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/v1/universities")
async def get_universities(limit: int = 50):
    """Get list of top universities (static list)"""
    try:
        # Return top CS universities
        top_universities = [
            {"name": "Stanford University", "ranking": 1, "location": "California, USA"},
            {"name": "Massachusetts Institute of Technology", "ranking": 2, "location": "Massachusetts, USA"},
            {"name": "Carnegie Mellon University", "ranking": 3, "location": "Pennsylvania, USA"},
            {"name": "University of California, Berkeley", "ranking": 4, "location": "California, USA"},
            {"name": "California Institute of Technology", "ranking": 5, "location": "California, USA"},
            {"name": "Harvard University", "ranking": 6, "location": "Massachusetts, USA"},
            {"name": "Princeton University", "ranking": 7, "location": "New Jersey, USA"},
            {"name": "University of Toronto", "ranking": 15, "location": "Ontario, Canada"},
            {"name": "ETH Zurich", "ranking": 8, "location": "Zurich, Switzerland"},
            {"name": "University of Oxford", "ranking": 5, "location": "Oxford, UK"},
        ]
        
        return {
            "universities": top_universities[:limit],
            "total": len(top_universities),
            "note": "For real-time faculty data, use the faculty search endpoint"
        }
        
    except Exception as e:
        logger.error(f"Universities error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch universities")

@app.get("/api/v1/stats")
async def get_stats():
    """Get application statistics (estimated)"""
    try:
        return {
            "faculty_count": "1000+",
            "program_count": "500+", 
            "university_count": 200,
            "hiring_faculty_count": "Real-time data",
            "last_updated": "Live data",
            "data_sources": [
                "University websites",
                "Tavily search API",
                "Social media monitoring",
                "Direct faculty pages"
            ]
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "faculty_count": "Unknown",
            "program_count": "Unknown",
            "university_count": 0,
            "hiring_faculty_count": "Unknown",
            "last_updated": "Error"
        }

@app.get("/api/v1/test-search")
async def test_search(query: str = "Stanford machine learning professors"):
    """Test endpoint to verify real-time search is working"""
    try:
        logger.info(f"Testing search with query: {query}")
        
        # Test the orchestrator directly
        response = await data_orchestrator.process_query(query)
        
        return {
            "query": query,
            "response": response["response"],
            "faculty_found": len(response["faculty_matches"]),
            "programs_found": len(response["program_matches"]),
            "sources_used": len(response["sources"]),
            "confidence": response["confidence_score"]
        }
        
    except Exception as e:
        logger.error(f"Test search error: {e}")
        return {
            "query": query,
            "error": str(e),
            "status": "failed"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test if we can make API calls
        api_status = "OK" if settings.OPENAI_API_KEY else "Missing OpenAI API key"
        tavily_status = "OK" if settings.TAVILY_API_KEY else "Missing Tavily API key"
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "mode": "real-time-online-data",
            "openai": api_status,
            "tavily": tavily_status,
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

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