# app/main.py - Real-time application with actual data and HuggingFace AI
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer
import uvicorn

from app.agents.real_ai_agent import RealDataAIAgent
from app.core.logging import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global instances
ai_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting STEM Graduate Admissions Assistant (REAL DATA EDITION)")
    
    # Initialize real AI agent
    global ai_agent
    ai_agent = RealDataAIAgent()
    
    logger.info("✅ Real data AI agent initialized - ready to scrape university websites!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="STEM Graduate Admissions Assistant",
    version="3.0.0",
    description="Real university data with HuggingFace AI - No dummy data!",
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

# Security
security = HTTPBearer(auto_error=False)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard with search history"""
    try:
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STEM Grad Assistant - Real Data Dashboard</title>
    <link rel="stylesheet" href="/static/css/dashboard.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="real-data-container">
        <header class="real-header">
            <h1>🎓 STEM Graduate Admissions Assistant</h1>
            <p class="subtitle">Real university data • Live web scraping • Your search history</p>
            <div class="status-badge">
                <span class="status-dot"></span>
                REAL DATA MODE - NO DUMMY INFORMATION
            </div>
        </header>

        <div class="main-grid">
            <!-- Search Section -->
            <div class="search-section">
                <h2>🔍 Search Real University Data</h2>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="e.g., 'Stanford machine learning professors'" />
                    <button id="searchBtn" onclick="performSearch()">Search</button>
                </div>
                <div class="search-suggestions">
                    <h3>Try searching for:</h3>
                    <div class="suggestion-chips">
                        <span class="chip" onclick="setSearch('Stanford computer science faculty')">Stanford CS Faculty</span>
                        <span class="chip" onclick="setSearch('MIT PhD requirements')">MIT PhD Requirements</span>
                        <span class="chip" onclick="setSearch('Berkeley machine learning professors')">Berkeley ML Professors</span>
                        <span class="chip" onclick="setSearch('CMU robotics faculty')">CMU Robotics Faculty</span>
                    </div>
                </div>
            </div>

            <!-- Search History -->
            <div class="history-section">
                <h2>📚 Your Search History</h2>
                <div id="searchHistory" class="history-list">
                    <div class="no-history">
                        <p>No previous searches yet.</p>
                        <p>Start by searching for professors or programs above!</p>
                    </div>
                </div>
            </div>

            <!-- Results Section -->
            <div class="results-section">
                <h2>📊 Latest Results</h2>
                <div id="searchResults" class="results-container">
                    <div class="no-results">
                        <h3>Welcome to Real Data Mode!</h3>
                        <p>This platform scrapes actual university websites for real professor and program information.</p>
                        <ul>
                            <li>✅ No dummy/fake data</li>
                            <li>✅ Real faculty information</li>
                            <li>✅ Live web scraping</li>
                            <li>✅ Search history tracking</li>
                            <li>✅ HuggingFace AI (no paid APIs needed)</li>
                        </ul>
                        <button onclick="window.location.href='/chat'" class="chat-btn">
                            💬 Start AI Chat
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <style>
        .real-data-container { max-width: 1200px; margin: 0 auto; padding: 20px; font-family: 'Inter', sans-serif; }
        .real-header { text-align: center; margin-bottom: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; }
        .real-header h1 { margin: 0; font-size: 2.5rem; }
        .subtitle { margin: 10px 0; opacity: 0.9; }
        .status-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; margin-top: 15px; }
        .status-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        .search-section, .history-section, .results-section { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .results-section { grid-column: 1 / -1; }
        
        .search-box { display: flex; gap: 10px; margin: 15px 0; }
        .search-box input { flex: 1; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px; }
        .search-box button { padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; }
        .search-box button:hover { background: #5a6fd8; }
        
        .suggestion-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .chip { background: #f3f4f6; padding: 6px 12px; border-radius: 16px; font-size: 12px; cursor: pointer; transition: all 0.2s; }
        .chip:hover { background: #667eea; color: white; }
        
        .history-list, .results-container { min-height: 200px; }
        .no-history, .no-results { text-align: center; padding: 40px 20px; color: #6b7280; }
        .no-results h3 { color: #1f2937; margin-bottom: 15px; }
        .no-results ul { text-align: left; max-width: 300px; margin: 20px auto; }
        .no-results li { margin: 8px 0; color: #10b981; }
        .chat-btn { background: #10b981; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; margin-top: 20px; }
        .chat-btn:hover { background: #059669; }
        
        .faculty-result { border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .faculty-result h4 { margin: 0 0 8px 0; color: #1f2937; }
        .faculty-result .university { color: #667eea; font-weight: 500; }
        .faculty-result .research { color: #6b7280; font-size: 14px; margin: 5px 0; }
        .faculty-result .email { color: #10b981; font-size: 12px; }
        
        .history-item { padding: 10px; border-left: 3px solid #667eea; margin: 10px 0; background: #f9fafb; border-radius: 0 8px 8px 0; cursor: pointer; }
        .history-item:hover { background: #f3f4f6; }
        .history-item .query { font-weight: 500; }
        .history-item .details { font-size: 12px; color: #6b7280; margin-top: 5px; }
    </style>

    <script>
        let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        
        function setSearch(query) {
            document.getElementById('searchInput').value = query;
            performSearch();
        }
        
        async function performSearch() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;
            
            // Show loading
            document.getElementById('searchResults').innerHTML = '<div class="loading">🔍 Searching real university websites...</div>';
            
            try {
                const response = await fetch('/api/v1/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                
                // Update search history
                addToHistory(query, data);
                
                // Display results
                displayResults(data);
                
            } catch (error) {
                document.getElementById('searchResults').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
            }
        }
        
        function addToHistory(query, data) {
            const historyItem = {
                query: query,
                timestamp: new Date().toISOString(),
                facultyCount: data.faculty_matches?.length || 0,
                programCount: data.program_matches?.length || 0
            };
            
            searchHistory.unshift(historyItem);
            searchHistory = searchHistory.slice(0, 10); // Keep only last 10
            localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
            
            updateHistoryDisplay();
        }
        
        function updateHistoryDisplay() {
            const historyContainer = document.getElementById('searchHistory');
            
            if (searchHistory.length === 0) {
                historyContainer.innerHTML = '<div class="no-history"><p>No previous searches yet.</p></div>';
                return;
            }
            
            historyContainer.innerHTML = searchHistory.map(item => `
                <div class="history-item" onclick="setSearch('${item.query}')">
                    <div class="query">${item.query}</div>
                    <div class="details">
                        ${item.facultyCount} faculty, ${item.programCount} programs • 
                        ${new Date(item.timestamp).toLocaleDateString()}
                    </div>
                </div>
            `).join('');
        }
        
        function displayResults(data) {
            const resultsContainer = document.getElementById('searchResults');
            
            if (!data.faculty_matches?.length && !data.program_matches?.length) {
                resultsContainer.innerHTML = `
                    <div class="no-results">
                        <h3>No results found</h3>
                        <p>${data.response || 'Try a different search term or university name.'}</p>
                    </div>
                `;
                return;
            }
            
            let html = '<h3>🎓 Search Results</h3>';
            
            if (data.faculty_matches?.length) {
                html += '<h4>Faculty Members:</h4>';
                data.faculty_matches.forEach(faculty => {
                    html += `
                        <div class="faculty-result">
                            <h4>${faculty.name}</h4>
                            <div class="university">${faculty.university}</div>
                            <div class="research">Research: ${faculty.research_areas?.join(', ') || 'Various areas'}</div>
                            ${faculty.email ? `<div class="email">📧 ${faculty.email}</div>` : ''}
                            ${faculty.from_history ? '<div class="badge">From your search history</div>' : '<div class="badge">Fresh from university website</div>'}
                        </div>
                    `;
                });
            }
            
            if (data.program_matches?.length) {
                html += '<h4>Programs:</h4>';
                data.program_matches.forEach(program => {
                    html += `
                        <div class="faculty-result">
                            <h4>${program.name}</h4>
                            <div class="university">${program.university}</div>
                            <div class="research">Degree: ${program.degree_type}</div>
                        </div>
                    `;
                });
            }
            
            if (data.response) {
                html += `<div class="ai-response"><h4>💡 AI Analysis:</h4><p>${data.response.replace(/\\n/g, '<br>')}</p></div>`;
            }
            
            resultsContainer.innerHTML = html;
        }
        
        // Handle Enter key
        document.addEventListener('DOMContentLoaded', () => {
            updateHistoryDisplay();
            document.getElementById('searchInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') performSearch();
            });
        });
    </script>
</body>
</html>
        """
        return HTMLResponse(content=dashboard_html)
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return HTMLResponse(f"<h1>Error loading dashboard: {e}</h1>")

@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    """Serve the chat interface"""
    try:
        chat_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STEM Grad Assistant - Real AI Chat</title>
    <link rel="stylesheet" href="/static/css/chat.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="chat-container">
        <header class="chat-header">
            <div class="header-left">
                <button class="back-btn" onclick="window.location.href='/'">←</button>
                <div class="chat-title">
                    <h1>🎓 STEM Grad Assistant</h1>
                    <p>Real Data • HuggingFace AI • No Dummy Information</p>
                </div>
            </div>
            <div class="header-right">
                <div class="status-indicator">
                    <div class="status-dot online"></div>
                    <span>Real Data Mode</span>
                </div>
            </div>
        </header>

        <div class="chat-messages" id="chatMessages">
            <!-- Welcome message -->
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="message-text">
                        👋 Welcome to the REAL DATA version! I scrape actual university websites and use HuggingFace AI. 
                        No more dummy data - ask me about real professors, programs, and requirements!
                    </div>
                    <div class="quick-actions">
                        <button class="quick-action" onclick="sendQuickMessage('Find machine learning professors at Stanford')">
                            🔬 Stanford ML Faculty
                        </button>
                        <button class="quick-action" onclick="sendQuickMessage('What are PhD requirements at MIT?')">
                            📚 MIT PhD Requirements
                        </button>
                        <button class="quick-action" onclick="sendQuickMessage('Show me Berkeley computer vision professors')">
                            👁️ Berkeley CV Faculty
                        </button>
                        <button class="quick-action" onclick="sendQuickMessage('Show my search history')">
                            📜 My Search History
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <div class="input-container">
                    <textarea id="messageInput" placeholder="Ask about real professors and programs..." rows="1" onkeydown="handleKeyPress(event)" oninput="autoResize(this)"></textarea>
                </div>
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
            </div>
        </div>
    </div>

    <template id="typingTemplate">
        <div class="message assistant typing">
            <div class="message-avatar">🤖</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    </template>

    <script>
        class RealChatInterface {
            constructor() {
                this.messages = [];
                this.isTyping = false;
            }

            async sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (!message || this.isTyping) return;

                input.value = '';
                input.style.height = 'auto';

                this.addMessage('user', message);
                this.showTypingIndicator();
                
                try {
                    const response = await fetch('/api/v1/chat/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message })
                    });
                    
                    const data = await response.json();
                    
                    this.hideTypingIndicator();
                    this.addMessage('assistant', data.response, {
                        facultyMatches: data.faculty_matches || [],
                        programMatches: data.program_matches || [],
                        searchHistory: data.search_history || []
                    });
                    
                } catch (error) {
                    this.hideTypingIndicator();
                    this.addMessage('assistant', 'Error connecting to server. Please try again.');
                    console.error('Chat error:', error);
                }
            }

            sendQuickMessage(message) {
                document.getElementById('messageInput').value = message;
                this.sendMessage();
            }

            addMessage(role, content, data = {}) {
                const messagesContainer = document.getElementById('chatMessages');
                const messageElement = this.createMessageElement(role, content, data);
                
                messagesContainer.appendChild(messageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                this.messages.push({ role, content, data, timestamp: new Date() });
            }

            createMessageElement(role, content, data = {}) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;
                
                const avatar = role === 'user' ? '👤' : '🤖';
                
                let messageContent = content.replace(/\\n/g, '<br>');
                
                messageDiv.innerHTML = `
                    <div class="message-avatar">${avatar}</div>
                    <div class="message-content">
                        <div class="message-text">${messageContent}</div>
                        ${data.facultyMatches ? this.createFacultyWidget(data.facultyMatches) : ''}
                        ${data.programMatches ? this.createProgramWidget(data.programMatches) : ''}
                        ${data.searchHistory ? this.createHistoryWidget(data.searchHistory) : ''}
                    </div>
                `;
                
                return messageDiv;
            }

            createFacultyWidget(facultyMatches) {
                if (!facultyMatches || facultyMatches.length === 0) return '';
                
                let html = `
                    <div class="data-widget faculty-widget">
                        <div class="widget-header">
                            <span class="widget-icon">👨‍🎓</span>
                            <span class="widget-title">Faculty Found (${facultyMatches.length})</span>
                        </div>
                        <div class="widget-content">
                `;
                
                facultyMatches.slice(0, 3).forEach(faculty => {
                    const areas = faculty.research_areas?.join(', ') || 'Various areas';
                    const fromHistory = faculty.from_history ? '📚 (From history)' : '🌐 (Fresh data)';
                    
                    html += `
                        <div class="faculty-match-item">
                            <div class="faculty-info">
                                <strong>${faculty.name}</strong><br>
                                <small>${faculty.university} • ${areas}</small><br>
                                <small>${fromHistory}</small>
                                ${faculty.email ? `<br><small>📧 ${faculty.email}</small>` : ''}
                            </div>
                        </div>
                    `;
                });
                
                if (facultyMatches.length > 3) {
                    html += `<div class="view-more">+${facultyMatches.length - 3} more faculty members</div>`;
                }
                
                html += '</div></div>';
                return html;
            }

            createProgramWidget(programMatches) {
                if (!programMatches || programMatches.length === 0) return '';
                
                let html = `
                    <div class="data-widget program-widget">
                        <div class="widget-header">
                            <span class="widget-icon">🎓</span>
                            <span class="widget-title">Programs Found (${programMatches.length})</span>
                        </div>
                        <div class="widget-content">
                `;
                
                programMatches.forEach(program => {
                    html += `
                        <div class="program-match-item">
                            <div class="program-info">
                                <strong>${program.name}</strong><br>
                                <small>${program.university} • ${program.degree_type}</small>
                            </div>
                        </div>
                    `;
                });
                
                html += '</div></div>';
                return html;
            }

            createHistoryWidget(searchHistory) {
                if (!searchHistory || searchHistory.length === 0) return '';
                
                let html = `
                    <div class="data-widget history-widget">
                        <div class="widget-header">
                            <span class="widget-icon">📚</span>
                            <span class="widget-title">Recent Searches</span>
                        </div>
                        <div class="widget-content">
                `;
                
                searchHistory.slice(0, 3).forEach(item => {
                    html += `
                        <div class="history-match-item" onclick="chatInterface.sendQuickMessage('${item.query}')">
                            <div class="history-info">
                                <strong>${item.query}</strong><br>
                                <small>${item.count} results • ${item.last_search}</small>
                            </div>
                        </div>
                    `;
                });
                
                html += '</div></div>';
                return html;
            }

            showTypingIndicator() {
                this.isTyping = true;
                const messagesContainer = document.getElementById('chatMessages');
                
                const typingTemplate = document.getElementById('typingTemplate');
                const typingElement = typingTemplate.content.cloneNode(true);
                typingElement.querySelector('.message').id = 'typingIndicator';
                
                messagesContainer.appendChild(typingElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            hideTypingIndicator() {
                this.isTyping = false;
                const typingIndicator = document.getElementById('typingIndicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
            }

            handleKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.sendMessage();
                }
            }

            autoResize(textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            }
        }

        // Global functions
        function sendQuickMessage(message) {
            chatInterface.sendQuickMessage(message);
        }

        function handleKeyPress(event) {
            chatInterface.handleKeyPress(event);
        }

        function autoResize(textarea) {
            chatInterface.autoResize(textarea);
        }

        function sendMessage() {
            chatInterface.sendMessage();
        }

        // Initialize
        let chatInterface;
        document.addEventListener('DOMContentLoaded', () => {
            chatInterface = new RealChatInterface();
        });
    </script>
