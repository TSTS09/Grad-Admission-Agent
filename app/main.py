# app/main.py - Intelligent Web Scraping with Gemini API
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from app.agents.intelligent_scraper import IntelligentScrapingAgent
from app.core.logging import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global agent
scraping_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Intelligent Grad Admissions Scraping Assistant with Gemini")
    
    # Get Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set!")
        raise ValueError("Gemini API key is required")
    
    # Initialize intelligent scraping agent
    global scraping_agent
    scraping_agent = IntelligentScrapingAgent(gemini_api_key)
    
    logger.info("✅ Intelligent scraping agent with Gemini initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="Intelligent Grad Admissions Assistant",
    version="1.0.0",
    description="AI-powered web scraping with Google Gemini for PhD and Master's admission information",
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

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    try:
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligent Grad Admissions Assistant - Powered by Gemini</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #4285f4 0%, #34a853 100%); min-height: 100vh; }
        
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .header .powered-by { font-size: 0.9rem; margin-top: 10px; background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 15px; display: inline-block; }
        
        .main-card { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        
        .search-section { margin-bottom: 30px; }
        .search-section h2 { margin-bottom: 20px; color: #333; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-box input { flex: 1; padding: 15px; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px; }
        .search-box button { padding: 15px 30px; background: #4285f4; color: white; border: none; border-radius: 10px; cursor: pointer; font-weight: 600; }
        .search-box button:hover { background: #3367d6; }
        
        .examples { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .example { padding: 15px; background: #f8f9fa; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
        .example:hover { background: #e8f0fe; transform: translateY(-2px); }
        .example h4 { color: #4285f4; margin-bottom: 5px; }
        .example p { color: #666; font-size: 14px; }
        
        .results-section { margin-top: 30px; }
        .loading { text-align: center; padding: 40px; color: #4285f4; }
        .loading::before { content: '🤖'; font-size: 2rem; display: block; margin-bottom: 10px; }
        .result-item { margin: 20px 0; padding: 25px; border: 1px solid #e1e5e9; border-radius: 10px; }
        .result-item h3 { color: #333; margin-bottom: 15px; display: flex; align-items: center; }
        .result-item h3::before { content: '🧠'; margin-right: 10px; }
        .result-item p { color: #666; line-height: 1.6; }
        .source-links { margin-top: 15px; }
        .source-link { display: inline-block; margin: 5px 5px 5px 0; padding: 5px 10px; background: #e8f0fe; border-radius: 5px; text-decoration: none; color: #4285f4; font-size: 12px; }
        .source-link:hover { background: #d2e3fc; }
        
        .history-section { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e1e5e9; }
        .history-item { padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; cursor: pointer; }
        .history-item:hover { background: #e8f0fe; }
        .history-query { font-weight: 600; color: #333; }
        .history-meta { font-size: 12px; color: #666; margin-top: 5px; }
        
        .gemini-badge { position: fixed; bottom: 20px; right: 20px; background: #4285f4; color: white; padding: 10px 15px; border-radius: 20px; font-size: 12px; z-index: 1000; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Intelligent Grad Admissions Assistant</h1>
            <p>AI-powered web scraping for PhD and Master's program information</p>
            <div class="powered-by">Powered by Google Gemini AI</div>
        </div>
        
        <div class="main-card">
            <div class="search-section">
                <h2>Ask anything about PhD or Master's admissions</h2>
                <div class="search-box">
                    <input type="text" id="queryInput" placeholder="e.g., What are the PhD requirements for computer science at Stanford?" />
                    <button onclick="performSearch()">Search with Gemini</button>
                </div>
                
                <div class="examples">
                    <div class="example" onclick="setQuery('What are the PhD admission requirements for MIT computer science?')">
                        <h4>📚 PhD Requirements</h4>
                        <p>Find specific admission requirements for PhD programs</p>
                    </div>
                    <div class="example" onclick="setQuery('Stanford master in AI program details and deadlines')">
                        <h4>⏰ Program Details</h4>
                        <p>Get program information and application deadlines</p>
                    </div>
                    <div class="example" onclick="setQuery('Berkeley EECS graduate program funding opportunities')">
                        <h4>💰 Funding Info</h4>
                        <p>Find funding and financial aid information</p>
                    </div>
                    <div class="example" onclick="setQuery('How to contact professors for PhD positions in machine learning')">
                        <h4>👨‍🏫 Faculty Contact</h4>
                        <p>Learn how to reach out to potential advisors</p>
                    </div>
                </div>
            </div>
            
            <div class="results-section" id="results" style="display: none;">
                <h3>Gemini AI Analysis</h3>
                <div id="resultsContent"></div>
            </div>
            
            <div class="history-section" id="historySection" style="display: none;">
                <h3>Recent Searches</h3>
                <div id="historyContent"></div>
            </div>
        </div>
    </div>

    <div class="gemini-badge">🤖 Gemini AI</div>

    <script>
        async function performSearch() {
            const query = document.getElementById('queryInput').value.trim();
            if (!query) return;
            
            const resultsSection = document.getElementById('results');
            const resultsContent = document.getElementById('resultsContent');
            
            // Show loading
            resultsSection.style.display = 'block';
            resultsContent.innerHTML = '<div class="loading">Gemini AI is analyzing your query and searching websites...</div>';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                displayResults(data);
                loadHistory();
                
            } catch (error) {
                resultsContent.innerHTML = `<div class="result-item"><h3>Error</h3><p>Failed to search: ${error.message}</p></div>`;
            }
        }
        
        function displayResults(data) {
            const resultsContent = document.getElementById('resultsContent');
            
            if (!data.response) {
                resultsContent.innerHTML = '<div class="result-item"><h3>No results</h3><p>No information found for your query.</p></div>';
                return;
            }
            
            let html = `
                <div class="result-item">
                    <h3>Gemini AI Analysis</h3>
                    <div style="white-space: pre-line;">${data.response}</div>
                    
                    ${data.source_links && data.source_links.length > 0 ? `
                        <div class="source-links">
                            <strong>🔗 Sources:</strong><br>
                            ${data.source_links.map(link => `<a href="${link}" target="_blank" class="source-link">${new URL(link).hostname}</a>`).join('')}
                        </div>
                    ` : ''}
                    
                    <div style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-radius: 5px; font-size: 12px; color: #666;">
                        🎯 Confidence: ${Math.round((data.confidence || 0) * 100)}% • 
                        📊 Sources: ${data.total_sources || 0} • 
                        🤖 Powered by Gemini AI
                    </div>
                </div>
            `;
            
            resultsContent.innerHTML = html;
        }
        
        function setQuery(query) {
            document.getElementById('queryInput').value = query;
            performSearch();
        }
        
        async function loadHistory() {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                
                if (data.history && data.history.length > 0) {
                    const historySection = document.getElementById('historySection');
                    const historyContent = document.getElementById('historyContent');
                    
                    historySection.style.display = 'block';
                    historyContent.innerHTML = data.history.map(item => `
                        <div class="history-item" onclick="setQuery('${item.user_query.replace(/'/g, "\\'").replace(/"/g, '&quot;')}')">
                            <div class="history-query">${item.user_query}</div>
                            <div class="history-meta">${item.search_timestamp} • Confidence: ${Math.round((item.confidence_score || 0) * 100)}%</div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Failed to load history:', error);
            }
        }
        
        // Handle Enter key
        document.getElementById('queryInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });
        
        // Load history on page load
        document.addEventListener('DOMContentLoaded', loadHistory);
    </script>
</body>
</html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return HTMLResponse(f"<h1>Error: {e}</h1>")

@app.post("/api/search")
async def search_information(request: dict):
    """Main search endpoint - handles any query about grad admissions"""
    try:
        query = request.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f"Processing search query with Gemini: {query}")
        
        # Use intelligent scraping agent with Gemini
        result = await scraping_agent.process_query(query)
        
        return result
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/history")
async def get_search_history():
    """Get recent search history"""
    try:
        history = scraping_agent.get_search_history(limit=5)
        return {"history": history}
        
    except Exception as e:
        logger.error(f"History error: {e}")
        return {"history": []}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "version": "1.0.0",
            "ai_provider": "Google Gemini",
            "features": [
                "Intelligent web scraping",
                "Gemini-powered analysis",
                "Real-time information extraction",
                "Source link compilation"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )