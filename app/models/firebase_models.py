# app/models/firebase_models.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.firebase_config import get_firebase

class FirebaseBaseModel(BaseModel):
    """Base model for Firebase documents"""
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

class University(FirebaseBaseModel):
    """University model for Firebase"""
    name: str
    short_name: str
    country: str
    state_province: Optional[str] = None
    city: Optional[str] = None
    cs_ranking: Optional[int] = None
    overall_ranking: Optional[int] = None
    acceptance_rate: Optional[float] = None
    website_url: Optional[str] = None
    admissions_email: Optional[str] = None
    is_active: bool = True
    scraping_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    async def create(cls, **kwargs) -> 'University':
        """Create a new university in Firebase"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('universities', data=kwargs)
        return cls(id=doc_id, **kwargs)
    
    @classmethod
    async def get_by_id(cls, doc_id: str) -> Optional['University']:
        """Get university by ID"""
        firebase = get_firebase()
        data = await firebase.get_document('universities', doc_id)
        return cls(**data) if data else None
    
    @classmethod
    async def search(cls, filters: List[tuple] = None, limit: int = 100) -> List['University']:
        """Search universities"""
        firebase = get_firebase()
        results = await firebase.query_collection('universities', filters, limit=limit)
        return [cls(**data) for data in results]

class Faculty(FirebaseBaseModel):
    """Faculty model for Firebase"""
    name: str
    email: Optional[str] = None
    title: Optional[str] = None
    university_id: str
    university_name: Optional[str] = None
    department: Optional[str] = None
    research_areas: List[str] = []
    research_statement: Optional[str] = None
    homepage_url: Optional[str] = None
    google_scholar_url: Optional[str] = None
    hiring_status: str = "unknown"  # hiring, maybe, not_hiring, unknown
    hiring_probability: float = 0.0
    hiring_indicators: List[str] = []
    last_hiring_update: Optional[str] = None
    h_index: Optional[int] = None
    citation_count: Optional[int] = None
    recent_publications: List[Dict[str, Any]] = []
    office_location: Optional[str] = None
    phone: Optional[str] = None
    twitter_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_active: bool = True
    last_scraped: Optional[datetime] = None
    scraping_sources: List[str] = []
    
    @classmethod
    async def create(cls, **kwargs) -> 'Faculty':
        """Create a new faculty in Firebase"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('faculty', data=kwargs)
        return cls(id=doc_id, **kwargs)
    
    @classmethod
    async def get_by_id(cls, doc_id: str) -> Optional['Faculty']:
        """Get faculty by ID"""
        firebase = get_firebase()
        data = await firebase.get_document('faculty', doc_id)
        return cls(**data) if data else None
    
    @classmethod
    async def search_by_research_area(cls, research_area: str, limit: int = 50) -> List['Faculty']:
        """Search faculty by research area"""
        firebase = get_firebase()
        results = await firebase.search_documents('faculty', 'research_areas', research_area, limit)
        return [cls(**data) for data in results]
    
    @classmethod
    async def search_hiring(cls, limit: int = 50) -> List['Faculty']:
        """Search faculty currently hiring"""
        firebase = get_firebase()
        filters = [('hiring_status', '==', 'hiring'), ('is_active', '==', True)]
        results = await firebase.query_collection('faculty', filters, limit=limit)
        return [cls(**data) for data in results]
    
    async def update_hiring_status(self, status: str, probability: float = None, indicators: List[str] = None):
        """Update hiring status"""
        firebase = get_firebase()
        update_data = {
            'hiring_status': status,
            'last_hiring_update': datetime.utcnow().isoformat()
        }
        if probability is not None:
            update_data['hiring_probability'] = probability
        if indicators:
            update_data['hiring_indicators'] = indicators
        
        await firebase.update_document('faculty', self.id, update_data)

