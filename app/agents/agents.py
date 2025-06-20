import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from bs4 import BeautifulSoup
from tavily import TavilyClient
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RealTimeDataOrchestrator:
    """Orchestrator that fetches real-time data from online sources"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY) if settings.TAVILY_API_KEY else None
        self.session = None
    
    async def process_query(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user query with real-time online data"""
        try:
            # Step 1: Classify and extract information
            query_info = await self._analyze_query(user_message)
            
            # Step 2: Fetch real-time data from multiple sources
            real_time_data = await self._fetch_real_time_data(query_info)
            
            # Step 3: Generate response with real data
            response = await self._generate_response(user_message, real_time_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I'm having trouble accessing the latest information right now. Please try again in a moment.",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": []
            }
    
    async def _analyze_query(self, message: str) -> Dict[str, Any]:
        """Analyze user query to understand what they're looking for"""
        try:
            prompt = f"""
            Analyze this graduate admissions query and extract key information:
            "{message}"
            
            Return JSON with:
            {{
                "intent": "faculty_search" | "program_search" | "deadline_info" | "general_info",
                "universities": ["list of university names mentioned"],
                "research_areas": ["machine learning", "computer vision", etc.],
                "degree_types": ["PhD", "MS", etc.],
                "specific_requirements": ["GRE", "TOEFL", "deadlines", etc.],
                "hiring_focus": true/false,
                "search_terms": ["terms to search online"]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Fallback to keyword extraction
            return self._extract_keywords(message)
    
    def _extract_keywords(self, message: str) -> Dict[str, Any]:
        """Fallback keyword extraction"""
        message_lower = message.lower()
        
        # Universities
        universities = []
        uni_keywords = ['stanford', 'mit', 'berkeley', 'cmu', 'caltech', 'harvard', 'princeton']
        for keyword in uni_keywords:
            if keyword in message_lower:
                universities.append(keyword.title())
        
        # Research areas
        research_areas = []
        research_keywords = [
            'machine learning', 'ml', 'artificial intelligence', 'ai',
            'computer vision', 'cv', 'natural language processing', 'nlp',
            'robotics', 'systems', 'algorithms', 'cybersecurity'
        ]
        for keyword in research_keywords:
            if keyword in message_lower:
                if keyword == 'ml':
                    research_areas.append('machine learning')
                elif keyword == 'ai':
                    research_areas.append('artificial intelligence')
                elif keyword == 'cv':
                    research_areas.append('computer vision')
                elif keyword == 'nlp':
                    research_areas.append('natural language processing')
                else:
                    research_areas.append(keyword)
        
        # Intent detection
        intent = "general_info"
        if any(word in message_lower for word in ['professor', 'faculty', 'advisor', 'hiring']):
            intent = "faculty_search"
        elif any(word in message_lower for word in ['program', 'degree', 'admission']):
            intent = "program_search"
        elif any(word in message_lower for word in ['deadline', 'application']):
            intent = "deadline_info"
        
        return {
            "intent": intent,
            "universities": universities,
            "research_areas": research_areas,
            "degree_types": [],
            "specific_requirements": [],
            "hiring_focus": 'hiring' in message_lower,
            "search_terms": universities + research_areas
        }
    
    async def _fetch_real_time_data(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch real-time data from multiple online sources"""
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            tasks = []
            
            # 1. Search with Tavily if available
            if self.tavily_client:
                tasks.append(self._search_with_tavily(query_info))
            
            # 2. Direct university website scraping
            if query_info.get("universities"):
                for university in query_info["universities"]:
                    tasks.append(self._scrape_university_faculty(university, query_info))
            
            # 3. Search Reddit for hiring information
            if query_info.get("hiring_focus"):
                tasks.append(self._search_reddit_hiring(query_info))
            
            # 4. Search for program information
            if query_info["intent"] == "program_search":
                tasks.append(self._search_program_info(query_info))
            
            # Execute all searches concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined_data = {
                "faculty_matches": [],
                "program_matches": [],
                "recent_updates": [],
                "sources": []
            }
            
            for result in results:
                if isinstance(result, dict):
                    for key in combined_data:
                        if key in result:
                            combined_data[key].extend(result[key])
            
            return combined_data
    
    async def _search_with_tavily(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Search using Tavily API for recent information"""
        try:
            # Build search query
            search_terms = []
            
            if query_info.get("universities"):
                search_terms.extend(query_info["universities"])
            
            if query_info.get("research_areas"):
                search_terms.extend(query_info["research_areas"])
            
            if query_info.get("hiring_focus"):
                search_terms.append("hiring PhD students")
            
            search_query = " ".join(search_terms) + " computer science faculty"
            
            # Search with Tavily
            search_results = self.tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=10
            )
            
            faculty_matches = []
            sources = []
            
            for result in search_results.get("results", []):
                # Extract faculty information from search results
                faculty_info = await self._extract_faculty_from_text(
                    result.get("content", ""), 
                    result.get("url", "")
                )
                
                if faculty_info:
                    faculty_matches.append(faculty_info)
                
                sources.append({
                    "type": "web_search",
                    "url": result.get("url", ""),
                    "title": result.get("title", "")
                })
            
            return {
                "faculty_matches": faculty_matches,
                "program_matches": [],
                "recent_updates": [],
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {"faculty_matches": [], "program_matches": [], "recent_updates": [], "sources": []}
    
    async def _scrape_university_faculty(self, university: str, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape university faculty pages directly"""
        try:
            # Get faculty page URL for university
            faculty_urls = self._get_university_faculty_urls(university)
            
            faculty_matches = []
            sources = []
            
            for url in faculty_urls:
                try:
                    async with self.session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            faculty_data = await self._extract_faculty_from_html(html, university, url)
                            
                            # Filter by research areas if specified
                            if query_info.get("research_areas"):
                                filtered_faculty = []
                                for faculty in faculty_data:
                                    faculty_areas = [area.lower() for area in faculty.get("research_areas", [])]
                                    query_areas = [area.lower() for area in query_info["research_areas"]]
                                    
                                    if any(q_area in f_area for q_area in query_areas for f_area in faculty_areas):
                                        filtered_faculty.append(faculty)
                                
                                faculty_data = filtered_faculty
                            
                            faculty_matches.extend(faculty_data)
                            sources.append({"type": "university_website", "url": url})
                
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
            
            return {
                "faculty_matches": faculty_matches,
                "program_matches": [],
                "recent_updates": [],
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error scraping university {university}: {e}")
            return {"faculty_matches": [], "program_matches": [], "recent_updates": [], "sources": []}
    
    def _get_university_faculty_urls(self, university: str) -> List[str]:
        """Get faculty page URLs for different universities"""
        university_lower = university.lower()
        
        urls = []
        
        if 'stanford' in university_lower:
            urls = [
                'https://cs.stanford.edu/people/faculty',
                'https://ee.stanford.edu/people/faculty'
            ]
        elif 'mit' in university_lower:
            urls = [
                'https://www.csail.mit.edu/people',
                'https://www.eecs.mit.edu/people/faculty-advisors'
            ]
        elif 'berkeley' in university_lower or 'ucb' in university_lower:
            urls = [
                'https://eecs.berkeley.edu/faculty',
                'https://www2.eecs.berkeley.edu/Faculty/'
            ]
        elif 'cmu' in university_lower or 'carnegie' in university_lower:
            urls = [
                'https://www.cs.cmu.edu/directory/faculty',
                'https://www.ece.cmu.edu/directory/department-faculty.html'
            ]
        elif 'caltech' in university_lower:
            urls = [
                'https://www.cms.caltech.edu/people/faculty',
                'https://www.ee.caltech.edu/people'
            ]
        elif 'harvard' in university_lower:
            urls = [
                'https://seas.harvard.edu/computer-science/people',
                'https://www.seas.harvard.edu/faculty-research/faculty-directory'
            ]
        elif 'princeton' in university_lower:
            urls = [
                'https://www.cs.princeton.edu/people/faculty',
                'https://ee.princeton.edu/people/faculty'
            ]
        
        return urls
    
    async def _extract_faculty_from_html(self, html: str, university: str, url: str) -> List[Dict[str, Any]]:
        """Extract faculty information from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            faculty_list = []
            
            # Common selectors for faculty information
            faculty_selectors = [
                '.faculty-member', '.person', '.directory-item',
                '.faculty-card', '.people-item', '.profile'
            ]
            
            faculty_elements = []
            for selector in faculty_selectors:
                elements = soup.select(selector)
                if elements:
                    faculty_elements = elements
                    break
            
            # If no structured elements, look for name patterns
            if not faculty_elements:
                # Look for professor names in the text
                text = soup.get_text()
                faculty_elements = self._extract_names_from_text(text)
            
            for element in faculty_elements[:20]:  # Limit to 20 faculty
                try:
                    if isinstance(element, str):
                        # Name extracted from text
                        faculty_info = {
                            "name": element,
                            "university": university,
                            "university_name": university,
                            "department": "Computer Science",
                            "research_areas": [],
                            "hiring_status": "unknown",
                            "match_score": 0.5,
                            "source_url": url
                        }
                    else:
                        # HTML element
                        name = self._extract_name_from_element(element)
                        if not name:
                            continue
                        
                        email = self._extract_email_from_element(element)
                        research_areas = self._extract_research_areas_from_element(element)
                        title = self._extract_title_from_element(element)
                        
                        faculty_info = {
                            "name": name,
                            "email": email,
                            "title": title,
                            "university": university,
                            "university_name": university,
                            "department": "Computer Science",
                            "research_areas": research_areas,
                            "hiring_status": "unknown",
                            "match_score": 0.7,
                            "source_url": url
                        }
                    
                    faculty_list.append(faculty_info)
                    
                except Exception as e:
                    logger.error(f"Error extracting faculty info: {e}")
                    continue
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []
    
    def _extract_names_from_text(self, text: str) -> List[str]:
        """Extract faculty names from text using patterns"""
        # Look for "Dr. FirstName LastName" or "Prof. FirstName LastName"
        patterns = [
            r'(?:Dr\.?|Prof\.?|Professor)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:Ph\.?D\.?|Professor|Assistant Professor|Associate Professor)'
        ]
        
        names = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            names.extend(matches)
        
        return list(set(names))  # Remove duplicates
    
    def _extract_name_from_element(self, element) -> Optional[str]:
        """Extract name from HTML element"""
        # Try different selectors
        name_selectors = ['h2', 'h3', '.name', '.person-name', '.faculty-name', 'a']
        
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text().strip()
                if name and len(name) < 100 and len(name.split()) >= 2:
                    return name
        
        return None
    
    def _extract_email_from_element(self, element) -> Optional[str]:
        """Extract email from HTML element"""
        text = element.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        for email in emails:
            if 'edu' in email:
                return email
        
        return emails[0] if emails else None
    
    def _extract_research_areas_from_element(self, element) -> List[str]:
        """Extract research areas from HTML element"""
        text = element.get_text().lower()
        areas = []
        
        research_keywords = {
            'machine learning': ['machine learning', 'ml'],
            'artificial intelligence': ['artificial intelligence', 'ai'],
            'computer vision': ['computer vision', 'cv'],
            'natural language processing': ['nlp', 'natural language'],
            'robotics': ['robotics', 'autonomous systems'],
            'systems': ['systems', 'distributed systems'],
            'algorithms': ['algorithms', 'theoretical'],
            'cybersecurity': ['security', 'cybersecurity', 'cryptography']
        }
        
        for area, keywords in research_keywords.items():
            if any(keyword in text for keyword in keywords):
                areas.append(area.title())
        
        return areas[:3]  # Limit to 3 areas
    
    def _extract_title_from_element(self, element) -> Optional[str]:
        """Extract academic title from HTML element"""
        text = element.get_text().lower()
        
        if 'assistant professor' in text:
            return 'Assistant Professor'
        elif 'associate professor' in text:
            return 'Associate Professor'
        elif 'professor' in text:
            return 'Professor'
        elif 'lecturer' in text:
            return 'Lecturer'
        
        return None
    
    async def _search_reddit_hiring(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Search Reddit for hiring information"""
        try:
            # This would use Reddit API to search for hiring posts
            # For now, return empty results
            return {
                "faculty_matches": [],
                "program_matches": [],
                "recent_updates": [],
                "sources": []
            }
        except Exception as e:
            logger.error(f"Reddit search error: {e}")
            return {"faculty_matches": [], "program_matches": [], "recent_updates": [], "sources": []}
    
    async def _search_program_info(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Search for program information"""
        try:
            # Search for program information using Tavily or direct scraping
            if self.tavily_client and query_info.get("universities"):
                search_query = " ".join(query_info["universities"]) + " PhD program computer science requirements deadlines"
                
                search_results = self.tavily_client.search(
                    query=search_query,
                    search_depth="basic",
                    max_results=5
                )
                
                program_matches = []
                for result in search_results.get("results", []):
                    program_info = {
                        "name": "Computer Science PhD",
                        "university": query_info["universities"][0] if query_info.get("universities") else "Unknown",
                        "degree_type": "PhD",
                        "description": result.get("content", "")[:200],
                        "source_url": result.get("url", ""),
                        "match_score": 0.8
                    }
                    program_matches.append(program_info)
                
                return {
                    "faculty_matches": [],
                    "program_matches": program_matches,
                    "recent_updates": [],
                    "sources": [{"type": "program_search", "count": len(program_matches)}]
                }
            
            return {"faculty_matches": [], "program_matches": [], "recent_updates": [], "sources": []}
            
        except Exception as e:
            logger.error(f"Program search error: {e}")
            return {"faculty_matches": [], "program_matches": [], "recent_updates": [], "sources": []}
    
    async def _extract_faculty_from_text(self, text: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract faculty information from text content"""
        try:
            # Use AI to extract structured information from text
            prompt = f"""
            Extract faculty information from this text about computer science professors:
            "{text[:1000]}"
            
            Return JSON with faculty info or null if no faculty found:
            {{
                "name": "Dr. FirstName LastName",
                "title": "Professor/Assistant Professor/etc",
                "research_areas": ["Machine Learning", "AI"],
                "university": "University Name",
                "hiring_status": "hiring/unknown",
                "email": "email@university.edu"
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            if result and result.get("name"):
                result["source_url"] = url
                result["match_score"] = 0.6
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting faculty from text: {e}")
            return None
    
    async def _generate_response(self, user_message: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response using real-time data"""
        try:
            # Prepare context
            faculty_count = len(data.get("faculty_matches", []))
            program_count = len(data.get("program_matches", []))
            
            context = f"""
            User Query: {user_message}
            
            Real-time Data Found:
            - {faculty_count} faculty members
            - {program_count} programs
            """
            
            if faculty_count > 0:
                context += "\nTop Faculty Found:\n"
                for i, faculty in enumerate(data["faculty_matches"][:3]):
                    status = faculty.get("hiring_status", "unknown")
                    areas = ", ".join(faculty.get("research_areas", []))
                    context += f"{i+1}. {faculty.get('name', 'Unknown')} at {faculty.get('university', 'Unknown')} - Research: {areas} - Status: {status}\n"
            
            prompt = f"""
            As a PhD admissions assistant with access to real-time data, provide a helpful response.
            
            {context}
            
            Guidelines:
            - Be specific about current findings
            - Mention if faculty are hiring when known
            - Provide actionable next steps
            - Be encouraging but realistic
            - Keep under 200 words
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "faculty_matches": data.get("faculty_matches", [])[:5],
                "program_matches": data.get("program_matches", [])[:5],
                "confidence_score": min(0.9, max(0.3, faculty_count * 0.1 + program_count * 0.1)),
                "sources": data.get("sources", [])
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": f"I found {len(data.get('faculty_matches', []))} faculty members and {len(data.get('program_matches', []))} programs. Let me know if you'd like more details about any of them.",
                "faculty_matches": data.get("faculty_matches", [])[:5],
                "program_matches": data.get("program_matches", [])[:5],
                "confidence_score": 0.5,
                "sources": data.get("sources", [])
            }