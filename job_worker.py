#!/usr/bin/env python3
"""
Isolated Worker Process for Job Application Automation
======================================================

This module runs a SINGLE job application in a completely isolated process.
Each worker has its own logging, timeout handling, and error isolation.

Key Features:
- Process-level isolation (no shared resources)
- Immediate log flushing (no lost logs)
- Signal-based timeout (30-minute default)
- JSON-based result communication
- Comprehensive error handling

Usage:
    python job_worker.py <job_json> <config_json> <job_index>
    
    Where:
        job_json: JSON string with keys: name, apply_link, date_posted
        config_json: JSON string with keys: skip_generation, headless
        job_index: Integer index of this job (0-based)
"""

import asyncio
import json
import logging
import sys
import signal
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import existing automation function (no changes to it)
from job_application_automation import automate_job_application


class TimeoutException(Exception):
    """Raised when worker process exceeds timeout."""
    pass


class JobWorker:
    """
    Isolated worker process that runs a single job application.
    
    This class handles:
    - Isolated logging with immediate flush
    - Process-level timeout using signals
    - Complete error isolation
    - JSON result serialization
    """
    
    def __init__(self, job_data: Dict[str, str], config: Dict[str, Any], job_index: int):
        """
        Initialize worker with job data and configuration.
        
        Args:
            job_data: Dictionary with keys: name, apply_link, date_posted
            config: Dictionary with keys: skip_generation, headless, timeout_minutes
            job_index: Index of this job in the batch (0-based)
        """
        self.job_data = job_data
        self.config = config
        self.job_index = job_index
        
        self.company_name = job_data.get('name', f'Job_{job_index+1}')
        self.job_url = job_data.get('apply_link', '')
        self.date_posted = job_data.get('date_posted', 'Unknown')
        
        self.skip_generation = config.get('skip_generation', False)
        self.headless = config.get('headless', False)
        self.timeout_minutes = config.get('timeout_minutes', 30)
        
        self.logger: Optional[logging.Logger] = None
        self.log_file_path: Optional[Path] = None
        self.start_time = datetime.now()
        
    def setup_logging(self) -> None:
        """
        Set up isolated logging for this worker.
        
        Creates:
        - File handler: logs/company_logs/{index:03d}_{company}_{timestamp}.log
        - Console handler with [JOB XX] prefix
        - Immediate flush after every log entry
        """
        # Create company logs directory
        logs_dir = Path('logs/company_logs')
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique log file name
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        safe_company = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                              for c in self.company_name)[:50]
        safe_company = safe_company.replace(' ', '_')
        
        log_filename = f"{self.job_index+1:03d}_{safe_company}_{timestamp}.log"
        self.log_file_path = logs_dir / log_filename
        
        # Create isolated logger (not root logger)
        logger_name = f'JobWorker_{self.job_index}'
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Remove any existing handlers
        self.logger.handlers.clear()
        
        # File handler with immediate flush
        file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with [JOB XX] prefix
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        # Set UTF-8 encoding to handle emojis (Windows fix)
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass  # Python < 3.7 doesn't have reconfigure
        console_formatter = logging.Formatter(
            f'%(asctime)s | [JOB {self.job_index+1:02d}] | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # IMPORTANT: Also configure the automation logger to write to same file
        # This ensures all automation steps are captured in the worker log
        automation_logger = logging.getLogger(f"JobAutomation_Job{self.job_index+1:02d}")
        automation_logger.setLevel(logging.INFO)
        automation_logger.propagate = False
        automation_logger.handlers.clear()
        automation_logger.addHandler(file_handler)
        automation_logger.addHandler(console_handler)
        
    def log_and_flush(self, level: str, message: str) -> None:
        """
        Log message and immediately flush to disk.
        
        This ensures no logs are lost even if process is killed.
        
        Args:
            level: Logging level (info, warning, error, etc.)
            message: Message to log
        """
        if self.logger:
            log_func = getattr(self.logger, level.lower(), self.logger.info)
            log_func(message)
            
            # CRITICAL: Flush all handlers immediately
            for handler in self.logger.handlers:
                handler.flush()
    
    def setup_timeout_handler(self) -> None:
        """
        Set up process-level timeout using SIGALRM.
        
        If worker exceeds timeout, SIGALRM is raised and TimeoutException is thrown.
        Note: signal.alarm() only works on Unix systems.
        """
        def timeout_handler(signum, frame):
            raise TimeoutException(f"Worker timeout after {self.timeout_minutes} minutes")
        
        # Only set up signal handler on Unix systems
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_minutes * 60)  # Convert to seconds
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the job application automation.
        
        Returns:
            Dictionary with keys:
                - status: 'success', 'failed', or 'timeout'
                - job_index: Index of this job
                - company_name: Company name
                - job_url: Job URL
                - error: Error message (if failed)
                - log_file: Path to log file
                - duration_seconds: Runtime in seconds
        """
        result = {
            'status': 'failed',
            'job_index': self.job_index,
            'company_name': self.company_name,
            'job_url': self.job_url,
            'date_posted': self.date_posted,
            'error': None,
            'log_file': str(self.log_file_path) if self.log_file_path else None,
            'duration_seconds': 0.0
        }
        
        try:
            self.log_and_flush('info', '=' * 80)
            self.log_and_flush('info', f'WORKER STARTED: {self.company_name}')
            self.log_and_flush('info', '=' * 80)
            self.log_and_flush('info', f'Job URL: {self.job_url}')
            self.log_and_flush('info', f'Date Posted: {self.date_posted}')
            self.log_and_flush('info', f'Index: {self.job_index + 1}')
            self.log_and_flush('info', f'Skip Generation: {self.skip_generation}')
            self.log_and_flush('info', f'Headless Mode: {self.headless}')
            self.log_and_flush('info', f'Timeout: {self.timeout_minutes} minutes')
            self.log_and_flush('info', f'Log File: {self.log_file_path}')
            self.log_and_flush('info', '=' * 80)
            self.log_and_flush('info', '')
            
            # Run the automation (calls existing function - no changes needed)
            self.log_and_flush('info', '🚀 Starting automation process...')
            
            automation_result = await automate_job_application(
                job_url=self.job_url,
                skip_generation=self.skip_generation,
                job_index=self.job_index,
                headless=self.headless
            )
            
            # Success
            result['status'] = 'success'
            result['details'] = automation_result
            
            self.log_and_flush('info', '')
            self.log_and_flush('info', '=' * 80)
            self.log_and_flush('info', '✅ APPLICATION COMPLETED SUCCESSFULLY')
            self.log_and_flush('info', '=' * 80)
            self.log_and_flush('info', '')
            
        except TimeoutException as e:
            # Worker timeout
            result['status'] = 'timeout'
            result['error'] = str(e)
            
            self.log_and_flush('error', '')
            self.log_and_flush('error', '=' * 80)
            self.log_and_flush('error', f'⏰ WORKER TIMEOUT: {e}')
            self.log_and_flush('error', '=' * 80)
            self.log_and_flush('error', '')
            
        except Exception as e:
            # Any other error
            result['status'] = 'failed'
            result['error'] = str(e)
            
            self.log_and_flush('error', '')
            self.log_and_flush('error', '=' * 80)
            self.log_and_flush('error', f'❌ WORKER FAILED: {e}')
            self.log_and_flush('error', '=' * 80)
            self.log_and_flush('error', 'Traceback:')
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.log_and_flush('error', line)
            self.log_and_flush('error', '=' * 80)
            self.log_and_flush('error', '')
            
        finally:
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            result['duration_seconds'] = duration
            
            # Final log flush
            self.log_and_flush('info', f'⏱️  Total Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)')
            self.log_and_flush('info', f'📊 Final Status: {result["status"].upper()}')
            
            # Ensure all logs are written
            if self.logger:
                for handler in self.logger.handlers:
                    handler.flush()
                    handler.close()
        
        return result


def worker_main(job_json: str, config_json: str, job_index: str) -> int:
    """
    Main entry point for worker process.
    
    This function:
    1. Parses input arguments
    2. Sets up worker with logging and timeout
    3. Runs automation
    4. Prints result as JSON between markers
    5. Returns exit code
    
    Args:
        job_json: JSON string with job data
        config_json: JSON string with configuration
        job_index: String representation of job index
        
    Returns:
        Exit code (0 for success, 1 for failure/timeout)
    """
    try:
        # Parse inputs
        job_data = json.loads(job_json)
        config = json.loads(config_json)
        index = int(job_index)
        
        # Create worker
        worker = JobWorker(job_data, config, index)
        
        # Set up logging
        worker.setup_logging()
        
        # Set up timeout handler (Unix only)
        if hasattr(signal, 'SIGALRM'):
            worker.setup_timeout_handler()
        
        # Run automation
        result = asyncio.run(worker.run())
        
        # Write result to JSON file (avoid stdout pipe deadlock)
        result_file = Path('logs') / f'result_{index:03d}.json'
        result_file.parent.mkdir(parents=True, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        # Print brief completion message (won't overflow pipe)
        print(f'Worker {index} completed: {result["status"]}')
        
        # Return exit code
        return 0 if result['status'] == 'success' else 1
        
    except Exception as e:
        # Catastrophic failure (couldn't even set up worker)
        index = int(job_index) if job_index.isdigit() else -1
        error_result = {
            'status': 'failed',
            'job_index': index,
            'company_name': 'Unknown',
            'job_url': '',
            'error': f'Worker initialization failed: {str(e)}',
            'log_file': None,
            'duration_seconds': 0.0
        }
        
        # Write error result to file
        result_file = Path('logs') / f'result_{index:03d}.json'
        result_file.parent.mkdir(parents=True, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        
        print(f'Worker {index} failed during init: {str(e)}')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python job_worker.py <job_json> <config_json> <job_index>', file=sys.stderr)
        sys.exit(1)
    
    exit_code = worker_main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(exit_code)
