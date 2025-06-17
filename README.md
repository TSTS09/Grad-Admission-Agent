# 🎓 STEM Graduate Admissions Assistant

An AI-powered platform to help STEM graduate school applicants navigate the complex admissions process with real-time faculty hiring data, program insights, and personalized guidance.

## ✨ Features

### 🤖 AI-Powered Assistance
- **LangGraph Agentic RAG System**: Multi-agent architecture for intelligent query processing
- **Specialized Agents**: Faculty search, program matching, research analysis, and conversational AI
- **Real-time Data**: Live faculty hiring status and program requirements

### 🔍 Comprehensive Search
- **Faculty Database**: 1,800+ faculty profiles across 200+ universities
- **Research Matching**: Advanced algorithms to match applicants with faculty based on research interests
- **Program Analysis**: Detailed program requirements, deadlines, and funding information

### 📊 Smart Dashboard
- **Application Tracking**: Monitor progress across multiple applications
- **Deadline Management**: Never miss important dates with intelligent reminders
- **Document Organization**: Keep track of transcripts, statements, and recommendations

### 🌐 Web Scraping Infrastructure
- **University Websites**: Automated scraping of faculty pages and program information
- **Social Media Monitoring**: Track hiring announcements on Reddit and Twitter
- **Compliance-First**: Respects robots.txt and terms of service

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/stem-grad-assistant/stem-grad-assistant.git
cd stem-grad-assistant
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Start with Docker Compose:**
```bash
make docker-up
```

4. **Or run locally:**
```bash
make install
make migrate
make seed
make dev
```

### API Keys Required
- `OPENAI_API_KEY`: For AI-powered features
- `TAVILY_API_KEY`: For web search capabilities
- `REDDIT_CLIENT_ID` & `REDDIT_CLIENT_SECRET`: For Reddit monitoring
- `TWITTER_BEARER_TOKEN`: For Twitter monitoring

## 🏗️ Architecture

### Backend (FastAPI + Python)
```
app/
├── api/          # REST API endpoints
├── agents/       # LangGraph AI agents
├── scrapers/     # Web scraping infrastructure
├── db/           # Database models and migrations
├── services/     # Business logic
└── utils/        # Shared utilities
```

### AI System (LangGraph + OpenAI)
- **Chat Agent**: Query classification and response generation
- **Faculty Agent**: Faculty search and matching
- **Program Agent**: Program analysis and recommendations  
- **Research Agent**: Research trend analysis

### Data Pipeline
- **University Scraper**: Faculty profiles and hiring status
- **Social Media Monitor**: Reddit/Twitter hiring announcements
- **Scheduler**: Intelligent update frequency based on data criticality

## 🎯 Usage Examples

### Dashboard Interface
Navigate to `http://localhost:8000` for the main dashboard with:
- Application progress tracking
- Faculty match recommendations
- Upcoming deadlines
- Research area analysis

### AI Chat Interface
Visit `http://localhost:8000/chat` for conversational assistance:

**Example Queries:**
- "Find ML professors at Stanford hiring for fall 2026"
- "Compare CS PhD programs at top 10 universities"
- "What are the GRE requirements for CMU?"
- "Review my research statement for AI programs"

### API Endpoints

**Chat API:**
```bash
POST /api/v1/chat/query
{
  "message": "Find CS professors at MIT",
  "context": {"research_interests": ["Machine Learning"]}
}
```

**Faculty Search:**
```bash
GET /api/v1/faculty?research_area=machine_learning&hiring_status=hiring
```

**Program Search:**
```bash
POST /api/v1/programs/search
{
  "degree_types": ["PhD"],
  "research_areas": ["Computer Vision"],
  "funding_required": true
}
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow integration tests
pytest tests/test_api/  # API tests only
```

## 🔧 Development

### Code Quality
```bash
make lint     # Check code style
make format   # Auto-format code
make test     # Run test suite
```

