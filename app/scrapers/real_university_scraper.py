import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
from urllib.parse import urljoin, urlparse
from app.core.config import get_firebase
from app.models.firebase_models import University, Faculty, Program, ScrapeJob, HiringSignal
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScrapingOrchestrator:
    """Main orchestrator for all scraping activities"""

    def __init__(self):
        self.university_scraper = UniversityScraper()
        self.social_media_scraper = SocialMediaScraper()
        self.max_concurrent = 5
        self.delay_range = (1, 3)  # seconds

    async def run_daily_scraping(self):
        """Run daily scraping routine"""
        logger.info("Starting daily scraping routine")

        try:
            # Create scraping jobs
            await self._create_scraping_jobs()

            # Run university scraping
            await self._run_university_scraping()

            # Run social media monitoring
            await self._run_social_media_scraping()

            # Process hiring signals
            await self._process_hiring_signals()

            logger.info("Daily scraping routine completed")

        except Exception as e:
            logger.error(f"Error in daily scraping: {e}")

    async def _create_scraping_jobs(self):
        """Create scraping jobs for prioritized targets"""
        try:
            firebase = get_firebase()

            # Get active universities
            universities = await firebase.query_collection('universities', [('is_active', '==', True)], limit=50)

            # Create jobs for high-priority universities
            high_priority_unis = [
                uni for uni in universities if uni.get('cs_ranking', 999) <= 50]

            for uni in high_priority_unis:
                await ScrapeJob.create(
                    job_type="faculty",
                    target=uni['name'],
                    status="pending",
                    priority="high" if uni.get(
                        'cs_ranking', 999) <= 20 else "medium",
                    next_scheduled=datetime.utcnow()
                )

            # Create social media jobs
            await ScrapeJob.create(
                job_type="social_media",
                target="reddit_cscareerquestions",
                status="pending",
                priority="medium",
                next_scheduled=datetime.utcnow()
            )

            await ScrapeJob.create(
                job_type="social_media",
                target="reddit_gradadmissions",
                status="pending",
                priority="high",
                next_scheduled=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error creating scraping jobs: {e}")

    async def _run_university_scraping(self):
        """Run university faculty and program scraping"""
        try:
            firebase = get_firebase()

            # Get pending university scraping jobs
            pending_jobs = await firebase.query_collection(
                'scrape_jobs',
                [('status', '==', 'pending'), ('job_type', '==', 'faculty')],
                limit=10
            )

            # Process jobs with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = []

            for job in pending_jobs:
                task = self._process_university_job(semaphore, job)
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error in university scraping: {e}")

    async def _process_university_job(self, semaphore: asyncio.Semaphore, job: Dict[str, Any]):
        """Process a single university scraping job"""
        async with semaphore:
            try:
                # Update job status
                firebase = get_firebase()
                await firebase.update_document('scrape_jobs', job['id'], {
                    'status': 'running',
                    'started_at': datetime.utcnow()
                })

                # Get university details
                university_name = job['target']
                universities = await firebase.query_collection(
                    'universities',
                    [('name', '==', university_name)],
                    limit=1
                )

                if not universities:
                    raise Exception(f"University {university_name} not found")

                university = universities[0]

                # Scrape faculty
                faculty_count = await self.university_scraper.scrape_university_faculty(university)

                # Mark job as completed
                await firebase.update_document('scrape_jobs', job['id'], {
                    'status': 'completed',
                    'completed_at': datetime.utcnow(),
                    'records_found': faculty_count,
                    'records_saved': faculty_count
                })

                # Add delay
                await asyncio.sleep(random.uniform(*self.delay_range))

            except Exception as e:
                logger.error(
                    f"Error processing university job {job['id']}: {e}")
                await firebase.update_document('scrape_jobs', job['id'], {
                    'status': 'failed',
                    'completed_at': datetime.utcnow(),
                    'error_message': str(e)
                })

    async def _run_social_media_scraping(self):
        """Run social media scraping"""
        try:
            await self.social_media_scraper.scrape_reddit_hiring_signals()
        except Exception as e:
            logger.error(f"Error in social media scraping: {e}")

    async def _process_hiring_signals(self):
        """Process unprocessed hiring signals"""
        try:
            signals = await HiringSignal.get_unprocessed(limit=20)

            for signal in signals:
                await self._match_signal_to_faculty(signal)

        except Exception as e:
            logger.error(f"Error processing hiring signals: {e}")

    async def _match_signal_to_faculty(self, signal: HiringSignal):
        """Match hiring signal to existing faculty"""
        try:
            firebase = get_firebase()

            # Simple matching based on faculty name and university
            if signal.faculty_name and signal.university_name:
                faculty_results = await firebase.query_collection(
                    'faculty',
                    [('name', '==', signal.faculty_name),
                     ('university_name', '==', signal.university_name)],
                    limit=1
                )

                if faculty_results:
                    faculty = faculty_results[0]

                    # Update faculty hiring status
                    new_status = 'hiring' if signal.signal_type == 'hiring_announcement' else faculty.get(
                        'hiring_status', 'unknown')

                    await firebase.update_document('faculty', faculty['id'], {
                        'hiring_status': new_status,
                        'hiring_indicators': faculty.get('hiring_indicators', []) + [signal.signal_type],
                        'last_hiring_update': datetime.utcnow().isoformat()
                    })

                    # Mark signal as processed
                    await firebase.update_document('hiring_signals', signal.id, {
                        'processed': True,
                        'faculty_id': faculty['id']
                    })

        except Exception as e:
            logger.error(f"Error matching hiring signal: {e}")


class UniversityScraper:
    """Scraper for university websites"""

    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def scrape_university_faculty(self, university: Dict[str, Any]) -> int:
        """Scrape faculty from a university"""
        try:
            faculty_count = 0

            # Get faculty URLs based on university
            faculty_urls = await self._get_faculty_urls(university)

            async with aiohttp.ClientSession(headers=self.headers) as session:
                self.session = session

                for url in faculty_urls:
                    try:
                        faculty_data = await self._scrape_faculty_page(url, university)
                        if faculty_data:
                            await self._save_faculty(faculty_data, university)
                            faculty_count += 1

                        # Respectful delay
                        await asyncio.sleep(random.uniform(1, 2))

                    except Exception as e:
                        logger.error(f"Error scraping faculty URL {url}: {e}")
                        continue

            return faculty_count

        except Exception as e:
            logger.error(
                f"Error scraping university {university['name']}: {e}")
            return 0

    async def _get_faculty_urls(self, university: Dict[str, Any]) -> List[str]:
        """Get faculty page URLs for a university"""
        base_urls = []
        university_name = university['name'].lower()

        # Common CS department URL patterns
        if 'stanford' in university_name:
            base_urls = ['https://cs.stanford.edu/people/faculty']
        elif 'mit' in university_name:
            base_urls = ['https://www.csail.mit.edu/people']
        elif 'berkeley' in university_name or 'ucb' in university_name:
            base_urls = ['https://eecs.berkeley.edu/faculty']
        elif 'cmu' in university_name or 'carnegie' in university_name:
            base_urls = ['https://www.cs.cmu.edu/directory/faculty']
        elif 'caltech' in university_name:
            base_urls = ['https://www.cms.caltech.edu/people/faculty']
        else:
            # Generic patterns to try
            domain = university.get('website_url', '').replace(
                'https://', '').replace('http://', '')
            if domain:
                base_urls = [
                    f"https://cs.{domain}/faculty",
                    f"https://www.{domain}/cs/faculty",
                    f"https://www.{domain}/computer-science/faculty"
                ]

        return base_urls

    async def _scrape_faculty_page(self, url: str, university: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scrape individual faculty page"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract faculty information
                faculty_data = {
                    'university_id': university['id'],
                    'university_name': university['name'],
                    'is_active': True,
                    'last_scraped': datetime.utcnow(),
                    'scraping_sources': [url]
                }

                # Try to extract name
                name = self._extract_faculty_name(soup)
                if not name:
                    return None
                faculty_data['name'] = name

                # Extract other information
                faculty_data['email'] = self._extract_email(soup)
                faculty_data['title'] = self._extract_title(soup)
                faculty_data['department'] = self._extract_department(soup)
                faculty_data['research_areas'] = self._extract_research_areas(
                    soup)
                faculty_data['homepage_url'] = url
                faculty_data['research_statement'] = self._extract_research_statement(
                    soup)

                # Determine hiring status
                faculty_data['hiring_status'] = self._determine_hiring_status(
                    soup)

                return faculty_data

        except Exception as e:
            logger.error(f"Error scraping faculty page {url}: {e}")
            return None

    def _extract_faculty_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract faculty name from page"""
        # Try common selectors
        selectors = [
            'h1', '.faculty-name', '.name', '[class*="name"]',
            '.person-name', '.profile-name', 'title'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text().strip()
                if name and len(name) < 100 and 'Dr.' in name or 'Prof.' in name or len(name.split()) >= 2:
                    return name

        return None

    def _extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract email from page"""
        # Look for email patterns
        text = soup.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        for email in emails:
            if 'edu' in email:
                return email

        return emails[0] if emails else None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract academic title"""
        text = soup.get_text().lower()

        if 'professor' in text:
            if 'assistant professor' in text:
                return 'Assistant Professor'
            elif 'associate professor' in text:
                return 'Associate Professor'
            elif 'full professor' in text or 'professor' in text:
                return 'Professor'

        return None

    def _extract_department(self, soup: BeautifulSoup) -> str:
        """Extract department"""
        text = soup.get_text().lower()

        if 'computer science' in text:
            return 'Computer Science'
        elif 'electrical engineering' in text:
            return 'Electrical Engineering'
        elif 'computer engineering' in text:
            return 'Computer Engineering'

        return 'Computer Science'  # Default

    def _extract_research_areas(self, soup: BeautifulSoup) -> List[str]:
        """Extract research areas"""
        text = soup.get_text().lower()
        areas = []
        
        # Common research areas
        research_keywords = {
            'machine learning': ['machine learning', 'ml', 'artificial intelligence', 'ai'],
            'computer vision': ['computer vision', 'cv', 'image processing'],
            'natural language processing': ['nlp', 'natural language', 'text mining'],
            'robotics': ['robotics', 'autonomous systems'],
            'systems': ['systems', 'distributed systems', 'operating systems'],
            'algorithms': ['algorithms', 'theoretical computer science'],
            'cybersecurity': ['security', 'cybersecurity', 'cryptography'],
            'human computer interaction': ['hci', 'human computer interaction', 'user interface']
        }

        for area, keywords in research_keywords.items():
            if any(keyword in text for keyword in keywords):
                areas.append(area.title())

        return areas[:5]  # Limit to 5 areas

    def _extract_research_statement(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract research statement or bio"""
        # Look for paragraphs that might contain research info
        paragraphs = soup.find_all('p')

        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 100 and ('research' in text.lower() or 'work' in text.lower()):
                return text[:500]  # Limit length

        return None

    def _determine_hiring_status(self, soup: BeautifulSoup) -> str:
        """Determine hiring status based on page content"""
        text = soup.get_text().lower()

        hiring_indicators = [
            'accepting students', 'seeking students', 'recruiting',
            'positions available', 'phd opportunities', 'graduate positions'
        ]

        for indicator in hiring_indicators:
            if indicator in text:
                return 'hiring'

        return 'unknown'

    async def _save_faculty(self, faculty_data: Dict[str, Any], university: Dict[str, Any]):
        """Save faculty data to Firebase"""
        try:
            firebase = get_firebase()

            # Check if faculty already exists
            existing = await firebase.query_collection(
                'faculty',
                [('name', '==', faculty_data['name']),
                 ('university_name', '==', university['name'])],
                limit=1
            )

            if existing:
                # Update existing faculty
                await firebase.update_document('faculty', existing[0]['id'], faculty_data)
            else:
                # Create new faculty
                await Faculty.create(**faculty_data)

        except Exception as e:
            logger.error(
                f"Error saving faculty {faculty_data.get('name', 'Unknown')}: {e}")


class SocialMediaScraper:
    """Scraper for social media hiring signals"""

    def __init__(self):
        self.reddit_headers = {
            'User-Agent': 'AcademicResearch:StemGradAssistant:v1.0 (by /u/researcher)'
        }

    async def scrape_reddit_hiring_signals(self):
        """Scrape Reddit for hiring signals"""
        try:
            subreddits = [
                'gradadmissions',
                'cscareerquestions',
                'MachineLearning',
                'compsci'
            ]

            for subreddit in subreddits:
                await self._scrape_subreddit(subreddit)
                await asyncio.sleep(2)  # Respectful delay

        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")

    async def _scrape_subreddit(self, subreddit: str):
        """Scrape a specific subreddit"""
        try:
            # Use Reddit's JSON API
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"

            async with aiohttp.ClientSession(headers=self.reddit_headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return

                    data = await response.json()
                    posts = data.get('data', {}).get('children', [])

                    for post in posts:
                        await self._analyze_reddit_post(post['data'], subreddit)

        except Exception as e:
            logger.error(f"Error scraping subreddit {subreddit}: {e}")

    async def _analyze_reddit_post(self, post_data: Dict[str, Any], subreddit: str):
        """Analyze Reddit post for hiring signals"""
        try:
            title = post_data.get('title', '').lower()
            content = post_data.get('selftext', '').lower()
            combined_text = f"{title} {content}"

            # Look for hiring-related keywords
            hiring_keywords = [
                'accepting students', 'hiring', 'positions available',
                'phd position', 'postdoc position', 'graduate positions',
                'looking for students', 'recruiting students'
            ]

            if any(keyword in combined_text for keyword in hiring_keywords):
                # Extract potential faculty/university names
                faculty_info = self._extract_faculty_info(combined_text)

                if faculty_info:
                    await HiringSignal.create(
                        source='reddit',
                        source_url=f"https://reddit.com{post_data.get('permalink', '')}",
                        signal_type='hiring_announcement',
                        content=combined_text[:1000],
                        confidence_score=0.7,
                        **faculty_info
                    )

        except Exception as e:
            logger.error(f"Error analyzing Reddit post: {e}")

    def _extract_faculty_info(self, text: str) -> Dict[str, Any]:
        """Extract faculty and university information from text"""
        info = {}

        # Simple university extraction
        universities = [
            'stanford', 'mit', 'berkeley', 'cmu', 'caltech', 'harvard',
            'princeton', 'yale', 'columbia', 'cornell', 'university'
        ]

        for uni in universities:
            if uni in text:
                if uni == 'university':
                    # Try to extract full university name
                    pattern = r'university of (\w+)'
                    match = re.search(pattern, text)
                    if match:
                        info['university_name'] = f"University of {match.group(1).title()}"
                else:
                    info['university_name'] = uni.title()
                break

        # Try to extract professor names (very basic)
        prof_patterns = [
            r'prof(?:essor)?\s+([a-z]+\s+[a-z]+)',
            r'dr\.?\s+([a-z]+\s+[a-z]+)',
        ]

        for pattern in prof_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).title()
                if len(name.split()) == 2:  # First and last name
                    info['faculty_name'] = name
                break

        return info
