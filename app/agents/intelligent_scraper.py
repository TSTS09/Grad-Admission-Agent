# app/agents/intelligent_scraper.py
import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
import google.generativeai as genai
from app.core.logging import get_logger

logger = get_logger(__name__)

class IntelligentScrapingAgent:
    """Intelligent web scraping agent using Google Gemini API for PhD/Master admissions information"""
    
    def __init__(self, gemini_api_key: str):
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.db_path = "admissions_search.db"
        self.session = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_query TEXT NOT NULL,
                    search_intent TEXT,
                    websites_found TEXT,
                    information_extracted TEXT,
                    source_links TEXT,
                    search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence_score REAL
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Main entry point - process any user query about grad admissions"""
        try:
            logger.info(f"Processing query: {user_query}")
            
            # Step 1: Understand what the user wants using Gemini
            search_plan = await self._analyze_user_intent(user_query)
            
            # Step 2: Find relevant websites to scrape
            target_websites = await self._find_relevant_websites(search_plan)
            
            # Step 3: Scrape the websites for information
            scraped_data = await self._scrape_websites(target_websites, search_plan)
            
            # Step 4: Extract and synthesize information
            final_response = await self._synthesize_information(user_query, scraped_data)
            
            # Step 5: Save results
            self._save_search_results(user_query, search_plan, scraped_data, final_response)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"I encountered an error while searching: {str(e)}",
                "information": [],
                "source_links": [],
                "confidence": 0.0
            }
    
    async def _analyze_user_intent(self, user_query: str) -> Dict[str, Any]:
        """Use Gemini to understand what the user wants to find"""
        try:
            prompt = f"""
            Analyze this graduate admissions query and create a search plan:
            Query: "{user_query}"
            
            Return a JSON object with:
            {{
                "search_intent": "Brief description of what user wants",
                "search_terms": ["list", "of", "search", "terms"],
                "website_types": ["university websites", "department pages", "program pages", etc.],
                "information_types": ["faculty info", "admission requirements", "deadlines", etc.],
                "specific_programs": ["PhD", "MS", "specific degree names if mentioned"],
                "universities_mentioned": ["any universities mentioned"],
                "general_search_strategy": "how to approach finding this information"
            }}
            
            Focus on PhD and Master's degree information. Be specific about what to look for.
            Return only valid JSON, no other text.
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"Search plan: {result['search_intent']}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            # Fallback plan
            return {
                "search_intent": f"Find information about: {user_query}",
                "search_terms": user_query.split(),
                "website_types": ["university websites"],
                "information_types": ["general admission info"],
                "specific_programs": ["PhD", "Master"],
                "universities_mentioned": [],
                "general_search_strategy": "Search university websites for relevant information"
            }
    
    async def _find_relevant_websites(self, search_plan: Dict[str, Any]) -> List[str]:
        """Intelligently find websites to scrape based on the search plan"""
        try:
            websites = []
            
            # If specific universities mentioned, go directly to their sites
            for university in search_plan.get("universities_mentioned", []):
                university_urls = await self._get_university_urls(university)
                websites.extend(university_urls)
            
            # If no specific universities, use search terms to find relevant sites
            if not websites:
                search_urls = await self._search_for_relevant_sites(search_plan)
                websites.extend(search_urls)
            
            # Remove duplicates and limit to reasonable number
            unique_websites = list(set(websites))[:10]
            logger.info(f"Found {len(unique_websites)} websites to scrape")
            
            return unique_websites
            
        except Exception as e:
            logger.error(f"Error finding websites: {e}")
            return []
    
    async def _get_university_urls(self, university_name: str) -> List[str]:
        """Get relevant URLs for a specific university using Gemini"""
        try:
            prompt = f"""
            For the university "{university_name}", provide likely URLs for graduate admissions information.
            
            Return a JSON list of URLs like:
            [
                "https://university.edu/graduate",
                "https://university.edu/admissions/graduate",
                "https://cs.university.edu/graduate"
            ]
            
            Focus on:
            - Main graduate admissions pages
            - Department graduate programs
            - PhD and Master's program pages
            
            Return only valid JSON array, no other text.
            """
            
            response = self.model.generate_content(prompt)
            urls = json.loads(response.text)
            
            # Also add some common patterns
            university_lower = university_name.lower().replace(" ", "").replace("university", "").replace("of", "")
            
            common_patterns = [
                f"https://{university_lower}.edu/graduate",
                f"https://www.{university_lower}.edu/admissions",
                f"https://grad.{university_lower}.edu",
                f"https://gradschool.{university_lower}.edu"
            ]
            
            urls.extend(common_patterns)
            return list(set(urls))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting university URLs: {e}")
            # Fallback to basic patterns
            university_lower = university_name.lower().replace(" ", "")
            return [
                f"https://{university_lower}.edu",
                f"https://www.{university_lower}.edu/graduate"
            ]
    
    async def _search_for_relevant_sites(self, search_plan: Dict[str, Any]) -> List[str]:
        """Use Gemini to suggest relevant websites based on search terms"""
        try:
            prompt = f"""
            Based on this search plan: {json.dumps(search_plan)}
            
            Suggest 8-10 university websites that would likely have this information.
            Focus on major research universities with strong graduate programs.
            
            Return a JSON list of URLs like:
            [
                "https://stanford.edu/academics/graduate",
                "https://mit.edu/academics/grad.html"
            ]
            
            Return only valid JSON array, no other text.
            """
            
            response = self.model.generate_content(prompt)
            urls = json.loads(response.text)
            return urls
            
        except Exception as e:
            logger.error(f"Error finding relevant sites: {e}")
            # Fallback to common graduate sites
            return [
                "https://www.harvard.edu/academics/graduate-and-professional-programs/",
                "https://www.stanford.edu/academics/",
                "https://www.mit.edu/academics/grad.html",
                "https://www.berkeley.edu/academics/",
                "https://www.cmu.edu/graduate/",
                "https://www.caltech.edu/academics/graduate"
            ]
    
    async def _scrape_websites(self, websites: List[str], search_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape the identified websites for relevant information"""
        scraped_data = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        ) as session:
            
            tasks = [self._scrape_single_website(session, url, search_plan) for url in websites]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result.get("content"):
                    scraped_data.append(result)
        
        logger.info(f"Successfully scraped {len(scraped_data)} websites")
        return scraped_data
    
    async def _scrape_single_website(self, session: aiohttp.ClientSession, url: str, search_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a single website"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract relevant information based on search plan
                    extracted_info = await self._extract_relevant_info(soup, search_plan, url)
                    
                    return {
                        "url": url,
                        "title": soup.title.string if soup.title else "No title",
                        "content": extracted_info,
                        "scraped_at": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Failed to scrape {url}: HTTP {response.status}")
                    return {"url": url, "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {"url": url, "error": str(e)}
    
    async def _extract_relevant_info(self, soup: BeautifulSoup, search_plan: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extract relevant information from parsed HTML"""
        try:
            # Get all text content
            page_text = soup.get_text()
            
            # Extract specific elements that might contain admission info
            info = {
                "headings": [],
                "links": [],
                "text_content": "",
                "tables": [],
                "lists": []
            }
            
            # Extract headings
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                text = heading.get_text().strip()
                if text and len(text) < 200:  # Reasonable heading length
                    info["headings"].append(text)
            
            # Extract relevant links
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip()
                link_url = urljoin(url, link['href'])
                if link_text and any(keyword in link_text.lower() for keyword in 
                    ['admission', 'phd', 'master', 'graduate', 'program', 'requirement', 'apply', 'deadline']):
                    info["links"].append({"text": link_text, "url": link_url})
            
            # Extract tables (often contain admission requirements)
            for table in soup.find_all('table'):
                table_data = []
                for row in table.find_all('tr'):
                    row_data = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                    if row_data and any(cell for cell in row_data):  # Non-empty row
                        table_data.append(row_data)
                if table_data:
                    info["tables"].append(table_data)
            
            # Extract lists (requirements, deadlines, etc.)
            for ul in soup.find_all(['ul', 'ol']):
                list_items = []
                for li in ul.find_all('li'):
                    item_text = li.get_text().strip()
                    if item_text and len(item_text) < 500:  # Reasonable item length
                        list_items.append(item_text)
                if list_items:
                    info["lists"].append(list_items)
            
            # Get relevant text content (limited to avoid too much data)
            info["text_content"] = page_text[:3000]  # First 3000 characters
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting info: {e}")
            return {"error": str(e)}
    
    async def _synthesize_information(self, user_query: str, scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Gemini to synthesize the scraped information into a helpful response"""
        try:
            # Prepare scraped content for Gemini
            content_summary = []
            source_links = []
            
            for data in scraped_data:
                if data.get("content"):
                    content_summary.append({
                        "source": data["url"],
                        "title": data.get("title", ""),
                        "headings": data["content"].get("headings", [])[:5],  # Top 5 headings
                        "links": data["content"].get("links", [])[:5],  # Top 5 relevant links
                        "text_preview": data["content"].get("text_content", "")[:800]  # First 800 chars
                    })
                    source_links.append(data["url"])
            
            # Use Gemini to synthesize the information
            synthesis_prompt = f"""
            User asked: "{user_query}"
            
            I scraped the following websites and found this information:
            {json.dumps(content_summary, indent=2)}
            
            Please provide a comprehensive, helpful response that:
            1. Directly answers the user's question
            2. Includes specific information found (requirements, deadlines, contact info, etc.)
            3. Organizes information clearly with headings and bullet points
            4. Mentions which sources the information came from
            5. Suggests next steps or additional resources if relevant
            
            Focus on PhD and Master's admission information. Be specific and factual.
            Format your response in clear, readable text with proper structure.
            """
            
            response = self.model.generate_content(synthesis_prompt)
            synthesized_response = response.text
            
            # Calculate confidence based on amount of relevant data found
            confidence = min(0.9, len(scraped_data) * 0.1 + (len(source_links) * 0.05))
            
            return {
                "response": synthesized_response,
                "information": content_summary,
                "source_links": source_links,
                "confidence": confidence,
                "total_sources": len(source_links)
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing information: {e}")
            return {
                "response": f"I found information from {len(scraped_data)} sources but encountered an error synthesizing it. Please check the source links for details.",
                "information": scraped_data,
                "source_links": [data.get("url") for data in scraped_data if data.get("url")],
                "confidence": 0.3,
                "total_sources": len(scraped_data)
            }
    
    def _save_search_results(self, user_query: str, search_plan: Dict[str, Any], scraped_data: List[Dict[str, Any]], final_response: Dict[str, Any]):
        """Save search results to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO search_results 
                (user_query, search_intent, websites_found, information_extracted, source_links, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_query,
                search_plan.get("search_intent", ""),
                json.dumps([data.get("url") for data in scraped_data]),
                json.dumps(final_response.get("information", [])),
                json.dumps(final_response.get("source_links", [])),
                final_response.get("confidence", 0.0)
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT user_query, search_intent, search_timestamp, confidence_score,
                       json_extract(source_links, '$') as source_count
                FROM search_results 
                ORDER BY search_timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return []