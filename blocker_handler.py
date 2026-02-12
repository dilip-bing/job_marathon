"""
═══════════════════════════════════════════════════════════════════════════════
BLOCKER HANDLER - Detect Impossible Tasks
═══════════════════════════════════════════════════════════════════════════════

Identifies scenarios where job application cannot be automated:
- Email verification codes (requires inbox access)
- CAPTCHA challenges (requires human verification)
- Expired/removed job postings
- Required document uploads we don't have

Expected Impact: Correctly identifies 30% of "failures" as impossible tasks

Author: Dilip Kumar
Date: February 12, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import re
from typing import Tuple, Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class BlockerType(Enum):
    """Types of blockers that prevent automation."""
    NONE = "none"
    EMAIL_VERIFICATION = "email_verification"
    CAPTCHA = "captcha"
    EXPIRED_JOB = "expired_job"
    PHONE_VERIFICATION = "phone_verification"
    ACCOUNT_LOCKED = "account_locked"
    VIDEO_REQUIRED = "video_required"
    ASSESSMENT_REQUIRED = "assessment_required"
    MISSING_DOCUMENTS = "missing_documents"
    LOCATION_RESTRICTED = "location_restricted"
    UNKNOWN = "unknown"


class BlockerDetector:
    """
    Detects various types of blockers on job application pages.
    """
    
    # Email verification patterns
    EMAIL_VERIFICATION_PATTERNS = [
        r"verification\s+code.*email",
        r"email.*verification.*code",
        r"code.*sent.*email",
        r"check.*email.*code",
        r"enter.*\d+.*character.*code.*email",
        r"8.*character.*code",  # 8-char is email specific
        r"confirm.*email.*code",
        r"email.*confirmation.*code",
        r"verify.*email.*code",
    ]
    
    # CAPTCHA patterns
    CAPTCHA_PATTERNS = [
        r"captcha",
        r"recaptcha",
        r"hcaptcha",
        r"i.*m\s+not\s+a\s+robot",
        r"verify.*you.*re.*human",
        r"security.*check",
        r"prove.*you.*re.*human",
    ]
    
    # Expired job patterns
    EXPIRED_JOB_PATTERNS = [
        r"job.*expired",
        r"position.*no.*longer.*available",
        r"posting.*closed",
        r"application.*closed",
        r"no.*longer.*accepting",
        r"deadline.*passed",
        r"job.*removed",
        r"position.*filled",
        r"sorry.*this.*job.*expired",
        r"no.*job.*openings.*at.*this.*time",
    ]
    
    # Phone verification patterns  
    PHONE_VERIFICATION_PATTERNS = [
        r"phone.*verification",
        r"sms.*code",
        r"text.*message.*code",
        r"verify.*phone.*number",
        r"code.*sent.*phone",
        r"code.*sent.*mobile",
        r"\d+.*digit.*code.*phone",
        r"\d+.*digit.*code.*mobile",
        r"mobile.*phone.*verification",
    ]
    
    # Account locked / login failure patterns
    ACCOUNT_LOCKED_PATTERNS = [
        r"account.*locked",
        r"account.*disabled",
        r"account.*suspended",
        r"wrong.*email.*password",
        r"wrong.*email.*address.*password",
        r"entered.*wrong.*email",
        r"incorrect.*email.*password",
        r"invalid.*email.*password",
        r"invalid.*credentials",
        r"authentication.*failed",
        r"login.*failed",
        r"sign.*in.*failed",
        r"email.*not.*found",
        r"account.*not.*found",
        r"password.*incorrect",
        r"too.*many.*attempts",
        r"temporarily.*locked",
    ]
    
    # Video requirement patterns
    VIDEO_PATTERNS = [
        r"video.*interview.*required",
        r"record.*video.*response",
        r"video.*submission.*required",
        r"hirevue",
        r"video.*assessment",
    ]
    
    # Assessment requirement patterns
    ASSESSMENT_PATTERNS = [
        r"complete.*assessment",
        r"take.*test",
        r"coding.*challenge.*required",
        r"technical.*assessment",
        r"online.*test.*required",
    ]
    
    @classmethod
    def detect_email_verification(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect email verification code requirement.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.EMAIL_VERIFICATION_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "Email verification code required - cannot access email inbox"
                logger.warning(f"🚫 BLOCKER: {reason}")
                return True, reason
        
        return False, ""
    
    @classmethod
    def detect_captcha(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect CAPTCHA requirement.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.CAPTCHA_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "CAPTCHA detected - requires human verification"
                logger.warning(f"🚫 BLOCKER: {reason}")
                return True, reason
        
        return False, ""
    
    @classmethod
    def detect_expired_job(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect expired or removed job posting.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.EXPIRED_JOB_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "Job posting expired or removed - impossible to apply"
                logger.warning(f"🚫 BLOCKER: {reason}")
                return True, reason
        
        return False, ""
    
    @classmethod
    def detect_phone_verification(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect phone verification requirement.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.PHONE_VERIFICATION_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "Phone verification code required - cannot access SMS"
                logger.warning(f"🚫 BLOCKER: {reason}")
                return True, reason
        
        return False, ""    
    @classmethod
    def detect_account_locked(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect account locked or authentication failure.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.ACCOUNT_LOCKED_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "Account locked or authentication failed - cannot proceed with automated login"
                logger.warning(f"🚫 BLOCKER: {reason}")
                return True, reason
        
        return False, ""    
    @classmethod
    def detect_video_requirement(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect video interview requirement.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.VIDEO_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "Video interview required - cannot automate video recording"
                logger.warning(f"⚠️  BLOCKER: {reason}")
                return True, reason
        
        return False, ""
    
    @classmethod
    def detect_assessment_requirement(cls, page_text: str, url: str) -> Tuple[bool, str]:
        """
        Detect online assessment requirement.
        
        Returns:
            (is_blocked, reason)
        """
        page_lower = page_text.lower()
        
        for pattern in cls.ASSESSMENT_PATTERNS:
            if re.search(pattern, page_lower, re.IGNORECASE):
                reason = "Online assessment/test required - cannot automate"
                logger.warning(f"⚠️  BLOCKER: {reason}")
                return True, reason
        
        return False, ""


class BlockerHandler:
    """
    Main handler for detecting and classifying blockers.
    """
    
    def __init__(self):
        self.detector = BlockerDetector()
        
        # Order matters - check in order of severity/likelihood
        # NOTE: Only HARD blockers included here (impossible to automate)
        # Soft blockers (video, assessment) are NOT checked automatically
        # Check phone verification BEFORE email verification to avoid conflicts
        self.detection_chain = [
            (BlockerType.EXPIRED_JOB, self.detector.detect_expired_job),
            (BlockerType.PHONE_VERIFICATION, self.detector.detect_phone_verification),
            (BlockerType.EMAIL_VERIFICATION, self.detector.detect_email_verification),
            (BlockerType.CAPTCHA, self.detector.detect_captcha),
            (BlockerType.ACCOUNT_LOCKED, self.detector.detect_account_locked),
        ]
    
    def check_for_blockers(self, page_text: str, url: str) -> Tuple[bool, BlockerType, str]:
        """
        Check for any blockers that would prevent automation.
        
        Args:
            page_text: Current page text content
            url: Current URL
            
        Returns:
            (is_blocked, blocker_type, reason)
        """
        for blocker_type, detect_func in self.detection_chain:
            is_blocked, reason = detect_func(page_text, url)
            if is_blocked:
                return True, blocker_type, reason
        
        return False, BlockerType.NONE, ""
    
    def should_terminate_with_impossible_task(self, blocker_type: BlockerType) -> bool:
        """
        Determine if blocker should be marked as impossible task.
        
        Hard blockers (impossible to automate):
        - Email verification
        - CAPTCHA
        - Expired jobs
        - Phone verification
        
        Soft blockers (possible but complex):
        - Video interviews
        - Assessments
        
        Returns:
            True if should mark as impossible_task=True
        """
        hard_blockers = [
            BlockerType.EMAIL_VERIFICATION,
            BlockerType.CAPTCHA,
            BlockerType.EXPIRED_JOB,
            BlockerType.PHONE_VERIFICATION,
            BlockerType.ACCOUNT_LOCKED,
        ]
        
        return blocker_type in hard_blockers
    
    def get_termination_message(self, blocker_type: BlockerType, reason: str) -> str:
        """
        Generate appropriate termination message for agent.
        
        Args:
            blocker_type: Type of blocker detected
            reason: Detailed reason
            
        Returns:
            Formatted message for agent to return
        """
        if blocker_type == BlockerType.EXPIRED_JOB:
            return f"Unable to complete application: {reason}. The job posting is no longer active on the company's website."
        
        elif blocker_type == BlockerType.EMAIL_VERIFICATION:
            return f"Unable to complete application: {reason}. The application system requires accessing an email inbox to retrieve a verification code, which cannot be automated."
        
        elif blocker_type == BlockerType.CAPTCHA:
            return f"Unable to complete application: {reason}. CAPTCHA challenges require human verification and cannot be automated."
        
        elif blocker_type == BlockerType.PHONE_VERIFICATION:
            return f"Unable to complete application: {reason}. The system requires SMS verification which cannot be automated."
        
        elif blocker_type == BlockerType.ACCOUNT_LOCKED:
            return f"Unable to complete application: {reason}. The account is locked or authentication failed. Please check the logged credentials and try manually."
        
        elif blocker_type == BlockerType.VIDEO_REQUIRED:
            return f"Unable to complete application: {reason}. Video recording requires human interaction and cannot be fully automated."
        
        elif blocker_type == BlockerType.ASSESSMENT_REQUIRED:
            return f"Unable to complete application: {reason}. Online assessments and coding challenges cannot be automated."
        
        else:
            return f"Unable to complete application: {reason}"
    
    def log_blocker_stats(self, blocker_type: BlockerType):
        """Log blocker statistics for reporting."""
        blocker_categories = {
            BlockerType.EMAIL_VERIFICATION: "Email Verification Blocker",
            BlockerType.CAPTCHA: "CAPTCHA Blocker",
            BlockerType.EXPIRED_JOB: "Expired Job",
            BlockerType.PHONE_VERIFICATION: "Phone Verification Blocker",
            BlockerType.ACCOUNT_LOCKED: "Account Locked / Auth Failed",
            BlockerType.VIDEO_REQUIRED: "Video Interview Required",
            BlockerType.ASSESSMENT_REQUIRED: "Assessment Required",
        }
        
        category = blocker_categories.get(blocker_type, "Unknown Blocker")
        logger.info(f"📊 Blocker Category: {category}")


# Convenience function for quick integration
def check_for_blockers(page_text: str, url: str) -> Tuple[bool, BlockerType, str, bool]:
    """
    Quick function to check for automation blockers.
    
    Args:
        page_text: Current page text
        url: Current URL
        
    Returns:
        (is_blocked, blocker_type, reason, is_impossible_task)
        
    Example:
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(page_text, url)
        if is_blocked:
            if is_impossible:
                # Mark as impossible task, not a failure
                return done(success=False, impossible_task=True, text=reason)
            else:
                # Try to proceed but warn
                logger.warning(f"Soft blocker detected: {reason}")
    """
    handler = BlockerHandler()
    is_blocked, blocker_type, reason = handler.check_for_blockers(page_text, url)
    
    if is_blocked:
        is_impossible = handler.should_terminate_with_impossible_task(blocker_type)
        handler.log_blocker_stats(blocker_type)
        return True, blocker_type, reason, is_impossible
    
    return False, BlockerType.NONE, "", False


def get_blocker_detection_prompt() -> str:
    """
    Get prompt to inject into agent instructions for self-detection.
    
    Returns:
        Prompt text for agent awareness of blockers
    """
    return """
