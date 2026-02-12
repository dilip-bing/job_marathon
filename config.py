"""
═══════════════════════════════════════════════════════════════════════════════
CONFIGURATION FILE
═══════════════════════════════════════════════════════════════════════════════

Central configuration for the Job Application Automation System.
Store all your API keys and settings here.

Author: Dilip Kumar
Date: February 11, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# API CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Resume & Cover Letter API
RESUME_API_URL = "https://resume-optimizer-api-fvpd.onrender.com"
RESUME_API_KEY = os.getenv("RESUME_API_KEY")

# Google Gemini API (for browser-use agent)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ═══════════════════════════════════════════════════════════════════════════
# MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Model for job scraping (faster, cheaper)
SCRAPING_MODEL = "gemini-2.5-pro"  # Pro model
SCRAPING_TEMPERATURE = 0.3

# Model for form filling (more accurate, better reasoning)
FORM_FILLING_MODEL = "gemini-2.5-pro"  # Stable Pro model, handles long contexts better
FORM_FILLING_TEMPERATURE = 0.3

# ═══════════════════════════════════════════════════════════════════════════
# FILE PATHS
# ═══════════════════════════════════════════════════════════════════════════

# Base directory
BASE_DIR = Path(__file__).parent

# User profile
USER_PROFILE_PATH = BASE_DIR / "user_profile.json"

# Generated documents directory
GENERATED_DOCS_DIR = BASE_DIR / "generated_documents"

# Logs directory
LOGS_DIR = BASE_DIR / "logs"

# Application log file
APPLICATION_LOG_FILE = LOGS_DIR / "application_log.json"

# ═══════════════════════════════════════════════════════════════════════════
# API TIMEOUTS & RETRY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# API request timeout (seconds) - 10 minutes for AI processing
API_TIMEOUT = 600

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 10  # seconds

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ═══════════════════════════════════════════════════════════════════════════
# BROWSER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Browser settings (for browser-use)
BROWSER_HEADLESS = False  # Set to True to run browser in background
BROWSER_SLOW_MO = 100      # Milliseconds delay between actions (for debugging)

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_configuration():
    """Validate that all required configuration is set."""
    errors = []
    
    # Check API keys
    if not RESUME_API_KEY or RESUME_API_KEY == "YOUR_API_KEY_HERE":
        errors.append("RESUME_API_KEY is not set")
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_KEY_HERE":
        errors.append("GEMINI_API_KEY is not set")
    
    # Check user profile exists
    if not USER_PROFILE_PATH.exists():
        errors.append(f"User profile not found at {USER_PROFILE_PATH}")
    
    # Create directories if they don't exist
    GENERATED_DOCS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    if errors:
        error_msg = "\n".join([f"  - {err}" for err in errors])
        raise ValueError(f"Configuration errors:\n{error_msg}")
    
    return True

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_resume_api_headers():
    """Get headers for Resume API requests."""
    return {
        "X-API-Key": RESUME_API_KEY,
        "Content-Type": "application/json"
    }

def get_llm_config_for_scraping():
    """Get LLM configuration for job scraping."""
    return {
        "model": SCRAPING_MODEL,
        "api_key": GEMINI_API_KEY,
        "temperature": SCRAPING_TEMPERATURE
    }

def get_llm_config_for_form_filling():
    """Get LLM configuration for form filling."""
    return {
        "model": FORM_FILLING_MODEL,
        "api_key": GEMINI_API_KEY,
        "temperature": FORM_FILLING_TEMPERATURE
    }

# ═══════════════════════════════════════════════════════════════════════════
# AUTO-VALIDATE ON IMPORT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ != "__main__":
    # Automatically validate when imported (but not when run directly)
    try:
        validate_configuration()
    except ValueError as e:
        print(f"⚠️  Configuration Warning: {e}")
