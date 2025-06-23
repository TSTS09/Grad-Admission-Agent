import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import praw
import tweepy
from serpapi import GoogleSearch

from app.core.config import settings
from app.core.logging import get_logger
from app.models.firebase_models import Faculty, Program, HiringSignal

logger = get_logger(__name__)

class RealTimeIntelligenceAgent:
    """Real-time intelligence agent that scrapes based on user prompts"""
    
    def __init__(self):
        # Initialize APIs
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Reddit API
        self.reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent="GradAdmissionsIntelligence/1.0"
        ) if hasattr(settings, 'REDDIT_CLIENT_ID') else None
        
        # Twitter API  
        self.twitter = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN
        ) if hasattr(settings, 'TWITTER_BEARER_TOKEN') else None
        
        self.session = None
        
    async def process_user_query(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point - processes user query with real web scraping"""
        
        try:
            logger.info(f"Processing real-time query: {user_message}")
            
            # Step 1: Analyze user intent
            query_analysis = await self._analyze_query_with_gemini(user_message)
            
            # Step 2: Execute real-time scraping based on analysis
            scraped_data = await self._execute_intelligent_scraping(query_analysis)
            
            # Step 3: Synthesize results with Gemini
            final_response = await self._synthesize_with_gemini(user_message, scraped_data)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in real-time intelligence: {e}")
            return {
                "response": "I encountered an error while gathering real-time information. Please try again.",
                "faculty_matches": [],
                "program_matches": [],
                "confidence_score": 0.0,
                "sources": []
            }
    
    async def _analyze_query_with_gemini(self, user_message: str) -> Dict[str, Any]:
        """Use Gemini to understand user intent and generate scraping strategy"""
        
        analysis_prompt = f"""
        Analyze this graduate admissions query and create a scraping strategy:
        
        Query: "{user_message}"
        
        Extract and return JSON:
        {{
            "intent": "faculty_hiring|program_requirements|admission_deadlines|application_tips|general_advice",
            "universities": ["universities mentioned or to research if field mentioned"],
            "departments": ["CS", "EE", "ME", etc.],
            "faculty_names": ["specific professors if mentioned"],
            "degree_type": "PhD|MS|MEng",
            "timeline": "Fall 2026|Spring 2027",
            "search_strategies": {{
                "university_sites": ["specific search terms for university websites"],
                "reddit_queries": ["terms for Reddit searches"],
                "twitter_queries": ["terms for Twitter searches"],
                "academic_forums": ["terms for academic job boards"]
            }},
            "priority_sources": ["reddit", "university_websites", "twitter", "academic_forums"]
        }}
        
        If no universities mentioned but field is specified, suggest top 10 US universities for that field.
        Focus on STEM fields especially engineering and computer science.
        """
        
        try:
            response = self.gemini_model.generate_content(analysis_prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._fallback_analysis(user_message)
    
    def _fallback_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback analysis if Gemini fails"""
        # Simple keyword extraction
        message_lower = message.lower()
        
        universities = []
        uni_keywords = {
            'stanford': 'Stanford University',
            'mit': 'MIT',
            'berkeley': 'UC Berkeley', 
            'cmu': 'Carnegie Mellon',
            'caltech': 'Caltech',
            'harvard': 'Harvard',
            'princeton': 'Princeton'
        }
        
        for keyword, full_name in uni_keywords.items():
            if keyword in message_lower:
                universities.append(full_name)
        
        departments = []
        if any(term in message_lower for term in ['cs', 'computer science', 'computer']):
            departments.append('Computer Science')
        if any(term in message_lower for term in ['ee', 'electrical', 'engineering']):
            departments.append('Electrical Engineering')
            
        return {
            "intent": "faculty_hiring",
            "universities": universities or ["Stanford University", "MIT", "UC Berkeley"],
            "departments": departments or ["Computer Science"],
            "faculty_names": [],
            "degree_type": "PhD",
            "timeline": "Fall 2026",
            "search_strategies": {
                "university_sites": [f"{' '.join(universities)} {' '.join(departments)} faculty"],
                "reddit_queries": [f"graduate admissions {' '.join(departments)}"],
                "twitter_queries": [f"PhD hiring {' '.join(departments)}"],
                "academic_forums": [f"{' '.join(departments)} PhD positions"]
            },
            "priority_sources": ["reddit", "university_websites", "twitter"]
        }
    
    async def _execute_intelligent_scraping(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute real scraping based on analysis"""
        
        all_scraped_data = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; GradBot/1.0)'}
        ) as session:
            self.session = session
            
            tasks = []
            
            # Priority-based scraping
            for source_type in analysis.get("priority_sources", []):
                if source_type == "reddit" and self.reddit:
                    tasks.append(self._scrape_reddit_discussions(analysis))
                elif source_type == "university_websites":
                    tasks.append(self._scrape_university_sites(analysis))
                elif source_type == "twitter" and self.twitter:
                    tasks.append(self._scrape_twitter_signals(analysis))
                elif source_type == "academic_forums":
                    tasks.append(self._scrape_academic_forums(analysis))
            
            # Execute all scraping tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_scraped_data.extend(result)
        
        return all_scraped_data
    
    async def _scrape_reddit_discussions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape Reddit for real graduate admissions discussions"""
        
        if not self.reddit:
            return []
        
        reddit_data = []
        
        try:
            # Target subreddits for graduate admissions
            subreddits = ['gradadmissions', 'PhD', 'GradSchool', 'MachineLearning', 'compsci', 'AskAcademia']
            
            for query in analysis["search_strategies"]["reddit_queries"]:
                for subreddit_name in subreddits:
                    try:
                        subreddit = self.reddit.subreddit(subreddit_name)
                        
                        # Search recent posts
                        for post in subreddit.search(query, time_filter="month", limit=10):
                            content = f"Title: {post.title}\n\nContent: {post.selftext}\n\n"
                            
                            # Get valuable comments
                            post.comments.replace_more(limit=0)
                            for comment in post.comments[:3]:
                                if hasattr(comment, 'body') and len(comment.body) > 50:
                                    content += f"Comment: {comment.body}\n"
                            
                            reddit_data.append({
                                "source_type": "reddit",
                                "url": f"https://reddit.com{post.permalink}",
                                "content": content,
                                "metadata": {
                                    "subreddit": subreddit_name,
                                    "upvotes": post.score,
                                    "created": datetime.fromtimestamp(post.created_utc)
                                }
                            })
                            
                    except Exception as e:
                        logger.error(f"Error scraping subreddit {subreddit_name}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Reddit scraping error: {e}")
        
        return reddit_data
    
    async def _scrape_university_sites(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape real university websites for faculty and program info"""
        
        university_data = []
        
        try:
            # Use SerpAPI for targeted university searches
            if hasattr(settings, 'SERPAPI_KEY'):
                for query in analysis["search_strategies"]["university_sites"]:
                    search = GoogleSearch({
                        "q": f"{query} site:edu",
                        "api_key": settings.SERPAPI_KEY,
                        "num": 10
                    })
                    
                    results = search.get_dict()
                    
                    for result in results.get("organic_results", []):
                        url = result.get("link", "")
                        
                        # Only scrape .edu domains
                        if ".edu" in url:
                            content = await self._fetch_university_page(url)
                            if content:
                                university_data.append({
                                    "source_type": "university_website",
                                    "url": url,
                                    "content": content,
                                    "metadata": {
                                        "title": result.get("title", ""),
                                        "snippet": result.get("snippet", "")
                                    }
                                })
            
            # Also try direct university department searches
            for university in analysis.get("universities", []):
                for department in analysis.get("departments", []):
                    direct_urls = self._generate_university_urls(university, department)
                    
                    for url in direct_urls:
                        content = await self._fetch_university_page(url)
                        if content:
                            university_data.append({
                                "source_type": "university_website",
                                "url": url,
                                "content": content,
                                "metadata": {
                                    "university": university,
                                    "department": department
                                }
                            })
                            
        except Exception as e:
            logger.error(f"University scraping error: {e}")
        
        return university_data
    
    def _generate_university_urls(self, university: str, department: str) -> List[str]:
        """Generate likely URLs for university departments"""
        
        # Mapping of universities to their domains and department patterns
        university_mappings = {
            "Stanford University": {
                "domain": "stanford.edu",
                "cs_urls": ["https://cs.stanford.edu/people/faculty", "https://cs.stanford.edu/directory/faculty"]
            },
            "MIT": {
                "domain": "mit.edu", 
                "cs_urls": ["https://www.csail.mit.edu/people", "https://www.eecs.mit.edu/people/faculty"]
            },
            "UC Berkeley": {
                "domain": "berkeley.edu",
                "cs_urls": ["https://eecs.berkeley.edu/faculty", "https://www2.eecs.berkeley.edu/Faculty/"]
            },
            "Carnegie Mellon": {
                "domain": "cmu.edu",
                "cs_urls": ["https://www.cs.cmu.edu/directory/faculty", "https://csd.cmu.edu/people/faculty"]
            }
        }
        
        urls = []
        
        if university in university_mappings:
            mapping = university_mappings[university]
            if department.lower() in ["computer science", "cs"]:
                urls.extend(mapping.get("cs_urls", []))
        
        return urls
    
    async def _fetch_university_page(self, url: str) -> Optional[str]:
        """Fetch and extract content from university page"""
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "footer", "header"]):
                        element.decompose()
                    
                    # Extract faculty information specifically
                    faculty_info = []
                    
                    # Look for faculty listings
                    faculty_elements = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'faculty|person|member', re.I))
                    
                    for element in faculty_elements:
                        text = element.get_text(strip=True)
                        if len(text) > 30 and any(title in text for title in ['Professor', 'Dr.', 'Assistant', 'Associate']):
                            faculty_info.append(text)
                    
                    # Also get general page text
                    page_text = soup.get_text(separator=' ', strip=True)
                    
                    # Combine faculty-specific info with general content
                    combined_content = '\n'.join(faculty_info) + '\n\n' + page_text[:2000]
                    
                    return combined_content
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def _scrape_twitter_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape Twitter for hiring signals and announcements"""
        
        if not self.twitter:
            return []
        
        twitter_data = []
        
        try:
            for query in analysis["search_strategies"]["twitter_queries"]:
                # Search recent tweets
                tweets = tweepy.Paginator(
                    self.twitter.search_recent_tweets,
                    query=f"{query} -is:retweet",
                    max_results=50
                ).flatten(limit=50)
                
                for tweet in tweets:
                    twitter_data.append({
                        "source_type": "twitter",
                        "url": f"https://twitter.com/user/status/{tweet.id}",
                        "content": tweet.text,
                        "metadata": {
                            "tweet_id": tweet.id,
                            "created_at": tweet.created_at
                        }
                    })
                    
        except Exception as e:
            logger.error(f"Twitter scraping error: {e}")
        
        return twitter_data
    
    async def _scrape_academic_forums(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape academic forums and job boards"""
        
        forum_data = []
        
        try:
            # Target academic forums
            forum_sites = [
                "thegradcafe.com",
                "academicjobsonline.org", 
                "jobs.ac.uk"
            ]
            
            if hasattr(settings, 'SERPAPI_KEY'):
                for query in analysis["search_strategies"]["academic_forums"]:
                    for site in forum_sites:
                        search = GoogleSearch({
                            "q": f"{query} site:{site}",
                            "api_key": settings.SERPAPI_KEY,
                            "num": 5
                        })
                        
                        results = search.get_dict()
                        
                        for result in results.get("organic_results", []):
                            url = result.get("link", "")
                            content = await self._fetch_forum_content(url)
                            
                            if content:
                                forum_data.append({
                                    "source_type": "academic_forum",
                                    "url": url,
                                    "content": content,
                                    "metadata": {
                                        "forum_site": site,
                                        "title": result.get("title", "")
                                    }
                                })
                                
        except Exception as e:
            logger.error(f"Academic forum scraping error: {e}")
        
        return forum_data
    
    async def _fetch_forum_content(self, url: str) -> Optional[str]:
        """Fetch content from academic forums"""
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "footer", "ads"]):
                        element.decompose()
                    
                    # Extract main content
                    text = soup.get_text(separator=' ', strip=True)
                    return text[:3000]  # Limit content length
                    
        except Exception as e:
            logger.error(f"Error fetching forum content from {url}: {e}")
            return None
    
    async def _synthesize_with_gemini(self, original_query: str, scraped_data: List[Dict]) -> Dict[str, Any]:
        """Use Gemini to synthesize all scraped data into actionable response"""
        
        # Prepare context for Gemini
        context = ""
        sources = []
        
        for i, data in enumerate(scraped_data[:15]):  # Limit to prevent token overflow
            context += f"\n--- SOURCE {i+1} ({data['source_type']}) ---\n"
            context += f"URL: {data['url']}\n"
            context += f"Content: {data['content'][:800]}\n"  # Limit per source
            sources.append(data['url'])
        
        synthesis_prompt = f"""
        You are an expert graduate admissions consultant. Analyze the following real-time scraped data to answer this query:
        
        QUERY: "{original_query}"
        
        REAL SCRAPED DATA:
        {context}
        
        Provide a comprehensive response in JSON format:
        {{
            "response": "Clear, actionable response based on the real data found",
            "faculty_matches": [
                {{
                    "name": "Faculty name if found",
                    "university": "University",
                    "research_areas": ["areas"],
                    "hiring_status": "hiring/maybe/unknown",
                    "evidence": "Specific evidence from scraped data",
                    "match_score": 0.85
                }}
            ],
            "program_matches": [
                {{
                    "name": "Program name",
                    "university": "University", 
                    "degree_type": "PhD/MS",
                    "requirements": "Requirements found",
                    "deadlines": "Deadline info",
                    "match_score": 0.80
                }}
            ],
            "key_insights": [
                "Important insight 1 from scraped data",
                "Important insight 2 from scraped data"
            ],
            "confidence_score": 0.75
        }}
        
        IMPORTANT: Base your response ONLY on the scraped data provided. If information isn't in the data, indicate uncertainty.
        """
        
        try:
            response = self.gemini_model.generate_content(synthesis_prompt)
            result = json.loads(response.text)
            
            # Add sources and metadata
            result["sources"] = sources
            result["data_sources_count"] = len(scraped_data)
            result["last_updated"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini synthesis: {e}")
            return {
                "response": f"I found {len(scraped_data)} real-time sources but had trouble synthesizing them. Key sources include Reddit discussions, university websites, and academic forums.",
                "faculty_matches": [],
                "program_matches": [],
                "key_insights": [f"Found {len(scraped_data)} real-time sources"],
                "confidence_score": 0.4,
                "sources": sources,
                "data_sources_count": len(scraped_data),
                "last_updated": datetime.now().isoformat()
            }

# Updated main chat agent to use real-time intelligence
class EnhancedChatAgent:
    """Enhanced chat agent with real-time web scraping"""
    
    def __init__(self):
        self.real_time_agent = RealTimeIntelligenceAgent()
    
    async def process_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """Process message with real-time intelligence"""
        
        # Use real-time agent for dynamic scraping
        response = await self.real_time_agent.process_user_query(message)
        
        # Add session metadata
        response["session_id"] = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return response