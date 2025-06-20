#!/usr/bin/env python3
"""
Monitoring and maintenance script for STEM Graduate Admissions Assistant
Monitors system health, database usage, and performs maintenance tasks.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.firebase_config import init_firebase, get_firebase
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class SystemMonitor:
    """System monitoring and maintenance"""
    
    def __init__(self):
        self.firebase = None
        self.alerts = []
    
    async def initialize(self):
        """Initialize Firebase connection"""
        await init_firebase()
        self.firebase = get_firebase()
        logger.info("System monitor initialized")
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        logger.info("Starting health check...")
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {},
            "metrics": {},
            "alerts": []
        }
        
        try:
            # Database connectivity check
            health_report["checks"]["database"] = await self._check_database_health()
            
            # Data freshness check
            health_report["checks"]["data_freshness"] = await self._check_data_freshness()
            
            # Collection size monitoring
            health_report["metrics"]["collections"] = await self._get_collection_metrics()
            
            # Scraping job status
            health_report["checks"]["scraping"] = await self._check_scraping_jobs()
            
            # Error rate monitoring
            health_report["metrics"]["errors"] = await self._get_error_metrics()
            
            # Generate alerts
            health_report["alerts"] = await self._generate_alerts(health_report)
            
            # Overall status
            failed_checks = [k for k, v in health_report["checks"].items() if not v.get("healthy", True)]
            if failed_checks:
                health_report["status"] = "unhealthy"
                logger.warning(f"Health check failed: {failed_checks}")
            else:
                logger.info("Health check passed")
            
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_report["status"] = "error"
            health_report["error"] = str(e)
            return health_report
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = datetime.utcnow()
            
            # Test basic query
            universities = await self.firebase.query_collection('universities', [], limit=1)
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "healthy": True,
                "response_time_seconds": response_time,
                "connection_status": "connected"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "connection_status": "failed"
            }
    
    async def _check_data_freshness(self) -> Dict[str, Any]:
        """Check if data is fresh enough"""
        try:
            # Check faculty data freshness
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            
            recent_faculty = await self.firebase.query_collection(
                'faculty',
                [('updated_at', '>=', one_week_ago)],
                limit=100
            )
            
            total_faculty = await self.firebase.query_collection('faculty', [('is_active', '==', True)], limit=1000)
            
            freshness_ratio = len(recent_faculty) / len(total_faculty) if total_faculty else 0
            
            return {
                "healthy": freshness_ratio > 0.1,  # At least 10% updated in last week
                "freshness_ratio": freshness_ratio,
                "recent_updates": len(recent_faculty),
                "total_records": len(total_faculty)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _get_collection_metrics(self) -> Dict[str, Any]:
        """Get metrics for all collections"""
        try:
            metrics = {}
            
            collections = ['universities', 'faculty', 'programs', 'chat_sessions', 'chat_messages', 'scrape_jobs']
            
            for collection in collections:
                try:
                    # Get total count
                    docs = await self.firebase.query_collection(collection, [], limit=1000)
                    total_count = len(docs)
                    
                    # Get active count (if applicable)
                    if collection in ['universities', 'faculty', 'programs']:
                        active_docs = await self.firebase.query_collection(
                            collection, 
                            [('is_active', '==', True)], 
                            limit=1000
                        )
                        active_count = len(active_docs)
                    else:
                        active_count = total_count
                    
                    # Calculate growth (last 24 hours)
                    yesterday = datetime.utcnow() - timedelta(days=1)
                    recent_docs = await self.firebase.query_collection(
                        collection,
                        [('created_at', '>=', yesterday)],
                        limit=1000
                    )
                    growth_24h = len(recent_docs)
                    
                    metrics[collection] = {
                        "total_count": total_count,
                        "active_count": active_count,
                        "growth_24h": growth_24h
                    }
                    
                except Exception as e:
                    metrics[collection] = {"error": str(e)}
            
            return metrics
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_scraping_jobs(self) -> Dict[str, Any]:
        """Check scraping job status"""
        try:
            # Get recent jobs
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_jobs = await self.firebase.query_collection(
                'scrape_jobs',
                [('created_at', '>=', yesterday)],
                limit=100
            )
            
            if not recent_jobs:
                return {
                    "healthy": False,
                    "message": "No scraping jobs in last 24 hours"
                }
            
            # Analyze job status
            completed = len([j for j in recent_jobs if j.get('status') == 'completed'])
            failed = len([j for j in recent_jobs if j.get('status') == 'failed'])
            running = len([j for j in recent_jobs if j.get('status') == 'running'])
            
            success_rate = completed / len(recent_jobs) if recent_jobs else 0
            
            return {
                "healthy": success_rate > 0.8,
                "total_jobs": len(recent_jobs),
                "completed": completed,
                "failed": failed,
                "running": running,
                "success_rate": success_rate
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics from logs (simplified)"""
        try:
            # This would integrate with your logging system
            # For now, return basic metrics
            return {
                "error_rate_24h": 0.02,  # 2% error rate
                "critical_errors": 0,
                "warnings": 5
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_alerts(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on health report"""
        alerts = []
        
        # Database response time alert
        db_check = health_report["checks"].get("database", {})
        if db_check.get("response_time_seconds", 0) > 5:
            alerts.append({
                "level": "warning",
                "message": f"Database response time high: {db_check['response_time_seconds']:.2f}s",
                "category": "performance"
            })
        
        # Data freshness alert
        freshness_check = health_report["checks"].get("data_freshness", {})
        if not freshness_check.get("healthy", True):
            alerts.append({
                "level": "warning",
                "message": f"Data freshness low: {freshness_check.get('freshness_ratio', 0):.2%} updated in last week",
                "category": "data_quality"
            })
        
        # Collection size alerts
        collections = health_report["metrics"].get("collections", {})
        faculty_count = collections.get("faculty", {}).get("total_count", 0)
        if faculty_count < 100:
            alerts.append({
                "level": "critical",
                "message": f"Faculty count too low: {faculty_count}",
                "category": "data_volume"
            })
        
        # Scraping job alerts
        scraping_check = health_report["checks"].get("scraping", {})
        if not scraping_check.get("healthy", True):
            alerts.append({
                "level": "warning",
                "message": scraping_check.get("message", "Scraping jobs unhealthy"),
                "category": "scraping"
            })
        
        return alerts
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Cleanup old data"""
        logger.info(f"Starting cleanup of data older than {days_to_keep} days...")
        
        cleanup_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "cleaned_collections": {},
            "total_deleted": 0
        }
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Cleanup old chat sessions
            old_sessions = await self.firebase.query_collection(
                'chat_sessions',
                [('created_at', '<', cutoff_date), ('is_active', '==', False)],
                limit=1000
            )
            
            for session in old_sessions:
                # Delete associated messages first
                messages = await self.firebase.query_collection(
                    'chat_messages',
                    [('session_id', '==', session['session_id'])],
                    limit=1000
                )
                
                for message in messages:
                    await self.firebase.db.collection('chat_messages').document(message['id']).delete()
                
                # Delete session
                await self.firebase.db.collection('chat_sessions').document(session['id']).delete()
            
            cleanup_report["cleaned_collections"]["chat_sessions"] = len(old_sessions)
            cleanup_report["total_deleted"] += len(old_sessions)
            
            # Cleanup old scraping jobs
            old_jobs = await self.firebase.query_collection(
                'scrape_jobs',
                [('created_at', '<', cutoff_date), ('status', 'in', ['completed', 'failed'])],
                limit=1000
            )
            
            for job in old_jobs:
                await self.firebase.db.collection('scrape_jobs').document(job['id']).delete()
            
            cleanup_report["cleaned_collections"]["scrape_jobs"] = len(old_jobs)
            cleanup_report["total_deleted"] += len(old_jobs)
            
            logger.info(f"Cleanup completed: {cleanup_report['total_deleted']} records deleted")
            return cleanup_report
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            cleanup_report["error"] = str(e)
            return cleanup_report
    
    async def update_faculty_hiring_scores(self) -> Dict[str, Any]:
        """Update faculty hiring probability scores based on recent signals"""
        logger.info("Updating faculty hiring scores...")
        
        update_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "faculty_updated": 0,
            "average_score_change": 0.0
        }
        
        try:
            # Get all active faculty
            faculty_list = await self.firebase.query_collection(
                'faculty',
                [('is_active', '==', True)],
                limit=1000
            )
            
            total_score_change = 0.0
            
            for faculty in faculty_list:
                # Get recent hiring signals for this faculty
                signals = await self.firebase.query_collection(
                    'hiring_signals',
                    [('faculty_id', '==', faculty['id'])],
                    limit=10
                )
                
                # Calculate new hiring probability
                old_score = faculty.get('hiring_probability', 0.0)
                new_score = self._calculate_hiring_probability(faculty, signals)
                
                # Update if score changed significantly
                if abs(new_score - old_score) > 0.1:
                    await self.firebase.update_document('faculty', faculty['id'], {
                        'hiring_probability': new_score,
                        'last_hiring_update': datetime.utcnow().isoformat()
                    })
                    
                    update_report["faculty_updated"] += 1
                    total_score_change += abs(new_score - old_score)
            
            if update_report["faculty_updated"] > 0:
                update_report["average_score_change"] = total_score_change / update_report["faculty_updated"]
            
            logger.info(f"Updated {update_report['faculty_updated']} faculty hiring scores")
            return update_report
            
        except Exception as e:
            logger.error(f"Hiring score update failed: {e}")
            update_report["error"] = str(e)
            return update_report
    
    def _calculate_hiring_probability(self, faculty: Dict[str, Any], signals: List[Dict[str, Any]]) -> float:
        """Calculate hiring probability based on faculty data and signals"""
        base_score = faculty.get('hiring_probability', 0.5)
        
        # Current hiring status
        hiring_status = faculty.get('hiring_status', 'unknown')
        if hiring_status == 'hiring':
            base_score = max(base_score, 0.8)
        elif hiring_status == 'not_hiring':
            base_score = min(base_score, 0.2)
        elif hiring_status == 'maybe':
            base_score = max(base_score, 0.5)
        
        # Adjust based on recent signals
        recent_hiring_signals = [s for s in signals if s.get('signal_type') == 'hiring_announcement']
        if recent_hiring_signals:
            base_score = min(base_score + 0.2, 1.0)
        
        # Adjust based on last update time
        last_update = faculty.get('last_hiring_update')
        if last_update:
            try:
                last_update_date = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                days_since_update = (datetime.utcnow() - last_update_date.replace(tzinfo=None)).days
                
                # Decrease confidence over time
                if days_since_update > 30:
                    base_score = base_score * 0.9
                elif days_since_update > 60:
                    base_score = base_score * 0.8
            except:
                pass
        
        return max(0.0, min(1.0, base_score))

