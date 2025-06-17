from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.services.faculty import search_faculty
from app.schemas.faculty import FacultySearch
from app.core.logging import get_logger

logger = get_logger(__name__)

class FacultyAgent(BaseAgent):
    """Agent specialized in faculty search and analysis"""
    
    def __init__(self):
        super().__init__()
        self.search_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in academic faculty search for STEM graduate admissions.
            Extract search criteria from the user query to find relevant faculty members.
            
            From the query, identify:
            1. Research areas/keywords
            2. Universities (if mentioned)
            3. Hiring preferences
            4. Degree type preferences
            
            Research areas to look for include:
            - Machine Learning, AI, Deep Learning
            - Computer Vision, NLP, Robotics
            - Systems, Networks, Security
            - Theory, Algorithms, Complexity
            - HCI, Graphics, Databases
            - Biocomputing, Quantum Computing
            
            Format your response as a structured search criteria."""),
            ("user", "{query}")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process faculty search request"""
        return await self.search_faculty(
            state["user_query"],
            user_context=state.get("context", {})
        )
    
    async def search_faculty(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for faculty members based on query"""
        try:
            # Extract search criteria using LLM
            search_criteria = await self._extract_search_criteria(query, user_context)
            
            # Search database
            async with AsyncSessionLocal() as db:
                faculty_results = await search_faculty(db, search_criteria)
            
            # Score and rank results
            scored_matches = await self._score_faculty_matches(query, faculty_results)
            
            # Get additional context from vector store
            similar_docs = await self.search_similar_documents(query, k=3)
            
            return {
                "matches": scored_matches[:10],  # Top 10 matches
                "sources": [
                    {"type": "database", "count": len(faculty_results)},
                    {"type": "vector_search", "documents": len(similar_docs)}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in faculty search: {e}")
            return {"matches": [], "sources": []}
    
    async def _extract_search_criteria(self, query: str, user_context: Dict[str, Any] = None) -> FacultySearch:
        """Extract search criteria from natural language query"""
        try:
            result = await self.llm.ainvoke(
                self.search_prompt.format_messages(query=query)
            )
            
            # Parse LLM response to extract criteria
            # This is simplified - you could make this more sophisticated
            research_areas = self._extract_research_areas(query)
            
            # Use user context if available
            if user_context and user_context.get("research_interests"):
                research_areas.extend(user_context["research_interests"])
            
            return FacultySearch(
                research_areas=list(set(research_areas)),  # Remove duplicates
                hiring_status=["hiring", "maybe"] if "hiring" in query.lower() else None,
                min_hiring_probability=0.5 if "hiring" in query.lower() else None
            )
            
        except Exception as e:
            logger.error(f"Error extracting search criteria: {e}")
            return FacultySearch(research_areas=["computer science"])
    
    def _extract_research_areas(self, query: str) -> List[str]:
        """Extract research areas from query using keyword matching"""
        research_keywords = {
            "machine learning": ["machine learning", "ml", "artificial intelligence", "ai"],
            "computer vision": ["computer vision", "cv", "image processing", "visual"],
            "natural language processing": ["nlp", "natural language", "text processing"],
            "robotics": ["robotics", "robot", "autonomous"],
            "systems": ["systems", "distributed", "operating systems"],
            "security": ["security", "cryptography", "privacy"],
            "theory": ["theory", "algorithms", "complexity"],
            "databases": ["database", "data management", "big data"],
            "networks": ["networking", "networks", "protocols"],
            "hci": ["hci", "human computer interaction", "user interface"]
        }
        
        found_areas = []
        query_lower = query.lower()
        
        for area, keywords in research_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_areas.append(area)
        
        return found_areas if found_areas else ["computer science"]
    
    async def _score_faculty_matches(self, query: str, faculty_list: List) -> List[Dict[str, Any]]:
        """Score and rank faculty matches"""
        scored_matches = []
        
        for faculty in faculty_list:
            score = self._calculate_match_score(query, faculty)
            
            scored_matches.append({
                "faculty_id": faculty.id,
                "name": faculty.name,
                "university": faculty.university.name if faculty.university else "Unknown",
                "department": faculty.department,
                "research_areas": faculty.research_areas or [],
                "hiring_status": faculty.hiring_status,
                "hiring_probability": faculty.hiring_probability,
                "match_score": score,
                "homepage_url": faculty.homepage_url,
                "email": faculty.email
            })
        
        # Sort by match score
        scored_matches.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_matches
    
    def _calculate_match_score(self, query: str, faculty) -> float:
        """Calculate match score for a faculty member"""
        score = 0.0
        query_lower = query.lower()
        
        # Research area matching (40% weight)
        if faculty.research_areas:
            area_matches = sum(
                1 for area in faculty.research_areas
                if any(keyword in query_lower for keyword in area.lower().split())
            )
            score += 0.4 * min(1.0, area_matches / max(1, len(faculty.research_areas)))
        
        # Hiring status (30% weight)
        if faculty.hiring_status == "hiring":
            score += 0.3
        elif faculty.hiring_status == "maybe":
            score += 0.15
        
        # Hiring probability (20% weight)
        if faculty.hiring_probability:
            score += 0.2 * faculty.hiring_probability
        
        # H-index and citations (10% weight)
        if faculty.h_index:
            # Normalize h-index to 0-1 range (assuming max reasonable h-index of 100)
            score += 0.1 * min(1.0, faculty.h_index / 100.0)
        
        return min(1.0, score)