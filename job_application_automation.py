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

async def fill_application_form(job_url: str, user_profile: Dict, resume_path: str, cover_letter_path: Optional[str]):
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
        
        IMPORTANT ERROR HANDLING:
        - If a dropdown only shows "Select" or "Please Select", try changing a related field first
        - If file upload doesn't work, note it and continue
        - If a field is unclear, put reasonable information or skip it
        - Answer questions relevantly based on the profile information above
        
        FALLBACK STRATEGIES (when specific answer not clear):
        - Dropdowns: Select first reasonable option, NEVER leave "Select"
        - Text fields: Use "N/A" or "See resume" for unknown required fields
        - Radio buttons: Default to "NO" for yes/no questions (except work auth = YES)
        - Checkboxes: Leave unchecked if uncertain, check if consent/agreement required
        - Multi-select courses: Select 8-12 relevant courses generously
        - Multi-select locations: Select 5-10 locations to maximize opportunities
        
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
        - Whether confirmation/thank you page appeared
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
        browser = Browser(cross_origin_iframes=True)
        
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
        
        # Capture screenshot from agent's browser
        screenshot_path = None
        try:
            from urllib.parse import urlparse
            domain = urlparse(job_url).netloc.replace('www.', '').split('.')[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = SCREENSHOTS_DIR / f"{domain}_{timestamp}.png"
            
            # Try multiple methods to get the current page
            current_page = None
            
            # Method 1: Access from agent.browser
            if hasattr(agent, 'browser'):
                try:
                    if hasattr(agent.browser, 'context') and agent.browser.context:
                        pages = agent.browser.context.pages
                        if pages and len(pages) > 0:
                            current_page = pages[-1]
                            logger.info("✓ Got page from agent.browser.context")
                except Exception:
                    pass
            
            # Method 2: Access from browser.contexts list
            if not current_page and hasattr(browser, 'contexts'):
                try:
                    contexts = browser.contexts
                    if contexts and len(contexts) > 0:
                        pages = contexts[0].pages
                        if pages and len(pages) > 0:
                            current_page = pages[-1]
                            logger.info("✓ Got page from browser.contexts[0]")
                except Exception:
                    pass
            
            # Method 3: Access from browser.context directly
            if not current_page and hasattr(browser, 'context'):
                try:
                    if browser.context:
                        pages = browser.context.pages
                        if pages and len(pages) > 0:
                            current_page = pages[-1]
                            logger.info("✓ Got page from browser.context")
                except Exception:
                    pass
            
            # Capture screenshot if we got a page
            if current_page:
                await current_page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            else:
                logger.warning(f"⚠️  Could not access browser page for screenshot")
                screenshot_path = None
        except Exception as screenshot_error:
            logger.warning(f"⚠️  Could not capture screenshot: {screenshot_error}")
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

async def automate_job_application(job_url: str, skip_generation: bool = False, job_index: int = 0):
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
        form_result = await fill_application_form(job_url, user_profile, resume_path, cover_letter_path)
        
        # Check if blocker was detected (form_result is dict with status key)
        if isinstance(form_result, dict) and "status" in form_result:
            blocker_status = form_result.get("status", "")
            if "Impossible Task" in blocker_status:
                # Blocker detected - mark as impossible, not success
                application_details["steps_completed"].append(f"Blocker detected: {form_result.get('blocker_type', 'unknown')}")
                application_details["form_result"] = form_result.get("reason", "Unknown blocker")
                application_details["blocker_type"] = form_result.get("blocker_type", "unknown")
                application_details["end_time"] = datetime.now().isoformat()
                application_details["status"] = blocker_status
                
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
                logger.info(f"   🚫 Blocker Type: {form_result.get('blocker_type', 'unknown')}")
                logger.info(f"   📝 Reason: {form_result.get('reason', 'Unknown')}")
                logger.info(f"   ⚠️  This is NOT a failure - task cannot be automated")
                logger.info("")
                
                return application_details
        
        # No blocker - proceed with normal success flow
        application_details["steps_completed"].append("Application form filled and submitted")
        application_details["form_result"] = form_result
        
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
    
    args = parser.parse_args()
    
    # Job URL from command-line or default
    JOB_URL = args.url
    
    logger.info("Configuration:")
    logger.info(f"   Mode: {'TEST (skip generation)' if args.skip_generation else 'NORMAL (generate new docs)'}")
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
        await automate_job_application(JOB_URL, skip_generation=args.skip_generation)
        
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