⚠️ BLOCKER DETECTION - CHECK FOR IMPOSSIBLE TASKS ⚠️

Before attempting to fill any form, CHECK for these BLOCKERS:

🚫 HARD BLOCKERS (Terminate immediately with impossible_task=True):

1. EMAIL VERIFICATION CODE
   - Page asks for "verification code" or "code sent to email"
   - Requires accessing email inbox
   → TERMINATE: Cannot access email

2. CAPTCHA
   - "I'm not a robot" checkbox
   - Image selection challenges
   - reCAPTCHA / hCaptcha / Cloudflare challenge
   - CAPTCHA during account creation or login
   → TERMINATE: Cannot solve CAPTCHA
   → If seen DURING account creation, stop immediately (account may already be created)

3. EXPIRED JOB
   - "Job expired" or "Position no longer available"
   - "No job openings at this time"
   → TERMINATE: Job removed

4. PHONE VERIFICATION
   - "Enter code sent to phone" or "SMS verification"
   → TERMINATE: Cannot access SMS

5. ACCOUNT LOCKED / LOGIN FAILED / POST-LOGIN ERRORS
   - "Account locked" or "Account disabled"  or "Account suspended"
   - "Wrong email address or password"
   - "Invalid credentials" or "Authentication failed"
   - "Your account has been locked temporarily"
   - "Account not found" or "Too many attempts"
   - "Please verify your email" or "Email verification required"
   - "Check your email for verification" or "Verification link sent"
   - ANY error message after account creation or login attempt with words:
     * "verification", "verify", "locked", "disabled", "suspended"
     * "temporary", "temporarily", "invalid", "wrong", "not found"
     * "failed", "error", "unable", "cannot"
   → TERMINATE IMMEDIATELY: Do NOT retry with "Forgot Password"
   → Do NOT attempt multiple logins
   → Do NOT try alternative login methods
   → NOTE: If you created an account, ALWAYS log the credentials before terminating:
     "Created account: email@example.com / Password123!"

🚨 CRITICAL: POST-ACCOUNT CREATION FAILURES 🚨
If you successfully create an account (entered email + password + clicked Create Account):
- And then see ANY error message (verification, locked, etc.)
- STOP IMMEDIATELY - do not retry login, do not use forgot password
- LOG THE CREDENTIALS in your response before terminating:
  Example: "Created account: dthirukondac@binghamton.edu / Ciena2026! 
  Unable to proceed: Email verification required."

⚠️ SOFT BLOCKERS (Note but attempt to proceed):

6. VIDEO INTERVIEW
   - "Record video response" or "HireVue"
   → PROCEED: Fill form first, video comes later

7. ASSESSMENT
   - "Complete assessment" or "Take test"
   → PROCEED: Fill application, assessment comes later

If you detect a HARD BLOCKER:
- Do NOT attempt to fill the form
- If you created account credentials, report them: "Created account: email@example.com / Password123!"
- Return done(success=False, impossible_task=True, text="<reason>")
- Be specific about which blocker type

If you detect a SOFT BLOCKER:
- Log a warning but continue with application
- The blocker comes AFTER basic application
"""
