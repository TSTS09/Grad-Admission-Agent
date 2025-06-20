import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore import AsyncClient
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)

class Settings(BaseSettings):
    """Application settings using Pydantic Settings"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # API Keys
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    TAVILY_API_KEY: str = Field(..., description="Tavily API key for web search")
    
    # Optional API Keys
    REDDIT_CLIENT_ID: Optional[str] = Field(default=None, description="Reddit client ID")
    REDDIT_CLIENT_SECRET: Optional[str] = Field(default=None, description="Reddit client secret")
    TWITTER_BEARER_TOKEN: Optional[str] = Field(default=None, description="Twitter bearer token")
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = Field(default="afya-a1006", description="Firebase project ID")
    FIREBASE_STORAGE_BUCKET: str = Field(default="stem-grad-assistant.appspot.com", description="Firebase storage bucket")
    FIREBASE_CONFIG: Optional[str] = Field(default=None, description="Firebase service account JSON")
    
    # Application Settings
    APP_NAME: str = Field(default="STEM Graduate Admissions Assistant", description="Application name")
    APP_VERSION: str = Field(default="2.0.0", description="Application version")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    
    # Scraping Settings
    ENABLE_BACKGROUND_SCRAPING: bool = Field(default=False, description="Enable background scraping")
    SCRAPING_INTERVAL_HOURS: int = Field(default=24, description="Scraping interval in hours")
    MAX_CONCURRENT_SCRAPES: int = Field(default=5, description="Max concurrent scraping jobs")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
settings = Settings()

class FirebaseManager:
    """Firebase manager for Firestore and Storage operations"""
    
    def __init__(self):
        self.db: Optional[AsyncClient] = None
        self.bucket = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Initialize from service account file or environment
            if os.path.exists("firebase-credentials.json"):
                cred = credentials.Certificate("firebase-credentials.json")
            else:
                # Use environment variable for deployment
                firebase_config = settings.FIREBASE_CONFIG
                if firebase_config:
                    cred = credentials.Certificate(json.loads(firebase_config))
                else:
                    # Use default credentials for Cloud Run/App Engine
                    cred = credentials.ApplicationDefault()
            
            # Initialize app if not already done
            if not firebase_admin._apps:
                app = firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
            
            # Initialize Firestore client
            self.db = firestore.AsyncClient()
            
            # Initialize Storage bucket
            self.bucket = storage.bucket()
            
            logger.info("Firebase initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    async def create_document(self, collection: str, doc_id: str = None, data: Dict[str, Any] = None) -> str:
        """Create a document in Firestore"""
        try:
            if data is None:
                data = {}
            
            # Add timestamps
            data['created_at'] = datetime.utcnow()
            data['updated_at'] = datetime.utcnow()
            
            if doc_id:
                doc_ref = self.db.collection(collection).document(doc_id)
                await doc_ref.set(data)
                return doc_id
            else:
                doc_ref = await self.db.collection(collection).add(data)
                return doc_ref[1].id
                
        except Exception as e:
            logger.error(f"Error creating document in {collection}: {e}")
            raise
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from Firestore"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = await doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from {collection}: {e}")
            return None
    
    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in Firestore"""
        try:
            data['updated_at'] = datetime.utcnow()
            doc_ref = self.db.collection(collection).document(doc_id)
            await doc_ref.update(data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id} in {collection}: {e}")
            return False
    
    async def query_collection(self, collection: str, filters: List[tuple] = None, 
                              order_by: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query a collection with filters"""
        try:
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = await query.get()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection {collection}: {e}")
            return []
    
    async def search_documents(self, collection: str, search_field: str, 
                              search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents using array-contains or text matching"""
        try:
            # For array fields (like research_areas)
            if isinstance(search_term, str) and search_field in ['research_areas', 'specializations']:
                query = self.db.collection(collection).where(search_field, 'array_contains', search_term)
            else:
                # For text fields - Firestore doesn't have full-text search, so we'll do prefix matching
                query = self.db.collection(collection).where(
                    search_field, '>=', search_term
                ).where(
                    search_field, '<=', search_term + '\uf8ff'
                )
            
            if limit:
                query = query.limit(limit)
            
            docs = await query.get()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching {collection} for {search_term}: {e}")
            return []

# Global Firebase manager instance
firebase_manager: Optional[FirebaseManager] = None

def get_firebase() -> FirebaseManager:
    """Get the global Firebase manager instance"""
    global firebase_manager
    if firebase_manager is None:
        firebase_manager = FirebaseManager()
    return firebase_manager

async def init_firebase():
    """Initialize Firebase manager"""
    global firebase_manager
    firebase_manager = FirebaseManager()
    return firebase_manager