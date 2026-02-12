"""
═══════════════════════════════════════════════════════════════════════════════
BATCH JOB APPLICATION AUTOMATION
═══════════════════════════════════════════════════════════════════════════════

Description:
    Batch processor to apply for multiple jobs listed in company_list.json.
    Features:
    - Processes each job one by one
    - Continues even if individual jobs fail
    - Detailed logs per company
    - Summary report for quick review
    - Fail-proof error handling

Author: Dilip Kumar
Date: February 11, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import the main automation function
from job_application_automation import automate_job_application, load_user_profile

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
COMPANY_LIST_FILE = BASE_DIR / "company_list.json"  # Can be overridden by --company-list
LOGS_DIR = BASE_DIR / "logs"
COMPANY_LOGS_DIR = LOGS_DIR / "company_logs"
SCREENSHOTS_DIR = LOGS_DIR / "screenshots"
BATCH_SUMMARY_FILE = LOGS_DIR / "batch_summary.txt"
BATCH_REPORT_FILE = LOGS_DIR / "batch_report.json"
PROGRESS_FILE = LOGS_DIR / "batch_progress.json"

# Create directories
LOGS_DIR.mkdir(exist_ok=True)
COMPANY_LOGS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════════════

def setup_batch_logging():
    """Configure logging for batch processing."""
    
    # Create timestamp for this batch run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_log_file = LOGS_DIR / f"batch_run_{timestamp}.log"
    
    # Configure logging format
    log_format = "%(asctime)s | %(levelname)8s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Setup root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(batch_log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger instance
    logger = logging.getLogger("BatchApply")
    logger.setLevel(logging.INFO)
    
    # Log startup
    logger.info("=" * 80)
    logger.info("BATCH JOB APPLICATION AUTOMATION - STARTED")
    logger.info("=" * 80)
    logger.info(f"Batch log file: {batch_log_file}")
    logger.info(f"Company logs directory: {COMPANY_LOGS_DIR}")
    logger.info(f"Summary file: {BATCH_SUMMARY_FILE}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("")
    
    return logger, batch_log_file

# Initialize logger
logger, batch_log_file = setup_batch_logging()

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def load_company_list(company_list_path: Path = None) -> List[Dict]:
    """Load company list from JSON file."""
    logger.info("=" * 80)
    logger.info("LOADING COMPANY LIST")
    logger.info("=" * 80)
    
    # Use provided path or default
    list_path = company_list_path if company_list_path else COMPANY_LIST_FILE
    
    try:
        if not list_path.exists():
            logger.error(f"❌ Company list file not found: {list_path}")
            raise FileNotFoundError(f"Company list not found at {list_path}")
        
        with open(list_path, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        logger.info(f"✅ Loaded {len(companies)} companies from {list_path.name}")
        logger.info("")
        
        return companies
        
    except Exception as e:
        logger.error(f"❌ Failed to load company list: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def load_progress() -> Dict:
    """Load progress from previous batch run if exists."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            logger.info(f"📋 Loaded progress from previous run")
            logger.info(f"   Completed: {len(progress.get('completed', []))}")
            logger.info(f"   Failed: {len(progress.get('failed', []))}")
            logger.info("")
            return progress
        except:
            logger.warning("⚠️  Could not load previous progress, starting fresh")
    
    return {
        "completed": [],
        "failed": [],
        "skipped": [],
        "in_progress": None
    }

def save_progress(progress: Dict):
    """Save current progress to file."""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"⚠️  Failed to save progress: {str(e)}")

def sanitize_filename(name: str) -> str:
    """Convert company name to safe filename."""
    # Remove special characters and replace spaces with underscores
    safe_name = "".join(c if c.isalnum() or c in (' ', '-') else '_' for c in name)
    safe_name = safe_name.replace(' ', '_')
    # Limit length
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    return safe_name

