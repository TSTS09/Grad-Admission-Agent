import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib

# HuggingFace transformers for local AI
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️  HuggingFace transformers not available. Install with: pip install transformers torch")

from app.core.logging import get_logger

logger = get_logger(__name__)

class RealDataAIAgent:
    """AI Agent that uses real web scraping and HuggingFace models"""
    
    def __init__(self):
        self.db_path = "search_history.db"
        self.session = None
        self.ai_model = None
        self.tokenizer = None
        self._init_database()
        self._init_ai_model()
    
    def _init_database(self):
        """Initialize SQLite database for search history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    faculty_name TEXT,
                    university TEXT,
                    department TEXT,
                    email TEXT,
                    research_areas TEXT,
                    profile_url TEXT,
                    scraped_data TEXT,
                    search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS program_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    program_name TEXT,
                    university TEXT,
                    degree_type TEXT,
                    requirements TEXT,
                    deadlines TEXT,
                    program_url TEXT,
                    scraped_data TEXT,
                    search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def _init_ai_model(self):
        """Initialize HuggingFace model for grad admissions"""
        try:
            if not HF_AVAILABLE:
                logger.warning("HuggingFace not available, using fallback responses")
                return
            
            # Use a smaller, efficient model that works well for Q&A
            model_name = "microsoft/DialoGPT-medium"  # Good for conversational AI
            
            logger.info(f"Loading AI model: {model_name}")
            
            # Initialize the model for text generation
            self.ai_model = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=model_name,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                pad_token_id=50256
            )
            
            logger.info("AI model loaded successfully")
            
        except Exception as e:
            logger.error(f"AI model initialization error: {e}")
            self.ai_model = None
    
    async def process_query(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user query with real data scraping and AI response"""
        try:
            # Check search history first
            historical_data = self._get_search_history(user_message)
            
            if historical_data:
                logger.info("Found historical data for query")
                return await self._format_historical_response(user_message, historical_data)
            
            # Analyze query to understand what user wants
            query_info = self._analyze_query_locally(user_message)
            
            # Fetch real data from web
            real_data = await self._fetch_real_data(query_info)
            
            # Save to search history
            self._save_search_results(user_message, real_data)
            
            # Generate AI response
            response = await self._generate_ai_response(user_message, real_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I encountered an error while searching for real data. Please try a more specific query about a university or professor.",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": [],
                "search_history": self._get_recent_searches()
            }
    
    def _analyze_query_locally(self, message: str) -> Dict[str, Any]:
        """Analyze query without external APIs"""
        message_lower = message.lower()
        
        # Extract universities
        universities = []
        university_keywords = {
            'stanford': 'Stanford University',
            'mit': 'Massachusetts Institute of Technology',
            'berkeley': 'UC Berkeley',
            'ucb': 'UC Berkeley',
            'cmu': 'Carnegie Mellon University',
            'carnegie mellon': 'Carnegie Mellon University',
            'caltech': 'California Institute of Technology',
            'harvard': 'Harvard University',
            'princeton': 'Princeton University',
            'columbia': 'Columbia University',
            'cornell': 'Cornell University',
            'yale': 'Yale University',
            'chicago': 'University of Chicago',
            'penn': 'University of Pennsylvania',
            'northwestern': 'Northwestern University'
        }
        
        for keyword, full_name in university_keywords.items():
            if keyword in message_lower:
                universities.append(full_name)
        
        # Extract research areas
        research_areas = []
        research_keywords = {
            'machine learning': ['machine learning', 'ml'],
            'artificial intelligence': ['artificial intelligence', 'ai'],
            'computer vision': ['computer vision', 'cv'],
            'natural language processing': ['nlp', 'natural language'],
            'robotics': ['robotics', 'robot'],
            'systems': ['systems', 'distributed'],
            'algorithms': ['algorithms', 'theoretical'],
            'cybersecurity': ['security', 'cybersecurity'],
            'data science': ['data science', 'big data'],
            'deep learning': ['deep learning', 'neural networks']
        }
        
        for area, keywords in research_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                research_areas.append(area)
        
        # Determine intent
        intent = "general_info"
        if any(word in message_lower for word in ['professor', 'faculty', 'advisor']):
            intent = "faculty_search"
        elif any(word in message_lower for word in ['program', 'admission', 'requirement', 'phd', 'ms']):
            intent = "program_search"
        
        return {
            "intent": intent,
            "universities": universities,
            "research_areas": research_areas,
            "degree_types": self._extract_degree_types(message_lower),
            "search_terms": universities + research_areas
        }
    
    def _extract_degree_types(self, message_lower: str) -> List[str]:
        """Extract degree types from message"""
        degree_types = []
        if 'phd' in message_lower or 'ph.d' in message_lower:
            degree_types.append('PhD')
        if 'ms' in message_lower or 'm.s' in message_lower or 'master' in message_lower:
            degree_types.append('MS')
        if 'bs' in message_lower or 'bachelor' in message_lower:
            degree_types.append('BS')
        
        return degree_types or ['PhD']  # Default to PhD
    
    async def _fetch_real_data(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch real data from university websites"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as session:
            self.session = session
            
            results = {
                "faculty_matches": [],
                "program_matches": [],
                "sources": []
            }
            
            # Search for faculty if universities specified
            if query_info.get("universities") and query_info["intent"] in ["faculty_search", "general_info"]:
                for university in query_info["universities"]:
                    faculty_data = await self._scrape_university_faculty(university, query_info)
                    results["faculty_matches"].extend(faculty_data)
            
            # Search for program information
            if query_info.get("universities") and query_info["intent"] in ["program_search", "general_info"]:
                for university in query_info["universities"]:
                    program_data = await self._scrape_university_programs(university, query_info)
                    results["program_matches"].extend(program_data)
            
            return results
    
    async def _scrape_university_faculty(self, university: str, query_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape real faculty data from university websites"""
        try:
            faculty_urls = self._get_faculty_urls(university)
            faculty_matches = []
            
            for url in faculty_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            faculty_data = self._parse_faculty_page(html, university, url)
                            
                            # Filter by research areas if specified
                            if query_info.get("research_areas"):
                                faculty_data = self._filter_by_research_areas(
                                    faculty_data, query_info["research_areas"]
                                )
                            
                            faculty_matches.extend(faculty_data)
                            
                            if len(faculty_matches) >= 10:  # Limit results
                                break
                                
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
            
            return faculty_matches[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error scraping faculty for {university}: {e}")
            return []
    
    def _get_faculty_urls(self, university: str) -> List[str]:
        """Get real faculty page URLs for universities"""
        university_lower = university.lower()
        
        if 'stanford' in university_lower:
            return [
                'https://cs.stanford.edu/people/faculty',
                'https://cs.stanford.edu/directory/faculty'
            ]
        elif 'mit' in university_lower:
            return [
                'https://www.csail.mit.edu/people',
                'https://www.eecs.mit.edu/people/faculty'
            ]
        elif 'berkeley' in university_lower:
            return [
                'https://eecs.berkeley.edu/faculty',
                'https://www2.eecs.berkeley.edu/Faculty/Lists/faculty.html'
            ]
        elif 'carnegie mellon' in university_lower or 'cmu' in university_lower:
            return [
                'https://www.cs.cmu.edu/directory/faculty',
                'https://csd.cmu.edu/people/faculty'
            ]
        elif 'caltech' in university_lower:
            return [
                'https://www.cms.caltech.edu/people/faculty'
            ]
        elif 'harvard' in university_lower:
            return [
                'https://seas.harvard.edu/computer-science/people'
            ]
        elif 'princeton' in university_lower:
            return [
                'https://www.cs.princeton.edu/people/faculty'
            ]
        
        return []
    
    def _parse_faculty_page(self, html: str, university: str, url: str) -> List[Dict[str, Any]]:
        """Parse faculty information from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            faculty_list = []
            
            # Look for faculty cards/items
            faculty_selectors = [
                '.faculty-member', '.person', '.directory-item',
                '.faculty-card', '.people-item', '.profile',
                '.faculty', '.member', '.person-card'
            ]
            
            faculty_elements = []
            for selector in faculty_selectors:
                elements = soup.select(selector)
                if elements:
                    faculty_elements = elements
                    break
            
            # If no structured elements, look for names in text
            if not faculty_elements:
                faculty_elements = self._extract_faculty_from_text(soup.get_text())
            
            for element in faculty_elements[:20]:  # Limit to 20 faculty
                try:
                    if isinstance(element, str):
                        # Text-based extraction
                        faculty_info = {
                            "name": element,
                            "university": university,
                            "department": "Computer Science",
                            "research_areas": [],
                            "email": "",
                            "profile_url": url,
                            "scraped_at": datetime.now().isoformat()
                        }
                    else:
                        # HTML element
                        name = self._extract_text_from_element(element, ['h2', 'h3', '.name', 'a'])
                        if not name or len(name.split()) < 2:
                            continue
                        
                        email = self._extract_email_from_element(element)
                        research_areas = self._extract_research_areas(element.get_text())
                        
                        faculty_info = {
                            "name": name,
                            "university": university,
                            "department": "Computer Science",
                            "research_areas": research_areas,
                            "email": email or "",
                            "profile_url": self._extract_profile_url(element, url),
                            "scraped_at": datetime.now().isoformat()
                        }
                    
                    faculty_list.append(faculty_info)
                    
                except Exception as e:
                    logger.error(f"Error parsing faculty element: {e}")
                    continue
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Error parsing faculty page: {e}")
            return []
    
    def _extract_faculty_from_text(self, text: str) -> List[str]:
        """Extract faculty names from plain text"""
        # Look for "Dr. Name" or "Prof. Name" patterns
        patterns = [
            r'(?:Dr\.?|Prof\.?|Professor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:Ph\.?D\.?|Professor)'
        ]
        
        names = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            names.extend(matches)
        
        return list(set(names))[:10]  # Remove duplicates, limit to 10
    
    def _extract_text_from_element(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text from HTML element using multiple selectors"""
        for selector in selectors:
            try:
                target = element.select_one(selector)
                if target:
                    text = target.get_text().strip()
                    if text and len(text) < 100:
                        return text
            except:
                continue
        return None
    
    def _extract_email_from_element(self, element) -> Optional[str]:
        """Extract email from HTML element"""
        text = element.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Prefer .edu emails
        for email in emails:
            if '.edu' in email:
                return email
        
        return emails[0] if emails else None
    
    def _extract_research_areas(self, text: str) -> List[str]:
        """Extract research areas from text"""
        text_lower = text.lower()
        areas = []
        
        research_keywords = {
            'Machine Learning': ['machine learning', 'ml'],
            'Artificial Intelligence': ['artificial intelligence', 'ai'],
            'Computer Vision': ['computer vision', 'cv'],
            'Natural Language Processing': ['nlp', 'natural language'],
            'Robotics': ['robotics', 'robot'],
            'Systems': ['systems', 'distributed'],
            'Algorithms': ['algorithms', 'theoretical'],
            'Cybersecurity': ['security', 'cybersecurity'],
            'Data Science': ['data science', 'big data'],
            'Deep Learning': ['deep learning', 'neural networks']
        }
        
        for area, keywords in research_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                areas.append(area)
        
        return areas[:5]  # Limit to 5 areas
    
    def _extract_profile_url(self, element, base_url: str) -> str:
        """Extract profile URL from element"""
        try:
            link = element.select_one('a')
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        except:
            pass
        return base_url
    
    def _filter_by_research_areas(self, faculty_data: List[Dict], target_areas: List[str]) -> List[Dict]:
        """Filter faculty by research areas"""
        filtered = []
        target_areas_lower = [area.lower() for area in target_areas]
        
        for faculty in faculty_data:
            faculty_areas_lower = [area.lower() for area in faculty.get('research_areas', [])]
            
            # Check for any overlap
            if any(target in faculty_area for target in target_areas_lower for faculty_area in faculty_areas_lower):
                filtered.append(faculty)
        
        return filtered
    
    async def _scrape_university_programs(self, university: str, query_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape program information from university websites"""
        try:
            program_urls = self._get_program_urls(university)
            program_matches = []
            
            for url in program_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            program_data = self._parse_program_page(html, university, url)
                            program_matches.extend(program_data)
                            
                except Exception as e:
                    logger.error(f"Error scraping program {url}: {e}")
                    continue
            
            return program_matches[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error scraping programs for {university}: {e}")
            return []
    
    def _get_program_urls(self, university: str) -> List[str]:
        """Get program page URLs"""
        university_lower = university.lower()
        
        if 'stanford' in university_lower:
            return ['https://cs.stanford.edu/academics/graduate']
        elif 'mit' in university_lower:
            return ['https://www.eecs.mit.edu/academics/graduate-programs/']
        elif 'berkeley' in university_lower:
            return ['https://eecs.berkeley.edu/academics/graduate']
        elif 'carnegie mellon' in university_lower or 'cmu' in university_lower:
            return ['https://www.cs.cmu.edu/academics/graduate']
        
        return []
    
    def _parse_program_page(self, html: str, university: str, url: str) -> List[Dict[str, Any]]:
        """Parse program information from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            programs = []
            
            # Look for program information
            text = soup.get_text()
            
            # Basic program extraction
            if 'phd' in text.lower() or 'ph.d' in text.lower():
                programs.append({
                    "name": "Computer Science PhD",
                    "university": university,
                    "degree_type": "PhD",
                    "description": "Doctoral program in Computer Science",
                    "program_url": url,
                    "scraped_at": datetime.now().isoformat()
                })
            
            if 'master' in text.lower() or 'ms' in text.lower():
                programs.append({
                    "name": "Computer Science MS",
                    "university": university,
                    "degree_type": "MS",
                    "description": "Master's program in Computer Science",
                    "program_url": url,
                    "scraped_at": datetime.now().isoformat()
                })
            
            return programs
            
        except Exception as e:
            logger.error(f"Error parsing program page: {e}")
            return []
    
    def _get_search_history(self, query: str) -> List[Dict[str, Any]]:
        """Get search history for similar queries"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Look for similar queries
            cursor = conn.execute('''
                SELECT * FROM search_history 
                WHERE query LIKE ? OR faculty_name LIKE ? OR university LIKE ?
                ORDER BY last_updated DESC
                LIMIT 10
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return []
    
    def _save_search_results(self, query: str, data: Dict[str, Any]):
        """Save search results to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Save faculty matches
            for faculty in data.get("faculty_matches", []):
                conn.execute('''
                    INSERT OR REPLACE INTO search_history 
                    (query, faculty_name, university, department, email, research_areas, profile_url, scraped_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    query,
                    faculty.get("name"),
                    faculty.get("university"),
                    faculty.get("department"),
                    faculty.get("email"),
                    json.dumps(faculty.get("research_areas", [])),
                    faculty.get("profile_url"),
                    json.dumps(faculty)
                ))
            
            # Save program matches
            for program in data.get("program_matches", []):
                conn.execute('''
                    INSERT OR REPLACE INTO program_history 
                    (query, program_name, university, degree_type, program_url, scraped_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    query,
                    program.get("name"),
                    program.get("university"),
                    program.get("degree_type"),
                    program.get("program_url"),
                    json.dumps(program)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving search results: {e}")
    
    def _get_recent_searches(self) -> List[Dict[str, Any]]:
        """Get recent search history for display"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT DISTINCT query, COUNT(*) as count, MAX(last_updated) as last_search
                FROM search_history 
                GROUP BY query
                ORDER BY last_search DESC
                LIMIT 5
            ''')
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting recent searches: {e}")
            return []
    
    async def _format_historical_response(self, query: str, historical_data: List[Dict]) -> Dict[str, Any]:
        """Format response using historical data"""
        faculty_matches = []
        
        for record in historical_data:
            if record.get('faculty_name'):
                faculty_match = {
                    "name": record['faculty_name'],
                    "university": record['university'],
                    "department": record['department'],
                    "email": record['email'],
                    "research_areas": json.loads(record['research_areas']) if record['research_areas'] else [],
                    "profile_url": record['profile_url'],
                    "last_updated": record['last_updated'],
                    "from_history": True
                }
                faculty_matches.append(faculty_match)
        
        response_text = f"Found {len(faculty_matches)} professors from your previous searches:\n\n"
        for faculty in faculty_matches[:3]:
            response_text += f"• **{faculty['name']}** at {faculty['university']}\n"
            response_text += f"  Research: {', '.join(faculty['research_areas'])}\n"
            response_text += f"  Last checked: {faculty['last_updated']}\n\n"
        
        if len(faculty_matches) > 3:
            response_text += f"...and {len(faculty_matches) - 3} more from your search history."
        
        return {
            "response": response_text,
            "faculty_matches": faculty_matches,
            "program_matches": [],
            "confidence_score": 0.9,
            "sources": [{"type": "search_history", "count": len(faculty_matches)}],
            "search_history": self._get_recent_searches()
        }
    
    async def _generate_ai_response(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response using HuggingFace model or fallback"""
        try:
            faculty_count = len(data.get("faculty_matches", []))
            program_count = len(data.get("program_matches", []))
            
            if faculty_count == 0 and program_count == 0:
                return {
                    "response": "I couldn't find any professors or programs matching your query. Try searching for a specific university like 'Stanford CS faculty' or 'MIT PhD requirements'.",
                    "faculty_matches": [],
                    "program_matches": [],
                    "confidence_score": 0.1,
                    "sources": [],
                    "search_history": self._get_recent_searches()
                }
            
            # Generate response based on findings
            if self.ai_model and HF_AVAILABLE:
                ai_response = await self._generate_hf_response(query, data)
            else:
                ai_response = self._generate_fallback_response(query, data)
            
            return {
                "response": ai_response,
                "faculty_matches": data.get("faculty_matches", [])[:5],
                "program_matches": data.get("program_matches", [])[:5],
                "confidence_score": min(0.9, max(0.3, faculty_count * 0.2)),
                "sources": [{"type": "real_web_scraping", "faculty": faculty_count, "programs": program_count}],
                "search_history": self._get_recent_searches()
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_fallback_response(query, data)
    
    async def _generate_hf_response(self, query: str, data: Dict[str, Any]) -> str:
        """Generate response using HuggingFace model"""
        try:
            faculty_info = ""
            if data.get("faculty_matches"):
                faculty_info = "Found professors: " + ", ".join([
                    f"{f['name']} at {f['university']}" 
                    for f in data["faculty_matches"][:3]
                ])
            
            prompt = f"User asked: {query}\n{faculty_info}\n\nProvide helpful graduate admissions advice:"
            
            # Generate response
            result = self.ai_model(prompt, max_length=200, num_return_sequences=1)
            generated_text = result[0]['generated_text']
            
            # Extract just the new text after the prompt
            response = generated_text.replace(prompt, "").strip()
            
            return response if response else self._generate_fallback_response(query, data)
            
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            return self._generate_fallback_response(query, data)
    
    def _generate_fallback_response(self, query: str, data: Dict[str, Any]) -> str:
        """Generate fallback response without AI"""
        faculty_matches = data.get("faculty_matches", [])
        program_matches = data.get("program_matches", [])
        
        if faculty_matches:
            response = f"I found {len(faculty_matches)} professors from real university websites:\n\n"
            for faculty in faculty_matches[:3]:
                areas = ", ".join(faculty.get("research_areas", [])) or "Various areas"
                response += f"🎓 **{faculty['name']}** at {faculty['university']}\n"
                response += f"   Research: {areas}\n"
                if faculty.get("email"):
                    response += f"   Email: {faculty['email']}\n"
                response += "\n"
            
            if len(faculty_matches) > 3:
                response += f"...and {len(faculty_matches) - 3} more professors found.\n\n"
            
            response += "💡 Tip: Click on any professor to see their full profile and research details."
        
        elif program_matches:
            response = f"I found {len(program_matches)} programs:\n\n"
            for program in program_matches:
                response += f"📚 **{program['name']}** at {program['university']}\n"
                response += f"   Degree: {program['degree_type']}\n\n"
        
        else:
            response = "No results found. Try searching for:\n"
            response += "• 'Stanford computer science faculty'\n"
            response += "• 'MIT PhD requirements'\n"
            response += "• 'Berkeley machine learning professors'"
        
        return response