</body>
</html>
        """
        return HTMLResponse(content=chat_html)
    except Exception as e:
        logger.error(f"Error serving chat: {e}")
        return HTMLResponse(f"<h1>Error loading chat: {e}</h1>")

@app.post("/api/v1/search")
async def search_real_data(request: dict):
    """Search for real university data"""
    try:
        query = request.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f"Real data search: {query}")
        
        # Use real AI agent to search
        response_data = await ai_agent.process_query(query)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.post("/api/v1/chat/query")
async def chat_query(request: dict):
    """Handle chat query with real AI agent"""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        context = request.get("context", {})
        
        logger.info(f"Real AI chat query: {message}")
        
        # Process with real AI agent
        response_data = await ai_agent.process_query(message, context)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Chat query error: {e}")
        raise HTTPException(status_code=500, detail="Chat failed")

@app.get("/api/v1/faculty/search")
async def search_faculty(q: str = "", university: str = None, research_area: str = None):
    """Search for real faculty data"""
    try:
        # Build search query
        search_parts = []
        if q:
            search_parts.append(q)
        if university:
            search_parts.append(university)
        if research_area:
            search_parts.append(research_area)
        
        search_query = " ".join(search_parts) + " faculty professors"
        
        # Search using real AI agent
        response_data = await ai_agent.process_query(search_query)
        
        return {
            "faculty": response_data.get("faculty_matches", []),
            "total": len(response_data.get("faculty_matches", [])),
            "sources": response_data.get("sources", []),
            "timestamp": "real-time"
        }
        
    except Exception as e:
        logger.error(f"Faculty search error: {e}")
        raise HTTPException(status_code=500, detail="Faculty search failed")

@app.get("/api/v1/search-history")
async def get_search_history():
    """Get user's search history"""
    try:
        # Get recent searches from AI agent
        history = ai_agent._get_recent_searches()
        
        return {
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Search history error: {e}")
        return {"history": [], "total": 0}

@app.get("/api/v1/stats")
async def get_real_stats():
    """Get real application statistics"""
    try:
        # Get actual counts from database
        conn = ai_agent.db_path
        import sqlite3
        
        db_conn = sqlite3.connect(conn)
        
        # Count faculty in history
        faculty_cursor = db_conn.execute("SELECT COUNT(DISTINCT faculty_name) FROM search_history WHERE faculty_name IS NOT NULL")
        faculty_count = faculty_cursor.fetchone()[0]
        
        # Count searches
        search_cursor = db_conn.execute("SELECT COUNT(*) FROM search_history")
        search_count = search_cursor.fetchone()[0]
        
        # Count unique queries
        query_cursor = db_conn.execute("SELECT COUNT(DISTINCT query) FROM search_history")
        query_count = query_cursor.fetchone()[0]
        
        db_conn.close()
        
        return {
            "faculty_scraped": faculty_count,
            "total_searches": search_count,
            "unique_queries": query_count,
            "data_source": "Real university websites",
            "ai_model": "HuggingFace Transformers (Local)",
            "last_updated": "Real-time",
            "mode": "REAL DATA - NO DUMMY INFORMATION"
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "faculty_scraped": 0,
            "total_searches": 0,
            "unique_queries": 0,
            "data_source": "Real university websites",
            "ai_model": "HuggingFace Transformers (Local)",
            "last_updated": "Real-time",
            "mode": "REAL DATA - NO DUMMY INFORMATION"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if AI agent is working
        agent_status = "OK" if ai_agent else "Not initialized"
        
        # Check database
        import sqlite3
        try:
            conn = sqlite3.connect(ai_agent.db_path)
            conn.execute("SELECT 1")
            conn.close()
            db_status = "OK"
        except Exception as e:
            db_status = f"Error: {e}"
        
        return {
            "status": "healthy",
            "version": "3.0.0",
            "mode": "REAL DATA ONLY",
            "ai_agent": agent_status,
            "database": db_status,
            "huggingface_available": ai_agent.ai_model is not None if ai_agent else False,
            "features": [
                "Real web scraping",
                "HuggingFace AI",
                "Search history",
                "No dummy data"
            ]
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
        reload=True
    )