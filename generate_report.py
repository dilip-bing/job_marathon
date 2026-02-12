"""
═══════════════════════════════════════════════════════════════════════════════
HTML REPORT GENERATOR
═══════════════════════════════════════════════════════════════════════════════

Generates beautiful HTML reports for job application automation results.
Shows applications, results, screenshots, failure details, and logs.

Author: Dilip Kumar
Date: February 12, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import base64

# Import config
from config import LOGS_DIR, SCREENSHOTS_DIR, APPLICATION_LOG_FILE, REPORTS_DIR


def load_application_logs() -> List[Dict]:
    """Load all application logs from JSON file."""
    if not APPLICATION_LOG_FILE.exists():
        return []
    
    with open(APPLICATION_LOG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both formats: list or dict with 'applications' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('applications', [])
        return []


def get_screenshot_for_url(job_url: str) -> str:
    """Find screenshot for a job URL."""
    from urllib.parse import urlparse
    
    try:
        domain = urlparse(job_url).netloc.replace('www.', '').split('.')[0]
        
        # Find most recent screenshot for this domain
        screenshots = list(SCREENSHOTS_DIR.glob(f"{domain}_*.png"))
        if screenshots:
            latest = max(screenshots, key=lambda p: p.stat().st_mtime)
            return str(latest)
    except Exception:
        pass
    
    return None


def screenshot_to_base64(screenshot_path: str) -> str:
    """Convert screenshot to base64 for embedding in HTML."""
    try:
        with open(screenshot_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        return None


def get_status_color(status: str) -> str:
    """Get color for status badge."""
    status_lower = status.lower()
    
    if 'success' in status_lower:
        return '#22c55e'  # Green
    elif 'impossible' in status_lower or 'blocker' in status_lower:
        return '#f59e0b'  # Orange
    elif 'fail' in status_lower or 'error' in status_lower:
        return '#ef4444'  # Red
    else:
        return '#6b7280'  # Gray


def get_status_icon(status: str) -> str:
    """Get emoji icon for status."""
    status_lower = status.lower()
    
    if 'success' in status_lower:
        return '✅'
    elif 'impossible' in status_lower or 'blocker' in status_lower:
        return '🚫'
    elif 'fail' in status_lower or 'error' in status_lower:
        return '❌'
    else:
        return '❓'


def generate_html_report(output_path: str = None, job_urls: List[str] = None, report_name: str = None, last_n_minutes: int = None) -> str:
    """
    Generate HTML report from application logs.
    
    Args:
        output_path: Path to save HTML report (default: auto-generated unique name)
        job_urls: Optional list of job URLs to filter (only include these jobs)
        report_name: Optional custom report name (e.g., 'batch_03', 'renesas_test')
        last_n_minutes: Optional - only include logs from last N minutes (for single-job runs)
    
    Returns:
        Path to generated report
    """
    # Generate unique report name if not specified
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if report_name:
            filename = f"report_{report_name}_{timestamp}.html"
        else:
            filename = f"report_{timestamp}.html"
        output_path = REPORTS_DIR / filename
    
    # Load logs
    all_logs = load_application_logs()
    
    # Apply time-based filter first (for single-job runs)
    if last_n_minutes is not None:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=last_n_minutes)
        all_logs = [
            log for log in all_logs 
            if datetime.fromisoformat(log.get('timestamp', '2000-01-01T00:00:00')) > cutoff_time
        ]
    
    # Filter logs if job_urls provided
    if job_urls:
        logs = [log for log in all_logs if log.get('job_url') in job_urls]
        if not logs:
            print(f"⚠️  No logs found for specified job URLs in the filtered time range")
            # Don't fall back to all logs - user wants specific jobs only
            logs = []
    else:
        logs = all_logs
    
    # Count statistics
    total = len(logs)
    successes = sum(1 for log in logs if 'success' in log.get('status', '').lower())
    blockers = sum(1 for log in logs if 'impossible' in log.get('status', '').lower())
    failures = sum(1 for log in logs if 'fail' in log.get('status', '').lower() or 'error' in log.get('status', '').lower())
    
    success_rate = (successes / total * 100) if total > 0 else 0
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Application Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .header h1 {{
            color: #1f2937;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        
        .header .subtitle {{
            color: #6b7280;
            font-size: 0.95em;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-card.success {{
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        }}
        
        .stat-card.blocker {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }}
        
        .stat-card.failure {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .applications {{
            display: grid;
            gap: 20px;
        }}
        
        .app-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .app-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .app-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .app-title {{
            flex: 1;
            min-width: 200px;
        }}
        
        .app-title h3 {{
            color: #1f2937;
            font-size: 1.3em;
            margin-bottom: 5px;
        }}
        
        .app-title .url {{
            color: #6b7280;
            font-size: 0.85em;
            word-break: break-all;
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            color: white;
        }}
        
        .app-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        
        .detail-section {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
        }}
        
        .detail-section h4 {{
            color: #374151;
            margin-bottom: 10px;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .detail-section ul {{
            list-style: none;
        }}
        
        .detail-section li {{
            color: #6b7280;
            font-size: 0.9em;
            padding: 5px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .detail-section li:last-child {{
            border-bottom: none;
        }}
        
        .detail-section li.success {{
            color: #16a34a;
        }}
        
        .detail-section li.error {{
            color: #dc2626;
        }}
        
        .screenshot-container {{
            margin-top: 15px;
        }}
        
        .screenshot-container h4 {{
            color: #374151;
            margin-bottom: 10px;
            font-size: 0.95em;
        }}
        
        .screenshot-container img {{
            width: 100%;
            max-width: 800px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .screenshot-container img:hover {{
            transform: scale(1.02);
        }}
        
        .no-screenshot {{
            color: #9ca3af;
            font-style: italic;
            font-size: 0.9em;
        }}
        
        .error-message {{
            background: #fee2e2;
            border-left: 4px solid #ef4444;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }}
        
        .error-message h4 {{
            color: #991b1b;
            margin-bottom: 8px;
            font-size: 0.95em;
        }}
        
        .error-message p {{
            color: #7f1d1d;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        
        .actions {{
            margin-top: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
        }}
        
        .btn-secondary {{
            background: #e5e7eb;
            color: #374151;
        }}
        
        .btn-secondary:hover {{
            background: #d1d5db;
        }}
        
        .timestamp {{
            color: #9ca3af;
            font-size: 0.85em;
            margin-top: 10px;
        }}
        
        .collapsible {{
            cursor: pointer;
            user-select: none;
        }}
        
        .collapsible::after {{
            content: ' ▼';
            font-size: 0.8em;
        }}
        
        .collapsible.collapsed::after {{
            content: ' ▶';
        }}
        
        .collapsible-content {{
            max-height: 1000px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        
        .collapsible-content.collapsed {{
            max-height: 0;
        }}
        
        .log-section {{
            margin-top: 20px;
            border-top: 1px solid #e5e7eb;
            padding-top: 15px;
        }}
        
        .btn-log {{
            background: #8b5cf6;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .btn-log:hover {{
            background: #7c3aed;
        }}
        
        .log-content {{
            margin-top: 15px;
            background: #1e293b;
            border-radius: 8px;
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .log-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .log-header h4 {{
            color: #f1f5f9;
            margin: 0;
        }}
        
        .btn-close {{
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 12px;
            cursor: pointer;
            font-weight: bold;
        }}
        
        .btn-close:hover {{
            background: #dc2626;
        }}
        
        .log-data {{
            background: #0f172a;
            color: #94a3b8;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
        }}
        
        @media (max-width: 768px) {{
            .app-details {{
                grid-template-columns: 1fr;
            }}
            
            .stats {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Job Application Automation Report</h1>
            <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="number">{total}</div>
                    <div class="label">Total Applications</div>
                </div>
                <div class="stat-card success">
                    <div class="number">{successes}</div>
                    <div class="label">✅ Successful</div>
                </div>
                <div class="stat-card blocker">
                    <div class="number">{blockers}</div>
                    <div class="label">🚫 Impossible Tasks</div>
                </div>
                <div class="stat-card failure">
                    <div class="number">{failures}</div>
                    <div class="label">❌ Failures</div>
                </div>
            </div>
            
            <div class="actions">
                <a href="application_log.json" class="btn btn-primary" target="_blank">📄 View Detailed Logs (JSON)</a>
                <a href="screenshots/" class="btn btn-secondary" target="_blank">📸 View All Screenshots</a>
            </div>
        </div>
        
        <div class="applications">
"""
    
    # Add application cards
    for i, log in enumerate(logs, 1):
        job_url = log.get('job_url', 'Unknown')
        status = log.get('status', 'Unknown')
        status_color = get_status_color(status)
        status_icon = get_status_icon(status)
        
        # Extract domain for title
        from urllib.parse import urlparse
        try:
            domain = urlparse(job_url).netloc.replace('www.', '').split('.')[0].title()
        except:
            domain = "Unknown Company"
        
        # Get timestamps
        start_time = log.get('start_time', '')
        end_time = log.get('end_time', '')
        
        try:
            start_dt = datetime.fromisoformat(start_time)
            start_formatted = start_dt.strftime('%b %d, %Y %I:%M %p')
        except:
            start_formatted = start_time
        
        # Get steps completed
        steps = log.get('steps_completed', [])
        
        # Get errors/blockers
        errors = log.get('errors', [])
        blocker_type = log.get('blocker_type', '')
        form_result = log.get('form_result', '')
        
        # Get screenshot
        screenshot_path = get_screenshot_for_url(job_url)
        
        html += f"""
            <div class="app-card">
                <div class="app-header">
                    <div class="app-title">
                        <h3>Application #{i}: {domain}</h3>
                        <p class="url">{job_url}</p>
                    </div>
                    <div class="status-badge" style="background-color: {status_color};">
                        {status_icon} {status}
                    </div>
                </div>
                
                <div class="timestamp">
                    🕐 Started: {start_formatted}
                </div>
                
                <div class="app-details">
                    <div class="detail-section">
                        <h4 class="collapsible" onclick="toggleCollapse(this)">Steps Completed ({len(steps)})</h4>
                        <ul class="collapsible-content">
"""
        
        for step in steps:
            step_class = 'success' if any(x in step.lower() for x in ['success', 'generated', 'filled', 'loaded']) else ''
            if 'error' in step.lower() or 'fail' in step.lower() or 'blocker' in step.lower():
                step_class = 'error'
            html += f"                            <li class='{step_class}'>✓ {step}</li>\n"
        
        html += """                        </ul>
                    </div>
"""
        
        # Add error/blocker section if present
        if errors or blocker_type or ('fail' in status.lower() or 'impossible' in status.lower()):
            html += """                    <div class="detail-section">
                        <h4>Issues Detected</h4>
"""
            if blocker_type:
                html += f"""                        <div class="error-message">
                            <h4>🚫 Blocker: {blocker_type.replace('_', ' ').title()}</h4>
                            <p>{form_result}</p>
                        </div>
"""
            
            if errors:
                for error in errors:
                    html += f"""                        <div class="error-message">
                            <h4>❌ Error</h4>
                            <p>{error}</p>
                        </div>
"""
            
            html += """                    </div>
"""
        
        html += """                </div>
"""
        
        # Add screenshot if available
        if screenshot_path and Path(screenshot_path).exists():
            screenshot_b64 = screenshot_to_base64(screenshot_path)
            if screenshot_b64:
                html += f"""                <div class="screenshot-container">
                    <h4 class="collapsible" onclick="toggleCollapse(this)">📸 Screenshot</h4>
                    <div class="collapsible-content">
                        <img src="data:image/png;base64,{screenshot_b64}" alt="Application Screenshot" onclick="window.open(this.src)">
                    </div>
                </div>
"""
        else:
            html += """                <div class="screenshot-container">
                    <p class="no-screenshot">📸 Screenshot not available</p>
                </div>
"""
        
        # Add View Log button and collapsible log section
        import json
        log_json = json.dumps(log, indent=2, default=str)
        log_json_escaped = log_json.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
        
        html += f"""                <div class="log-section">
                    <button class="btn btn-log" onclick="toggleLog('log-{i}')">📋 View Application Log</button>
                    <div id="log-{i}" class="log-content" style="display: none;">
                        <div class="log-header">
                            <h4>Application Log Details</h4>
                            <button class="btn-close" onclick="toggleLog('log-{i}')">✕</button>
                        </div>
                        <pre class="log-data">{log_json}</pre>
                    </div>
                </div>
"""
        
        html += """            </div>
"""
    
    # Close HTML
    html += """        </div>
    </div>
    
    <script>
        function toggleCollapse(element) {
            element.classList.toggle('collapsed');
            const content = element.nextElementSibling;
            content.classList.toggle('collapsed');
        }
        
        function toggleLog(logId) {
            const logContent = document.getElementById(logId);
            if (logContent.style.display === 'none') {
                logContent.style.display = 'block';
            } else {
                logContent.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""
    
    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_path}")
    print(f"   Total applications: {total}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"\n🌐 Open in browser: file:///{output_path.absolute()}")
    
    return str(output_path)


if __name__ == "__main__":
    generate_html_report()
