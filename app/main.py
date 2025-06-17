import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.api_v1.api import api_router
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.db.session import engine
from app.db.base import Base
from app.agents.workflow import STEMAdmissionsWorkflow
from app.utils.cache import init_redis

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Global workflow instance
workflow_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting STEM Graduate Admissions Assistant")
    
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis
    await init_redis()
    
    # Initialize LangGraph workflow
    global workflow_instance
    workflow_instance = STEMAdmissionsWorkflow()
    await workflow_instance.initialize()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    if workflow_instance:
        await workflow_instance.cleanup()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered STEM graduate admissions assistant",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    with open("static/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    """Serve the chat interface"""
    with open("static/chat.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

def get_workflow() -> STEMAdmissionsWorkflow:
    """Get the global workflow instance"""
    return workflow_instance

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        access_log=False,  # We handle logging in middleware
    )