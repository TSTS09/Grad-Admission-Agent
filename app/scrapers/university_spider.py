import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.scrapers.base import BaseScraper
from app.core.logging import get_logger

logger = get_logger(__name__)

class UniversitySpider(BaseScraper):
    """Spider for scraping university faculty and program information"""
    
    def __init__(self):
        super().__init__("university_spider")
        
        # University-specific configurations
        self.university_configs = {
            'stanford': {
                'base_url': 'https://cs.stanford.edu',
                'faculty_path': '/directory/faculty',
                'faculty_selectors': {
                    'name': 'h3.person-name, h2.person-name, .faculty-name',
                    'title': '.person-title, .faculty-title',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="stanford.edu/~"], a[href*="/people/"]',
                    'research': '.research-interests, .person-bio, .faculty-bio'
                }
            },
            'mit': {
                'base_url': 'https://www.csail.mit.edu',
                'faculty_path': '/people',
                'faculty_selectors': {
                    'name': '.person-name, h3.name',
                    'title': '.person-title, .title',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="mit.edu/~"], a[href*="people"]',
                    'research': '.person-research, .research-areas'
                }
            },
            'cmu': {
                'base_url': 'https://csd.cmu.edu',
                'faculty_path': '/directory/faculty',
                'faculty_selectors': {
                    'name': '.person-name, h2.name',
                    'title': '.person-title, .position',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="cmu.edu/~"], a[href*="people"]',
                    'research': '.research-interests, .person-research'
                }
            },
            'berkeley': {
                'base_url': 'https://eecs.berkeley.edu',
                'faculty_path': '/faculty',
                'faculty_selectors': {
                    'name': '.faculty-name, h3.name',
                    'title': '.faculty-title, .title',
                    'email': 'a[href^="mailto:"]',
                    'homepage': 'a[href*="berkeley.edu/~"], a[href*="people"]',
                    'research': '.research-areas, .faculty-research'
                }
            }
        }
    
    async def scrape(self, universities: List[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Scrape faculty information from specified universities"""
        results = []
        
        universities = universities or list(self.university_configs.keys())
        
        for university in universities:
            if university not in self.university_configs:
                logger.warning(f"No configuration for university: {university}")
                continue
            
            try:
                faculty_data = await self.scrape_university_faculty(university)
                results.extend(faculty_data)
                
                logger.info(f"Scraped {len(faculty_data)} faculty from {university}")
                
            except Exception as e:
                logger.error(f"Error scraping {university}: {e}")
        
        return results
    
    async def scrape_university_faculty(self, university: str) -> List[Dict[str, Any]]:
        """Scrape faculty information from a specific university"""
        config = self.university_configs[university]
        faculty_url = config['base_url'] + config['faculty_path']
        
        # Fetch faculty listing page
        page_data = await self.fetch_url(faculty_url)
        if not page_data:
            return []
        
        soup = BeautifulSoup(page_data['content'], 'html.parser')
        
        # Find all faculty profile links
        faculty_links = self.extract_faculty_links(soup, config['base_url'])
        
        # Scrape individual faculty profiles
        faculty_data = []
        for link in faculty_links[:50]:  # Limit to 50 faculty per university
            profile_data = await self.scrape_faculty_profile(link, university, config)
            if profile_data:
                faculty_data.append(profile_data)
        
        return faculty_data
    
    def extract_faculty_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract faculty profile links from faculty listing page"""
        links = []
        
        # Common patterns for faculty profile links
        patterns = [
            'a[href*="/people/"]',
            'a[href*="/faculty/"]',
            'a[href*="/~"]',
            'a[href*="profile"]'
        ]
        
        for pattern in patterns:
            elements = soup.select(pattern)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in links:
                        links.append(full_url)
        
        # Also look for faculty names as links
        name_links = soup.select('a')
        for link in name_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if link text looks like a faculty name
            if (len(text.split()) >= 2 and 
                text[0].isupper() and 
                any(keyword in href.lower() for keyword in ['people', 'faculty', 'staff', '~'])):
                full_url = urljoin(base_url, href)
                if full_url not in links:
                    links.append(full_url)
        
        return links
    
    async def scrape_faculty_profile(self, url: str, university: str, config: Dict) -> Optional[Dict[str, Any]]:
        """Scrape individual faculty profile"""
        page_data = await self.fetch_url(url)
        if not page_data:
            return None
        
        soup = BeautifulSoup(page_data['content'], 'html.parser')
        selectors = config['faculty_selectors']
        
        # Extract faculty information
        name = self.extract_text_by_selector(soup, selectors['name'])
        title = self.extract_text_by_selector(soup, selectors['title'])
        email = self.extract_email(soup, selectors['email'])
        homepage = self.extract_homepage(soup, selectors['homepage'], url)
        research_areas = self.extract_research_areas(soup, selectors['research'])
        
        # Detect hiring signals
        hiring_signals = self.detect_hiring_signals(page_data['content'])
        
        if not name:
            return None
        
        return {
            'name': name,
            'title': title,
            'email': email,
            'homepage_url': homepage,
            'university': university,
            'department': 'Computer Science',  # Assume CS for now
            'research_areas': research_areas,
            'hiring_status': hiring_signals['status'],
            'hiring_probability': hiring_signals['probability'],
            'hiring_indicators': hiring_signals['indicators'],
            'profile_url': url,
            'scraped_at': page_data['scraped_at']
        }
    
    def extract_text_by_selector(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        selectors = selector.split(', ')
        
        for sel in selectors:
            element = soup.select_one(sel.strip())
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        
        return None
    
    def extract_email(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract email address"""
        element = soup.select_one(selector)
        if element:
            href = element.get('href', '')
            if href.startswith('mailto:'):
                return href[7:]  # Remove 'mailto:' prefix
        
        # Also search for email patterns in text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        matches = re.findall(email_pattern, text)
        
        return matches[0] if matches else None
    
    def extract_homepage(self, soup: BeautifulSoup, selector: str, current_url: str) -> Optional[str]:
        """Extract homepage URL"""
        element = soup.select_one(selector)
        if element:
            href = element.get('href')
            if href:
                return urljoin(current_url, href)
        
        # Look for "homepage" or "website" links
        homepage_links = soup.find_all('a', string=re.compile(r'homepage|website|personal', re.I))
        if homepage_links:
            href = homepage_links[0].get('href')
            if href:
                return urljoin(current_url, href)
        
        return None
    
    def extract_research_areas(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """Extract research areas/interests"""
        selectors = selector.split(', ')
        research_text = ""
        
        for sel in selectors:
            element = soup.select_one(sel.strip())
            if element:
                research_text = element.get_text()
                break
        
        if not research_text:
            # Look for common research keywords in the page
            full_text = soup.get_text().lower()
        else:
            full_text = research_text.lower()
        
        # Common CS research areas
        research_keywords = [
            'machine learning', 'artificial intelligence', 'computer vision',
            'natural language processing', 'robotics', 'systems', 'theory',
            'algorithms', 'databases', 'security', 'networking', 'hci',
            'graphics', 'software engineering', 'programming languages'
        ]
        
        found_areas = []
        for keyword in research_keywords:
            if keyword in full_text:
                found_areas.append(keyword)
        
        return found_areas
    
    def detect_hiring_signals(self, page_content: str) -> Dict[str, Any]:
        """Detect hiring signals in faculty page content"""
        content_lower = page_content.lower()
        
        # Positive hiring signals
        positive_signals = [
            'accepting students', 'recruiting phd', 'graduate positions',
            'seeking students', 'applications welcome', 'phd openings',
            'prospective students', 'interested students should',
            'looking for motivated', 'graduate student positions'
        ]
        
        # Negative hiring signals
        negative_signals = [
            'not accepting', 'no openings', 'full capacity', 'no positions',
            'not taking students', 'fully booked', 'no space'
        ]
        
        positive_count = sum(1 for signal in positive_signals if signal in content_lower)
        negative_count = sum(1 for signal in negative_signals if signal in content_lower)
        
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
            if signal in content_lower:
                indicators.append(signal)
        
        for signal in negative_signals:
            if signal in content_lower:
                indicators.append(signal)
        
        return {
            'status': status,
            'probability': probability,
            'indicators': indicators
        }
