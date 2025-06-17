import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.cache import cache_set, cache_get

logger = get_logger(__name__)

class BaseScraper(ABC):
    """Base class for all web scrapers"""
    
    def __init__(self, name: str, delay: float = None):
        self.name = name
        self.delay = delay or settings.SCRAPING_DELAY
        self.session = None
        self.robots_cache = {}
        self.request_history = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': settings.SCRAPING_USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Check cache first
            if base_url in self.robots_cache:
                rp = self.robots_cache[base_url]
            else:
                # Fetch and parse robots.txt
                robots_url = urljoin(base_url, '/robots.txt')
                rp = RobotFileParser()
                rp.set_url(robots_url)
                
                try:
                    async with self.session.get(robots_url) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            # Parse robots content (simplified)
                            rp.read()
                except:
                    # If robots.txt not found, assume allowed
                    pass
                
                self.robots_cache[base_url] = rp
            
            return rp.can_fetch(settings.SCRAPING_USER_AGENT, url)
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if check fails
    
    async def rate_limit(self, domain: str):
        """Implement rate limiting per domain"""
        current_time = time.time()
        
        if domain in self.request_history:
            last_request = self.request_history[domain]
            time_diff = current_time - last_request
            
            if time_diff < self.delay:
                wait_time = self.delay - time_diff
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)
        
        self.request_history[domain] = current_time
    
    async def fetch_url(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch a URL with rate limiting and robots.txt compliance"""
        try:
            # Check robots.txt
            if not await self.can_fetch(url):
                logger.warning(f"Blocked by robots.txt: {url}")
                return None
            
            # Rate limiting
            domain = urlparse(url).netloc
            await self.rate_limit(domain)
            
            # Check cache first
            cache_key = f"scraper:{self.name}:{url}"
            cached_result = await cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {url}")
                return cached_result
            
            # Fetch URL
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    content = await response.text()
                    result = {
                        'url': url,
                        'content': content,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'scraped_at': time.time()
                    }
                    
                    # Cache result for 1 hour
                    await cache_set(cache_key, result, expire=3600)
                    
                    logger.debug(f"Successfully fetched {url}")
                    return result
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @abstractmethod
    async def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """Main scraping method to be implemented by subclasses"""
        pass
