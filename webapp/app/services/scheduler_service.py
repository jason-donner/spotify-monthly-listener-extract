"""
Scheduler service for automated daily scraping.
"""

import schedule
import time
import threading
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for scheduling automated scraping jobs."""
    
    def __init__(self, job_service):
        self.job_service = job_service
        self.scheduler_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.schedule_time = "02:00"  # Default to 2 AM
        
    def set_schedule_time(self, time_str: str):
        """
        Set the daily schedule time.
        
        Args:
            time_str: Time in HH:MM format (24-hour)
        """
        try:
            # Validate time format
            datetime.strptime(time_str, '%H:%M')
            self.schedule_time = time_str
            logger.info(f"Daily scraping scheduled for {time_str}")
            
            # Clear existing schedule and set new one
            schedule.clear()
            schedule.every().day.at(self.schedule_time).do(self._run_daily_scrape)
            
        except ValueError:
            logger.error(f"Invalid time format: {time_str}. Use HH:MM format.")
            raise
    
    def _run_daily_scrape(self):
        """Execute the daily scraping job."""
        try:
            logger.info("Starting automated daily scraping...")
            # Create a full scraping job (not today-only)
            job_id = self.job_service.create_scraping_job(
                headless=True,  # Run in headless mode for automation
                today_only=False  # Full scrape
            )
            if self.job_service.start_scraping_job(job_id):
                logger.info(f"Daily scraping job started successfully. Job ID: {job_id}")
            else:
                logger.error("Failed to start daily scraping job")
                
        except Exception as e:
            logger.error(f"Error during automated daily scraping: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Set up the default schedule
        schedule.clear()
        schedule.every().day.at(self.schedule_time).do(self._run_daily_scrape)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Scheduler started. Daily scraping at {self.schedule_time}")
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def get_next_run_time(self):
        """Get the next scheduled run time."""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
    
    def get_status(self):
        """Get scheduler status."""
        return {
            'running': self.is_running,
            'schedule_time': self.schedule_time,
            'next_run': self.get_next_run_time().isoformat() if self.get_next_run_time() else None,
            'jobs_count': len(schedule.get_jobs())
        }
