import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from app.scrapers.base import BaseScraper
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RedditMonitor(BaseScraper):
    """Monitor Reddit for graduate admissions discussions"""
    
    def __init__(self):
        super().__init__("reddit_monitor")
        self.base_url = "https://www.reddit.com"
        
        # Relevant subreddits
        self.subreddits = [
            'gradadmissions',
            'PhD',
            'MachineLearning',
            'compsci',
            'AskAcademia',
            'gradschool',
            'cscareerquestions'
        ]
        
        # Keywords to look for
        self.hiring_keywords = [
            'professor hiring', 'faculty position', 'phd advisor',
            'accepting students', 'graduate positions', 'lab openings',
            'research opportunities', 'advisor looking for',
            'positions available', 'recruiting students'
        ]
    
    async def scrape(self, subreddits: List[str] = None, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """Scrape Reddit for hiring-related posts"""
        subreddits = subreddits or self.subreddits
        all_posts = []
        
        for subreddit in subreddits:
            try:
                posts = await self.scrape_subreddit(subreddit, limit=limit//len(subreddits))
                all_posts.extend(posts)
                
                logger.info(f"Found {len(posts)} relevant posts in r/{subreddit}")
                
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit}: {e}")
        
        return all_posts
    
    async def scrape_subreddit(self, subreddit: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape a specific subreddit for relevant posts"""
        url = f"{self.base_url}/r/{subreddit}/new.json"
        
        posts_data = await self.fetch_reddit_json(url, limit=limit)
        if not posts_data:
            return []
        
        relevant_posts = []
        
        for post_data in posts_data.get('data', {}).get('children', []):
            post = post_data.get('data', {})
            
            if self.is_relevant_post(post):
                processed_post = self.process_reddit_post(post, subreddit)
                if processed_post:
                    relevant_posts.append(processed_post)
        
        return relevant_posts
    
    async def fetch_reddit_json(self, url: str, limit: int = 50) -> Optional[Dict]:
        """Fetch Reddit JSON data"""
        params = {'limit': limit}
        
        try:
            page_data = await self.fetch_url(url, params=params)
            if page_data:
                import json
                return json.loads(page_data['content'])
        except Exception as e:
            logger.error(f"Error fetching Reddit JSON from {url}: {e}")
        
        return None
    
    def is_relevant_post(self, post: Dict) -> bool:
        """Check if a Reddit post is relevant to faculty hiring"""
        title = post.get('title', '').lower()
        selftext = post.get('selftext', '').lower()
        
        # Check for hiring keywords
        text_to_check = f"{title} {selftext}"
        
        return any(keyword in text_to_check for keyword in self.hiring_keywords)
    
    def process_reddit_post(self, post: Dict, subreddit: str) -> Optional[Dict[str, Any]]:
        """Process a relevant Reddit post"""
        try:
            return {
                'id': post.get('id'),
                'title': post.get('title'),
                'content': post.get('selftext', ''),
                'author': post.get('author'),
                'subreddit': subreddit,
                'score': post.get('score', 0),
                'num_comments': post.get('num_comments', 0),
                'created_utc': post.get('created_utc'),
                'url': f"{self.base_url}{post.get('permalink', '')}",
                'source': 'reddit',
                'relevance_type': 'faculty_hiring',
                'scraped_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Reddit post: {e}")
            return None

class TwitterMonitor(BaseScraper):
    """Monitor Twitter for academic hiring announcements"""
    
    def __init__(self):
        super().__init__("twitter_monitor")
        self.base_url = "https://api.twitter.com/2"
        
        # Academic hiring keywords
        self.search_terms = [
            'PhD position available',
            'faculty hiring',
            'postdoc position',
            'graduate student position',
            'research assistant opening',
            'academic job opening',
            'professor position',
            'CS faculty search'
        ]
    
    async def scrape(self, search_terms: List[str] = None, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """Scrape Twitter for academic hiring tweets"""
        if not settings.TWITTER_BEARER_TOKEN:
            logger.warning("Twitter Bearer Token not configured")
            return []
        
        search_terms = search_terms or self.search_terms
        all_tweets = []
        
        for term in search_terms:
            try:
                tweets = await self.search_tweets(term, limit=limit//len(search_terms))
                all_tweets.extend(tweets)
                
                logger.info(f"Found {len(tweets)} tweets for '{term}'")
                
            except Exception as e:
                logger.error(f"Error searching Twitter for '{term}': {e}")
        
        return all_tweets
    
    async def search_tweets(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for tweets using Twitter API v2"""
        if not settings.TWITTER_BEARER_TOKEN:
            return []
        
        url = f"{self.base_url}/tweets/search/recent"
        
        params = {
            'query': f'"{query}" -is:retweet lang:en',
            'max_results': min(limit, 100),  # API limit
            'tweet.fields': 'created_at,author_id,public_metrics,context_annotations'
        }
        
        headers = {
            'Authorization': f'Bearer {settings.TWITTER_BEARER_TOKEN}'
        }
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.process_twitter_response(data, query)
                else:
                    logger.error(f"Twitter API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error calling Twitter API: {e}")
            return []
    
    def process_twitter_response(self, data: Dict, query: str) -> List[Dict[str, Any]]:
        """Process Twitter API response"""
        tweets = []
        
        for tweet_data in data.get('data', []):
            try:
                processed_tweet = {
                    'id': tweet_data.get('id'),
                    'text': tweet_data.get('text'),
                    'author_id': tweet_data.get('author_id'),
                    'created_at': tweet_data.get('created_at'),
                    'retweet_count': tweet_data.get('public_metrics', {}).get('retweet_count', 0),
                    'like_count': tweet_data.get('public_metrics', {}).get('like_count', 0),
                    'search_query': query,
                    'source': 'twitter',
                    'relevance_type': 'academic_hiring',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                tweets.append(processed_tweet)
                
            except Exception as e:
                logger.error(f"Error processing tweet: {e}")
        
        return tweets