class Program(FirebaseBaseModel):
    """Program model for Firebase"""
    name: str
    degree_type: str
    university_id: str
    university_name: Optional[str] = None
    department: Optional[str] = None
    application_deadline: Optional[str] = None
    application_requirements: Dict[str, Any] = {}
    gre_required: Optional[bool] = None
    toefl_required: Optional[bool] = None
    min_gpa: Optional[float] = None
    duration_years: Optional[int] = None
    research_areas: List[str] = []
    specializations: List[str] = []
    tuition_annual: Optional[float] = None
    funding_available: Optional[bool] = None
    average_funding_amount: Optional[float] = None
    funding_details: Dict[str, Any] = {}
    acceptance_rate: Optional[float] = None
    enrollment_size: Optional[int] = None
    international_student_percentage: Optional[float] = None
    is_active: bool = True
    faculty_ids: List[str] = []
    
    @classmethod
    async def create(cls, **kwargs) -> 'Program':
        """Create a new program in Firebase"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('programs', data=kwargs)
        return cls(id=doc_id, **kwargs)
    
    @classmethod
    async def search_by_criteria(cls, degree_types: List[str] = None, 
                                research_areas: List[str] = None,
                                university_ids: List[str] = None,
                                limit: int = 50) -> List['Program']:
        """Search programs by criteria"""
        firebase = get_firebase()
        filters = [('is_active', '==', True)]
        
        if degree_types:
            filters.append(('degree_type', 'in', degree_types))
        
        if university_ids:
            filters.append(('university_id', 'in', university_ids))
        
        results = await firebase.query_collection('programs', filters, limit=limit)
        programs = [cls(**data) for data in results]
        
        # Filter by research areas if specified (post-query filtering for array contains)
        if research_areas:
            filtered_programs = []
            for program in programs:
                if any(area in program.research_areas for area in research_areas):
                    filtered_programs.append(program)
            return filtered_programs
        
        return programs

class ScrapeJob(FirebaseBaseModel):
    """Scrape job tracking model"""
    job_type: str  # faculty, programs, social_media
    target: str    # university name, subreddit, etc.
    status: str    # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_found: int = 0
    records_saved: int = 0
    error_message: Optional[str] = None
    next_scheduled: Optional[datetime] = None
    priority: str = "medium"  # critical, high, medium, low
    
    @classmethod
    async def create(cls, **kwargs) -> 'ScrapeJob':
        """Create a new scrape job"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('scrape_jobs', data=kwargs)
        return cls(id=doc_id, **kwargs)
    
    async def update_status(self, status: str, **kwargs):
        """Update job status"""
        firebase = get_firebase()
        update_data = {'status': status}
        update_data.update(kwargs)
        await firebase.update_document('scrape_jobs', self.id, update_data)

class HiringSignal(FirebaseBaseModel):
    """Hiring signal from social media or websites"""
    source: str           # reddit, twitter, website
    source_url: str
    faculty_name: Optional[str] = None
    university_name: Optional[str] = None
    department: Optional[str] = None
    signal_type: str      # hiring_announcement, position_filled, etc.
    confidence_score: float = 0.0
    content: str
    extracted_info: Dict[str, Any] = {}
    processed: bool = False
    faculty_id: Optional[str] = None
    
    @classmethod
    async def create(cls, **kwargs) -> 'HiringSignal':
        """Create a new hiring signal"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('hiring_signals', data=kwargs)
        return cls(id=doc_id, **kwargs)
    
    @classmethod
    async def get_unprocessed(cls, limit: int = 50) -> List['HiringSignal']:
        """Get unprocessed hiring signals"""
        firebase = get_firebase()
        filters = [('processed', '==', False)]
        results = await firebase.query_collection('hiring_signals', filters, 
                                                 order_by='created_at', limit=limit)
        return [cls(**data) for data in results]

class ChatSession(FirebaseBaseModel):
    """Chat session model"""
    user_id: Optional[str] = None
    session_id: str
    title: Optional[str] = None
    is_active: bool = True
    message_count: int = 0
    
    @classmethod
    async def create(cls, **kwargs) -> 'ChatSession':
        """Create a new chat session"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('chat_sessions', data=kwargs)
        return cls(id=doc_id, **kwargs)

class ChatMessage(FirebaseBaseModel):
    """Chat message model"""
    session_id: str
    role: str  # user, assistant, system
    content: str
    agent_type: Optional[str] = None
    confidence_score: Optional[float] = None
    sources: List[Dict[str, Any]] = []
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None
    
    @classmethod
    async def create(cls, **kwargs) -> 'ChatMessage':
        """Create a new chat message"""
        firebase = get_firebase()
        doc_id = await firebase.create_document('chat_messages', data=kwargs)
        return cls(id=doc_id, **kwargs)
    
    @classmethod
    async def get_session_messages(cls, session_id: str, limit: int = 50) -> List['ChatMessage']:
        """Get messages for a session"""
        firebase = get_firebase()
        filters = [('session_id', '==', session_id)]
        results = await firebase.query_collection('chat_messages', filters, 
                                                 order_by='created_at', limit=limit)
        return [cls(**data) for data in results]