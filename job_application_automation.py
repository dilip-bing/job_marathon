"""
═══════════════════════════════════════════════════════════════════════════════
JOB APPLICATION AUTOMATION SYSTEM
═══════════════════════════════════════════════════════════════════════════════

Description:
    Automated job application system using AI agents (browser-use + LangChain)
    to scrape job descriptions, generate tailored resumes/cover letters,
    and fill out application forms.

Author: Dilip Kumar
Date: February 11, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
import traceback
import glob
import yaml

# Third-party imports
import requests
import base64
from browser_use import Agent, ChatGoogle, Browser

# Import handlers for login and blocker detection
from login_handler import detect_and_bypass_login
from blocker_handler import check_for_blockers, get_blocker_detection_prompt

# Import configuration
from config import (
    RESUME_API_URL,
    RESUME_API_KEY,
    GEMINI_API_KEY,
    SCRAPING_MODEL,
    FORM_FILLING_MODEL,
    SCREENSHOTS_DIR,
    SCRAPING_TEMPERATURE,
    FORM_FILLING_TEMPERATURE
)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# File Paths
BASE_DIR = Path(__file__).parent
USER_PROFILE_PATH = BASE_DIR / "user_profile.json"
FORM_RESPONSES_PATH = BASE_DIR / "form_responses.yaml"
GENERATED_DOCS_DIR = BASE_DIR / "generated_documents"
LOGS_DIR = BASE_DIR / "logs"
APPLICATION_LOG_FILE = LOGS_DIR / "application_log.json"

# Create directories if they don't exist
GENERATED_DOCS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def setup_logging():
    """Configure detailed logging for the application."""
    
    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"automation_{timestamp}.log"
    
    # Configure logging format
    log_format = "%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Setup root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger instance
    logger = logging.getLogger("JobAutomation")
    logger.setLevel(logging.INFO)
    
    # Log startup
    logger.info("=" * 80)
    logger.info("JOB APPLICATION AUTOMATION SYSTEM - STARTED")
    logger.info("=" * 80)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    return logger

# Initialize logger
logger = setup_logging()

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def load_user_profile() -> Dict:
    """Load user profile from JSON file."""
    logger.info("=" * 80)
    logger.info("STEP: LOADING USER PROFILE")
    logger.info("=" * 80)
    
    try:
        logger.info(f"Reading user profile from: {USER_PROFILE_PATH}")
        
        if not USER_PROFILE_PATH.exists():
            logger.error(f"User profile file not found: {USER_PROFILE_PATH}")
            raise FileNotFoundError(f"User profile not found at {USER_PROFILE_PATH}")
        
        with open(USER_PROFILE_PATH, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        logger.info(f"✅ User profile loaded successfully")
        logger.info(f"   Name: {profile.get('personal_info', {}).get('full_name', 'N/A')}")
        logger.info(f"   Email: {profile.get('personal_info', {}).get('email', 'N/A')}")
        logger.info(f"   Phone: {profile.get('personal_info', {}).get('phone', 'N/A')}")
        logger.info(f"   Total skills: {len(profile.get('skills', {}).get('programming_languages', []))}")
        
        return profile
        
    except Exception as e:
        logger.error(f"❌ Failed to load user profile: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def load_form_responses() -> Dict:
    """Load form responses configuration from YAML file."""
    try:
        logger.info(f"Reading form responses from: {FORM_RESPONSES_PATH}")
        
        if not FORM_RESPONSES_PATH.exists():
            logger.warning(f"⚠️  Form responses file not found: {FORM_RESPONSES_PATH}")
            logger.warning("   Using default form responses")
            return {}
        
        with open(FORM_RESPONSES_PATH, 'r', encoding='utf-8') as f:
            responses = yaml.safe_load(f)
        
        logger.info(f"✅ Form responses loaded successfully")
        logger.info(f"   Categories: {', '.join(responses.keys())}")
        
        return responses
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to load form responses: {str(e)}")
        logger.warning("   Using default form responses")
        return {}

def save_application_log(job_url: str, status: str, details: Dict):
    """Save application status to log file."""
    logger.info("=" * 80)
    logger.info("STEP: SAVING APPLICATION LOG")
    logger.info("=" * 80)
    
    try:
        # Load existing logs
        if APPLICATION_LOG_FILE.exists():
            with open(APPLICATION_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Create new log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "job_url": job_url,
            "status": status,
            "details": details
        }
        
        # Append and save
        logs.append(log_entry)
        
        with open(APPLICATION_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Application log saved: {status}")
        logger.info(f"   Total applications logged: {len(logs)}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save application log: {str(e)}")
        logger.error(traceback.format_exc())

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: SCRAPE JOB DESCRIPTION
# ═══════════════════════════════════════════════════════════════════════════

async def scrape_job_description(job_url: str) -> str:
    """
    Use browser-use agent to visit job URL and extract job description.
    
    Args:
        job_url: URL of the job posting
        
    Returns:
        Extracted job description text
    """
    logger.info("=" * 80)
    logger.info("STEP 1: SCRAPE JOB DESCRIPTION")
    logger.info("=" * 80)
    
    try:
        logger.info(f"Target URL: {job_url}")
        logger.info("Initializing browser-use agent...")
        
        # Initialize Google Gemini LLM
        llm = ChatGoogle(
            model=SCRAPING_MODEL,
            api_key=GEMINI_API_KEY,
            temperature=SCRAPING_TEMPERATURE
        )
        logger.info(f"✅ Gemini LLM initialized (model: {SCRAPING_MODEL})")
        
        # Create task for the agent
        scrape_task = f"""
        Go to this URL: {job_url}
        
        Extract the complete job description including:
        1. Job title
        2. Company name
        3. Job requirements
        4. Responsibilities
        5. Qualifications
        6. Skills required
        7. Any other relevant details
        
        Return ONLY the extracted job description text, nothing else.
        """
        
        logger.info("Creating browser-use agent...")
        logger.info(f"Task: Extract job description from {job_url}")
        
        # Create and run agent
        agent = Agent(
            task=scrape_task,
            llm=llm,
        )
        
        logger.info("🤖 Agent created, starting browser automation...")
        logger.info("📋 Browser-use logs:")
        logger.info("-" * 80)
        
        # Run the task
        result = await agent.run()
        
        logger.info("-" * 80)
        logger.info("✅ Job description extracted successfully")
        logger.info(f"   Length: {len(str(result))} characters")
        logger.info(f"   Preview: {str(result)[:200]}...")
        
        return str(result)
        
    except Exception as e:
        logger.error(f"❌ Failed to scrape job description: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: GENERATE RESUME
# ═══════════════════════════════════════════════════════════════════════════

def generate_resume(job_description: str, retry_count: int = 0, max_retries: int = 1) -> str:
    """
    Generate tailored resume using the Resume Optimizer API.
    
    Args:
        job_description: Extracted job description
        retry_count: Current retry attempt
        max_retries: Maximum number of retries (default 1 = 2 total attempts)
        
    Returns:
        Path to generated resume file
    """
    logger.info("=" * 80)
    logger.info("STEP 2: GENERATE TAILORED RESUME")
    logger.info("=" * 80)
    
    try:
        if retry_count > 0:
            logger.info(f"🔄 Retry attempt {retry_count}/{max_retries}...")
        
        logger.info("Calling Resume Optimizer API...")
        logger.info(f"API URL: {RESUME_API_URL}/api/v1/optimize")
        logger.info(f"Job description length: {len(job_description)} characters")
        
        # Prepare request
        payload = {
            "job_description": job_description,
            "return_format": "base64"
        }
        
        headers = {
            "X-API-Key": RESUME_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Increase timeout for resume generation - 10 minutes for AI processing
        timeout = 600
        logger.info(f"⏳ Sending request to API (timeout: {timeout}s, may take up to 10 minutes)...")
        
        # Make API request
        response = requests.post(
            f"{RESUME_API_URL}/api/v1/optimize",
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        # Check response
        if response.status_code == 401:
            logger.error("❌ Authentication failed - Invalid API key")
            raise Exception("Invalid API key")
        elif response.status_code == 403:
            logger.error("❌ Access forbidden - Check API key")
            raise Exception("Access forbidden")
        elif response.status_code != 200:
            logger.error(f"❌ API error: {response.status_code} - {response.text}")
            raise Exception(f"API returned status {response.status_code}")
        
        # Parse response
        result = response.json()
        logger.info("✅ API response received")
        logger.info(f"   Match Score: {result.get('match_score', 'N/A')}")
        logger.info(f"   Keywords Added: {result.get('keywords_added', 'N/A')}")
        logger.info(f"   Filename: {result.get('filename', 'N/A')}")
        
        # Decode and save resume
        if "resume_base64" not in result:
            logger.error("❌ No resume data in response")
            raise Exception("No resume_base64 in API response")
        
        resume_bytes = base64.b64decode(result["resume_base64"])
        
        # Generate filename with user name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resume_filename = f"dilip_kumar_tc_resume_{timestamp}.docx"
        resume_path = GENERATED_DOCS_DIR / resume_filename
        
        # Save file
        with open(resume_path, 'wb') as f:
            f.write(resume_bytes)
        
        # Get absolute path
        resume_absolute_path = str(resume_path.resolve())
        
        logger.info(f"✅ Resume saved: {resume_absolute_path}")
        logger.info(f"   File size: {len(resume_bytes)} bytes")
        logger.info(f"   Filename: {resume_filename}")
        
        return resume_absolute_path
        
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ API request timed out (>{timeout} seconds / 10 minutes)")
        if retry_count < max_retries:
            logger.warning(f"⚠️  Retrying in 10 seconds... ({retry_count + 1}/{max_retries})")
            import time
            time.sleep(10)
            return generate_resume(job_description, retry_count + 1, max_retries)
        else:
            logger.error("❌ Max retries reached. Resume generation failed.")
            raise
    except Exception as e:
        logger.error(f"❌ Failed to generate resume: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: GENERATE COVER LETTER
# ═══════════════════════════════════════════════════════════════════════════

def generate_cover_letter(job_description: str, user_profile: Dict, retry_count: int = 0, max_retries: int = 0) -> Optional[str]:
    """
    Generate tailored cover letter using the Resume API.
    
    Args:
        job_description: Extracted job description
        user_profile: User profile data
        retry_count: Current retry attempt
        max_retries: Maximum number of retries (default 0 = no retries, ignored if failed)
        
    Returns:
        Path to generated cover letter file, or None if failed
    """
    logger.info("=" * 80)
    logger.info("STEP 3: GENERATE TAILORED COVER LETTER")
    logger.info("=" * 80)
    
    try:
        if retry_count > 0:
            logger.info(f"🔄 Retry attempt {retry_count}/{max_retries}...")
        
        logger.info("Calling Cover Letter API...")
        logger.info(f"API URL: {RESUME_API_URL}/api/v1/generate-cover-letter")
        
        # Extract user info
        personal_info = user_profile.get("personal_info", {})
        applicant_name = personal_info.get("full_name", "Dilip Kumar")
        applicant_email = personal_info.get("email", "")
        applicant_phone = personal_info.get("phone", "")
        
        logger.info(f"   Applicant: {applicant_name}")
        logger.info(f"   Email: {applicant_email}")
        
        # Prepare request
        payload = {
            "job_description": job_description,
            "applicant_name": applicant_name,
            "applicant_email": applicant_email,
            "applicant_phone": applicant_phone,
            "return_format": "base64"
        }
        
        headers = {
            "X-API-Key": RESUME_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Increase timeout for cover letter generation - 10 minutes for AI processing
        timeout = 600
        logger.info(f"⏳ Sending request to API (timeout: {timeout}s, may take up to 10 minutes)...")
        
        # Make API request
        response = requests.post(
            f"{RESUME_API_URL}/api/v1/generate-cover-letter",
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        # Check response
        if response.status_code != 200:
            logger.error(f"❌ API error: {response.status_code} - {response.text}")
            raise Exception(f"API returned status {response.status_code}")
        
        # Parse response
        result = response.json()
        logger.info("✅ API response received")
        logger.info(f"   Company: {result.get('company_name', 'N/A')}")
        logger.info(f"   Filename: {result.get('filename', 'N/A')}")
        
        # Decode and save cover letter
        if "cover_letter_base64" not in result:
            logger.error("❌ No cover letter data in response")
            raise Exception("No cover_letter_base64 in API response")
        
        cover_letter_bytes = base64.b64decode(result["cover_letter_base64"])
        
        # Generate filename with user name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cover_letter_filename = f"dilip_kumar_tc_cover_letter_{timestamp}.docx"
        cover_letter_path = GENERATED_DOCS_DIR / cover_letter_filename
        
        # Save file
        with open(cover_letter_path, 'wb') as f:
            f.write(cover_letter_bytes)
        
        # Get absolute path
        cover_letter_absolute_path = str(cover_letter_path.resolve())
        
        logger.info(f"✅ Cover letter saved: {cover_letter_absolute_path}")
        logger.info(f"   File size: {len(cover_letter_bytes)} bytes")
        logger.info(f"   Filename: {cover_letter_filename}")
        
        return cover_letter_absolute_path
        
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ API request timed out (>{timeout} seconds / 10 minutes)")
        if retry_count < max_retries:
            logger.warning(f"⚠️  Retrying in 10 seconds... ({retry_count + 1}/{max_retries})")
            import time
            time.sleep(10)
            return generate_cover_letter(job_description, user_profile, retry_count + 1, max_retries)
        else:
            logger.error("❌ Max retries reached. Cover letter generation failed.")
            logger.warning("⚠️  Continuing without cover letter...")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to generate cover letter: {str(e)}")
        logger.error(traceback.format_exc())
        logger.warning("⚠️  Continuing without cover letter...")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: GENERATE DOCUMENTS IN PARALLEL
# ═══════════════════════════════════════════════════════════════════════════

async def generate_documents_parallel(job_description: str, user_profile: Dict) -> Tuple[str, Optional[str]]:
    """
    Generate resume and cover letter in parallel for efficiency.
    
    Args:
        job_description: Extracted job description
        user_profile: User profile data
        
    Returns:
        Tuple of (resume_path, cover_letter_path) - cover_letter_path may be None if it fails
    """
    logger.info("=" * 80)
    logger.info("STEP 2 & 3: GENERATING DOCUMENTS IN PARALLEL")
    logger.info("=" * 80)
    
    try:
        logger.info("⚡ Starting parallel document generation...")
        logger.info("   - Resume generation (Thread 1)")
        logger.info("   - Cover letter generation (Thread 2)")
        
        # Run both API calls in parallel using asyncio
        loop = asyncio.get_event_loop()
        
        resume_task = loop.run_in_executor(None, generate_resume, job_description)
        cover_letter_task = loop.run_in_executor(None, generate_cover_letter, job_description, user_profile)
        
        # Wait for both to complete
        resume_path, cover_letter_path = await asyncio.gather(resume_task, cover_letter_task, return_exceptions=False)
        
        logger.info("=" * 80)
        if cover_letter_path:
            logger.info("✅ BOTH DOCUMENTS GENERATED SUCCESSFULLY")
        else:
            logger.warning("⚠️  RESUME GENERATED, COVER LETTER FAILED")
        logger.info("=" * 80)
        logger.info(f"   Resume: {resume_path}")
        if cover_letter_path:
            logger.info(f"   Cover Letter: {cover_letter_path}")
        else:
            logger.warning(f"   Cover Letter: SKIPPED (API timeout)")
        
        return resume_path, cover_letter_path
        
    except Exception as e:
        logger.error(f"❌ Failed to generate documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5-9: FILL APPLICATION FORM
# ═══════════════════════════════════════════════════════════════════════════

async def fill_application_form(job_url: str, user_profile: Dict, resume_path: str, cover_letter_path: Optional[str], headless: bool = False):
    """
    Use browser-use agent to fill out job application form.
    
    Args:
        job_url: URL of the job posting
        user_profile: User profile data
        resume_path: Path to generated resume
        cover_letter_path: Path to generated cover letter
    """
    logger.info("=" * 80)
    logger.info("STEP 5-9: FILLING APPLICATION FORM")
    logger.info("=" * 80)
    
    try:
        # Load form responses configuration
        form_responses = load_form_responses()
        
        # Ensure we have absolute paths
        resume_absolute = Path(resume_path).resolve()
        cover_letter_absolute = Path(cover_letter_path).resolve() if cover_letter_path else None
        
        logger.info(f"Target URL: {job_url}")
        logger.info(f"Resume Path: {resume_absolute}")
        logger.info(f"Resume Exists: {resume_absolute.exists()}")
        if cover_letter_absolute:
            logger.info(f"Cover Letter Path: {cover_letter_absolute}")
            logger.info(f"Cover Letter Exists: {cover_letter_absolute.exists()}")
        else:
            logger.warning(f"Cover Letter: NOT AVAILABLE (will skip upload)")
        logger.info("Initializing browser-use agent...")
        
        # Initialize Google Gemini LLM (using Pro for better form filling)
        llm = ChatGoogle(
            model=FORM_FILLING_MODEL,
            api_key=GEMINI_API_KEY,
            temperature=FORM_FILLING_TEMPERATURE
        )
        logger.info(f"✅ Gemini LLM initialized (model: {FORM_FILLING_MODEL})")
        
        # Extract key user information
        personal_info = user_profile.get("personal_info", {})
        address = user_profile.get("address", {})
        professional = user_profile.get("professional_summary", {})
        work_auth = user_profile.get("work_authorization", {})
        
        # Create detailed task for form filling with resilient instructions
        fill_form_task = f"""
        Go to this job application URL: {job_url}
        
        Your task is to fill out ONLY the MANDATORY fields in the job application form and SUBMIT it.
        If you cannot fill a field, SKIP IT and move to the next field.
        
        ⚠️⚠️⚠️ CRITICAL DATA SEPARATION RULES - READ FIRST ⚠️⚠️⚠️
        NEVER COMBINE SEPARATE PIECES OF DATA INTO ONE FIELD:
        
        ❌ WRONG Examples (DO NOT DO THIS):
        - "May 20273.67" (graduation month + year + GPA combined)
        - "Dilip Thirukonda Chandrasekaran(607) 624-9390" (name + phone combined)
        - "103 Chestnut Street Apt 1Binghamton" (address merged without spaces)
        - "Senior Automation Engineer5" (job title + years combined)
        - "Test-Lab2024-2025" (project name + dates combined)
        - "NYC, Austin, Boston" (multiple cities in single selection field)
        - "3.672027" (GPA + year combined)
        - "BinghamtonNY13905" (city + state + zip combined)
        
        ✅ CORRECT Approach:
        - If form has SEPARATE fields → Fill each field separately with its own value
        - Graduation: Month field = "May", Year field = "2027", GPA field = "3.67"
        - Name: First = "Dilip", Last = "Thirukonda Chandrasekaran"
        - Address: Street = "103 Chestnut Street", Apt = "Apt 1", City = "Binghamton"
        - Work: Title = "Senior Automation Engineer", Years = "5"
        - Projects: Name = "Test-Lab", Start = "2024", End = "2025"
        
        GOLDEN RULE: Each form field gets ONE piece of data. Do NOT merge adjacent data values!
        
        CRITICAL INSTRUCTIONS:
        - Focus ONLY on required/mandatory fields (marked with * or "required")
        - If a field cannot be filled, SKIP it and continue
        - If file upload fails, NOTE it and continue with other fields
        - DO NOT stop if one step fails - keep going
        - AT THE END: Click the Submit/Send/Apply button to SUBMIT the application
        
        PERSONAL INFORMATION (use these for mandatory fields only):
        - Full Name: {personal_info.get('full_name', '')}
        - First Name: {personal_info.get('first_name', '')}
        - Last Name: {personal_info.get('last_name', '')}
        - Email: {personal_info.get('email', '')}
        - Phone: {personal_info.get('phone', '')}
        - LinkedIn: {personal_info.get('linkedin', '')}
        - GitHub: {personal_info.get('github', '')}
        - Portfolio: {personal_info.get('portfolio', '')}
        
        ⚠️ PERSONAL INFO - FIELD SEPARATION RULES:
        - If form has "First Name" and "Last Name" fields: Fill separately (Dilip, Thirukonda Chandrasekaran)
        - If form has only "Full Name": Use complete name (Dilip Kumar Thirukonda Chandrasekaran)
        - Phone: Keep format (607) 624-9390 - do NOT remove parentheses or dashes
        - URLs: Enter complete URL including https:// - do NOT truncate protocol
        
        ADDRESS (if required):
        - Street: {address.get('street', '')}
        - Apartment: {address.get('apt_suite', '')}
        - City: {address.get('city', '')}
        - State: {address.get('state', '')}
        - ZIP/Postal Code: {address.get('zip_code', '')}
        - Country: {address.get('country', '')}
        
        ⚠️ ADDRESS - FIELD SEPARATION RULES:
        - If form has "Street Address" and "Apt/Suite": Fill separately (103 Chestnut Street, Apt 1)
        - If form has only "Address Line 1" and "Address Line 2": Put street in Line 1, apartment in Line 2
        - Do NOT combine: "103 Chestnut Street Apt 1" unless only one address field exists
        - City, State, ZIP: Always separate fields - do NOT combine into "Binghamton, NY 13905"
        - If single line: Format as "103 Chestnut Street Apt 1, Binghamton, NY 13905"
        
        WORK AUTHORIZATION (IMPORTANT - F-1 Visa Student):
        - Are you legally authorized to work in the US? YES
        - Visa Status: F-1 Student Visa
        - Will you require sponsorship? YES (general sponsorship question)
        - Do you need H-1B sponsorship? NO (if question ONLY asks about H-1B and does NOT mention OPT/CPT - you'll use OPT/CPT first)
        - Do you need OPT/CPT? YES (if question asks about needing it)
        - Are you currently on OPT/CPT? NO (if question contains "currently" or "already have")
        - Eligible for CPT/OPT? YES
        
        ACADEMIC STATUS (Current Graduate Student):
        - Are you currently a student? YES
        - Current degree: Master of Science in Computer Science
        - Academic year in Fall 2026: Senior / Second Year (started Fall 2025, graduating May 2027)
        - Expected graduation: May 2027
        - Enrollment status: Full-time
        - GPA: 3.67
        
        EDUCATION DETAILS - CRITICAL FIELD SEPARATION:
        When filling education fields, SEPARATE these values:
        - University/School Name: Binghamton University (or State University of New York at Binghamton)
        - Degree: Master of Science (or MS)
        - Major/Field of Study: Computer Science
        - Graduation Month: May (select from dropdown if available)
        - Graduation Year: 2027 (ONLY the year, do NOT combine with month or GPA)
        - GPA: 3.67 (separate field, do NOT append to year)
        - Expected/Anticipated Graduation: May 2027 (only if single combined field)
        - Start Date: August 2025 (if required)
        - End Date: May 2027 (if required)
        
        ⚠️ COMMON MISTAKES TO AVOID:
        - DO NOT enter "May 20273.67" - keep month, year, and GPA separate!
        - DO NOT combine graduation date with GPA
        - If form has separate "Month" and "Year" fields, fill them separately
        - If form has single "Graduation Date" field, enter "May 2027" or "05/2027"
        
        DEMOGRAPHICS (if required):
        - Veteran Status: I am not a veteran / No
        - Disability Status: No disability / No
        - Pronouns: He/Him/His (or "Prefer not to say")
        - Sexual Orientation / LGBTQ+: Prefer not to say
        
        COURSEWORK / COURSES (IMPORTANT - BE GENEROUS):
        If asked to select relevant coursework, SELECT 8-12 COURSES that are relevant to the job:
        - Always include: Data Structures, Algorithms, OOP, Database Systems
        - If AI/ML job: Machine Learning, Data Mining, NLP, Deep Learning, Computer Vision
        - If Backend/Systems: Operating Systems, Computer Networks, Distributed Systems
        - If Software Engineering: Software Engineering, Testing, Agile, Design Patterns
        - Other relevant: Cloud Computing, Cybersecurity, Web Development, Mobile Development
        - BE GENEROUS - select all that apply to increase match score
        
        PROJECTS (Pull from profile if asked):
        1. Test-Lab: Cloud-based testing, Docker, CI/CD, REST APIs (2024-2025)
        2. Earthworm AI: Plant disease detection, TensorFlow, 95% accuracy (2018)
        3. 3D Printer/Scanner: C++, embedded systems, NIT competition winner (2019)
        4. Obstacle Robot: C++, autonomous navigation, PHYSICA'16 winner (2016)
        
        ⚠️ PROJECT DATES - FIELD SEPARATION RULES:
        - If form has "Start Date" and "End Date": Fill separately
          * Test-Lab: Start = 2024 (or January 2024), End = 2025 (or December 2025)
        - If form has "Start Year" and "End Year": Numeric only (2024, 2025)
        - If form has "Project Duration": Use "2024-2025" or "1 year"
        - Do NOT combine project name with dates: "Test-Lab2024" or "Test-Lab2024-2025" is WRONG
        - Do NOT combine dates with description: "2024Docker" or "DockerCI/CD2025" is WRONG
        - Do NOT combine accuracy with year: "95%2018" is WRONG - keep metrics separate from dates
        
        LOCATION PREFERENCES (If asked - BE GENEROUS):
        Preferred locations (select 5-10 to maximize opportunities):
        - First priority: NY (NYC, Albany, Buffalo, Rochester, Binghamton)
        - Second priority: Texas (Austin, Dallas, Houston)
        - Third priority: NC (Charlotte, Raleigh, Durham)
        - Fourth priority: Tech hubs (SF, Seattle, Boston, Chicago, Denver, Atlanta)
        - Final: "Open to any US location" or "Willing to relocate"
        - RULE: Select multiple locations (5-10) to increase chances
        
        ⚠️ LOCATION - SELECTION RULES:
        - Multi-select dropdown: Check 5-10 individual cities (NYC, Austin, Boston, etc.)
        - Do NOT select just one location unless form limits to single selection
        - Do NOT combine cities into one string: "NYC, Austin, Boston" in one field is WRONG
        - Each city should be separate checkbox/selection
        - Priority order: NY cities first, then TX, then NC, then tech hubs
        
        LANGUAGES (if asked):
        - English: Native or Bilingual / Fluent
        - Tamil: Native or Bilingual
        - Hindi: Fluent
        
        LEGAL/COMPLIANCE QUESTIONS:
        - Are you 18 or older? YES
        - Relatives employed here? NO
        - Non-compete agreement? NO
        - Government official? NO
        - Subject to NDA? NO
        
        JOB SOURCE / HOW DID YOU HEAR (IMPORTANT - avoid "Select" option):
        - Primary: Social Media (or Job Board, Company Website, Indeed, etc.)
        - Secondary: LinkedIn (if there's a dependent field)
        - RULE: Never leave "Select" or "Please Select" - always choose an actual value
        - RULE: If primary field has limited options, try changing it to unlock secondary field options
        - Example: If "Job Board" -> "Select" stuck, try "Social Media" -> "LinkedIn"
        
        WORK INFO (if required):
        - Current Title: {professional.get('title', '')}
        - Years of Experience: {professional.get('years_of_experience', '')}
        
        ⚠️ WORK EXPERIENCE - FIELD SEPARATION RULES:
        - If form has "Job Title" and "Years of Experience" as separate fields: Fill separately
        - Do NOT combine: "Senior Automation Engineer 5" or "Senior Automation Engineer5 years" is WRONG
        - Years of Experience field:
          * If numeric input: Enter "5"
          * If text input: Enter "5 years" or "5"
        - Current Company field (if exists): Enter company name only, not combined with title
        - Do NOT append experience to job title
        
        FILE UPLOAD - CRITICAL INSTRUCTIONS:
        You have access to files by INDEX (not by path):
        - Index 0 = Resume file
        - Index 1 = Cover Letter file
        
        To upload files, use the BUILT-IN upload_file_to_element action:
        
        For Resume Upload:
        1. Find the resume upload input element (look for input[type="file"], keywords: "resume", "CV")
        2. Use action: upload_file_to_element
        3. Parameters: element=<found_input_element>, index=0
        4. Example: upload_file_to_element(element=<input_element>, index=0)
        
        For Cover Letter Upload (if field exists):
        1. Find the cover letter upload input (keywords: "cover letter", "additional documents")
        2. Use action: upload_file_to_element
        3. Parameters: element=<found_input_element>, index=1
        4. Example: upload_file_to_element(element=<input_element>, index=1)
        
        UPLOAD ERROR HANDLING:
        - If upload shows an error dialog, click "OK" or "Accept" to dismiss it
        - Do NOT retry the upload multiple times - try once and move on
        - Do NOT stop the entire process if upload fails
        - Continue filling other fields even if uploads fail
        - Report in your final response: which files uploaded successfully, which failed
        
        STEP-BY-STEP PROCESS:
        1. Navigate to the application page
        2. Click "Apply" or "Apply Now" if present
        3. Identify MANDATORY fields only (marked with * or "required")
        4. Fill personal information fields (KEEP EACH FIELD SEPARATE):
           - First Name: Dilip (separate field)
           - Last Name: Thirukonda Chandrasekaran (separate field)
           - Full Name: Dilip Kumar Thirukonda Chandrasekaran (only if single name field)
           - Email: dthirukondac@binghamton.edu
           - Phone: (607) 624-9390 (keep formatting - do NOT remove parentheses)
           - LinkedIn: https://linkedin.com/in/dilipkumartc (full URL with https://)
        5. Fill address fields (KEEP EACH FIELD SEPARATE):
           - Address Line 1 / Street: 103 Chestnut Street
           - Address Line 2 / Apt/Suite: Apt 1
           - City: Binghamton
           - State: NY (or New York)
           - ZIP Code: 13905
           - Country: United States
           - ❌ WRONG: "103 Chestnut Street Apt 1" (unless form has only ONE address field)
        6. Fill education details (MOST CRITICAL - KEEP SEPARATE):
           - School: Binghamton University (State University of New York at Binghamton)
           - Degree: Master of Science (MS)
           - Major: Computer Science
           - **Graduation Month**: May (separate dropdown/field)
           - **Graduation Year**: 2027 (ONLY the number 2027, separate field)
           - **GPA**: 3.67 (separate field - do NOT combine: ❌ "20273.67" or "May 20273.67")
           - Start Date: August 2025 (separate field if asked)
           - End Date: May 2027 (separate field if asked)
           - Expected Graduation: May 2027 (only if SINGLE combined field exists)
        7. Select coursework (8-12 relevant courses - be generous, select all that match job)
        8. Handle "How did you hear" / Source fields (choose Social Media -> LinkedIn if available)
        9. Fill work authorization:
           - General sponsorship: YES
           - H-1B only questions (no OPT/CPT mentioned): NO
           - OPT/CPT questions: YES (eligible), NO (not currently on it)
        10. Fill academic status (if student-related questions):
           - Current student: YES
           - Academic year Fall 2026: Senior/Second Year
           - Graduation: May 2027
        11. Fill demographics (not a veteran, no disability, pronouns: He/Him or prefer not to say)
        12. Fill location preferences (select 5-10 locations: NY, TX, NC, tech hubs, any US)
        13. Fill legal/compliance (18+: YES, relatives/NDA/non-compete: NO)
        14. Fill projects if asked (Test-Lab, Earthworm AI, 3D Printer, Robot)
        15. Fill languages (English: Native, Tamil: Native, Hindi: Fluent)
        16. Upload resume: use upload_file_to_element(element=<resume_input>, index=0)
        17. Upload cover letter: use upload_file_to_element(element=<cover_letter_input>, index=1) if field exists
        18. If upload fails, dismiss error dialog and continue
        19. Fill any other mandatory fields with relevant information
        20. Leave all optional fields empty
        21. FINAL STEP: Click the Submit/Send/Apply button to SUBMIT the application
        22. Wait for confirmation page or success message
        23. Report the submission status and which files uploaded successfully
        
        ⚠️⚠️⚠️ POST-SUBMIT VALIDATION ERROR HANDLING - CRITICAL ⚠️⚠️⚠️
        
        After clicking Submit, the form may show validation errors for incomplete/incorrect fields.
        You MUST handle these errors systematically:
        
        📋 POST-SUBMIT ERROR RESOLUTION PROCESS:
        
        STEP 1: After clicking Submit, WAIT 2-3 seconds for page to respond
        
        STEP 2: Check if you're on a NEW page (confirmation/thank you) or SAME page (errors exist)
           - NEW page indicators: "Thank you", "Application submitted", "Confirmation", different URL
           - SAME page indicators: Still on form, URL unchanged, error messages visible
        
        STEP 3: If SAME page, scan for validation errors:
           
           🔍 ERROR INDICATORS TO LOOK FOR:
           1. Red or highlighted field borders (border-color: red, #ff0000, #dc2626, etc.)
           2. Error messages near fields (usually in red text, aria-invalid="true")
           3. Field labels marked with red asterisk or exclamation mark
           4. Error summary at top of page: "Please fix the following errors"
           5. Fields with aria-describedby pointing to error messages
           6. Validation messages like "This field is required", "Invalid format", "Please select an option"
           7. Dropdowns still showing "Select" or "Please Select" with red borders
           8. Unchecked required checkboxes with error indicators
           
           🎯 HOW TO FIND ERROR FIELDS:
           - Use find_elements with selector: '[aria-invalid="true"]', '.error', '.invalid', '[required]:invalid'
           - Look for elements with text content containing: "required", "error", "invalid", "must"
           - Scan for red-colored elements (color: red, rgb(220, 38, 38), #dc2626, etc.)
           - Check for fields with empty values that show error borders
        
        STEP 4: Fix each error field ONE BY ONE:
           
           ✅ FOR EACH ERROR FIELD FOUND:
           a) Identify what's wrong:
              - Field is empty but required
              - Dropdown still shows "Select" or placeholder
              - Invalid format (phone, email, date, GPA)
              - Checkbox not checked
              - Text field has wrong data type (text in number field)
           
           b) Fix the specific issue:
              - Empty required field → Fill with appropriate data from profile
              - Dropdown with "Select" → Choose first valid option
              - Invalid phone → Re-enter as (607) 624-9390
              - Invalid email → Re-enter as dthirukondac@binghamton.edu
              - Invalid GPA → Re-enter as just "3.67" (no text, no merging)
              - Invalid graduation year → Re-enter as just "2027" (numbers only)
              - Unchecked required checkbox → Check it
              - Wrong data type → Clear and re-enter with correct format
           
           c) IMPORTANT - ONLY fix fields that SHOW errors:
              - DO NOT modify fields that are working correctly
              - DO NOT touch fields with no error indicators
              - Only change fields with visible validation errors
        
        STEP 5: After fixing ALL error fields, scroll to top/bottom to find Submit button again
        
        STEP 6: Click Submit button AGAIN
        
        STEP 7: Wait 2-3 seconds and repeat STEP 2-6 until:
           - You reach confirmation/thank you page (SUCCESS), OR
           - Same errors persist after 2 attempts (report the specific persistent errors)
        
        📊 COMMON VALIDATION ERRORS & FIXES:
        
        | Error Type | Indicator | Fix |
        |------------|-----------|-----|
        | Empty required field | Red border, "required" message | Fill with profile data |
        | Dropdown = "Select" | Red border, still shows placeholder | Select first valid option |
        | Invalid phone format | "Invalid format" message | Re-enter as (607) 624-9390 |
        | Invalid GPA | "Must be number" or "Invalid" | Clear and enter just "3.67" |
        | Invalid year | "Invalid" or "Must be 4 digits" | Clear and enter just "2027" |
        | Merged data | "Invalid format" | Clear and separate into correct fields |
        | Unchecked agreement | "Must agree" or red checkbox | Check the checkbox |
        | Email format | "Invalid email" | Re-enter dthirukondac@binghamton.edu |
        | Date format | "Invalid date" | Re-format as MM/DD/YYYY or YYYY-MM-DD |
        
        🎯 EXAMPLE ERROR RESOLUTION FLOW:
        
        1. Click Submit → Page stays same (errors exist)
        2. Scan page → Find 3 fields with red borders:
           - GPA field shows "20273.67" → Clear, enter "3.67"
           - Country dropdown shows "Select" → Select "United States"
           - Privacy checkbox unchecked with red label → Check it
        3. All errors fixed → Scroll to Submit button
        4. Click Submit again → New page appears with "Thank you"
        5. SUCCESS - report completion
        
        ⚠️ CRITICAL RULES:
        - NEVER skip error checking after submit
        - ALWAYS wait for page response before assuming success
        - Fix errors systematically, not all at once
        - Re-submit after fixing errors
        - Report persistent errors if can't be resolved after 2 attempts
        - DO NOT modify correctly filled fields when fixing errors
        
        IMPORTANT ERROR HANDLING:
        - If a dropdown only shows "Select" or "Please Select", try changing a related field first
        - If file upload doesn't work, note it and continue
        - If a field is unclear, put reasonable information or skip it
        - Answer questions relevantly based on the profile information above
        
        FALLBACK STRATEGIES (when specific answer not clear):
        - Dropdowns: Select first reasonable option, NEVER leave "Select"
        - Text fields: Use "N/A" or "See resume" for unknown required fields
        - Radio buttons: Default to "NO" for yes/no questions (except work auth = YES)
        - Multi-select courses: Select 8-12 relevant courses generously
        - Multi-select locations: Select 5-10 locations to maximize opportunities
        
        ⚠️⚠️⚠️ CRITICAL: CHECKBOX HANDLING - READ CAREFULLY ⚠️⚠️⚠️
        Checkboxes are often REQUIRED to proceed. Handle them systematically:
        
        ✅ ALWAYS CHECK these checkboxes (these are MANDATORY):
        1. Agreement checkboxes (CRITICAL - forms won't submit without these):
           - "I agree to the terms and conditions"
           - "I have read and accept the privacy policy"
           - "I acknowledge the data processing agreement"
           - "I consent to receive communications"
           - "I certify that the information provided is true and accurate"
           - "I understand and agree to the terms of employment"
           - "I accept Workday's privacy policy" (Workday-specific)
           - "I agree to create an account" (Account creation)
        2. Authorization checkboxes:
           - "I authorize background check"
           - "I authorize verification of information"
           - "I give consent to contact references"
        3. Compliance checkboxes:
           - "I am 18 years or older"
           - "I am legally authorized to work in the US"
        
        🎯 CRITICAL FOR WORKDAY FORMS:
        - The "Create Account" checkbox is MANDATORY - won't proceed without it
        - Look for data-automation-id="createAccountCheckbox"
        - This checkbox is often BEFORE the email/password fields
        - Check it FIRST before filling account creation form
        - If you see "Create Account" button disabled, the checkbox is unchecked!
        
        ✅ CHECK WITH CARE (read the label first):
        1. Marketing/Newsletter: CHECK if it says "required" or has *, OTHERWISE skip
        2. Phone/SMS consent: CHECK if it says "required" or has *, OTHERWISE skip
        3. Additional services: CHECK only if marked mandatory
        
        ❌ NEVER CHECK these:
        1. Options that cost money or require payment
        2. Commitments you're not sure about ("I commit to relocate immediately")
        3. Disability disclosure (leave blank unless specifically preferred)
        
        🔍 HOW TO CLICK CHECKBOXES - MULTIPLE STRATEGIES:
        
        STRATEGY 1 - Direct Click (Try First):
        1. Locate checkbox: <input type="checkbox"> or data-automation-id="...Checkbox"
        2. Scroll element into view (critical - checkbox must be visible)
        3. Click directly on the checkbox element itself
        4. Wait 500ms for visual update
        5. Check if aria-checked changed from "false" to "true"
        
        STRATEGY 2 - Label Click (If Strategy 1 Fails):
        1. Find the <label> element associated with the checkbox
        2. Look for label with "for" attribute matching checkbox id
        3. OR look for label text containing agreement keywords
        4. Click the label element instead of checkbox
        5. Wait 500ms and verify checkbox is checked
        
        STRATEGY 3 - Parent Container Click (Workday-specific):
        1. Workday often wraps checkboxes in clickable <div> containers
        2. Look for parent <div> containing the checkbox
        3. Click the parent div element (usually has click handler)
        4. This often toggles the checkbox state
        5. Verify aria-checked or visual change
        
        STRATEGY 4 - JavaScript Force Click (Last Resort):
        1. If none of the above work, use JavaScript
        2. Get checkbox element reference
        3. Execute: element.click() via JavaScript
        4. OR execute: element.checked = true
        5. Trigger change event: element.dispatchEvent(new Event('change'))
        
        STRATEGY 5 - Keyboard Space (Alternative):
        1. Focus on the checkbox element
        2. Press Space key to toggle
        3. Verify state changed
        
        📍 WORKDAY CHECKBOX SPECIFICS:
        - Workday checkboxes have data-automation-id="createAccountCheckbox" etc.
        - They use aria-checked="false" / "true" to track state
        - Visual state may not match actual checkbox.checked property
        - The clickable area is often the PARENT div, not the input itself
        - Label text is usually in a span NEXT to the checkbox
        
        ⚡ QUICK FIX FOR STUBBORN CHECKBOXES:
        If checkbox won't check after 2 tries:
        1. Scroll page up/down to refresh viewport
        2. Click parent element instead of checkbox itself
        3. Try clicking 10-20 pixels to the RIGHT of checkbox (where label usually is)
        4. Use JavaScript: document.querySelector('[data-automation-id="createAccountCheckbox"]').click()
        
        ✅ VERIFICATION:
        After clicking, ALWAYS verify:
        - Visual: checkbox shows checkmark or filled state
        - Attribute: aria-checked="true" or checked="checked"
        - Don't assume click worked - verify before moving on!
        
        🚨 IF FORM WON'T SUBMIT - CHECK FOR UNCHECKED AGREEMENTS:
        - Look for red error messages mentioning "must agree" or "required checkbox"
        - Scroll through the form to find any highlighted/red checkbox fields
        - Check ALL agreement/terms checkboxes you may have missed
        - Try submitting again after checking missing agreements
        
        ⚠️⚠️⚠️ FINAL DATA VALIDATION CHECKLIST - BEFORE SUBMITTING ⚠️⚠️⚠️
        Before clicking Submit, mentally verify these COMMON MISTAKES are NOT present:
        
        ❌ Check you did NOT create these errors:
        1. Graduation Year field contains: "20273.67", "May 2027", "May20273.67" → Should be just "2027"
        2. GPA field contains: "2027", "May 2027", "20273.67" → Should be just "3.67"
        3. Phone field contains: "6076249390" (no formatting) → Should be "(607) 624-9390"
        4. Name merged: "DilipThirukonda Chandrasekaran" → Should have proper spacing
        5. Address merged: "103 Chestnut StreetApt 1" → Should be separate or with space
        6. City/State merged: "BinghamtonNY" → Should be separate fields
        7. Job title merged: "Senior Automation Engineer5" → Should be separate from years
        8. Project dates merged with name: "Test-Lab2024" → Should be separate
        9. Multiple locations in one field: "NYC, Austin" → Should be individual selections
        10. URL missing protocol: "linkedin.com/in/dilipkumartc" → Should have "https://"
        
        ✅ Verify each piece of data is in its CORRECT, SEPARATE field!
        
        WHAT TO REPORT BACK:
        - Which mandatory fields you filled successfully
        - Which fields you could NOT fill (and why)
        - How many courses you selected (target: 8-12)
        - How many locations you selected (target: 5-10)
        - Whether projects were asked for and filled
        - File upload status: Resume uploaded? Cover letter uploaded? Any errors?
        - Any "Select" dropdowns that couldn't be resolved
        - Any errors you encountered (but keep going despite errors)
        - Overall form completion percentage
        - Whether Submit button was clicked
        - POST-SUBMIT VALIDATION ERRORS (if any):
          * How many validation errors appeared after first submit
          * Which fields had errors (field name + error message)
          * Which errors you fixed and how
          * Whether you had to submit multiple times
          * Whether errors persisted after fixes
        - Whether confirmation/thank you page appeared after final submit
        - Final status: Success (on confirmation page) OR Failed (stuck on form with errors)
        """
        
        logger.info("Creating browser-use agent for form filling...")
        logger.info("Task: Fill MANDATORY fields only, skip failures, DO NOT SUBMIT")
        logger.info("Strategy: Resilient form filling with skip-on-error")
        
        # Prepare available file paths for the agent
        available_file_paths = [str(resume_absolute)]
        if cover_letter_absolute:
            available_file_paths.append(str(cover_letter_absolute))
        
        logger.info(f"Available files for upload (by index):")
        logger.info(f"   [0] Resume: {resume_absolute}")
        if cover_letter_absolute:
            logger.info(f"   [1] Cover Letter: {cover_letter_absolute}")
        
        # Create browser instance
        browser = Browser(cross_origin_iframes=True, headless=headless)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 🔍 PRE-CHECK: Detect blockers and login walls before agent execution
        # ═══════════════════════════════════════════════════════════════════════════
        logger.info("🔍 Pre-checking page for blockers and login requirements...")
        
        try:
            # Navigate to page to extract content for analysis
            page = await browser.new_page()
            await page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
            page_text = await page.text_content('body')
            logger.info(f"   Page loaded, extracted {len(page_text)} characters for analysis")
            
            # Check for impossible blockers (email verification, CAPTCHA, expired jobs)
            is_blocked, blocker_type, blocker_reason, is_impossible = check_for_blockers(
                page_text=page_text,
                url=job_url
            )
            
            if is_blocked and is_impossible:
                logger.warning(f"🚫 IMPOSSIBLE TASK DETECTED: {blocker_reason}")
                logger.warning(f"   Blocker Type: {blocker_type.value}")
                logger.warning(f"   This is NOT a failure - task cannot be automated")
                
                await page.close()
                await browser.close()
                
                return {
                    "status": f"Impossible Task - {blocker_type.value}",
                    "blocker_type": blocker_type.value,
                    "reason": blocker_reason,
                    "form_result": blocker_reason
                }
            elif is_blocked:
                logger.info(f"⚠️  Soft blocker detected: {blocker_reason}")
                logger.info(f"   Will attempt to proceed...")
            else:
                logger.info("✅ No hard blockers detected")
            
            # Check for login requirements
            needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
                page_text=page_text,
                url=job_url
            )
            
            if needs_bypass:
                logger.warning(f"🚫 Login wall detected on {platform} platform")
                logger.info(f"   Enhancing agent prompt with bypass instructions...")
                # Inject bypass instructions into agent's task
                fill_form_task = fill_form_task + "\n\n" + bypass_prompt
            else:
                logger.info("✅ No login wall detected")
            
            # Add blocker detection awareness to agent prompt
            fill_form_task = fill_form_task + "\n\n" + get_blocker_detection_prompt()
            
            # Add account creation and credential logging instructions
            account_creation_prompt = f"""

🔐 ACCOUNT CREATION (Workday, Greenhouse, etc.):

If the application requires creating an account:

STEP 1 - Check for CAPTCHA FIRST:
- If you see reCAPTCHA, hCaptcha, "I'm not a robot", or any CAPTCHA challenge
- STOP IMMEDIATELY with done(success=False, impossible_task=True, text="CAPTCHA required during account creation")
- Do NOT attempt to create the account

STEP 2 - Create Account (ONE ATTEMPT ONLY):
- Use email: {personal_info.get('email', 'dthirukondac@binghamton.edu')}
- Generate password: CompanyName2026! (e.g., Ciena2026!, Workday2026!)
  * Requirements: 8+ chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
- Fill both password fields identically
- Check ALL required checkboxes (privacy policy, terms, etc.)
- Click "Create Account" button ONCE
- Wait 2-3 seconds

STEP 3 - Check Account Creation Result:
- If redirected to sign-in page → Continue to STEP 4
- If error appears → TERMINATE with credentials logged
- Do NOT click "Create Account" again

STEP 4 - Sign In (ONE ATTEMPT ONLY):
- Fill email: {personal_info.get('email', 'dthirukondac@binghamton.edu')}
- Fill password: (the password you created, e.g., Ciena2026!)
- Click "Sign In" button ONCE
- Wait 5 seconds for page to navigate

STEP 5 - Check Sign-In Result:
- If page navigates to application form → SUCCESS, continue filling form
- If page STAYS on sign-in (URL unchanged, still shows Sign In) → TERMINATE with credentials
- If ANY error message appears → TERMINATE with credentials
- DO NOT click "Sign In" again (max 1 attempt)
- DO NOT click "Create Account" again
- DO NOT click "Forgot Password"
- DO NOT try alternative methods

🚨 CRITICAL STOP CONDITIONS 🚨
TERMINATE IMMEDIATELY if after clicking "Sign In":
- Page URL is still the sign-in URL (hasn't changed)
- Page still shows "Sign In" heading/button after 5 seconds
- Still see email/password input fields
- No navigation to application form
- Any error text appears (even without explicit error message)

⚠️ ALWAYS LOG CREDENTIALS BEFORE TERMINATING:
Format: "Created account: {personal_info.get('email', 'email')} / Password123!"

Example termination after sign-in failure:
"Unable to complete application: Sign-in page did not navigate after clicking Sign In button. 
Page remains on sign-in screen with no error messages displayed.
Created account: dthirukondac@binghamton.edu / Ciena2026!
Account may require email verification or has authentication restrictions."

✅ ONLY CONTINUE if:
- After clicking "Sign In", you are redirected to a NEW page
- The new page shows application form fields (not sign-in fields)
- URL has changed from sign-in URL to application URL
            """
            
            fill_form_task = fill_form_task + "\n\n" + account_creation_prompt
            
            # Close pre-check page (agent will create its own browser session)
            await page.close()
            
            logger.info("✅ Pre-check completed, creating agent...")
            
        except Exception as e:
            logger.warning(f"⚠️  Pre-check failed: {e}")
            logger.info(f"   Proceeding with agent anyway...")
            # If pre-check fails, still add blocker detection to prompt
            fill_form_task = fill_form_task + "\n\n" + get_blocker_detection_prompt()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # End of pre-check
        # ═══════════════════════════════════════════════════════════════════════════
        
        # Create and run agent with file upload support (prompt may be enhanced)
        agent = Agent(
            task=fill_form_task,
            llm=llm,
            browser=browser,
            available_file_paths=available_file_paths,
            use_vision=True,  # Enable vision mode for automatic screenshot capture
        )
        
        logger.info("🤖 Agent created, starting form filling automation...")
        logger.info("📋 Browser-use logs:")
        logger.info("-" * 80)
        
        # Run the task  
        result = await agent.run()
        
        logger.info("-" * 80)
        logger.info("✅ Form filling process completed")
        logger.info("")
        logger.info("📋 AGENT REPORT:")
        logger.info(f"{str(result)}")
        logger.info("")
        
        # Extract screenshot from agent history (captured during execution due to use_vision=True)
        screenshot_path = None
        try:
            from urllib.parse import urlparse
            import shutil
            
            domain = urlparse(job_url).netloc.replace('www.', '').split('.')[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_screenshot_path = SCREENSHOTS_DIR / f"{domain}_{timestamp}.png"
            
            # Check agent history for screenshots (captured with use_vision=True)
            # We want the LAST screenshot to capture the final state (blocker, failure, or success)
            if hasattr(result, 'history') and result.history:
                last_screenshot = None
                last_step_num = 0
                
                # Iterate through ALL steps to find the LAST screenshot
                for i, step in enumerate(result.history):
                    # Check if step has a state with screenshot_path
                    if hasattr(step, 'state') and step.state and hasattr(step.state, 'screenshot_path'):
                        if step.state.screenshot_path and os.path.exists(step.state.screenshot_path):
                            # Keep track of the last screenshot found
                            last_screenshot = step.state.screenshot_path
                            last_step_num = i + 1
                
                # Copy the LAST screenshot (final state) to our directory
                if last_screenshot:
                    shutil.copy2(last_screenshot, final_screenshot_path)
                    screenshot_path = final_screenshot_path
                    logger.info(f"📸 Screenshot captured: FINAL STATE from step {last_step_num}/{len(result.history)}")
                    logger.info(f"   Path: {screenshot_path}")
                    logger.info(f"   Size: {screenshot_path.stat().st_size} bytes")
                    logger.info(f"   This is the last screenshot showing where the application stopped")
            
            if not screenshot_path:
                logger.warning("⚠️  No screenshots found in agent history")
                logger.info("   Agent may not have enabled vision mode or no screenshots were captured")
                    
        except Exception as screenshot_error:
            logger.warning(f"⚠️  Could not extract screenshot from agent history: {screenshot_error}")
            screenshot_path = None
        
        logger.info("")
        logger.info("⚠️  IMPORTANT: Review the browser and agent report")
        logger.info("   - Check which fields were filled successfully")
        logger.info("   - Check if files were uploaded (see agent report)")
        logger.info("   - Check if Submit button was clicked")
        logger.info("   - Look for confirmation/thank you page")
        logger.info("   - Check your email for application confirmation")
        logger.info("")
        
        # Return both agent result and screenshot path for logging
        return {
            "agent_result": str(result),
            "screenshot_path": str(screenshot_path) if screenshot_path else None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fill application form: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTION: FIND LATEST GENERATED FILES
# ═══════════════════════════════════════════════════════════════════════════

def find_latest_documents() -> Tuple[Optional[str], Optional[str]]:
    """
    Find the latest resume and cover letter files in generated_documents/.
    
    Returns:
        Tuple of (resume_path, cover_letter_path) - either may be None if not found
    """
    logger.info("🔍 Searching for latest generated documents...")
    
    # Find all resume files
    resume_pattern = str(GENERATED_DOCS_DIR / "dilip_kumar_tc_resume_*.docx")
    resume_files = glob.glob(resume_pattern)
    
    # Find all cover letter files
    cover_letter_pattern = str(GENERATED_DOCS_DIR / "dilip_kumar_tc_cover_letter_*.docx")
    cover_letter_files = glob.glob(cover_letter_pattern)
    
    # Get the latest resume (most recent modification time)
    latest_resume = None
    if resume_files:
        latest_resume = max(resume_files, key=os.path.getmtime)
        resume_time = datetime.fromtimestamp(os.path.getmtime(latest_resume))
        logger.info(f"✅ Found latest resume: {latest_resume}")
        logger.info(f"   Created: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        logger.warning("⚠️  No resume files found in generated_documents/")
    
    # Get the latest cover letter
    latest_cover_letter = None
    if cover_letter_files:
        latest_cover_letter = max(cover_letter_files, key=os.path.getmtime)
        cl_time = datetime.fromtimestamp(os.path.getmtime(latest_cover_letter))
        logger.info(f"✅ Found latest cover letter: {latest_cover_letter}")
        logger.info(f"   Created: {cl_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        logger.warning("⚠️  No cover letter files found in generated_documents/")
    
    return latest_resume, latest_cover_letter

# ═══════════════════════════════════════════════════════════════════════════
# MAIN AUTOMATION WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

async def automate_job_application(job_url: str, skip_generation: bool = False, job_index: int = 0, headless: bool = False):
    """
    Main workflow to automate job application.
    
    Args:
        job_url: URL of the job posting
        skip_generation: If True, skip resume/cover letter generation and use latest files
        job_index: Job index for logging (used in parallel execution)
    """
    # Use job-specific logger for parallel execution clarity
    logger = logging.getLogger(f"JobAutomation_Job{job_index+1:02d}")
    
    logger.info("")
    logger.info("█" * 80)
    logger.info("█" + " " * 78 + "█")
    logger.info("█" + " " * 20 + "JOB APPLICATION AUTOMATION STARTED" + " " * 24 + "█")
    logger.info("█" + " " * 78 + "█")
    logger.info("█" * 80)
    logger.info("")
    
    application_details = {
        "job_url": job_url,
        "start_time": datetime.now().isoformat(),
        "steps_completed": [],
        "errors": []
    }
    
    try:
        # Load user profile
        user_profile = load_user_profile()
        application_details["steps_completed"].append("User profile loaded")
        
        if skip_generation:
            # Skip generation, use latest existing files
            logger.info("⚡ SKIP MODE: Using latest existing documents (no API calls)")
            logger.info("="*80)
            
            resume_path, cover_letter_path = find_latest_documents()
            
            if not resume_path:
                raise Exception("No resume files found in generated_documents/. Generate at least one first.")
            
            application_details["steps_completed"].append("Using existing resume")
            if cover_letter_path:
                application_details["steps_completed"].append("Using existing cover letter")
            else:
                application_details["steps_completed"].append("No cover letter found")
            application_details["resume_path"] = resume_path
            application_details["cover_letter_path"] = cover_letter_path or "NOT FOUND"
            
            # Use empty job description for skip mode
            job_description = "[Skipped scraping in test mode]"
            application_details["job_description_length"] = 0
        else:
            # Normal mode: Scrape and generate
            # Step 1: Scrape job description
            job_description = await scrape_job_description(job_url)
            application_details["steps_completed"].append("Job description scraped")
            application_details["job_description_length"] = len(job_description)
            
            # Steps 2 & 3: Generate documents in parallel
            resume_path, cover_letter_path = await generate_documents_parallel(job_description, user_profile)
            application_details["steps_completed"].append("Resume generated")
            if cover_letter_path:
                application_details["steps_completed"].append("Cover letter generated")
            else:
                application_details["steps_completed"].append("Cover letter SKIPPED (timeout)")
            application_details["resume_path"] = resume_path
            application_details["cover_letter_path"] = cover_letter_path or "NOT GENERATED"
        
        # Steps 5-9: Fill application form and submit
        form_result = await fill_application_form(job_url, user_profile, resume_path, cover_letter_path, headless=headless)
        
        # Extract values from form_result dict (new format)
        if isinstance(form_result, dict):
            agent_result_str = form_result.get("agent_result", str(form_result))
            screenshot_path = form_result.get("screenshot_path", None)
            
            # Add screenshot to details if captured
            if screenshot_path:
                application_details["screenshot"] = str(screenshot_path)
                application_details["steps_completed"].append(f"Screenshot captured: {screenshot_path}")
        else:
            # Fallback for old string format
            agent_result_str = str(form_result)
            screenshot_path = None
        
        # Check if blocker was detected by parsing agent result
        if "impossible_task=True" in agent_result_str or "impossible_task":  # Parse the agent result
            # Try to extract blocker details from the JudgementResult
            if "failure_reason" in agent_result_str:
                # Extract failure reason using string parsing
                try:
                    failure_start = agent_result_str.find("failure_reason='")
                    if failure_start != -1:
                        failure_start += len("failure_reason='")
                        failure_end = agent_result_str.find("'", failure_start)
                        failure_reason = agent_result_str[failure_start:failure_end]
                    else:
                        failure_reason = "Task marked as impossible by agent"
                except:
                    failure_reason = "Task marked as impossible by agent"
            else:
                failure_reason = "Task marked as impossible by agent"
            
            # Determine blocker type from the failure reason
            failure_lower = failure_reason.lower()
            if "expired" in failure_lower:
                blocker_type = "EXPIRED_JOB"
            elif "captcha" in failure_lower:
                blocker_type = "CAPTCHA"
            elif "email" in failure_lower and "verif" in failure_lower:
                blocker_type = "EMAIL_VERIFICATION"
            elif "phone" in failure_lower and ("verif" in failure_lower or "sms" in failure_lower):
                blocker_type = "PHONE_VERIFICATION"
            elif "locked" in failure_lower or "wrong" in failure_lower or "invalid" in failure_lower or "authentication" in failure_lower:
                blocker_type = "ACCOUNT_LOCKED"
            elif "login" in failure_lower or "sign in" in failure_lower:
                blocker_type = "LOGIN_REQUIRED"
            else:
                blocker_type = "UNKNOWN_BLOCKER"
            
            # Mark as IMPOSSIBLE_TASK
            application_details["steps_completed"].append(f"Blocker detected by agent: {blocker_type}")
            application_details["form_result"] = agent_result_str
            application_details["blocker_type"] = blocker_type
            application_details["blocker_reason"] = failure_reason
            application_details["end_time"] = datetime.now().isoformat()
            application_details["status"] = f"Impossible Task - {blocker_type}"
            
            # Save log as IMPOSSIBLE_TASK
            save_application_log(job_url, "IMPOSSIBLE_TASK", application_details)
            
            logger.info("")
            logger.info("█" * 80)
            logger.info("█" + " " * 78 + "█")
            logger.info("█" + " " * 20 + "⚠️  IMPOSSIBLE TASK DETECTED" + " " * 30 + "█")
            logger.info("█" + " " * 78 + "█")
            logger.info("█" * 80)
            logger.info("")
            logger.info("📊 SUMMARY:")
            logger.info(f"   🚫 Blocker Type: {blocker_type}")
            logger.info(f"   📝 Reason: {failure_reason}")
            logger.info(f"   ⚠️  This is NOT a failure - task cannot be automated")
            logger.info("")
            
            return application_details
        
        # No blocker - proceed with normal success flow
        application_details["steps_completed"].append("Application form filled and submitted")
        application_details["form_result"] = agent_result_str if 'agent_result_str' in locals() else str(form_result)
        
        # Add screenshot info if available
        if 'screenshot_path' in locals() and screenshot_path:
            application_details["screenshot"] = str(screenshot_path)
        
        # Mark as success
        application_details["end_time"] = datetime.now().isoformat()
        application_details["status"] = "Success - Form filled and submitted"
        
        # Save log
        save_application_log(job_url, "SUCCESS", application_details)
        
        logger.info("")
        logger.info("█" * 80)
        logger.info("█" + " " * 78 + "█")
        logger.info("█" + " " * 18 + "✅ JOB APPLICATION AUTOMATION COMPLETED" + " " * 20 + "█")
        logger.info("█" + " " * 78 + "█")
        logger.info("█" * 80)
        logger.info("")
        logger.info("📊 SUMMARY:")
        if not skip_generation:
            logger.info(f"   ✅ Job description scraped")
        else:
            logger.info(f"   ⏩ Job description: SKIPPED (test mode)")
        logger.info(f"   ✅ Resume: {resume_path}")
        if cover_letter_path:
            logger.info(f"   ✅ Cover letter: {cover_letter_path}")
        else:
            logger.warning(f"   ⚠️  Cover letter: NOT AVAILABLE")
        logger.info(f"   ✅ Application form filled and submitted by AI agent")
        logger.info("")
        logger.info("⚠️  CRITICAL - VERIFY SUBMISSION:")
        logger.info("   1. Check agent report above for file upload status")
        logger.info("   2. Check if browser showing confirmation/thank you page")
        logger.info("   3. Check your EMAIL for application confirmation")
        logger.info("   4. If NO confirmation email: Application may have failed")
        logger.info("")
        logger.info("💡 If files didn't upload or submission failed:")
        logger.info("   - Check agent report for specific errors")
        logger.info("   - Review browser for any error messages or validation issues")
        logger.info("   - You may need to upload files/submit manually")
        logger.info("")
        
        return application_details
        
    except Exception as e:
        # Log error
        error_msg = f"Application failed: {str(e)}"
        logger.error("")
        logger.error("█" * 80)
        logger.error(f"❌ {error_msg}")
        logger.error("█" * 80)
        logger.error(traceback.format_exc())
        
        application_details["end_time"] = datetime.now().isoformat()
        application_details["status"] = "Failed"
        application_details["error"] = str(e)
        application_details["traceback"] = traceback.format_exc()
        
        # Save error log
        save_application_log(job_url, "FAILED", application_details)
        
        raise

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """Main entry point for the automation script."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Job Application Automation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal mode - generate new resume and cover letter:
  python job_application_automation.py
  
  # Test mode - use latest existing files (skip generation):
  python job_application_automation.py --skip-generation
  
  # With custom job URL:
  python job_application_automation.py --url "https://example.com/job/12345"
  
  # Test mode with custom URL:
  python job_application_automation.py --skip-generation --url "https://example.com/job/12345"
        """
    )
    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='Skip resume/cover letter generation and use latest existing files (for testing)'
    )
    parser.add_argument(
        '--url',
        type=str,
        default="https://www.example.com/jobs/12345",
        help='Job posting URL to apply to'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no window visible, faster)'
    )
    
    args = parser.parse_args()
    
    # Job URL from command-line or default
    JOB_URL = args.url
    
    logger.info("Configuration:")
    logger.info(f"   Mode: {'TEST (skip generation)' if args.skip_generation else 'NORMAL (generate new docs)'}")
    logger.info(f"   Browser: {'HEADLESS (no window)' if args.headless else 'NORMAL (window visible)'}")
    logger.info(f"   Job URL: {JOB_URL}")
    logger.info(f"   User Profile: {USER_PROFILE_PATH}")
    logger.info(f"   Documents Directory: {GENERATED_DOCS_DIR}")
    logger.info(f"   Logs Directory: {LOGS_DIR}")
    logger.info("")
    
    if args.skip_generation:
        logger.info("⚡ SKIP MODE ACTIVE - Will use latest existing resume/cover letter")
        logger.info("   No API calls will be made for document generation")
        logger.info("")
    
    # Check if user profile exists
    if not USER_PROFILE_PATH.exists():
        logger.error(f"❌ User profile not found: {USER_PROFILE_PATH}")
        logger.error("   Please create user_profile.json before running")
        return
    
    # Validate job URL
    if JOB_URL == "https://www.example.com/jobs/12345":
        logger.warning("")
        logger.warning("⚠️  WARNING: Using example job URL!")
        logger.warning("   Please replace JOB_URL in main() with actual job posting URL")
        logger.warning("")
        
        # Uncomment to prevent running with example URL
        # return
    
    # Run automation
    try:
        await automate_job_application(JOB_URL, skip_generation=args.skip_generation, headless=args.headless)
        
        # Generate HTML report for this run
        try:
            from generate_report import generate_html_report
            from urllib.parse import urlparse
            
            # Extract company name for report
            domain = urlparse(JOB_URL).netloc.replace('www.', '').split('.')[0]
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 Generating HTML report...")
            
            report_path = generate_html_report(
                job_urls=[JOB_URL],     # Only include this job
                report_name=domain,     # Use company name
                last_n_minutes=5        # Only include logs from last 5 minutes (current run)
            )
            
            logger.info(f"✅ Report generated: {report_path}")
            logger.info(f"🌐 Open in browser: file:///{Path(report_path).absolute()}")
            logger.info("=" * 80)
            
        except Exception as report_error:
            logger.warning(f"⚠️  Could not generate report: {report_error}")
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Automation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Automation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
