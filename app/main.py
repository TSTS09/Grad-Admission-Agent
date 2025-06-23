# app/main.py - Updated with Real-Time Scraping System

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime

from app.agents.realtime_intelligence_agent import EnhancedChatAgent
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.firebase_config import init_firebase

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global chat agent
enhanced_chat_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting Real-Time Graduate Admissions Intelligence System")
    
    # Validate required API keys
    required_keys = ["GEMINI_API_KEY"]
    missing_keys = [key for key in required_keys if not getattr(settings, key, None)]
    
    if missing_keys:
        logger.error(f"❌ Missing required API keys: {missing_keys}")
        raise ValueError(f"Missing API keys: {missing_keys}")
    
    # Initialize Firebase (optional)
    try:
        await init_firebase()
        logger.info("✅ Firebase initialized")
    except Exception as e:
        logger.warning(f"⚠️ Firebase initialization failed: {e}")
    
    # Initialize enhanced chat agent with real-time scraping
    global enhanced_chat_agent
    enhanced_chat_agent = EnhancedChatAgent()
    
    logger.info("✅ Real-time intelligence agent initialized")
    logger.info("🌐 System ready for dynamic web scraping")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="Graduate Admissions Intelligence System",
    version="2.0.0",
    description="Real-time web scraping and AI-powered graduate admissions intelligence",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    context: dict = {}

class ChatResponse(BaseModel):
    response: str
    session_id: str
    faculty_matches: list = []
    program_matches: list = []
    key_insights: list = []
    confidence_score: float = 0.0
    sources: list = []
    data_sources_count: int = 0
    last_updated: str = ""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the enhanced dashboard with real-time capabilities"""
    try:
        with open("static/dashboard.html", "r") as f:
            html_content = f.read()
        
        # Update the HTML to show real-time capabilities
        updated_html = html_content.replace(
            "AI-powered admissions guide", 
            "Real-time AI intelligence with live web scraping"
        )
        
        return HTMLResponse(content=updated_html)
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Graduate Admissions Intelligence</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .container { max-width: 800px; margin: 0 auto; text-align: center; }
                .card { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin: 20px 0; }
                .btn { background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }
                .feature { background: rgba(255,255,255,0.05); padding: 20px; margin: 10px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎓 Graduate Admissions Intelligence System</h1>
                <div class="card">
                    <h2>Real-Time Web Scraping & AI Analysis</h2>
                    <p>Dynamic intelligence for PhD and Master's applications with live data from universities, Reddit, Twitter, and academic forums.</p>
                    <a href="/chat" class="btn">Start Chat Intelligence</a>
                    <a href="/api/v1/docs" class="btn">API Documentation</a>
                </div>
                
                <div class="feature">
                    <h3>🔍 Real-Time Data Sources</h3>
                    <p>• University websites and faculty pages<br>
                    • Reddit graduate admissions discussions<br>
                    • Twitter academic announcements<br>
                    • Academic job boards and forums</p>
                </div>
                
                <div class="feature">
                    <h3>🤖 AI-Powered Analysis</h3>
                    <p>• Faculty hiring status detection<br>
                    • Program requirement extraction<br>
                    • Application deadline tracking<br>
                    • Personalized advice generation</p>
                </div>
                
                <div class="feature">
                    <h3>📊 Live Intelligence</h3>
                    <p>• No hardcoded data - everything scraped in real-time<br>
                    • Query-driven research based on your specific needs<br>
                    • Multiple source verification and confidence scoring</p>
                </div>
            </div>
        </body>
        </html>
        """)

