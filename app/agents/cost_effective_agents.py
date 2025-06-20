import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import openai
from app.core.config import get_firebase
from app.models.firebase_models import Faculty, Program, University, HiringSignal
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatOrchestrator:
    """Main orchestrator for chat queries using cost-effective approach"""

    def __init__(self):
        self.client = openai.AsyncOpenAI()
        self.faculty_agent = FacultyAgent()
        self.program_agent = ProgramAgent()
        self.research_agent = ResearchAgent()

    async def process_query(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user query and return comprehensive response"""
        try:
            # Step 1: Classify the query
            query_type = await self._classify_query(user_message)

            # Step 2: Extract key information
            extracted_info = await self._extract_information(user_message)

            # Step 3: Route to appropriate agents
            results = await self._route_to_agents(query_type, extracted_info, user_message)

            # Step 4: Generate final response
            response = await self._generate_response(user_message, results, query_type)

            return response

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
        """Classify the type of query"""
        message_lower = message.lower()

        # Simple keyword-based classification
        if any(word in message_lower for word in ['faculty', 'professor', 'hiring', 'advisor']):
            return "faculty_search"
        elif any(word in message_lower for word in ['program', 'degree', 'phd', 'masters', 'admission']):
            return "program_search"
        elif any(word in message_lower for word in ['deadline', 'application', 'requirement']):
            return "application_info"
        elif any(word in message_lower for word in ['research', 'area', 'field', 'topic']):
            return "research_info"
        else:
            return "general_chat"

    async def _extract_information(self, message: str) -> Dict[str, Any]:
        """Extract key information from user message using GPT"""
        try:
            prompt = f"""
            Extract key information from this graduate admissions query:
            "{message}"
            
            Return a JSON object with the following fields (use null for missing info):
            {{
                "universities": ["list of mentioned universities"],
                "research_areas": ["list of research areas/fields"],
                "degree_types": ["PhD", "MS", "MEng", etc.],
                "deadlines": ["any mentioned deadlines"],
                "faculty_names": ["any mentioned faculty names"],
                "locations": ["countries, states, cities mentioned"],
                "requirements": ["GRE", "TOEFL", "publications", etc.]
            }}
            """

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )

            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback to keyword extraction
                return self._fallback_extraction(message)

        except Exception as e:
            logger.error(f"Error in information extraction: {e}")
            return self._fallback_extraction(message)

    def _fallback_extraction(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based extraction"""
        message_lower = message.lower()

        # Common research areas
        research_areas = []
        research_keywords = [
            'machine learning', 'artificial intelligence', 'computer vision',
            'natural language processing', 'robotics', 'data science',
            'cybersecurity', 'software engineering', 'algorithms', 'systems',
            'human-computer interaction', 'bioinformatics', 'quantum computing'
        ]
        for keyword in research_keywords:
            if keyword in message_lower:
                research_areas.append(keyword.title())

        # Common universities (simplified)
        universities = []
        university_keywords = [
            'stanford', 'mit', 'berkeley', 'cmu', 'caltech', 'harvard',
            'princeton', 'yale', 'columbia', 'cornell', 'university of'
        ]
        for keyword in university_keywords:
            if keyword in message_lower:
                if keyword == 'university of':
                    # Try to extract the full name
                    pattern = r'university of (\w+)'
                    matches = re.findall(pattern, message_lower)
                    universities.extend(
                        [f"University of {match.title()}" for match in matches])
                else:
                    universities.append(keyword.title())

        return {
            "universities": universities,
            "research_areas": research_areas,
            "degree_types": [],
            "deadlines": [],
            "faculty_names": [],
            "locations": [],
            "requirements": []
        }

    async def _route_to_agents(self, query_type: str, extracted_info: Dict[str, Any],
                               original_message: str) -> Dict[str, Any]:
        """Route query to appropriate specialized agents"""
        results = {
            "faculty_matches": [],
            "program_matches": [],
            "research_insights": [],
            "application_info": []
        }

        try:
            if query_type == "faculty_search":
                results["faculty_matches"] = await self.faculty_agent.search_faculty(extracted_info)

            elif query_type == "program_search":
                results["program_matches"] = await self.program_agent.search_programs(extracted_info)

            elif query_type == "research_info":
                results["research_insights"] = await self.research_agent.get_research_insights(extracted_info)

            elif query_type == "application_info":
                # Get both faculty and program info for application queries
                results["faculty_matches"] = await self.faculty_agent.search_faculty(extracted_info)
                results["program_matches"] = await self.program_agent.search_programs(extracted_info)

        except Exception as e:
            logger.error(f"Error routing to agents: {e}")

        return results

    async def _generate_response(self, user_message: str, results: Dict[str, Any],
                                 query_type: str) -> Dict[str, Any]:
        """Generate final response using GPT"""
        try:
            # Prepare context for GPT
            context = f"""
            User Query: {user_message}
            Query Type: {query_type}
            
            Available Data:
            - Faculty Matches: {len(results['faculty_matches'])} found
            - Program Matches: {len(results['program_matches'])} found
            - Research Insights: {len(results['research_insights'])} insights
            """

            if results['faculty_matches']:
                context += f"\n\nTop Faculty Matches:\n"
                for i, faculty in enumerate(results['faculty_matches'][:3]):
                    context += f"{i+1}. {faculty.get('name', 'Unknown')} at {faculty.get('university_name', 'Unknown')} - {faculty.get('hiring_status', 'Unknown')} status\n"

            if results['program_matches']:
                context += f"\n\nTop Program Matches:\n"
                for i, program in enumerate(results['program_matches'][:3]):
                    context += f"{i+1}. {program.get('name', 'Unknown')} at {program.get('university_name', 'Unknown')}\n"

            prompt = f"""
            As a PhD admissions assistant, provide a helpful and informative response to the user's query.
            
            {context}
            
            Guidelines:
            - Be specific and actionable
            - Mention hiring status when relevant
            - Include deadlines if asked
            - Provide next steps
            - Be encouraging but realistic
            - Keep response under 200 words
            
            Response:
            """

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250
            )

            ai_response = response.choices[0].message.content

            return {
                "response": ai_response,
                "faculty_matches": results["faculty_matches"][:5],
                "program_matches": results["program_matches"][:5],
                "confidence_score": min(0.8, len(results["faculty_matches"]) * 0.1 + len(results["program_matches"]) * 0.1),
                "sources": [{"type": "database", "count": len(results["faculty_matches"]) + len(results["program_matches"])}]
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I found some relevant information for your query. Let me know if you'd like more details about any specific faculty or programs.",
                "faculty_matches": results["faculty_matches"][:5],
                "program_matches": results["program_matches"][:5],
                "confidence_score": 0.5,
                "sources": []
            }


