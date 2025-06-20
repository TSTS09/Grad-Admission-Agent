import asyncio
import json
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import get_logger
from app.models.firebase_models import Faculty, Program, HiringSignal

logger = get_logger(__name__)

class ChatOrchestrator:
    """Main chat orchestrator for handling user queries"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.conversation_history = []
    
    async def process_query(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user query and return response"""
        try:
            # Initialize context if None
            if context is None:
                context = {}
            
            # Classify the query
            query_type = await self._classify_query(message)
            
            # Initialize response structure
            response_data = {
                "response": "",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.8,
                "sources": [{"type": "ai_agent", "count": 1}]
            }
            
            # Route to appropriate handler based on query type
            if query_type == "faculty_search":
                response_data = await self._handle_faculty_search(message, context)
            elif query_type == "program_search":
                response_data = await self._handle_program_search(message, context)
            elif query_type == "general_chat":
                response_data = await self._handle_general_chat(message, context)
            else:
                response_data = await self._handle_mixed_query(message, context)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": []
            }
    
    async def _classify_query(self, message: str) -> str:
        """Classify the user query"""
        try:
            prompt = f"""
            Classify this graduate admissions query into one of these categories:
            - faculty_search: Finding professors or faculty members
            - program_search: Finding academic programs or degrees
            - general_chat: General conversation or help
            - mixed: Multiple categories combined
            
            Query: "{message}"
            
            Return only the category name.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )
            
            classification = response.choices[0].message.content.strip().lower()
            return classification if classification in ["faculty_search", "program_search", "general_chat", "mixed"] else "general_chat"
            
        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            return "general_chat"
    
    async def _handle_faculty_search(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle faculty search queries"""
        try:
            # Extract search terms
            search_terms = await self._extract_search_terms(message)
            
            # Search for faculty
            faculty_matches = []
            if search_terms.get("research_area"):
                faculty_results = await Faculty.search_by_research_area(
                    search_terms["research_area"], limit=10
                )
                faculty_matches = [
                    {
                        "id": f.id,
                        "name": f.name,
                        "university": f.university_name,
                        "research_areas": f.research_areas,
                        "hiring_status": f.hiring_status,
                        "match_score": 0.85
                    }
                    for f in faculty_results[:5]
                ]
            
            # Generate response
            response = await self._generate_faculty_response(message, faculty_matches, search_terms)
            
            return {
                "response": response,
                "faculty_matches": faculty_matches,
                "program_matches": [],
                "confidence_score": 0.9,
                "sources": [{"type": "faculty_database", "count": len(faculty_matches)}]
            }
            
        except Exception as e:
            logger.error(f"Error handling faculty search: {e}")
            return await self._handle_general_chat(message, context)
    
    async def _handle_program_search(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle program search queries"""
        try:
            # Extract search criteria
            search_criteria = await self._extract_program_criteria(message)
            
            # Search for programs
            program_matches = []
            if search_criteria:
                program_results = await Program.search_by_criteria(
                    degree_types=search_criteria.get("degree_types"),
                    research_areas=search_criteria.get("research_areas"),
                    limit=10
                )
                program_matches = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "university": p.university_name,
                        "degree_type": p.degree_type,
                        "match_score": 0.82
                    }
                    for p in program_results[:5]
                ]
            
            # Generate response
            response = await self._generate_program_response(message, program_matches, search_criteria)
            
            return {
                "response": response,
                "faculty_matches": [],
                "program_matches": program_matches,
                "confidence_score": 0.85,
                "sources": [{"type": "program_database", "count": len(program_matches)}]
            }
            
        except Exception as e:
            logger.error(f"Error handling program search: {e}")
            return await self._handle_general_chat(message, context)
    
    async def _handle_general_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general chat queries"""
        try:
            prompt = f"""
            You are a helpful AI assistant for STEM graduate admissions. 
            Provide helpful, accurate advice about graduate school applications, 
            research, faculty, programs, and admissions processes.
            
            User question: {message}
            
            Provide a helpful response:
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return {
                "response": response.choices[0].message.content.strip(),
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.75,
                "sources": [{"type": "ai_knowledge", "count": 1}]
            }
            
        except Exception as e:
            logger.error(f"Error handling general chat: {e}")
            return {
                "response": "I'm here to help with your graduate admissions questions. Could you please rephrase your question?",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.5,
                "sources": []
            }
    
    async def _handle_mixed_query(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries that involve multiple aspects"""
        # For now, try both faculty and program search
        faculty_result = await self._handle_faculty_search(message, context)
        program_result = await self._handle_program_search(message, context)
        
        # Combine results
        combined_response = f"{faculty_result['response']}\n\n{program_result['response']}"
        
        return {
            "response": combined_response,
            "faculty_matches": faculty_result["faculty_matches"],
            "program_matches": program_result["program_matches"],
            "confidence_score": 0.8,
            "sources": faculty_result["sources"] + program_result["sources"]
        }
    
    async def _extract_search_terms(self, message: str) -> Dict[str, str]:
        """Extract search terms from message"""
        # Simple keyword extraction - can be enhanced with NLP
        message_lower = message.lower()
        
        research_areas = []
        if "machine learning" in message_lower or "ml" in message_lower:
            research_areas.append("Machine Learning")
        if "computer vision" in message_lower or "cv" in message_lower:
            research_areas.append("Computer Vision")
        if "nlp" in message_lower or "natural language" in message_lower:
            research_areas.append("Natural Language Processing")
        if "ai" in message_lower or "artificial intelligence" in message_lower:
            research_areas.append("Artificial Intelligence")
        
        return {
            "research_area": research_areas[0] if research_areas else "Computer Science"
        }
    
    async def _extract_program_criteria(self, message: str) -> Dict[str, List[str]]:
        """Extract program search criteria"""
        message_lower = message.lower()
        
        degree_types = []
        if "phd" in message_lower or "ph.d" in message_lower:
            degree_types.append("PhD")
        if "ms" in message_lower or "m.s" in message_lower or "master" in message_lower:
            degree_types.append("MS")
        
        research_areas = []
        if "computer science" in message_lower or "cs" in message_lower:
            research_areas.append("Computer Science")
        if "engineering" in message_lower:
            research_areas.append("Engineering")
        
        return {
            "degree_types": degree_types or ["PhD"],
            "research_areas": research_areas or ["Computer Science"]
        }
    
    async def _generate_faculty_response(self, query: str, matches: List[Dict], terms: Dict) -> str:
        """Generate response for faculty search"""
        if not matches:
            return f"I didn't find any faculty matches for your search. You might want to try different keywords or check our database for more options."
        
        response = f"I found {len(matches)} faculty members that might interest you:\n\n"
        for match in matches:
            status_emoji = "🟢" if match["hiring_status"] == "hiring" else "🟡" if match["hiring_status"] == "maybe" else "🔴"
            response += f"{status_emoji} **{match['name']}** at {match['university']}\n"
            response += f"   Research: {', '.join(match['research_areas'])}\n"
            response += f"   Hiring Status: {match['hiring_status'].title()}\n\n"
        
        response += "Would you like more details about any of these faculty members?"
        return response
    
    async def _generate_program_response(self, query: str, matches: List[Dict], criteria: Dict) -> str:
        """Generate response for program search"""
        if not matches:
            return f"I didn't find any programs matching your criteria. You might want to broaden your search or try different keywords."
        
        response = f"I found {len(matches)} programs that match your interests:\n\n"
        for match in matches:
            response += f"🎓 **{match['name']}** at {match['university']}\n"
            response += f"   Degree: {match['degree_type']}\n\n"
        
        response += "Would you like more information about requirements, deadlines, or faculty for any of these programs?"
        return response