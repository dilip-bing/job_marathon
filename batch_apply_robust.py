#!/usr/bin/env python3
"""
Robust Process-Pool Batch Job Application System
=================================================

This module supervises multiple isolated worker processes executing job applications
in parallel with strict resource control, timeout handling, and health monitoring.

Key Features:
- Process isolation (each job in separate Python process)
- Controlled concurrency (max 5 workers default, configurable)
- Individual worker timeouts (30 minutes default)
- Health monitoring every 2 seconds
- Graceful shutdown (Ctrl+C kills all workers)
- Complete logging (no lost logs)
- Batch reports (JSON + human-readable summary)

Usage:
    python batch_apply_robust.py --company-list batches/batch_01.json --skip-generation
    
    Optional flags:
        --max-concurrent 5      # Max workers running simultaneously
        --timeout 30            # Worker timeout in minutes
        --headless              # Run browsers in headless mode
        --skip-generation       # Skip resume/cover letter generation

Architecture:
    Supervisor Process (this file)
        ├── Worker Process 1 (job_worker.py) → Job Application 1
        ├── Worker Process 2 (job_worker.py) → Job Application 2
        ├── Worker Process 3 (job_worker.py) → Job Application 3
        ├── Worker Process 4 (job_worker.py) → Job Application 4
        └── Worker Process 5 (job_worker.py) → Job Application 5
    
    Each worker:
    - Runs in isolated Python process
    - Has own logging with immediate flush
    - Can be killed independently
    - Returns result via JSON
"""

import asyncio
import json
import logging
import subprocess
import sys
import signal
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

# Import HTML report generation
from generate_report import generate_html_report