class FacultyAgent:
    """Agent specialized in faculty search and analysis"""

    async def search_faculty(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for faculty based on criteria"""
        try:
            firebase = get_firebase()
            results = []

            # Search by research areas
            if criteria.get("research_areas"):
                for area in criteria["research_areas"]:
                    faculty_results = await firebase.search_documents('faculty', 'research_areas', area, limit=10)
                    results.extend(faculty_results)

            # Search by university
            if criteria.get("universities"):
                for university in criteria["universities"]:
                    filters = [('university_name', '==', university),
                               ('is_active', '==', True)]
                    university_faculty = await firebase.query_collection('faculty', filters, limit=10)
                    results.extend(university_faculty)

            # If no specific criteria, get hiring faculty
            if not results:
                filters = [('hiring_status', '==', 'hiring'),
                           ('is_active', '==', True)]
                results = await firebase.query_collection('faculty', filters, limit=10)

            # Remove duplicates and add match scores
            unique_results = {}
            for faculty in results:
                faculty_id = faculty.get('id')
                if faculty_id not in unique_results:
                    faculty['match_score'] = self._calculate_match_score(
                        faculty, criteria)
                    unique_results[faculty_id] = faculty

            # Sort by match score
            sorted_results = sorted(unique_results.values(
            ), key=lambda x: x['match_score'], reverse=True)

            return sorted_results[:10]

        except Exception as e:
            logger.error(f"Error searching faculty: {e}")
            return []

    def _calculate_match_score(self, faculty: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate match score for faculty"""
        score = 0.0

        # Base score for hiring status
        hiring_status = faculty.get('hiring_status', 'unknown')
        if hiring_status == 'hiring':
            score += 0.5
        elif hiring_status == 'maybe':
            score += 0.3

        # Research area match
        faculty_areas = [area.lower()
                         for area in faculty.get('research_areas', [])]
        criteria_areas = [area.lower()
                          for area in criteria.get('research_areas', [])]

        if criteria_areas:
            matches = sum(1 for area in criteria_areas if any(
                area in faculty_area for faculty_area in faculty_areas))
            score += (matches / len(criteria_areas)) * 0.4

        # University match
        if criteria.get('universities'):
            university_match = any(uni.lower() in faculty.get('university_name', '').lower()
                                   for uni in criteria['universities'])
            if university_match:
                score += 0.1

        return min(score, 1.0)


class ProgramAgent:
    """Agent specialized in program search and analysis"""

    async def search_programs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for programs based on criteria"""
        try:
            firebase = get_firebase()
            filters = [('is_active', '==', True)]

            # Filter by degree type if specified
            if criteria.get("degree_types"):
                # For simplicity, take the first degree type
                degree_type = criteria["degree_types"][0]
                filters.append(('degree_type', '==', degree_type))

            # Get programs
            results = await firebase.query_collection('programs', filters, limit=20)

            # Filter and score results
            scored_results = []
            for program in results:
                score = self._calculate_program_match_score(program, criteria)
                if score > 0.1:  # Only include relevant programs
                    program['match_score'] = score
                    scored_results.append(program)

            # Sort by match score
            sorted_results = sorted(
                scored_results, key=lambda x: x['match_score'], reverse=True)

            return sorted_results[:10]

        except Exception as e:
            logger.error(f"Error searching programs: {e}")
            return []

    def _calculate_program_match_score(self, program: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate match score for program"""
        score = 0.0

        # Research area match
        program_areas = [area.lower()
                         for area in program.get('research_areas', [])]
        criteria_areas = [area.lower()
                          for area in criteria.get('research_areas', [])]

        if criteria_areas and program_areas:
            matches = sum(1 for area in criteria_areas if any(
                area in prog_area for prog_area in program_areas))
            score += (matches / len(criteria_areas)) * 0.6

        # University match
        if criteria.get('universities'):
            university_match = any(uni.lower() in program.get('university_name', '').lower()
                                   for uni in criteria['universities'])
            if university_match:
                score += 0.3

        # Funding availability
        if program.get('funding_available'):
            score += 0.1

        return min(score, 1.0)


class ResearchAgent:
    """Agent specialized in research insights and trends"""

    async def get_research_insights(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get research insights based on criteria"""
        try:
            insights = []

            # Get trending research areas
            if criteria.get("research_areas"):
                for area in criteria["research_areas"]:
                    insight = await self._analyze_research_area(area)
                    if insight:
                        insights.append(insight)

            return insights

        except Exception as e:
            logger.error(f"Error getting research insights: {e}")
            return []

    async def _analyze_research_area(self, research_area: str) -> Optional[Dict[str, Any]]:
        """Analyze a specific research area"""
        try:
            firebase = get_firebase()

            # Count faculty in this area
            faculty_results = await firebase.search_documents('faculty', 'research_areas', research_area, limit=100)
            hiring_faculty = [f for f in faculty_results if f.get(
                'hiring_status') == 'hiring']

            # Count programs in this area
            program_results = await firebase.search_documents('programs', 'research_areas', research_area, limit=100)

            return {
                "research_area": research_area,
                "total_faculty": len(faculty_results),
                "hiring_faculty": len(hiring_faculty),
                "total_programs": len(program_results),
                "hiring_rate": len(hiring_faculty) / len(faculty_results) if faculty_results else 0,
                "insight": f"Found {len(hiring_faculty)} hiring faculty out of {len(faculty_results)} total in {research_area}"
            }

        except Exception as e:
            logger.error(f"Error analyzing research area {research_area}: {e}")
            return None