### Database Operations
```bash
make migrate         # Run migrations
make migrate-create MSG="description"  # Create new migration
make seed           # Seed with sample data
make backup-db      # Backup database
```

### Worker Management
```bash
make worker    # Start Celery worker
make beat      # Start Celery beat scheduler
make flower    # Start Flower monitoring
```

## 📊 Monitoring

### Prometheus + Grafana
```bash
make monitor  # Start monitoring stack
```

Visit:
- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`

### Key Metrics
- API response times and error rates
- Database connection health
- Scraping job success rates
- AI agent performance

## 🚢 Deployment

### Production Deployment
```bash
# Build and deploy
make build
make deploy

# With monitoring
docker-compose --profile production --profile monitoring up -d
```

### Environment Variables
Key production settings:
```bash
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run quality checks: `make lint test`
5. Submit a pull request

### Development Workflow
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure CI/CD passes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/stem-grad-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/stem-grad-assistant/discussions)

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- LangChain community for the framework
- All university websites for public data
- STEM graduate student community for feedback

---

**Built with ❤️ for the STEM graduate community**

<!-- ===============================
docs/API.md
=============================== -->
# API Documentation

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```bash
Authorization: Bearer <your-token>
```

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

## Chat API

### Send Message
```bash
POST /api/v1/chat/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Find CS professors at Stanford hiring for fall 2026",
  "session_id": "optional-session-id",
  "context": {
    "research_interests": ["Machine Learning", "Computer Vision"]
  }
}
```

Response:
```json
{
  "response": "I found several CS professors at Stanford who are hiring...",
  "session_id": "generated-session-id",
  "faculty_matches": [
    {
      "name": "Dr. Andrew Ng",
      "university": "Stanford University",
      "research_areas": ["Machine Learning", "AI"],
      "hiring_status": "hiring",
      "match_score": 0.94
    }
  ],
  "program_matches": [],
  "confidence_score": 0.85,
  "sources": [
    {
      "type": "database",
      "count": 5
    }
  ]
}
```

## Faculty API

### List Faculty
```bash
GET /api/v1/faculty?university_id=1&research_area=machine_learning&hiring_status=hiring&skip=0&limit=50
```

### Search Faculty
```bash
POST /api/v1/faculty/search
Content-Type: application/json

{
  "research_areas": ["Machine Learning", "Computer Vision"],
  "universities": [1, 2, 3],
  "hiring_status": ["hiring", "maybe"],
  "min_hiring_probability": 0.7,
  "degree_types": ["PhD"]
}
```

### Get Faculty by Research Area
```bash
GET /api/v1/faculty/research/machine%20learning?hiring_only=true&limit=20
```

## Programs API

### List Programs
```bash
GET /api/v1/programs?degree_type=PhD&university_id=1&skip=0&limit=50
```

### Search Programs
```bash
POST /api/v1/programs/search
Content-Type: application/json

{
  "degree_types": ["PhD", "MS"],
  "research_areas": ["Computer Science", "AI"],
  "universities": [1, 2, 3],
  "max_tuition": 60000,
  "funding_required": true,
  "gre_required": false
}
```

### Get Program Recommendations
```bash
GET /api/v1/programs/match/recommendations
Authorization: Bearer <token>
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 429 Rate Limited
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- API endpoints: 100 requests per minute
- Chat endpoints: 20 requests per minute
- Search endpoints: 50 requests per minute

## Pagination

List endpoints support pagination:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)

## Filtering

### Faculty Filters
- `university_id`: Filter by university
- `research_area`: Filter by research area
- `hiring_status`: Filter by hiring status (`hiring`, `maybe`, `not_hiring`, `unknown`)

### Program Filters  
- `degree_type`: Filter by degree type (`PhD`, `MS`, `MEng`, etc.)
- `university_id`: Filter by university
- `funding_required`: Filter programs with funding

## WebSocket API

Real-time chat via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/session-id');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "Hello",
    user_id: 123
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response);
};
```