async def main():
    """Main monitoring function"""
    if len(sys.argv) < 2:
        print("Usage: python monitor.py <command>")
        print("Commands: health, cleanup, update-scores, full-maintenance")
        sys.exit(1)
    
    command = sys.argv[1]
    
    monitor = SystemMonitor()
    await monitor.initialize()
    
    if command == "health":
        report = await monitor.run_health_check()
        print(json.dumps(report, indent=2, default=str))
        
        # Exit with error code if unhealthy
        if report["status"] != "healthy":
            sys.exit(1)
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        report = await monitor.cleanup_old_data(days)
        print(json.dumps(report, indent=2, default=str))
    
    elif command == "update-scores":
        report = await monitor.update_faculty_hiring_scores()
        print(json.dumps(report, indent=2, default=str))
    
    elif command == "full-maintenance":
        print("Running full maintenance...")
        
        # Health check
        health_report = await monitor.run_health_check()
        print("Health Check:", health_report["status"])
        
        # Cleanup
        cleanup_report = await monitor.cleanup_old_data()
        print(f"Cleanup: {cleanup_report['total_deleted']} records deleted")
        
        # Update scores
        update_report = await monitor.update_faculty_hiring_scores()
        print(f"Score Updates: {update_report['faculty_updated']} faculty updated")
        
        print("Full maintenance completed!")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())