class WorkerProcess:
    """
    Represents a single worker subprocess running one job application.
    
    This class manages:
    - Subprocess lifecycle (start, monitor, kill)
    - Result collection from subprocess stdout
    - Runtime tracking
    - Status reporting
    """
    
    def __init__(self, job_data: Dict[str, str], config: Dict[str, Any], job_index: int):
        """
        Initialize worker process metadata.
        
        Args:
            job_data: Job information (name, apply_link, date_posted)
            config: Configuration (skip_generation, headless, timeout_minutes)
            job_index: Index of this job in batch (0-based)
        """
        self.job_data = job_data
        self.config = config
        self.job_index = job_index
        
        self.company_name = job_data.get('name', f'Job_{job_index+1}')
        self.job_url = job_data.get('apply_link', '')
        
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.status: str = 'pending'  # pending, running, completed, failed, timeout
        
    def start(self) -> None:
        """
        Launch worker subprocess.
        
        Starts a new Python process running job_worker.py with job data and config
        passed as JSON command-line arguments.
        """
        # Prepare JSON arguments
        job_json = json.dumps(self.job_data)
        config_json = json.dumps(self.config)
        index_str = str(self.job_index)
        
        # Launch subprocess (use DEVNULL to avoid pipe deadlock)
        self.process = subprocess.Popen(
            [sys.executable, 'job_worker.py', job_json, config_json, index_str],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        self.start_time = datetime.now()
        self.status = 'running'
        
    def is_running(self) -> bool:
        """
        Check if subprocess is still running.
        
        Returns:
            True if process is running, False if completed/failed
        """
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def kill(self) -> None:
        """
        Force kill the subprocess.
        
        Used when worker exceeds timeout or batch is interrupted.
        """
        if self.process and self.is_running():
            self.process.kill()
            self.process.wait(timeout=5)  # Wait up to 5 seconds
            self.end_time = datetime.now()
            self.status = 'killed'
    
    def get_runtime(self) -> timedelta:
        """
        Get current runtime of worker.
        
        Returns:
            timedelta representing how long worker has been running
        """
        if self.start_time is None:
            return timedelta(0)
        
        end = self.end_time if self.end_time else datetime.now()
        return end - self.start_time
    
    def collect_result(self) -> Dict[str, Any]:
        """
        Collect result from completed subprocess.
        
        Reads result from JSON file written by worker (avoids pipe deadlock).
        
        Returns:
            Dictionary with worker result, or error result if parsing fails
        """
        if self.process is None:
            return self._error_result('Worker process was never started')
        
        # Wait for process to complete
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.kill()
            return self._error_result('Worker did not terminate cleanly')
        
        self.end_time = datetime.now()
        
        # Read result from JSON file
        result_file = Path('logs') / f'result_{self.job_index:03d}.json'
        
        try:
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    self.result = json.load(f)
                self.status = self.result.get('status', 'failed')
                # Clean up result file
                result_file.unlink()
                return self.result
            else:
                return self._error_result(f'Worker did not create result file: {result_file}')
                
        except json.JSONDecodeError as e:
            return self._error_result(f'Invalid JSON result: {e}')
        except Exception as e:
            return self._error_result(f'Result collection failed: {e}')
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {
            'status': 'failed',
            'job_index': self.job_index,
            'company_name': self.company_name,
            'job_url': self.job_url,
            'error': error_msg,
            'log_file': None,
            'duration_seconds': self.get_runtime().total_seconds()
        }


class ProcessPoolSupervisor:
    """
    Supervisor that manages a pool of worker processes.
    
    Responsibilities:
    - Maintain queue of pending workers
    - Start workers up to max_concurrent limit
    - Monitor worker health every 2 seconds
    - Kill workers that exceed timeout
    - Collect results from completed workers
    - Handle graceful shutdown (Ctrl+C)
    - Generate batch reports
    """
    
    def __init__(self, max_concurrent: int = 5, worker_timeout: int = 30):
        """
        Initialize supervisor.
        
        Args:
            max_concurrent: Maximum workers running simultaneously
            worker_timeout: Worker timeout in minutes
        """
        self.max_concurrent = max_concurrent
        self.worker_timeout = worker_timeout
        
        self.workers: List[WorkerProcess] = []
        self.supervisor_log_path: Optional[Path] = None
        self.logger = self._setup_logging()
        
        self.shutdown_requested = False
        
    def _setup_logging(self) -> logging.Logger:
        """
        Set up supervisor logging.
        
        Returns:
            Logger instance with file and console handlers
        """
        # Create logs directory
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Create logger
        logger = logging.getLogger('ProcessPoolSupervisor')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # File handler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = logs_dir / f'supervisor_{timestamp}.log'
        self.supervisor_log_path = log_file  # Store for later use
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s | SUPERVISOR | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        # Set UTF-8 encoding to handle emojis (Windows fix)
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass  # Python < 3.7 doesn't have reconfigure
        console_formatter = logging.Formatter(
            '%(asctime)s | SUPERVISOR | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _log_and_flush(self, level: str, message: str) -> None:
        """Log message and flush immediately."""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)
        for handler in self.logger.handlers:
            handler.flush()
    
    async def run_batch(self, jobs: List[Dict[str, str]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run batch of jobs with process pool.
        
        Args:
            jobs: List of job data dictionaries
            config: Configuration dictionary
            
        Returns:
            List of result dictionaries from all workers
        """
        start_time = datetime.now()
        total_jobs = len(jobs)
        
        # Create all workers
        self.workers = [
            WorkerProcess(job, config, idx)
            for idx, job in enumerate(jobs)
        ]
        
        # Set up Ctrl+C handler
        def signal_handler(sig, frame):
            self.shutdown_requested = True
            self._log_and_flush('warning', '\n⚠️  BATCH INTERRUPTED BY USER - Initiating graceful shutdown...')
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Log batch start
        self._log_and_flush('info', '=' * 80)
        self._log_and_flush('info', f'🚀 BATCH STARTED: {total_jobs} jobs')
        self._log_and_flush('info', f'   Max Concurrent: {self.max_concurrent}')
        self._log_and_flush('info', f'   Worker Timeout: {self.worker_timeout} minutes')
        self._log_and_flush('info', f'   Headless Mode: {config.get("headless", False)}')
        self._log_and_flush('info', f'   Skip Generation: {config.get("skip_generation", False)}')
        self._log_and_flush('info', '=' * 80)
        self._log_and_flush('info', '')
        
        # Queues
        pending = deque(self.workers)
        running: List[WorkerProcess] = []
        results: List[Dict[str, Any]] = []
        
        # Main supervision loop
        while (pending or running) and not self.shutdown_requested:
            # Start new workers up to max_concurrent
            while pending and len(running) < self.max_concurrent:
                worker = pending.popleft()
                worker.start()
                running.append(worker)
                
                self._log_and_flush('info', f'▶️  Starting Job {worker.job_index + 1}/{total_jobs}: {worker.company_name}')
            
            # Wait before checking status
            await asyncio.sleep(2)
            
            # Check running workers
            completed = []
            for worker in running:
                # Check if completed
                if not worker.is_running():
                    completed.append(worker)
                    continue
                
                # Check if exceeded timeout
                runtime_minutes = worker.get_runtime().total_seconds() / 60
                if runtime_minutes > self.worker_timeout:
                    self._log_and_flush('warning', f'⏰ Job {worker.job_index + 1}/{total_jobs} TIMEOUT after {runtime_minutes:.1f}m - killing process')
                    worker.kill()
                    completed.append(worker)
            
            # Collect results from completed workers
            for worker in completed:
                running.remove(worker)
                result = worker.collect_result()
                results.append(result)
                
                runtime = worker.get_runtime().total_seconds() / 60
                
                if result['status'] == 'success':
                    self._log_and_flush('info', f'✅ Job {worker.job_index + 1}/{total_jobs} COMPLETED in {runtime:.1f}m: {worker.company_name}')
                elif result['status'] == 'timeout':
                    self._log_and_flush('warning', f'⏰ Job {worker.job_index + 1}/{total_jobs} TIMEOUT in {runtime:.1f}m: {worker.company_name}')
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self._log_and_flush('error', f'❌ Job {worker.job_index + 1}/{total_jobs} FAILED in {runtime:.1f}m: {worker.company_name}')
                    self._log_and_flush('error', f'   Error: {error_msg[:200]}')
            
            # Log progress
            if running:
                completed_count = len(results)
                active_workers = ', '.join([
                    f'Job {w.job_index + 1} ({w.get_runtime().total_seconds() / 60:.1f}m)'
                    for w in running[:3]  # Show first 3
                ])
                if len(running) > 3:
                    active_workers += f' +{len(running) - 3} more'
                
                self._log_and_flush('info', f'📊 Progress: {completed_count}/{total_jobs} jobs processed')
                self._log_and_flush('info', f'🔄 Active: {len(running)} workers - {active_workers}')
        
        # Handle shutdown if interrupted
        if self.shutdown_requested:
            self._log_and_flush('warning', f'⚠️  Killing {len(running)} remaining workers...')
            for worker in running:
                worker.kill()
                result = worker._error_result('Batch interrupted by user')
                results.append(result)
        
        # Calculate stats
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Helper to get actual application status (not just worker status)
        def get_app_status(result):
            if result['status'] == 'failed':
                return 'failed'
            if result['status'] == 'timeout':
                return 'timeout'
            # Check application status in details
            details_status = result.get('details', {}).get('status', '')
            if 'impossible' in details_status.lower() or result.get('details', {}).get('blocker_type'):
                return 'impossible'
            return 'success'
        
        successful = sum(1 for r in results if get_app_status(r) == 'success')
        impossible = sum(1 for r in results if get_app_status(r) == 'impossible')
        failed = sum(1 for r in results if get_app_status(r) == 'failed')
        timeouts = sum(1 for r in results if get_app_status(r) == 'timeout')
        
        # Log final summary
        self._log_and_flush('info', '')
        self._log_and_flush('info', '=' * 80)
        self._log_and_flush('info', '🏁 BATCH COMPLETED')
        self._log_and_flush('info', '=' * 80)
        self._log_and_flush('info', f'Duration: {duration / 60:.1f} minutes ({duration:.1f} seconds)')
        self._log_and_flush('info', f'Total Jobs: {total_jobs}')
        self._log_and_flush('info', f'✅ Successful: {successful}')
        self._log_and_flush('info', f'🚫 Impossible Tasks (Blockers): {impossible}')
        self._log_and_flush('info', f'❌ Failed: {failed}')
        self._log_and_flush('info', f'⏰ Timeouts: {timeouts}')
        
        success_rate = (successful / total_jobs * 100) if total_jobs > 0 else 0
        self._log_and_flush('info', f'📈 Success Rate: {success_rate:.1f}%')
        self._log_and_flush('info', '=' * 80)
        self._log_and_flush('info', '')
        
        # Generate reports
        self._generate_batch_report(results, start_time, end_time)
        
        return results
    
    def _generate_batch_report(self, results: List[Dict[str, Any]], start_time: datetime, end_time: datetime) -> None:
        """
        Generate batch reports (JSON + human-readable summary).
        
        Args:
            results: List of worker results
            start_time: Batch start time
            end_time: Batch end time
        """
        timestamp = start_time.strftime('%Y%m%d_%H%M%S')
        duration = (end_time - start_time).total_seconds()
        
        # Helper to get actual application status
        def get_app_status(result):
            if result['status'] == 'failed':
                return 'failed'
            if result['status'] == 'timeout':
                return 'timeout'
            details_status = result.get('details', {}).get('status', '')
            if 'impossible' in details_status.lower() or result.get('details', {}).get('blocker_type'):
                return 'impossible'
            return 'success'
        
        # Stats
        total = len(results)
        successful = sum(1 for r in results if get_app_status(r) == 'success')
        impossible = sum(1 for r in results if get_app_status(r) == 'impossible')
        failed = sum(1 for r in results if get_app_status(r) == 'failed')
        timeouts = sum(1 for r in results if get_app_status(r) == 'timeout')
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # JSON report
        json_report = {
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'total_jobs': total,
            'successful': successful,
            'impossible_tasks': impossible,
            'failed': failed,
            'timeouts': timeouts,
            'success_rate': success_rate,
            'results': results
        }
        
        json_path = Path('logs') / f'batch_report_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2)
        
        # Human-readable summary
        summary_lines = []
        summary_lines.append('=' * 80)
        summary_lines.append('BATCH APPLICATION SUMMARY')
        summary_lines.append('=' * 80)
        summary_lines.append(f'Start Time: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')
        summary_lines.append(f'End Time: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
        summary_lines.append(f'Duration: {duration / 60:.1f} minutes ({duration:.1f} seconds)')
        summary_lines.append(f'Total Jobs: {total}')
        summary_lines.append(f'✅ Successful: {successful}')
        summary_lines.append(f'🚫 Impossible Tasks (Blockers): {impossible}')
        summary_lines.append(f'❌ Failed: {failed}')
        summary_lines.append(f'⏰ Timeouts: {timeouts}')
        summary_lines.append(f'Success Rate: {success_rate:.1f}%')
        summary_lines.append('')
        summary_lines.append('=' * 80)
        summary_lines.append('JOB DETAILS')
        summary_lines.append('=' * 80)
        
        for result in results:
            job_num = result['job_index'] + 1
            company = result['company_name']
            worker_status = result['status'].upper()
            duration_min = result.get('duration_seconds', 0) / 60
            
            # Determine actual application status
            details_status = result.get('details', {}).get('status', '')
            blocker_type = result.get('details', {}).get('blocker_type', '')
            
            if worker_status == 'FAILED' or worker_status == 'TIMEOUT':
                # Worker crashed or timed out
                if worker_status == 'TIMEOUT':
                    summary_lines.append(f'⏰ Job {job_num:02d}: {company} [TIMEOUT] ({duration_min:.1f}m)')
                else:
                    error = result.get('error', 'Unknown error')[:100]
                    summary_lines.append(f'❌ Job {job_num:02d}: {company} [FAILED] ({duration_min:.1f}m)')
                    summary_lines.append(f'    Error: {error}')
            elif 'impossible' in details_status.lower() or blocker_type:
                # Application encountered blocker (CAPTCHA, expired job, etc.)
                blocker = blocker_type or 'Unknown'
                summary_lines.append(f'🚫 Job {job_num:02d}: {company} [IMPOSSIBLE_TASK - {blocker}] ({duration_min:.1f}m)')
            else:
                # Actual success
                summary_lines.append(f'✅ Job {job_num:02d}: {company} [SUCCESS] ({duration_min:.1f}m)')
        
        summary_lines.append('')
        summary_lines.append('=' * 80)
        summary_lines.append('LOG FILES')
        summary_lines.append('=' * 80)
        summary_lines.append(f'JSON Report: {json_path}')
        summary_lines.append('Company Logs: logs/company_logs/')
        summary_lines.append('Screenshots: logs/screenshots/')
        summary_lines.append('=' * 80)
        
        summary_text = '\n'.join(summary_lines)
        
        summary_path = Path('logs') / f'batch_summary_{timestamp}.txt'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        # Print summary to console
        print('\n' + summary_text + '\n')
        
        self._log_and_flush('info', f'📄 Batch report saved:')
        self._log_and_flush('info', f'   JSON: {json_path}')
        self._log_and_flush('info', f'   Summary: {summary_path}')
        
        # Generate HTML report with supervisor log
        self._generate_html_report_with_supervisor_log(results, start_time, timestamp)
    
    def _generate_html_report_with_supervisor_log(self, results: List[Dict[str, Any]], start_time: datetime, timestamp: str) -> None:
        """
        Generate HTML report with supervisor log included at the top.
        
        Args:
            results: List of worker results
            start_time: Batch start time
            timestamp: Timestamp string for filenames
        """
        try:
            from log_parser import parse_worker_log, format_step_timeline_html
            
            # Read supervisor log
            supervisor_log_content = ""
            if self.supervisor_log_path and self.supervisor_log_path.exists():
                with open(self.supervisor_log_path, 'r', encoding='utf-8') as f:
                    supervisor_log_content = f.read()
            
            # Parse worker logs for step-by-step timelines
            job_timelines = {}
            for r in results:
                if r.get('log_file'):
                    parsed_log = parse_worker_log(r['log_file'])
                    job_timelines[r.get('job_url', '')] = format_step_timeline_html(parsed_log)
            
            # Extract job URLs from results
            job_urls = [r['job_url'] for r in results if r.get('job_url')]
            
            # Generate base HTML report using existing function
            # Use last_n_minutes to get recent logs (generous time window)
            batch_duration_minutes = int((datetime.now() - start_time).total_seconds() / 60) + 10
            
            # Create reports directory
            reports_dir = Path('reports')
            reports_dir.mkdir(exist_ok=True)
            
            html_path = reports_dir / f'batch_report_{timestamp}.html'
            generate_html_report(
                output_path=str(html_path),
                job_urls=job_urls if job_urls else None,
                report_name=f'batch_{timestamp}',
                last_n_minutes=batch_duration_minutes
            )
            
            # Now enhance the HTML report with supervisor log at the top
            if html_path.exists():
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Create supervisor log section HTML
                supervisor_section = f"""
        <div class="supervisor-log-section" style="background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="color: #1f2937; margin-bottom: 20px; font-size: 1.5em; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                📊 Batch Supervisor Log
            </h2>
            <div style="background: #f9fafb; border-radius: 8px; padding: 20px; border: 1px solid #e5e7eb;">
                <pre style="margin: 0; font-family: 'Courier New', monospace; font-size: 0.85em; color: #374151; white-space: pre-wrap; word-wrap: break-word; max-height: 600px; overflow-y: auto;">{supervisor_log_content}</pre>
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 4px;">
                <p style="color: #1e40af; font-size: 0.9em; margin: 0;">
                    💡 <strong>Tip:</strong> This log shows the supervisor's view of batch execution including worker lifecycle, progress monitoring, and final statistics.
                </p>
            </div>
        </div>
"""
                
                # Insert supervisor section after the header (before stats section)
                # Find the closing </div> of the header section and insert after it
                header_end = html_content.find('</div>', html_content.find('class="header"'))
                if header_end != -1:
                    # Find the next section start (stats section)
                    stats_start = html_content.find('class="stats"', header_end)
                    if stats_start != -1:
                        # Find the opening <div of stats section
                        div_start = html_content.rfind('<div', header_end, stats_start)
                        if div_start != -1:
                            # Insert supervisor section before stats
                            html_content = html_content[:div_start] + supervisor_section + html_content[div_start:]
                
                # Write enhanced HTML back
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Second pass: Add step timelines to job cards
                if job_timelines:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    for job_url, timeline_html in job_timelines.items():
                        # Find the job card for this URL
                        # Job cards have the URL in an <a> tag
                        url_pos = html_content.find(f'href="{job_url}"')
                        if url_pos == -1:
                            continue
                        
                        # Find the job card div (go backwards to find opening div)
                        card_start = html_content.rfind('<div class="job-card"', 0, url_pos)
                        if card_start == -1:
                            continue
                        
                        # Find the next closing div after the screenshot section
                        # Look for the screenshot div first
                        screenshot_pos = html_content.find('class="screenshot-container"', card_start)
                        if screenshot_pos == -1:
                            # No screenshot, insert before job-card closing
                            card_end = html_content.find('</div>', url_pos)
                        else:
                            # Insert after screenshot div closes
                            card_end = html_content.find('</div>', screenshot_pos) + len('</div>')
                        
                        if card_end == -1:
                            continue
                        
                        # Create timeline section
                        timeline_section = f'''
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                            <h4 style="color: #1f2937; margin-bottom: 15px; font-size: 1.1em;">
                                📋 Application Timeline
                            </h4>
                            {timeline_html}
                        </div>
                        '''
                        
                        # Insert timeline before card closing
                        html_content = html_content[:card_end] + timeline_section + html_content[card_end:]
                    
                    # Write final HTML
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                
                self._log_and_flush('info', f'   HTML Report: {html_path}')
                self._log_and_flush('info', f'   🌐 Open in browser: file:///{html_path.absolute()}')
            
        except Exception as e:
            self._log_and_flush('warning', f'⚠️  HTML report generation failed: {e}')
            # Don't fail the whole batch if HTML generation fails


def load_company_list(file_path: Path) -> List[Dict[str, str]]:
    """
    Load company list from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of job dictionaries
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def main():
    """Main entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description='Robust Process-Pool Batch Job Application System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 5 jobs with defaults
  python batch_apply_robust.py --company-list batches/batch_01.json --skip-generation
  
  # Run with 10 concurrent workers, 45-minute timeout, headless mode
  python batch_apply_robust.py --company-list batches/batch_02.json \\
      --skip-generation --headless --max-concurrent 10 --timeout 45
  
  # Production run (generate docs, normal browser)
  python batch_apply_robust.py --company-list batches/batch_04_to_08_merged.json
        """
    )
    
    parser.add_argument(
        '--company-list',
        type=str,
        required=True,
        help='Path to company list JSON file'
    )
    
    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='Skip resume/cover letter generation (use existing files)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no window, faster)'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=0,  # 0 = auto-detect based on skip_generation
        help='Maximum concurrent workers (0=auto: 10 for skip-generation, 3 for resume generation)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Worker timeout in minutes (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Load jobs
    company_list_path = Path(args.company_list)
    if not company_list_path.exists():
        print(f'❌ Company list file not found: {company_list_path}', file=sys.stderr)
        return 1
    
    jobs = load_company_list(company_list_path)
    
    # Auto-detect max_concurrent based on skip_generation
    max_concurrent = args.max_concurrent
    if max_concurrent == 0:
        # Auto-detect: More workers for skip mode, fewer for API calls
        max_concurrent = 10 if args.skip_generation else 3
        print(f'ℹ️  Auto-detected max concurrent workers: {max_concurrent} (skip_generation={args.skip_generation})')
    
    # Configuration
    config = {
        'skip_generation': args.skip_generation,
        'headless': args.headless,
        'timeout_minutes': args.timeout
    }
    
    # Create supervisor
    supervisor = ProcessPoolSupervisor(
        max_concurrent=max_concurrent,
        worker_timeout=args.timeout
    )
    
    # Run batch
    try:
        results = await supervisor.run_batch(jobs, config)
        
        # Return exit code based on success rate (count only actual successes, not blockers)
        def get_app_status(result):
            if result['status'] == 'failed' or result['status'] == 'timeout':
                return result['status']
            details_status = result.get('details', {}).get('status', '')
            if 'impossible' in details_status.lower() or result.get('details', {}).get('blocker_type'):
                return 'impossible'
            return 'success'
        
        successful = sum(1 for r in results if get_app_status(r) == 'success')
        success_rate = (successful / len(results) * 100) if results else 0
        
        # Exit code 0 if at least 50% success
        return 0 if success_rate >= 50 else 1
        
    except Exception as e:
        print(f'❌ Batch processing failed: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