def setup_company_logger(company_name: str, index: int) -> logging.Logger:
    """Create a separate logger for each company."""
    
    # Create safe filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(company_name)
    log_filename = f"{index+1:03d}_{safe_name}_{timestamp}.log"
    log_filepath = COMPANY_LOGS_DIR / log_filename
    
    # Create logger
    company_logger = logging.getLogger(f"Company_{index}")
    company_logger.setLevel(logging.INFO)
    company_logger.handlers = []  # Clear any existing handlers
    
    # Add file handler
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    company_logger.addHandler(file_handler)
    
    # Add console handler with job prefix for parallel execution clarity
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        f"%(asctime)s | %(levelname)8s | [JOB {index+1:02d}] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    company_logger.addHandler(console_handler)
    
    return company_logger, log_filepath

def save_batch_report(results: List[Dict], start_time: datetime, end_time: datetime):
    """Save detailed batch report as JSON and readable summary."""
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    duration = end_time - start_time
    
    # Create detailed report
    report = {
        "batch_info": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration)
        },
        "statistics": {
            "total_jobs": total,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        },
        "results": results
    }
    
    # Save JSON report
    with open(BATCH_REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Create human-readable summary
    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append("BATCH JOB APPLICATION AUTOMATION - SUMMARY REPORT")
    summary_lines.append("=" * 80)
    summary_lines.append("")
    summary_lines.append(f"📅 Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append(f"📅 Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append(f"⏱️  Duration: {duration}")
    summary_lines.append("")
    summary_lines.append("=" * 80)
    summary_lines.append("STATISTICS")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Total Jobs:     {total}")
    summary_lines.append(f"✅ Successful:  {successful}")
    summary_lines.append(f"❌ Failed:      {failed}")
    summary_lines.append(f"⏭️  Skipped:     {skipped}")
    summary_lines.append(f"📊 Success Rate: {(successful/total*100):.1f}%" if total > 0 else "0%")
    summary_lines.append("")
    summary_lines.append("=" * 80)
    summary_lines.append("DETAILED RESULTS")
    summary_lines.append("=" * 80)
    summary_lines.append("")
    
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'failed' else "⏭️"
        summary_lines.append(f"{i}. {status_icon} {result['company_name']}")
        summary_lines.append(f"   Status: {result['status'].upper()}")
        summary_lines.append(f"   URL: {result['job_url']}")
        summary_lines.append(f"   Log: {result.get('log_file', 'N/A')}")
        if result['status'] == 'failed':
            summary_lines.append(f"   Error: {result.get('error', 'Unknown error')}")
        summary_lines.append("")
    
    summary_lines.append("=" * 80)
    summary_lines.append("LOG FILES")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Batch log: {batch_log_file}")
    summary_lines.append(f"Company logs: {COMPANY_LOGS_DIR}")
    summary_lines.append(f"JSON report: {BATCH_REPORT_FILE}")
    summary_lines.append(f"Summary: {BATCH_SUMMARY_FILE}")
    summary_lines.append("")
    summary_lines.append("=" * 80)
    
    # Save summary
    summary_text = "\n".join(summary_lines)
    with open(BATCH_SUMMARY_FILE, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    
    # Also print to console
    print("\n" + summary_text)
    
    logger.info(f"📊 Batch report saved:")
    logger.info(f"   JSON: {BATCH_REPORT_FILE}")
    logger.info(f"   Summary: {BATCH_SUMMARY_FILE}")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN BATCH PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

async def process_single_job(company: Dict, index: int, total: int, skip_generation: bool = False) -> Dict:
    """
    Process a single job application.
    
    Args:
        company: Company info dict with name, apply_link, date_posted
        index: Current job index (0-based)
        total: Total number of jobs
        skip_generation: Whether to skip document generation
        
    Returns:
        Result dictionary with status and details
    """
    
    company_name = company.get('name', f'Company_{index+1}')
    job_url = company.get('apply_link', '')
    date_posted = company.get('date_posted', 'Unknown')
    
    # Setup company-specific logger
    company_logger, log_filepath = setup_company_logger(company_name, index)
    
    result = {
        "company_name": company_name,
        "job_url": job_url,
        "date_posted": date_posted,
        "index": index + 1,
        "log_file": str(log_filepath),
        "start_time": datetime.now().isoformat(),
        "status": "pending"
    }
    
    try:
        logger.info("")
        logger.info("█" * 80)
        logger.info(f"█  PROCESSING JOB {index+1}/{total}")
        logger.info("█" * 80)
        logger.info(f"█  Company: {company_name}")
        logger.info(f"█  Posted: {date_posted}")
        logger.info(f"█  URL: {job_url}")
        logger.info(f"█  Log: {log_filepath.name}")
        logger.info("█" * 80)
        logger.info("")
        
        company_logger.info("=" * 80)
        company_logger.info(f"JOB APPLICATION: {company_name}")
        company_logger.info("=" * 80)
        company_logger.info(f"Job URL: {job_url}")
        company_logger.info(f"Date Posted: {date_posted}")
        company_logger.info(f"Index: {index+1}/{total}")
        company_logger.info(f"Skip Generation: {skip_generation}")
        company_logger.info("")
        
        # Validate URL
        if not job_url or job_url.strip() == '':
            raise ValueError("Empty job URL")
        
        # Run automation for this job
        company_logger.info("Starting automation...")
        application_result = await automate_job_application(job_url, skip_generation=skip_generation, job_index=index)
        
        # Mark as success
        result["status"] = "success"
        result["end_time"] = datetime.now().isoformat()
        result["details"] = application_result
        
        company_logger.info("")
        company_logger.info("=" * 80)
        company_logger.info("✅ APPLICATION COMPLETED SUCCESSFULLY")
        company_logger.info("=" * 80)
        company_logger.info("")
        
        logger.info(f"✅ Job {index+1}/{total} completed: {company_name}")
        logger.info("")
        
    except Exception as e:
        # Log error but continue to next job
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        result["status"] = "failed"
        result["end_time"] = datetime.now().isoformat()
        result["error"] = error_msg
        result["traceback"] = error_trace
        
        company_logger.error("")
        company_logger.error("=" * 80)
        company_logger.error(f"❌ APPLICATION FAILED: {error_msg}")
        company_logger.error("=" * 80)
        company_logger.error(error_trace)
        company_logger.error("")
        
        logger.error(f"❌ Job {index+1}/{total} failed: {company_name}")
        logger.error(f"   Error: {error_msg}")
        logger.error(f"   Continuing to next job...")
        logger.error("")
    
    finally:
        # Close company logger handlers
        for handler in company_logger.handlers[:]:
            handler.close()
            company_logger.removeHandler(handler)
    
    return result

async def batch_process_jobs_parallel(skip_generation: bool = False, company_list_path: Path = None, limit: int = None):
    """
    Process ALL jobs in parallel (simultaneously).
    
    WARNING: This will open multiple browser windows at once!
    Only recommended for small batches (5-10 jobs).
    
    Args:
        skip_generation: If True, skip resume/cover letter generation for all jobs
        company_list_path: Optional custom path to company list JSON file
        limit: Optional limit on number of jobs to process (for testing)
    """
    
    start_time = datetime.now()
    
    logger.info("")
    logger.info("█" * 80)
    logger.info("█" + " " * 78 + "█")
    logger.info("█" + " " * 20 + "🚀 PARALLEL BATCH PROCESSING STARTED 🚀" + " " * 18 + "█")
    logger.info("█" + " " * 78 + "█")
    logger.info("█" * 80)
    logger.info("")
    
    try:
        # Load company list
        companies = load_company_list(company_list_path)
        
        # Apply limit if specified
        if limit and limit > 0:
            logger.info(f"⚠️  LIMIT MODE: Processing only first {limit} jobs (out of {len(companies)})")
            companies = companies[:limit]
            logger.info("")
        total_jobs = len(companies)
        
        logger.info(f"📋 Total jobs to process IN PARALLEL: {total_jobs}")
        logger.info(f"   Mode: {'TEST (skip generation)' if skip_generation else 'NORMAL (generate docs)'}")
        logger.info(f"   ⚠️  WARNING: {total_jobs} browser windows will open simultaneously!")
        logger.info("")
        
        # Create tasks for all jobs with staggered start to avoid overwhelming API
        logger.info("🚀 Launching all jobs in parallel with staggered start...")
        logger.info("")
        
        async def delayed_job(company, index, total, skip_gen, delay_seconds):
            """Start job after delay to avoid overwhelming the resume API."""
            if delay_seconds > 0:
                logger.info(f"⏳ Job {index+1}/{total}: Waiting {delay_seconds}s before start...")
                await asyncio.sleep(delay_seconds)
            return await process_single_job(company, index, total, skip_gen)
        
        tasks = []
        stagger_delay = 0  # Start all jobs immediately for true parallel execution
        for i, company in enumerate(companies):
            delay = i * stagger_delay  # All will be 0s - simultaneous start
            task = delayed_job(company, i, total_jobs, skip_generation, delay)
            tasks.append(task)
        
        if total_jobs > 1:
            logger.info(f"   🚀 All {total_jobs} jobs will start SIMULTANEOUSLY (no stagger)")
            logger.info(f"   📊 Check individual job logs for progress tracking")
            logger.info("")
        
        # Run all tasks in parallel (with staggered starts)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "company_name": companies[i].get('name', 'Unknown'),
                    "job_url": companies[i].get('apply_link', ''),
                    "status": "failed",
                    "error": str(result),
                    "duration": "N/A"
                })
            else:
                final_results.append(result)
        
        # Generate final report
        end_time = datetime.now()
        save_batch_report(final_results, start_time, end_time)
        
        logger.info("")
        logger.info("█" * 80)
        logger.info("█" + " " * 78 + "█")
        logger.info("█" + " " * 18 + "🚀 PARALLEL BATCH PROCESSING COMPLETED 🚀" + " " * 17 + "█")
        logger.info("█" + " " * 78 + "█")
        logger.info("█" * 80)
        logger.info("")
        
        # Print summary
        success_count = sum(1 for r in final_results if r.get("status") == "success")
        failed_count = sum(1 for r in final_results if r.get("status") == "failed")
        
        logger.info("📊 FINAL SUMMARY:")
        logger.info(f"   ✅ Successful: {success_count}/{total_jobs}")
        logger.info(f"   ❌ Failed: {failed_count}/{total_jobs}")
        logger.info(f"   ⏱️  Total Time: {(end_time - start_time).total_seconds():.2f} seconds")
        logger.info(f"   📄 Summary: {BATCH_SUMMARY_FILE}")
        logger.info(f"   📋 Detailed Report: {BATCH_REPORT_FILE}")
        logger.info("")
        
        return final_results
        
    except Exception as e:
        logger.error(f"❌ Parallel batch processing failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def batch_process_jobs(skip_generation: bool = False, resume_from_progress: bool = False, 
                            company_list_path: Path = None, limit: int = None):
    """
    Process all jobs from company_list.json one by one.
    
    Args:
        skip_generation: If True, skip resume/cover letter generation for all jobs
        resume_from_progress: If True, resume from previous progress
        company_list_path: Optional custom path to company list JSON file
        limit: Optional limit on number of jobs to process (for testing)
    """
    
    start_time = datetime.now()
    
    logger.info("")
    logger.info("█" * 80)
    logger.info("█" + " " * 78 + "█")
    logger.info("█" + " " * 25 + "BATCH PROCESSING STARTED" + " " * 29 + "█")
    logger.info("█" + " " * 78 + "█")
    logger.info("█" * 80)
    logger.info("")
    
    try:
        # Load company list
        companies = load_company_list(company_list_path)
        
        # Apply limit if specified
        if limit and limit > 0:
            logger.info(f"⚠️  LIMIT MODE: Processing only first {limit} jobs (out of {len(companies)})")
            companies = companies[:limit]
            logger.info("")
        total_jobs = len(companies)
        
        # Load progress if resuming
        progress = load_progress() if resume_from_progress else {
            "completed": [],
            "failed": [],
            "skipped": [],
            "in_progress": None
        }
        
        completed_urls = set(progress.get("completed", []))
        failed_urls = set(progress.get("failed", []))
        
        logger.info(f"📋 Total jobs to process: {total_jobs}")
        if resume_from_progress:
            logger.info(f"   Already completed: {len(completed_urls)}")
            logger.info(f"   Already failed: {len(failed_urls)}")
            logger.info(f"   Remaining: {total_jobs - len(completed_urls) - len(failed_urls)}")
        logger.info(f"   Mode: {'TEST (skip generation)' if skip_generation else 'NORMAL (generate docs)'}")
        logger.info("")
        
        # Process each job
        results = []
        
        for i, company in enumerate(companies):
            job_url = company.get('apply_link', '')
            
            # Skip if already processed (if resuming)
            if resume_from_progress and (job_url in completed_urls or job_url in failed_urls):
                logger.info(f"⏭️  Skipping job {i+1}/{total_jobs} (already processed): {company.get('name', 'Unknown')}")
                results.append({
                    "company_name": company.get('name', 'Unknown'),
                    "job_url": job_url,
                    "status": "skipped",
                    "reason": "Already processed in previous run"
                })
                continue
            
            # Update progress
            progress["in_progress"] = job_url
            save_progress(progress)
            
            # Process this job
            result = await process_single_job(company, i, total_jobs, skip_generation)
            results.append(result)
            
            # Update progress
            if result["status"] == "success":
                progress["completed"].append(job_url)
            elif result["status"] == "failed":
                progress["failed"].append(job_url)
            progress["in_progress"] = None
            save_progress(progress)
            
            # Add delay between jobs to avoid overwhelming systems
            if i < total_jobs - 1:  # Don't delay after last job
                delay_seconds = 5
                logger.info(f"⏸️  Waiting {delay_seconds} seconds before next job...")
                logger.info("")
                await asyncio.sleep(delay_seconds)
        
        # Generate final report
        end_time = datetime.now()
        save_batch_report(results, start_time, end_time)
        
        logger.info("")
        logger.info("█" * 80)
        logger.info("█" + " " * 78 + "█")
        logger.info("█" + " " * 22 + "✅ BATCH PROCESSING COMPLETED" + " " * 26 + "█")
        logger.info("█" + " " * 78 + "█")
        logger.info("█" * 80)
        logger.info("")
        
        return results
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Batch processing interrupted by user")
        logger.info("   Progress has been saved. You can resume later with --resume flag")
        raise
        
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """Main entry point for batch processing."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch Job Application Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all jobs (generate new docs for each):
  python batch_apply.py
  
  # Process all jobs in test mode (use existing docs):
  python batch_apply.py --skip-generation
  
  # Resume from previous run:
  python batch_apply.py --resume
  
  # Resume in test mode:
  python batch_apply.py --resume --skip-generation
        """
    )
    
    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='Skip resume/cover letter generation and use latest existing files (for testing)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous run (skip already processed jobs)'
    )
    
    parser.add_argument(
        '--company-list',
        type=str,
        default=None,
        help='Path to company list JSON file (default: company_list.json)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of jobs to process (useful for testing batches of 5)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run all jobs in parallel (WARNING: Opens multiple browsers simultaneously)'
    )
    
    args = parser.parse_args()
    
    # Determine company list path
    company_list_path = Path(args.company_list) if args.company_list else COMPANY_LIST_FILE
    
    logger.info("Configuration:")
    logger.info(f"   Company List: {company_list_path}")
    if args.limit:
        logger.info(f"   Limit: First {args.limit} jobs only")
    logger.info(f"   Mode: {'TEST (skip generation)' if args.skip_generation else 'NORMAL (generate docs)'}")
    logger.info(f"   Resume: {'YES (skip already processed)' if args.resume else 'NO (process all)'}")
    logger.info(f"   Parallel: {'YES (all jobs at once)' if args.parallel else 'NO (sequential)'}")
    logger.info(f"   Logs Directory: {LOGS_DIR}")
    logger.info(f"   Company Logs: {COMPANY_LOGS_DIR}")
    logger.info(f"   Screenshots: {SCREENSHOTS_DIR}")
    logger.info("")
    
    # Check if company list exists
    if not company_list_path.exists():
        logger.error(f"❌ Company list file not found: {company_list_path}")
        logger.error("   Please create the company list JSON file")
        return
    
    try:
        if args.parallel:
            await batch_process_jobs_parallel(
                skip_generation=args.skip_generation,
                company_list_path=company_list_path,
                limit=args.limit
            )
        else:
            await batch_process_jobs(
                skip_generation=args.skip_generation,
                resume_from_progress=args.resume,
                company_list_path=company_list_path,
                limit=args.limit
            )
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
