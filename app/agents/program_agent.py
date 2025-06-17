from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.services.program import search_programs
from app.schemas.program import ProgramSearch
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProgramAgent(BaseAgent):
    """Agent specialized in academic program search and analysis"""
    
    def __init__(self):
        super().__init__()
        self.search_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in STEM graduate program search and admissions.
            Extract search criteria from the user query to find relevant academic programs.
            
            From the query, identify:
            1. Degree types (PhD, MS, MEng, etc.)
            2. Research areas/specializations
            3. Universities or location preferences
            4. Funding requirements
            5. Application requirements (GRE, TOEFL, etc.)
            
            Common degree types:
            - PhD (Doctor of Philosophy)
            - MS (Master of Science)
            - MEng (Master of Engineering)
            - MCS (Master of Computer Science)
            
            Research specializations in CS/Engineering:
            - Artificial Intelligence
            - Machine Learning
            - Computer Systems
            - Software Engineering
            - Cybersecurity
            - Data Science
            
            Format your response as structured search criteria."""),
            ("user", "{query}")
        ])
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process program search request"""
        return await self.search_programs(
            state["user_query"],
            user_context=state.get("context", {})
        )
    
    async def search_programs(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for academic programs based on query"""
        try:
            # Extract search criteria
            search_criteria = await self._extract_search_criteria(query, user_context)
            
            # Search database
            async with AsyncSessionLocal() as db:
                program_results = await search_programs(db, search_criteria)
            
            # Score and rank results
            scored_matches = await self._score_program_matches(query, program_results)
            
            # Get additional context
            similar_docs = await self.search_similar_documents(query, k=3)
            
            return {
                "matches": scored_matches[:10],  # Top 10 matches
                "sources": [
                    {"type": "database", "count": len(program_results)},
                    {"type": "vector_search", "documents": len(similar_docs)}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in program search: {e}")
            return {"matches": [], "sources": []}
    
    async def _extract_search_criteria(self, query: str, user_context: Dict[str, Any] = None) -> ProgramSearch:
        """Extract search criteria from natural language query"""
        try:
            # Use LLM to extract criteria
            result = await self.llm.ainvoke(
                self.search_prompt.format_messages(query=query)
            )
            
            # Extract degree types
            degree_types = self._extract_degree_types(query)
            
            # Extract research areas
            research_areas = self._extract_research_areas(query)
            
            # Use user context
            if user_context:
                if user_context.get("degree_preferences"):
                    degree_types.extend(user_context["degree_preferences"])
                if user_context.get("research_interests"):
                    research_areas.extend(user_context["research_interests"])
            
            return ProgramSearch(
                degree_types=list(set(degree_types)) if degree_types else ["PhD"],
                research_areas=list(set(research_areas)) if research_areas else None,
                funding_required="funding" in query.lower() or "financial" in query.lower(),
                gre_required=None if "no gre" in query.lower() else None
            )
            
        except Exception as e:
            logger.error(f"Error extracting program search criteria: {e}")
            return ProgramSearch(degree_types=["PhD"])
    
    def _extract_degree_types(self, query: str) -> List[str]:
        """Extract degree types from query"""
        degree_keywords = {
            "PhD": ["phd", "doctorate", "doctoral", "ph.d"],
            "MS": ["ms", "masters", "master's", "m.s", "msc"],
            "MEng": ["meng", "m.eng", "master of engineering"],
            "MCS": ["mcs", "m.cs", "master of computer science"]
        }
        
        found_types = []
        query_lower = query.lower()
        
        for degree, keywords in degree_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_types.append(degree)
        
        return found_types
    
    def _extract_research_areas(self, query: str) -> List[str]:
        """Extract research areas from query"""
        # Reuse the research area extraction from faculty agent
        research_keywords = {
            "machine learning": ["machine learning", "ml", "artificial intelligence", "ai"],
            "computer vision": ["computer vision", "cv", "image processing"],
            "natural language processing": ["nlp", "natural language"],
            "robotics": ["robotics", "robot", "autonomous"],
            "systems": ["systems", "distributed", "operating systems"],
            "security": ["security", "cybersecurity", "cryptography"],
            "data science": ["data science", "big data", "analytics"],
            "software engineering": ["software engineering", "software development"]
        }
        
        found_areas = []
        query_lower = query.lower()
        
        for area, keywords in research_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_areas.append(area)
        
        return found_areas
    
    async def _score_program_matches(self, query: str, program_list: List) -> List[Dict[str, Any]]:
        """Score and rank program matches"""
        scored_matches = []
        
        for program in program_list:
            score = self._calculate_program_score(query, program)
            
            scored_matches.append({
                "program_id": program.id,
                "name": program.name,
                "degree_type": program.degree_type,
                "university": program.university.name if program.university else "Unknown",
                "department": program.department,
                "research_areas": program.research_areas or [],
                "application_deadline": program.application_deadline,
                "funding_available": program.funding_available,
                "tuition_annual": program.tuition_annual,
                "acceptance_rate": program.acceptance_rate,
                "match_score": score
            })
        
        # Sort by match score
        scored_matches.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_matches
    
    def _calculate_program_score(self, query: str, program) -> float:
        """Calculate match score for a program"""
        score = 0.0
        query_lower = query.lower()
        
        # Research area matching (40% weight)
        if program.research_areas:
            area_matches = sum(
                1 for area in program.research_areas
                if any(keyword in query_lower for keyword in area.lower().split())
            )
            score += 0.4 * min(1.0, area_matches / max(1, len(program.research_areas)))
        
        # Funding availability (25% weight)
        if "funding" in query_lower and program.funding_available:
            score += 0.25
        
        # Acceptance rate (20% weight) - higher acceptance rate = higher score
        if program.acceptance_rate:
            score += 0.2 * program.acceptance_rate
        
        # Application requirements match (15% weight)
        if "no gre" in query_lower and not program.gre_required:
            score += 0.15
        elif "gre" not in query_lower and program.gre_required:
            score += 0.05  # Slight penalty for GRE requirement if not mentioned
        
        return min(1.0, score)