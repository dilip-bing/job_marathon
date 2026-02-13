#!/usr/bin/env python3
"""
Log Parser for Job Application Automation
==========================================

Parses worker log files to extract application steps and timeline.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def parse_worker_log(log_file_path: str) -> Dict:
    """
    Parse a worker log file to extract application steps.
    
    Args:
        log_file_path: Path to worker log file
        
    Returns:
        Dictionary with:
            - steps: List of step dictionaries (timestamp, message, level)
            - duration: Total duration in seconds
            - status: final status (SUCCESS/FAILED/TIMEOUT)
            - error: Error message if failed
    """
    log_path = Path(log_file_path)
    
    if not log_path.exists():
        return {
            'steps': [],
            'duration': 0,
            'status': 'UNKNOWN',
            'error': 'Log file not found'
        }
    
    steps = []
    start_time = None
    end_time = None
    status = 'UNKNOWN'
    error = None
    
    # Step patterns to detect
    step_patterns = [
        (r'WORKER STARTED:', 'Worker Started', 'info'),
        (r'JOB APPLICATION AUTOMATION STARTED', 'Automation Started', 'info'),
        (r'SKIP MODE: Using latest existing documents', 'Using Existing Documents', 'info'),
        (r'User profile loaded', 'Profile Loaded', 'info'),
        (r'Job description scraped', 'Job Description Scraped', 'info'),
        (r'Resume generated', 'Resume Generated', 'success'),
        (r'Resume saved:', 'Resume Saved', 'success'),
        (r'Cover letter generated', 'Cover Letter Generated', 'success'),
        (r'Cover letter SKIPPED', 'Cover Letter Skipped', 'warning'),
        (r'Launching browser', 'Browser Launched', 'info'),
        (r'Navigating to job URL', 'Navigated to Job', 'info'),
        (r'Filling application form', 'Filling Form', 'info'),
        (r'Screenshot captured:', 'Screenshot Captured', 'info'),
        (r'APPLICATION COMPLETED SUCCESSFULLY', 'Application Completed', 'success'),
        (r'WORKER FAILED:', 'Worker Failed', 'error'),
        (r'WORKER TIMEOUT:', 'Worker Timeout', 'error'),
        (r'impossible_task=True', 'Blocker Detected', 'warning'),
        (r'EXPIRED_JOB', 'Job Expired', 'error'),
        (r'CAPTCHA', 'CAPTCHA Detected', 'error'),
        (r'EMAIL_VERIFICATION', 'Email Verification Required', 'error'),
    ]
    
    # Parse log file
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Extract timestamp and message
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s+\| (.+)', line)
            if not match:
                continue
            
            timestamp_str, level, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Track start/end times
            if start_time is None:
                start_time = timestamp
            end_time = timestamp
            
            # Check for status markers
            if 'APPLICATION COMPLETED SUCCESSFULLY' in message:
                status = 'SUCCESS'
            elif 'WORKER FAILED' in message or 'FAILED' in message.upper():
                status = 'FAILED'
                error = message
            elif 'WORKER TIMEOUT' in message:
                status = 'TIMEOUT'
                error = message
            
            # Match step patterns
            for pattern, step_name, step_level in step_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    # Extract additional details if present
                    details = message.strip()
                    
                    steps.append({
                        'timestamp': timestamp_str,
                        'name': step_name,
                        'level': step_level,
                        'details': details,
                        'elapsed_seconds': (timestamp - start_time).total_seconds() if start_time else 0
                    })
                    break
    
    # Calculate duration
    duration = (end_time - start_time).total_seconds() if start_time and end_time else 0
    
    return {
        'steps': steps,
        'duration': duration,
        'status': status,
        'error': error,
        'start_time': start_time.isoformat() if start_time else None,
        'end_time': end_time.isoformat() if end_time else None
    }


def format_step_timeline_html(parsed_log: Dict) -> str:
    """
    Format parsed log as HTML timeline.
    
    Args:
        parsed_log: Output from parse_worker_log()
        
    Returns:
        HTML string with step-by-step timeline
    """
    if not parsed_log['steps']:
        return '<p style="color: #6b7280; font-style: italic;">No steps recorded</p>'
    
    html_parts = []
    html_parts.append('<div style="margin-top: 20px;">')
    html_parts.append('<div style="position: relative; padding-left: 30px;">')
    
    # Timeline line
    html_parts.append('<div style="position: absolute; left: 10px; top: 0; bottom: 0; width: 2px; background: #e5e7eb;"></div>')
    
    for step in parsed_log['steps']:
        # Choose icon and color based on level
        if step['level'] == 'success':
            icon = '✅'
            border_color = '#10b981'
        elif step['level'] == 'error':
            icon = '❌'
            border_color = '#ef4444'
        elif step['level'] == 'warning':
            icon = '⚠️'
            border_color = '#f59e0b'
        else:
            icon = '▶️'
            border_color = '#3b82f6'
        
        elapsed_min = step['elapsed_seconds'] / 60
        
        html_parts.append(f'''
        <div style="position: relative; margin-bottom: 15px;">
            <div style="position: absolute; left: -25px; width: 20px; height: 20px; background: white; border: 2px solid {border_color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px;">
                {icon}
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <strong style="color: #1f2937; font-size: 0.95em;">{step['name']}</strong>
                    <span style="color: #6b7280; font-size: 0.85em;">+{elapsed_min:.1f}m</span>
                </div>
                <div style="color: #4b5563; font-size: 0.85em; font-family: 'Courier New', monospace;">
                    {step['timestamp']}
                </div>
            </div>
        </div>
        ''')
    
    html_parts.append('</div>')
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


if __name__ == '__main__':
    # Test with latest worker log
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        # Find latest worker log
        logs_dir = Path('logs/company_logs')
        log_files = sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
        if log_files:
            log_file = str(log_files[0])
        else:
            print('No log files found')
            sys.exit(1)
    
    print(f'\n=== Parsing: {log_file} ===\n')
    
    parsed = parse_worker_log(log_file)
    
    print(f'Status: {parsed["status"]}')
    print(f'Duration: {parsed["duration"]:.1f} seconds ({parsed["duration"]/60:.1f} minutes)')
    print(f'Steps: {len(parsed["steps"])}')
    print('\nTimeline:')
    for step in parsed['steps']:
        print(f'  [{step["elapsed_seconds"]:>6.1f}s] {step["name"]:30s} | {step["timestamp"]}')
