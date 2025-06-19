# app/scrapers/real_university_scraper.py
import aiohttp
import asyncio
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json
from app.models.firebase_models import Faculty, University, HiringSignal
from app.core.logging import get_logger

logger = get_logger(__name__)

class RealUniversityScraper:
    """Real web scraper for university faculty information"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.university_configs = {
            'stanford': {
                'name': 'Stanford University',
                'base_url': 'https://cs.stanford.edu',
                'faculty_path': '/directory/faculty',
                'selectors': {
                    'faculty_list': '.person-card, .faculty-card, .directory-entry',
                    'name': 'h3, h2, .name, .person-name',
                    'title': '.title, .position, .rank',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="stanford.edu"], a[href*="/people/"], .homepage-link',
                    'research': '.research, .interests, .bio'
                }
            },
            'mit': {
                'name': 'Massachusetts Institute of Technology',
                'base_url': 'https://www.csail.mit.edu',
                'faculty_path': '/people',
                'selectors': {
                    'faculty_list': '.person, .faculty-member, .people-item',
                    'name': '.name, h3, h2',
                    'title': '.title, .position',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="mit.edu"], .website',
                    'research': '.research, .bio, .description'
                }
            },
            'cmu': {
                'name': 'Carnegie Mellon University',
                'base_url': 'https://csd.cmu.edu',
                'faculty_path': '/directory/faculty',
                'selectors': {
                    'faculty_list': '.faculty-card, .person',
                    'name': '.name, h3',
                    'title': '.title, .position',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="cmu.edu"], .homepage',
                    'research': '.research, .interests'
                }
            },
            'berkeley': {
                'name': 'University of California, Berkeley',
                'base_url': 'https://eecs.berkeley.edu',
                'faculty_path': '/faculty',
                'selectors': {
                    'faculty_list': '.faculty-item, .person',
                    'name': '.name, h3',
                    'title': '.title, .rank',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="berkeley.edu"], .website',
                    'research': '.research, .bio'
                }
            },
            'caltech': {
                'name': 'California Institute of Technology',
                'base_url': 'https://www.cms.caltech.edu',
                'faculty_path': '/people/faculty',
                'selectors': {
                    'faculty_list': '.faculty-member, .person',
                    'name': '.name, h3, h2',
                    'title': '.title, .position',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="caltech.edu"], .homepage',
                    'research': '.research, .bio'
                }
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch URL with retry logic"""
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(1 * attempt)  # Progressive delay
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    elif response.status == 429:  # Rate limited
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed for {url}")
        
        return None
    
    async def scrape_university(self, university_key: str) -> List[Dict[str, Any]]:
        """Scrape faculty data for a specific university"""
        if university_key not in self.university_configs:
            logger.error(f"No configuration for university: {university_key}")
            return []
        
        config = self.university_configs[university_key]
        faculty_url = config['base_url'] + config['faculty_path']
        
        logger.info(f"Scraping faculty from {config['name']}: {faculty_url}")
        
        try:
            # Fetch main faculty page
            html_content = await self.fetch_with_retry(faculty_url)
            if not html_content:
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract faculty information
            faculty_data = await self.extract_faculty_from_page(soup, config, university_key)
            
            logger.info(f"Found {len(faculty_data)} faculty members at {config['name']}")
            return faculty_data
            
        except Exception as e:
            logger.error(f"Error scraping {config['name']}: {e}")
            return []
    
    async def extract_faculty_from_page(self, soup: BeautifulSoup, config: Dict, university_key: str) -> List[Dict[str, Any]]:
        """Extract faculty information from the faculty page"""
        faculty_data = []
        selectors = config['selectors']
        
        # Find faculty entries
        faculty_elements = soup.select(selectors['faculty_list'])
        
        for element in faculty_elements[:20]:  # Limit to 20 per university for now
            try:
                faculty_info = await self.extract_single_faculty(element, config, university_key)
                if faculty_info:
                    faculty_data.append(faculty_info)
                    
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error extracting faculty info: {e}")
                continue
        
        return faculty_data
    
    async def extract_single_faculty(self, element: BeautifulSoup, config: Dict, university_key: str) -> Optional[Dict[str, Any]]:
        """Extract information for a single faculty member"""
        selectors = config['selectors']
        
        # Extract name
        name_elem = element.select_one(selectors['name'])
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        if not name or len(name) < 3:
            return None
        
        # Extract other information
        title_elem = element.select_one(selectors['title'])
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract email
        email_elem = element.select_one(selectors['email'])
        email = None
        if email_elem:
            href = email_elem.get('href', '')
            if href.startswith('mailto:'):
                email = href[7:]
        
        # Extract homepage
        homepage_elem = element.select_one(selectors['homepage'])
        homepage = None
        if homepage_elem:
            href = homepage_elem.get('href', '')
            if href:
                homepage = urljoin(config['base_url'], href)
        
        # Extract research areas
        research_elem = element.select_one(selectors['research'])
        research_areas = []
        if research_elem:
            research_text = research_elem.get_text().lower()
            research_areas = self.extract_research_keywords(research_text)
        
        # Try to get more detailed info from personal page
        additional_info = {}
        if homepage:
            additional_info = await self.scrape_personal_page(homepage)
        
        # Detect hiring signals
        hiring_info = self.detect_hiring_signals(element.get_text(), additional_info.get('content', ''))
        
        faculty_info = {
            'name': name,
            'title': title,
            'email': email,
            'university_name': config['name'],
            'department': 'Computer Science',  # Default for CS departments
            'homepage_url': homepage,
            'research_areas': research_areas or additional_info.get('research_areas', []),
            'hiring_status': hiring_info['status'],
            'hiring_probability': hiring_info['probability'],
            'hiring_indicators': hiring_info['indicators'],
            'last_scraped': datetime.utcnow(),
            'scraping_sources': [config['base_url']]
        }
        
        return faculty_info
    
    def extract_research_keywords(self, text: str) -> List[str]:
        """Extract research keywords from text"""
        research_keywords = {
            'machine learning': ['machine learning', 'ml', 'deep learning', 'neural network'],
            'artificial intelligence': ['artificial intelligence', 'ai', 'intelligent systems'],
            'computer vision': ['computer vision', 'cv', 'image processing', 'visual computing'],
            'natural language processing': ['nlp', 'natural language', 'text processing', 'computational linguistics'],
            'robotics': ['robotics', 'robot', 'autonomous systems', 'embodied ai'],
            'systems': ['systems', 'distributed systems', 'operating systems', 'computer systems'],
            'theory': ['theory', 'algorithms', 'complexity', 'theoretical computer science'],
            'security': ['security', 'cybersecurity', 'cryptography', 'privacy'],
            'databases': ['database', 'data management', 'big data', 'data systems'],
            'networks': ['networking', 'networks', 'protocols', 'internet'],
            'hci': ['hci', 'human computer interaction', 'user interface', 'ux'],
            'graphics': ['graphics', 'computer graphics', 'visualization', 'rendering'],
            'software engineering': ['software engineering', 'programming languages', 'software development'],
            'bioinformatics': ['bioinformatics', 'computational biology', 'genomics']
        }
        
        found_areas = []
        text_lower = text.lower()
        
        for area, keywords in research_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_areas.append(area)
        
        return found_areas
    
    def detect_hiring_signals(self, main_text: str, additional_text: str = '') -> Dict[str, Any]:
        """Detect hiring signals in faculty text"""
        combined_text = (main_text + ' ' + additional_text).lower()
        
        # Positive hiring signals
        positive_signals = [
            'accepting students', 'recruiting phd', 'graduate positions',
            'seeking students', 'applications welcome', 'phd openings',
            'prospective students', 'interested students should',
            'looking for motivated', 'graduate student positions',
            'available positions', 'currently recruiting', 'open positions'
        ]
        
        # Negative hiring signals
        negative_signals = [
            'not accepting', 'no openings', 'full capacity', 'no positions',
            'not taking students', 'fully booked', 'no space', 'not recruiting'
        ]
        
        positive_count = sum(1 for signal in positive_signals if signal in combined_text)
        negative_count = sum(1 for signal in negative_signals if signal in combined_text)
        
        # Determine hiring status and probability
        if negative_count > 0:
            status = "not_hiring"
            probability = max(0.1, 0.3 - (negative_count * 0.1))
        elif positive_count > 0:
            status = "hiring"
            probability = min(0.9, 0.7 + (positive_count * 0.1))
        else:
            status = "unknown"
            probability = 0.5
        
        # Find specific indicators
        indicators = []
        for signal in positive_signals:
            if signal in combined_text:
                indicators.append(signal)
        
        for signal in negative_signals:
            if signal in combined_text:
                indicators.append(signal)
        
        return {
            'status': status,
            'probability': probability,
            'indicators': indicators
        }
    
    async def scrape_personal_page(self, url: str) -> Dict[str, Any]:
        """Scrape additional information from personal pages"""
        try:
            html_content = await self.fetch_with_retry(url)
            if not html_content:
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract content
            content = soup.get_text()
            research_areas = self.extract_research_keywords(content)
            
            return {
                'content': content[:1000],  # First 1000 chars
                'research_areas': research_areas
            }
            
        except Exception as e:
            logger.warning(f"Error scraping personal page {url}: {e}")
            return {}

