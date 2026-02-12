"""
═══════════════════════════════════════════════════════════════════════════════
UTILITY FUNCTIONS
═══════════════════════════════════════════════════════════════════════════════

Helper functions for the Job Application Automation System.

Author: Dilip Kumar
Date: February 11, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re

logger = logging.getLogger("JobAutomation.Utils")

# ═══════════════════════════════════════════════════════════════════════════
# FILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

def load_json_file(file_path: Path) -> Dict:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data as dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise

def save_json_file(data: Dict, file_path: Path):
    """
    Save dictionary to JSON file.
    
    Args:
        data: Dictionary to save
        file_path: Path to save to
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        raise

# ═══════════════════════════════════════════════════════════════════════════
# USER PROFILE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_user_info_summary(user_profile: Dict) -> str:
    """
    Get a formatted summary of user information.
    
    Args:
        user_profile: User profile dictionary
        
    Returns:
        Formatted summary string
    """
    personal = user_profile.get("personal_info", {})
    professional = user_profile.get("professional_summary", {})
    
    summary = f"""
    Name: {personal.get('full_name', 'N/A')}
    Email: {personal.get('email', 'N/A')}
    Phone: {personal.get('phone', 'N/A')}
    Role: {professional.get('title', 'N/A')}
    Experience: {professional.get('years_of_experience', 'N/A')} years
    """
    
    return summary.strip()

def extract_contact_info(user_profile: Dict) -> Dict:
    """
    Extract contact information from user profile.
    
    Args:
        user_profile: User profile dictionary
        
    Returns:
        Dictionary with contact info
    """
    personal = user_profile.get("personal_info", {})
    
    return {
        "name": personal.get("full_name", ""),
        "email": personal.get("email", ""),
        "phone": personal.get("phone", ""),
        "linkedin": personal.get("linkedin", ""),
        "github": personal.get("github", ""),
    }

# ═══════════════════════════════════════════════════════════════════════════
# TEXT PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_company_name(job_description: str) -> Optional[str]:
    """
    Try to extract company name from job description.
    
    Args:
        job_description: Job description text
        
    Returns:
        Company name if found, None otherwise
    """
    # Common patterns for company names in job postings
    patterns = [
        r'Company:\s*([A-Z][A-Za-z\s&.]+)',
        r'at\s+([A-Z][A-Za-z\s&.]+)\s+is',
        r'([A-Z][A-Za-z\s&.]+)\s+is\s+hiring',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, job_description)
        if match:
            return match.group(1).strip()
    
    return None

def extract_job_title(job_description: str) -> Optional[str]:
    """
    Try to extract job title from job description.
    
    Args:
        job_description: Job description text
        
    Returns:
        Job title if found, None otherwise
    """
    # Common patterns for job titles
    patterns = [
        r'Job Title:\s*([A-Za-z\s-]+)',
        r'Position:\s*([A-Za-z\s-]+)',
        r'^([A-Za-z\s-]+)\s*-\s*Job',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, job_description, re.MULTILINE)
        if match:
            return match.group(1).strip()
    
    return None

# ═══════════════════════════════════════════════════════════════════════════
# DATE/TIME HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_timestamp_string() -> str:
    """Get current timestamp as formatted string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_readable_timestamp() -> str:
    """Get current timestamp in human-readable format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def is_valid_url(url: str) -> bool:
    """
    Check if string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def is_valid_email(email: str) -> bool:
    """
    Check if string is a valid email.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email, False otherwise
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def log_section_header(title: str, logger_instance: logging.Logger = None):
    """
    Log a formatted section header.
    
    Args:
        title: Section title
        logger_instance: Logger to use (defaults to module logger)
    """
    if logger_instance is None:
        logger_instance = logger
    
    logger_instance.info("=" * 80)
    logger_instance.info(title)
    logger_instance.info("=" * 80)

def log_step(step_number: int, description: str, logger_instance: logging.Logger = None):
    """
    Log a step in the process.
    
    Args:
        step_number: Step number
        description: Step description
        logger_instance: Logger to use
    """
    if logger_instance is None:
        logger_instance = logger
    
    logger_instance.info(f"STEP {step_number}: {description}")

def log_success(message: str, logger_instance: logging.Logger = None):
    """
    Log a success message.
    
    Args:
        message: Success message
        logger_instance: Logger to use
    """
    if logger_instance is None:
        logger_instance = logger
    
    logger_instance.info(f"✅ {message}")

def log_error(message: str, logger_instance: logging.Logger = None):
    """
    Log an error message.
    
    Args:
        message: Error message
        logger_instance: Logger to use
    """
    if logger_instance is None:
        logger_instance = logger
    
    logger_instance.error(f"❌ {message}")

def log_warning(message: str, logger_instance: logging.Logger = None):
    """
    Log a warning message.
    
    Args:
        message: Warning message
        logger_instance: Logger to use
    """
    if logger_instance is None:
        logger_instance = logger
    
    logger_instance.warning(f"⚠️  {message}")

# ═══════════════════════════════════════════════════════════════════════════
# FILE SIZE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def human_readable_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable size.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_file_size(file_path: Path) -> str:
    """
    Get file size in human-readable format.
    
    Args:
        file_path: Path to file
        
    Returns:
        Human-readable file size
    """
    if not file_path.exists():
        return "File not found"
    
    size_bytes = file_path.stat().st_size
    return human_readable_size(size_bytes)

# ═══════════════════════════════════════════════════════════════════════════
# PROGRESS TRACKING
# ═══════════════════════════════════════════════════════════════════════════

class ProgressTracker:
    """Simple progress tracker for multi-step operations."""
    
    def __init__(self, total_steps: int, logger_instance: logging.Logger = None):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            logger_instance: Logger to use
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = logger_instance or logger
        self.start_time = datetime.now()
    
    def next_step(self, step_name: str):
        """
        Move to next step.
        
        Args:
            step_name: Name of the step
        """
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        
        self.logger.info(f"[{self.current_step}/{self.total_steps}] ({progress:.0f}%) {step_name}")
    
    def complete(self):
        """Mark all steps as complete."""
        elapsed = datetime.now() - self.start_time
        self.logger.info(f"✅ All {self.total_steps} steps completed in {elapsed}")
