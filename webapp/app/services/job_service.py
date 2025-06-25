"""
Job service module for handling background jobs.
"""

import json
import os
import uuid
import tempfile
import subprocess
import threading
import sys
import glob
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class JobService:
    """Service class for managing background jobs."""
    
    def __init__(self, chromedriver_path: str, scraping_timeout: int = 1800):
        self.chromedriver_path = chromedriver_path
        self.scraping_timeout = scraping_timeout
        self.temp_dir = tempfile.gettempdir()
    
    def create_scraping_job(self, today_only: bool = False) -> str:
        """
        Create a new scraping job.
        
        Args:
            today_only: Whether to scrape only today's artists
        
        Returns:
            Job ID string
        """
        job_id = str(uuid.uuid4())
        job_file = os.path.join(self.temp_dir, f"scraping_job_{job_id}.json")
        
        initial_job_data = {
            'job_id': job_id,
            'status': 'starting',
            'started_at': datetime.now().isoformat(),
            'output': '',
            'error': '',
            'completed': False,
            'today_only': today_only
        }
        
        # Save initial job status to file
        try:
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(initial_job_data, f)
            logger.info(f"Created scraping job {job_id}")
        except Exception as e:
            logger.error(f"Error creating job file: {e}")
            raise
        
        return job_id
    
    def start_scraping_job(self, job_id: str) -> bool:
        """
        Start a scraping job in the background.
        
        Args:
            job_id: Job ID to start
        
        Returns:
            True if job started successfully, False otherwise
        """
        job_data = self.get_job_status(job_id)
        if not job_data:
            logger.error(f"Job {job_id} not found")
            return False
        
        def run_scraping():
            self._execute_scraping_job(job_id, job_data)
        
        # Start scraping in background thread
        thread = threading.Thread(target=run_scraping)
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started scraping job {job_id}")
        return True
    
    def _execute_scraping_job(self, job_id: str, job_data: Dict[str, Any]):
        """
        Execute the actual scraping job.
        
        Args:
            job_id: Job ID
            job_data: Job configuration data
        """
        def update_job_status(updates: Dict[str, Any]):
            """Helper function to update job status file."""
            try:
                job_file = os.path.join(self.temp_dir, f"scraping_job_{job_id}.json")
                
                if os.path.exists(job_file):
                    with open(job_file, 'r', encoding='utf-8') as f:
                        current_data = json.load(f)
                else:
                    current_data = job_data.copy()
                
                current_data.update(updates)
                
                with open(job_file, 'w', encoding='utf-8') as f:
                    json.dump(current_data, f)
            
            except Exception as e:
                logger.error(f"Error updating job status for {job_id}: {e}")
        
        try:
            # Set environment variables for the subprocess
            env = os.environ.copy()
            env['CHROMEDRIVER_PATH'] = self.chromedriver_path
            
            # Choose the appropriate scraping script
            script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scraping")
            
            if job_data.get('today_only', False):
                scrape_script = os.path.join(script_dir, "scrape_filtered.py")
            else:
                scrape_script = os.path.join(script_dir, "scrape.py")
            
            # Build the command
            cmd = [sys.executable, scrape_script]
            
            # Add arguments
            cmd.append("--no-prompt")  # Skip login prompt
            
            # Note: --headless argument removed from scrape.py (browser now runs in non-headless mode)
            # The duplicate protection is enabled by default in scrape.py
            
            if job_data.get('today_only', False):
                # Use today's date in YYYY-MM-DD format
                today_date = datetime.now().strftime('%Y-%m-%d')
                cmd.extend(["--date", today_date])
            
            logger.info(f"Running scraping command for job {job_id}: {' '.join(cmd)}")
            
            # Update status to running
            update_job_status({'status': 'running'})
            
            # Run the script
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(scrape_script),
                capture_output=True,
                text=True,
                timeout=self.scraping_timeout,
                env=env
            )
            
            # Update job status with results
            final_status = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'output': result.stdout,
                'error': result.stderr,
                'completed': True,
                'return_code': result.returncode,
                'completed_at': datetime.now().isoformat()
            }
            update_job_status(final_status)
            
            logger.info(f"Scraping job {job_id} completed with return code: {result.returncode}")
        
        except subprocess.TimeoutExpired:
            update_job_status({
                'status': 'timeout',
                'error': f'Scraping script timed out after {self.scraping_timeout // 60} minutes',
                'completed': True,
                'completed_at': datetime.now().isoformat()
            })
            logger.warning(f"Scraping job {job_id} timed out")
        
        except Exception as e:
            update_job_status({
                'status': 'error',
                'error': str(e),
                'completed': True,
                'completed_at': datetime.now().isoformat()
            })
            logger.error(f"Scraping job {job_id} error: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific job.
        
        Args:
            job_id: Job ID to check
        
        Returns:
            Job status dictionary or None if not found
        """
        job_file = os.path.join(self.temp_dir, f"scraping_job_{job_id}.json")
        
        if not os.path.exists(job_file):
            return None
        
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading job file for {job_id}: {e}")
            return None
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all scraping jobs.
        
        Returns:
            Dictionary mapping job IDs to job data
        """
        job_pattern = os.path.join(self.temp_dir, "scraping_job_*.json")
        job_files = glob.glob(job_pattern)
        
        jobs = {}
        for job_file in job_files:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job_id = job_data.get('job_id')
                    if job_id:
                        jobs[job_id] = job_data
            except Exception as e:
                logger.error(f"Error reading job file {job_file}: {e}")
                continue
        
        return jobs
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Clean up job files older than specified hours.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        job_pattern = os.path.join(self.temp_dir, "scraping_job_*.json")
        job_files = glob.glob(job_pattern)
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        for job_file in job_files:
            try:
                # Check if file is older than max age
                if current_time - os.path.getmtime(job_file) > max_age_seconds:
                    os.remove(job_file)
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Error cleaning up job file {job_file}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old job files")
    
    def run_process_suggestions(self) -> Dict[str, Any]:
        """
        Run the process suggestions script.
        
        Returns:
            Dictionary with success status and output/error information
        """
        try:
            # Path to the suggestion processing script
            script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scraping")
            process_script = os.path.join(script_dir, "process_suggestions.py")
            
            # Set environment variables for the subprocess
            env = os.environ.copy()
            env['SPOTIPY_CLIENT_ID'] = os.getenv('SPOTIPY_CLIENT_ID', '')
            env['SPOTIPY_CLIENT_SECRET'] = os.getenv('SPOTIPY_CLIENT_SECRET', '')
            env['SPOTIPY_REDIRECT_URI'] = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5000/admin/callback')
            
            logger.info(f"Running process suggestions script: {process_script}")
            
            # Run the processing script
            result = subprocess.run(
                [sys.executable, process_script],
                cwd=os.path.dirname(process_script),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )
            
            logger.info(f"Process suggestions completed with return code: {result.returncode}")
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Successfully processed approved suggestions!",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "message": f"Processing failed with return code {result.returncode}",
                    "error": result.stderr,
                    "output": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Processing timed out after 5 minutes"
            }
        except Exception as e:
            logger.error(f"Error processing suggestions: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
