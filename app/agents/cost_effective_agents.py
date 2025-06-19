# app/agents/cost_effective_agents.py
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from app.models.firebase_models import Faculty, Program, HiringSignal
from app.core.firebase_config import get_firebase
from app.core.logging import get_logger

logger = get_logger(__name__)

class CostEffectiveLLMManager:
    """Manager for cost-effective LLM usage with fallbacks"""
    
    def __init__(self):
        self.openai_client = None
        self.use_openai = bool(os.getenv('OPENAI_API_KEY'))
        
        # Initialize OpenAI if available
        if self.use_openai:
            self.openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Cost tracking
        self.daily_token_usage = 0
        self.max_daily_tokens = 50000  # Limit daily usage
        
        logger.info(f"LLM Manager initialized. OpenAI available: {self.use_openai}")
    
    async def generate_response(self, prompt: str, max_tokens: int = 500, temperature: float = 0.0) -> str:
        """Generate response with cost optimization"""
        try:
            # Check daily limits
            if self.daily_token_usage > self.max_daily_tokens:
                return self._fallback_response(prompt)
            
            if self.use_openai and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Cheaper than GPT-4
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Track usage
                self.daily_token_usage += response.usage.total_tokens
                
                return response.choices[0].message.content
            else:
                return self._fallback_response(prompt)
                
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM is unavailable or limited"""
        # Simple keyword-based responses for common queries
        prompt_lower = prompt.lower()
        
        if "faculty" in prompt_lower and "hiring" in prompt_lower:
            return "I found several faculty members who may be hiring. Check their latest publications and lab websites for current openings."
        
        elif "program" in prompt_lower and "requirement" in prompt_lower:
            return "Most PhD programs require: GRE scores, transcripts, statement of purpose, letters of recommendation, and research experience."
        
        elif "deadline" in prompt_lower:
            return "Application deadlines vary by program but typically fall between December 1-15 for Fall admission. Check specific program websites for exact dates."
        
        else:
            return "I'd be happy to help with your graduate admissions questions. Please check the specific program websites for the most current information."

class SmartFacultyAgent:
    """Faculty search agent with intelligent filtering"""
    
    def __init__(self):
        self.llm_manager = CostEffectiveLLMManager()
    
    async def search_faculty(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for faculty with intelligent matching"""
        try:
            # Extract search criteria from query
            criteria = self._extract_search_criteria(query, user_context)
            
            # Search Firebase for faculty
            faculty_results = await self._search_firebase_faculty(criteria)
            
            # Score and rank results
            scored_matches = self._score_faculty_matches(query, faculty_results)
            
            # Generate AI insights if budget allows
            ai_insights = ""
            if len(scored_matches) > 0:
                insight_prompt = f"Based on these faculty matches for query '{query}', provide brief advice: {[f['name'] for f in scored_matches[:3]]}"
                ai_insights = await self.llm_manager.generate_response(insight_prompt, max_tokens=150)
            
            return {
                "matches": scored_matches[:10],
                "total_found": len(faculty_results),
                "ai_insights": ai_insights,
                "sources": [{"type": "firebase_search", "count": len(faculty_results)}]
            }
            
        except Exception as e:
            logger.error(f"Faculty search error: {e}")
            return {"matches": [], "total_found": 0, "ai_insights": "", "sources": []}
    
    def _extract_search_criteria(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract search criteria using keyword matching"""
        query_lower = query.lower()
        criteria = {}
        
        # Research areas
        research_keywords = {
            'machine learning': ['machine learning', 'ml', 'deep learning'],
            'artificial intelligence': ['artificial intelligence', 'ai'],
            'computer vision': ['computer vision', 'cv', 'image processing'],
            'natural language processing': ['nlp', 'natural language'],
            'robotics': ['robotics', 'robot'],
            'systems': ['systems', 'distributed'],
            'theory': ['theory', 'algorithms'],
            'security': ['security', 'cryptography'],
        }
        
        research_areas = []
        for area, keywords in research_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                research_areas.append(area)
        
        if research_areas:
            criteria['research_areas'] = research_areas
        
        # Universities
        university_keywords = ['stanford', 'mit', 'berkeley', 'cmu', 'caltech', 'harvard', 'princeton']
        for uni in university_keywords:
            if uni in query_lower:
                criteria['university'] = uni
                break
        
        # Hiring status
        if any(word in query_lower for word in ['hiring', 'recruiting', 'accepting']):
            criteria['hiring_status'] = 'hiring'
        
        # Add user context
        if user_context:
            if user_context.get('research_interests'):
                criteria.setdefault('research_areas', []).extend(user_context['research_interests'])
        
        return criteria
    
    async def _search_firebase_faculty(self, criteria: Dict[str, Any]) -> List[Faculty]:
        """Search faculty in Firebase based on criteria"""
        firebase = get_firebase()
        
        # Base filters
        filters = [('is_active', '==', True)]
        
        # Add hiring status filter
        if criteria.get('hiring_status'):
            filters.append(('hiring_status', '==', criteria['hiring_status']))
        
        # Add university filter
        if criteria.get('university'):
            filters.append(('university_name', '==', criteria['university']))
        
        # Get faculty from Firebase
        results = await firebase.query_collection('faculty', filters, limit=100)
        faculty_list = [Faculty(**data) for data in results]
        
        # Filter by research areas (post-query filtering)
        if criteria.get('research_areas'):
            filtered_faculty = []
            for faculty in faculty_list:
                if any(area in faculty.research_areas for area in criteria['research_areas']):
                    filtered_faculty.append(faculty)
            faculty_list = filtered_faculty
        
        return faculty_list
    
    def _score_faculty_matches(self, query: str, faculty_list: List[Faculty]) -> List[Dict[str, Any]]:
        """Score and rank faculty matches"""
        scored_matches = []
        query_lower = query.lower()
        
        for faculty in faculty_list:
            score = 0.0
            
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
            
            # Recent updates (10% weight)
            if faculty.last_scraped:
                days_old = (datetime.utcnow() - faculty.last_scraped).days
                freshness = max(0, 1 - days_old / 30)  # Decay over 30 days
                score += 0.1 * freshness
            
            scored_matches.append({
                "faculty_id": faculty.id,
                "name": faculty.name,
                "university": faculty.university_name,
                "department": faculty.department,
                "research_areas": faculty.research_areas or [],
                "hiring_status": faculty.hiring_status,
                "hiring_probability": faculty.hiring_probability,
                "homepage_url": faculty.homepage_url,
                "email": faculty.email,
                "match_score": score,
                "last_updated": faculty.last_scraped.isoformat() if faculty.last_scraped else None
            })
        
        # Sort by match score
        scored_matches.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_matches

class SmartProgramAgent:
    """Program search agent"""
    
    def __init__(self):
        self.llm_manager = CostEffectiveLLMManager()
    
    async def search_programs(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for academic programs"""
        try:
            # Extract search criteria
            criteria = self._extract_program_criteria(query, user_context)
            
            # Search Firebase
            programs = await self._search_firebase_programs(criteria)
            
            # Score and rank
            scored_matches = self._score_program_matches(query, programs)
            
            return {
                "matches": scored_matches[:10],
                "total_found": len(programs),
                "sources": [{"type": "firebase_search", "count": len(programs)}]
            }
            
        except Exception as e:
            logger.error(f"Program search error: {e}")
            return {"matches": [], "total_found": 0, "sources": []}
    
    def _extract_program_criteria(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract program search criteria"""
        query_lower = query.lower()
        criteria = {}
        
        # Degree types
        if any(word in query_lower for word in ['phd', 'doctorate', 'doctoral']):
            criteria['degree_types'] = ['PhD']
        elif any(word in query_lower for word in ['ms', 'master', 'masters']):
            criteria['degree_types'] = ['MS', 'MSc']
        
        # Funding requirements
        if any(word in query_lower for word in ['funding', 'funded', 'financial']):
            criteria['funding_required'] = True
        
        return criteria
    
    async def _search_firebase_programs(self, criteria: Dict[str, Any]) -> List[Program]:
        """Search programs in Firebase"""
        firebase = get_firebase()
        
        filters = [('is_active', '==', True)]
        
        if criteria.get('funding_required'):
            filters.append(('funding_available', '==', True))
        
        results = await firebase.query_collection('programs', filters, limit=100)
        programs = [Program(**data) for data in results]
        
        # Filter by degree types if specified
        if criteria.get('degree_types'):
            programs = [p for p in programs if p.degree_type in criteria['degree_types']]
        
        return programs
    
    def _score_program_matches(self, query: str, programs: List[Program]) -> List[Dict[str, Any]]:
        """Score and rank program matches"""
        scored_matches = []
        
        for program in programs:
            score = 0.5  # Base score
            
            # Add scoring logic here
            if program.funding_available and 'funding' in query.lower():
                score += 0.3
            
            if program.acceptance_rate and program.acceptance_rate > 0.1:
                score += 0.2
            
            scored_matches.append({
                "program_id": program.id,
                "name": program.name,
                "university": program.university_name,
                "degree_type": program.degree_type,
                "department": program.department,
                "funding_available": program.funding_available,
                "application_deadline": program.application_deadline,
                "match_score": score
            })
        
        scored_matches.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_matches

class ChatOrchestrator:
    """Main chat orchestrator with cost optimization"""
    
    def __init__(self):
        self.faculty_agent = SmartFacultyAgent()
        self.program_agent = SmartProgramAgent()
        self.llm_manager = CostEffectiveLLMManager()
    
    async def process_query(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user query with intelligent routing"""
        try:
            # Classify query type
            query_type = self._classify_query(query)
            
            response_data = {
                "response": "",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": []
            }
            
            if query_type == "faculty_search":
                result = await self.faculty_agent.search_faculty(query, user_context)
                response_data["faculty_matches"] = result["matches"]
                response_data["sources"] = result["sources"]
                response_data["response"] = self._generate_faculty_response(result)
                response_data["confidence_score"] = 0.8 if result["matches"] else 0.3
                
            elif query_type == "program_search":
                result = await self.program_agent.search_programs(query, user_context)
                response_data["program_matches"] = result["matches"]
                response_data["sources"] = result["sources"]
                response_data["response"] = self._generate_program_response(result)
                response_data["confidence_score"] = 0.8 if result["matches"] else 0.3
                
            else:
                # General chat - use LLM if available
                response_data["response"] = await self.llm_manager.generate_response(
                    f"Answer this graduate admissions question: {query}",
                    max_tokens=300
                )
                response_data["confidence_score"] = 0.6
            
            return response_data
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": []
            }
    
    def _classify_query(self, query: str) -> str:
        """Classify query type using keyword matching"""
        query_lower = query.lower()
        
        faculty_keywords = ['professor', 'faculty', 'advisor', 'supervisor', 'hiring', 'recruiting']
        program_keywords = ['program', 'degree', 'phd', 'masters', 'requirements', 'deadline']
        
        faculty_score = sum(1 for keyword in faculty_keywords if keyword in query_lower)
        program_score = sum(1 for keyword in program_keywords if keyword in query_lower)
        
        if faculty_score > program_score:
            return "faculty_search"
        elif program_score > faculty_score:
            return "program_search"
        else:
            return "general_chat"
    
    def _generate_faculty_response(self, result: Dict[str, Any]) -> str:
        """Generate response for faculty search results"""
        matches = result["matches"]
        
        if not matches:
            return "I couldn't find any faculty members matching your criteria. Try broadening your search or checking different universities."
        
        response = f"I found {len(matches)} faculty members who might interest you:\n\n"
        
        for i, faculty in enumerate(matches[:3], 1):
            status_emoji = "🟢" if faculty["hiring_status"] == "hiring" else "🟡" if faculty["hiring_status"] == "maybe" else "🔴"
            response += f"{i}. **{faculty['name']}** at {faculty['university']} {status_emoji}\n"
            response += f"   Research: {', '.join(faculty['research_areas'][:3])}\n"
            response += f"   Match: {faculty['match_score']:.0%}\n\n"
        
        if result.get("ai_insights"):
            response += f"💡 **Tip:** {result['ai_insights']}"
        
        return response
    
    def _generate_program_response(self, result: Dict[str, Any]) -> str:
        """Generate response for program search results"""
        matches = result["matches"]
        
        if not matches:
            return "I couldn't find any programs matching your criteria. Try adjusting your search parameters."
        
        response = f"I found {len(matches)} programs that might interest you:\n\n"
        
        for i, program in enumerate(matches[:3], 1):
            funding_emoji = "💰" if program["funding_available"] else "💸"
            response += f"{i}. **{program['name']}** at {program['university']} {funding_emoji}\n"
            response += f"   Degree: {program['degree_type']}\n"
            if program['application_deadline']:
                response += f"   Deadline: {program['application_deadline']}\n"
            response += f"   Match: {program['match_score']:.0%}\n\n"
        
        return response