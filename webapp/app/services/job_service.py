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
    
    def create_scraping_job(self, headless: bool = True, today_only: bool = False, allow_duplicates: bool = False) -> str:
        """
        Create a new scraping job.
        
        Args:
            headless: Whether to run browser in headless mode (applies to both scripts)
            today_only: Whether to scrape only today's artists
            allow_duplicates: Whether to allow re-scraping artists already scraped today
        
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
            'today_only': today_only,
            'headless': headless,
            'allow_duplicates': allow_duplicates
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
            env['PYTHONIOENCODING'] = 'utf-8'  # Force UTF-8 output for subprocess
            
            # Choose the appropriate scraping script
            script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scraping")
            
            if job_data.get('today_only', False):
                scrape_script = os.path.join(script_dir, "scrape_filtered.py")
            else:
                scrape_script = os.path.join(script_dir, "scrape.py")
            
            # Build the command
            cmd = [sys.executable, scrape_script]
            
            # Always pass the input file explicitly
            data_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "results"))
            input_file = os.path.join(data_dir, "spotify-followed-artists-master.json")
            cmd.extend(["--input", input_file])

            # Add arguments based on headless mode
            if job_data.get('headless', True):
                cmd.append("--headless")
                cmd.append("--no-prompt")  # Only skip login prompt in headless mode
            
            # Add allow duplicates flag for both scripts
            if job_data.get('allow_duplicates', False):
                cmd.append("--allow-duplicates")
            
            if job_data.get('today_only', False):
                # Use today's date in YYYY-MM-DD format for filtered script
                today_date = datetime.now().strftime('%Y-%m-%d')
                cmd.extend(["--date", today_date])
            else:
                # Full scraping with scrape.py (now supports headless too)
                pass
            

            logger.info(f"Running scraping command for job {job_id}: {' '.join(cmd)} (cwd={os.path.dirname(scrape_script)})")

            # Update status to running
            update_job_status({'status': 'running'})

            # Run the script with real-time progress tracking
            progress_data = {'current': 0, 'total': 0, 'phase': 'Initializing'}
            output_lines = []
            error_lines = []

            try:
                # Set working directory to the scraping folder
                process = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(scrape_script),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env=env
                )
                # Read output line by line for progress tracking and print to stdout
                for line in iter(process.stdout.readline, ''):
                    if line:
                        output_lines.append(line.rstrip())
                        print(f"[SCRAPER] {line.rstrip()}")
                        # Parse progress information from output
                        parsed_progress = self._parse_progress_line(line.rstrip())
                        if parsed_progress:
                            progress_data.update(parsed_progress)
                            update_job_status({
                                'status': 'running',
                                'progress': progress_data.copy()
                            })
                
                # Wait for process to complete
                return_code = process.wait(timeout=self.scraping_timeout)
                
            except subprocess.TimeoutExpired:
                process.kill()
                raise
            
            # Combine output
            output = '\n'.join(output_lines)
            
            # Update job status with results
            final_status = {
                'status': 'completed' if return_code == 0 else 'failed',
                'output': output,
                'error': '\n'.join(error_lines) if error_lines else '',
                'completed': True,
                'return_code': return_code,
                'completed_at': datetime.now().isoformat()
            }
            update_job_status(final_status)
            
            logger.info(f"Scraping job {job_id} completed with return code: {return_code}")
        
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
    
    def _parse_progress_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a line of output for progress information.
        
        Expected formats:
        - "PROGRESS: Starting scrape of 150 artists"
        - "PROGRESS: Processing artist 45/150: Artist Name"
        - "PROGRESS: Completed scraping 150 artists"
        - "Skipping Artist Name - already scraped today"
        
        Returns:
            Dictionary with progress data or None if no progress found
        """
        import re
        
        # Check for explicit progress markers
        if line.startswith('PROGRESS:'):
            progress_line = line[9:].strip()  # Remove "PROGRESS:" prefix
            
            # Pattern for starting: "Starting scrape of X artists"
            start_match = re.search(r'Starting scrape of (\d+) artists', progress_line)
            if start_match:
                total = int(start_match.group(1))
                return {
                    'total': total,
                    'current': 0,
                    'phase': f'Starting to scrape {total} artists',
                    'details': 'Initializing scraping process...'
                }
            
            # Pattern for current progress: "Processing artist X/Y: Artist Name"
            progress_match = re.search(r'Processing artist (\d+)/(\d+):\s*(.+)', progress_line)
            if progress_match:
                current = int(progress_match.group(1))
                total = int(progress_match.group(2))
                artist_name = progress_match.group(3).strip()
                return {
                    'current': current,
                    'total': total,
                    'phase': f'Scraping artists ({current}/{total})',
                    'current_artist': artist_name,
                    'details': f'Processing: {artist_name}'
                }
            
            # Pattern for completion: "Completed scraping X artists"
            completed_match = re.search(r'Completed scraping (\d+) artists', progress_line)
            if completed_match:
                count = int(completed_match.group(1))
                return {
                    'current': count,
                    'total': count,
                    'phase': 'Completed',
                    'details': f'Successfully processed {count} artists'
                }
        
        # Pattern for skipped artists
        if 'Skipping' in line and 'already scraped today' in line:
            # Extract artist name
            artist_match = re.search(r'Skipping (.+?) - already scraped today', line)
            if artist_match:
                artist_name = artist_match.group(1).strip()
                return {
                    'details': f'Skipped: {artist_name} (already scraped)'
                }
        
        # Pattern for legacy tqdm output fallback
        tqdm_match = re.search(r'(\d+)%.*?(\d+)/(\d+)', line)
        if tqdm_match:
            current = int(tqdm_match.group(2))
            total = int(tqdm_match.group(3))
            return {
                'current': current,
                'total': total,
                'phase': 'Scraping artists'
            }
        
        return None

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
    
    # Removed: run_process_suggestions and all suggestion-processing logic