class SocialMediaScraper:
    """Real scraper for social media hiring signals"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_reddit_hiring(self, subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """Scrape Reddit for hiring discussions"""
        if not subreddits:
            subreddits = ['gradadmissions', 'PhD', 'AskAcademia', 'gradschool', 'MachineLearning']
        
        hiring_signals = []
        
        for subreddit in subreddits:
            try:
                # Use Reddit's JSON API
                url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        for post_data in posts:
                            post = post_data.get('data', {})
                            if self.is_hiring_related(post):
                                signal = self.process_reddit_post(post, subreddit)
                                if signal:
                                    hiring_signals.append(signal)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit}: {e}")
        
        return hiring_signals
    
    def is_hiring_related(self, post: Dict) -> bool:
        """Check if a Reddit post is hiring-related"""
        title = post.get('title', '').lower()
        text = post.get('selftext', '').lower()
        
        hiring_keywords = [
            'professor hiring', 'faculty position', 'phd advisor',
            'accepting students', 'graduate positions', 'lab openings',
            'research opportunities', 'advisor looking for',
            'positions available', 'recruiting students', 'fall 2025',
            'fall 2026', 'faculty search', 'hiring announcement'
        ]
        
        combined_text = f"{title} {text}"
        return any(keyword in combined_text for keyword in hiring_keywords)
    
    def process_reddit_post(self, post: Dict, subreddit: str) -> Optional[Dict[str, Any]]:
        """Process a hiring-related Reddit post"""
        try:
            title = post.get('title', '')
            content = post.get('selftext', '')
            
            # Extract potential faculty/university names
            extracted_info = self.extract_hiring_info(f"{title} {content}")
            
            if not extracted_info:
                return None
            
            return {
                'source': 'reddit',
                'source_url': f"https://reddit.com{post.get('permalink', '')}",
                'content': f"{title}\n\n{content}"[:500],
                'signal_type': 'hiring_discussion',
                'confidence_score': self.calculate_confidence(title, content),
                'extracted_info': extracted_info,
                'processed': False
            }
            
        except Exception as e:
            logger.error(f"Error processing Reddit post: {e}")
            return None
    
    def extract_hiring_info(self, text: str) -> Dict[str, Any]:
        """Extract hiring information from text"""
        # Common university patterns
        university_patterns = [
            r'(Stanford|MIT|Carnegie Mellon|Berkeley|Caltech|Harvard|Princeton|Yale)',
            r'University of ([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+ University)',
            r'([A-Z][a-zA-Z\s]+ Institute of Technology)'
        ]
        
        # Faculty name patterns (Dr./Prof. followed by name)
        faculty_patterns = [
            r'(?:Dr\.|Prof\.|Professor)\s+([A-Z][a-zA-Z\-]+\s+[A-Z][a-zA-Z\-]+)',
            r'([A-Z][a-zA-Z\-]+\s+[A-Z][a-zA-Z\-]+)(?:\s+is\s+(?:hiring|recruiting|accepting))'
        ]
        
        extracted = {}
        
        # Extract universities
        for pattern in university_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                extracted['universities'] = matches
                break
        
        # Extract faculty names
        for pattern in faculty_patterns:
            matches = re.findall(pattern, text)
            if matches:
                extracted['faculty_names'] = matches
                break
        
        # Extract research areas
        research_areas = []
        research_keywords = [
            'machine learning', 'AI', 'computer vision', 'NLP', 'robotics',
            'systems', 'theory', 'security', 'databases', 'HCI'
        ]
        
        text_lower = text.lower()
        for keyword in research_keywords:
            if keyword in text_lower:
                research_areas.append(keyword)
        
        if research_areas:
            extracted['research_areas'] = research_areas
        
        return extracted if extracted else None
    
    def calculate_confidence(self, title: str, content: str) -> float:
        """Calculate confidence score for hiring signal"""
        score = 0.0
        
        # Title indicators (higher weight)
        title_lower = title.lower()
        if any(word in title_lower for word in ['hiring', 'recruiting', 'positions']):
            score += 0.4
        
        # Content indicators
        content_lower = content.lower()
        hiring_terms = ['accepting students', 'phd openings', 'graduate positions']
        for term in hiring_terms:
            if term in content_lower:
                score += 0.2
        
        # University/faculty name presence
        if any(char.isupper() for char in title + content):  # Proper nouns
            score += 0.2
        
        # Recency (if post is recent)
        score += 0.2  # Assume recent for now
        
        return min(1.0, score)

# Scraping orchestrator
class ScrapingOrchestrator:
    """Orchestrates all scraping activities"""
    
    def __init__(self):
        self.university_scraper = None
        self.social_scraper = None
    
    async def run_daily_scraping(self):
        """Run daily scraping routine"""
        logger.info("Starting daily scraping routine")
        
        # Scrape universities
        await self.scrape_universities()
        
        # Scrape social media
        await self.scrape_social_media()
        
        logger.info("Daily scraping routine completed")
    
    async def scrape_universities(self):
        """Scrape all configured universities"""
        async with RealUniversityScraper() as scraper:
            universities = ['stanford', 'mit', 'cmu', 'berkeley', 'caltech']
            
            for university_key in universities:
                try:
                    faculty_data = await scraper.scrape_university(university_key)
                    
                    # Save to Firebase
                    for faculty_info in faculty_data:
                        await Faculty.create(**faculty_info)
                    
                    logger.info(f"Saved {len(faculty_data)} faculty from {university_key}")
                    
                    # Rate limiting between universities
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error scraping {university_key}: {e}")
    
    async def scrape_social_media(self):
        """Scrape social media for hiring signals"""
        async with SocialMediaScraper() as scraper:
            try:
                # Scrape Reddit
                signals = await scraper.scrape_reddit_hiring()
                
                # Save hiring signals
                for signal in signals:
                    await HiringSignal.create(**signal)
                
                logger.info(f"Saved {len(signals)} hiring signals from social media")
                
            except Exception as e:
                logger.error(f"Error scraping social media: {e}")