@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    """Serve the chat interface"""
    try:
        with open("static/chat.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat - Graduate Admissions Intelligence</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; }
                .chat-container { max-width: 800px; margin: 0 auto; padding: 20px; height: 100vh; display: flex; flex-direction: column; }
                .chat-header { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px 15px 0 0; }
                .chat-messages { flex: 1; background: rgba(255,255,255,0.05); padding: 20px; overflow-y: auto; }
                .chat-input { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 0 0 15px 15px; display: flex; gap: 10px; }
                .chat-input input { flex: 1; padding: 10px; border: none; border-radius: 5px; }
                .chat-input button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
                .message { margin: 10px 0; padding: 10px; border-radius: 10px; }
                .user { background: rgba(255,255,255,0.2); text-align: right; }
                .assistant { background: rgba(255,255,255,0.1); }
                h1, h2, p { color: white; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">
                    <h1>🎓 Graduate Admissions Chat Intelligence</h1>
                    <p>Ask me anything about graduate admissions. I'll scrape real-time data to give you current information.</p>
                </div>
                <div class="chat-messages" id="messages">
                    <div class="message assistant">
                        <strong>🤖 Assistant:</strong> Hello! I can help you with real-time graduate admissions intelligence. Try asking:
                        <br>• "Which CS professors at Stanford are hiring PhD students?"
                        <br>• "What are the latest discussions about MIT EECS PhD admissions?"
                        <br>• "Tell me about recent faculty hiring at top ML programs"
                    </div>
                </div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="Ask about graduate admissions..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <script>
                async function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    const messagesDiv = document.getElementById('messages');
                    
                    // Add user message
                    messagesDiv.innerHTML += `<div class="message user"><strong>You:</strong> ${message}</div>`;
                    
                    // Add loading message
                    messagesDiv.innerHTML += `<div class="message assistant" id="loading"><strong>🤖 Assistant:</strong> 🔍 Scraping real-time data and analyzing...</div>`;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    
                    input.value = '';
                    
                    try {
                        const response = await fetch('/api/v1/chat/query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message: message })
                        });
                        
                        const data = await response.json();
                        
                        // Remove loading message
                        document.getElementById('loading').remove();
                        
                        // Add response
                        let responseHtml = `<div class="message assistant"><strong>🤖 Assistant:</strong> ${data.response}`;
                        
                        if (data.key_insights && data.key_insights.length > 0) {
                            responseHtml += `<br><br><strong>🔍 Key Insights:</strong><br>`;
                            data.key_insights.forEach(insight => {
                                responseHtml += `• ${insight}<br>`;
                            });
                        }
                        
                        if (data.sources && data.sources.length > 0) {
                            responseHtml += `<br><br><strong>📚 Sources (${data.sources.length}):</strong> Real-time data from universities, Reddit, Twitter, and academic forums`;
                        }
                        
                        responseHtml += `<br><br><small>Confidence: ${(data.confidence_score * 100).toFixed(0)}% | Sources: ${data.data_sources_count} | Updated: ${new Date().toLocaleTimeString()}</small></div>`;
                        
                        messagesDiv.innerHTML += responseHtml;
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        
                    } catch (error) {
                        document.getElementById('loading').remove();
                        messagesDiv.innerHTML += `<div class="message assistant"><strong>🤖 Assistant:</strong> Sorry, I encountered an error while scraping data. Please try again.</div>`;
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    }
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
            </script>
        </body>
        </html>
        """)

@app.post("/api/v1/chat/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """Main chat endpoint with real-time web scraping"""
    
    if not enhanced_chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")
    
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing real-time query: {request.message}")
        
        # Process with real-time scraping
        result = await enhanced_chat_agent.process_message(
            message=request.message,
            session_id=request.session_id
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query processed in {processing_time:.2f}s with {result.get('data_sources_count', 0)} sources")
        
        return ChatResponse(
            response=result.get("response", ""),
            session_id=result.get("session_id", ""),
            faculty_matches=result.get("faculty_matches", []),
            program_matches=result.get("program_matches", []),
            key_insights=result.get("key_insights", []),
            confidence_score=result.get("confidence_score", 0.0),
            sources=result.get("sources", []),
            data_sources_count=result.get("data_sources_count", 0),
            last_updated=result.get("last_updated", datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Error in chat query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    """Enhanced health check with scraping capabilities"""
    
    try:
        health_info = {
            "status": "healthy",
            "version": "2.0.0",
            "features": [
                "Real-time web scraping",
                "Multi-source intelligence (Reddit, Twitter, Universities)",
                "AI-powered synthesis with Gemini",
                "Dynamic query-based research"
            ],
            "capabilities": {
                "reddit_scraping": hasattr(settings, 'REDDIT_CLIENT_ID') and settings.REDDIT_CLIENT_ID,
                "twitter_scraping": hasattr(settings, 'TWITTER_BEARER_TOKEN') and settings.TWITTER_BEARER_TOKEN,
                "google_search": hasattr(settings, 'SERPAPI_KEY') and settings.SERPAPI_KEY,
                "gemini_ai": hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/api/v1/test-scraping")
async def test_scraping():
    """Test endpoint to verify scraping capabilities"""
    
    if not enhanced_chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")
    
    try:
        # Test with a simple query
        test_result = await enhanced_chat_agent.process_message(
            "Test query: CS PhD programs at Stanford"
        )
        
        return {
            "status": "success",
            "sources_found": test_result.get("data_sources_count", 0),
            "response_preview": test_result.get("response", "")[:200] + "...",
            "confidence": test_result.get("confidence_score", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Scraping test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping test failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )