"""
═══════════════════════════════════════════════════════════════════════════════
LOGIN HANDLER - Bypass Sign-In Pages
═══════════════════════════════════════════════════════════════════════════════

Detects and bypasses login requirements on job application sites.
Handles major ATS platforms: Greenhouse, Workday, Lever, iCIMS, Ashby, etc.

Expected Impact: Fixes 40% of failures caused by login walls

Author: Dilip Kumar
Date: February 12, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Optional, Dict, Tuple
import re

logger = logging.getLogger(__name__)


class LoginDetector:
    """
    Detects login/sign-in requirements on job application pages.
    """
    
    # Common sign-in indicators
    LOGIN_INDICATORS = [
        "sign in",
        "log in",
        "login",
        "create account",
        "create an account",
        "register",
        "sign up",
        "existing user",
        "returning user",
        "already have an account",
        "member login",
        "candidate login",
        "applicant login",
    ]
    
    # ATS-specific patterns
    ATS_PATTERNS = {
        "greenhouse": [
            "greenhouse.io",  # Covers jobs.greenhouse.io, boards.greenhouse.io, etc.
            "grnh.se"
        ],
        "workday": [
            "myworkdayjobs.com",
            "myworkdaysite.com",
            "wd1.myworkdaysite.com",
            "wd5.myworkdayjobs.com"
        ],
        "lever": [
            "jobs.lever.co",
            "lever.co/apply"
        ],
        "icims": [
            "icims.com",
            "apply.icims.com",
            "careers.icims.com",
            "careers.",  # Generic careers subdomain (weak match - should be last)
        ],
        "ashby": [
            "jobs.ashbyhq.com",
            "ashbyhq.com"
        ],
        "smartrecruiters": [
            "jobs.smartrecruiters.com",
            "smartrecruiters.com"
        ],
        "taleo": [
            "taleo.net",
            "oracle.taleo.net"
        ],
        "jobvite": [
            "jobvite.com",
            "jobs.jobvite.com"
        ]
    }
    
    @classmethod
    def detect_ats_platform(cls, url: str) -> Optional[str]:
        """
        Detect which ATS platform the job is using.
        
        Args:
            url: Job application URL
            
        Returns:
            ATS platform name or None
        """
        url_lower = url.lower()
        
        for platform, patterns in cls.ATS_PATTERNS.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return platform
        
        return None
    
    @classmethod
    def detect_login_requirement(cls, page_text: str, url: str) -> Tuple[bool, str, str]:
        """
        Detect if page requires login.
        
        Args:
            page_text: Current page text content
            url: Current URL
            
        Returns:
            (requires_login, platform, reason)
        """
        page_lower = page_text.lower()
        
        # Check for login indicators
        login_found = False
        for indicator in cls.LOGIN_INDICATORS:
            if indicator in page_lower:
                login_found = True
                break
        
        if not login_found:
            return False, "", ""
        
        # Detect ATS platform
        platform = cls.detect_ats_platform(url) or "unknown"
        
        # Build reason message
        reason = f"Login detected on {platform} platform"
        
        return True, platform, reason


class LoginBypassHandler:
    """
    Handles bypassing login requirements using available strategies.
    """
    
    @staticmethod
    def get_bypass_strategies(platform: str) -> Dict[str, str]:
        """
        Get bypass strategies for specific ATS platform.
        
        Args:
            platform: ATS platform name
            
        Returns:
            Dictionary of strategy instructions
        """
        strategies = {
            "greenhouse": {
                "email_only": "Look for 'Apply with email' or 'Continue as guest' button and click it",
                "skip_login": "Look for 'Skip' or 'Apply without account' link below the login form",
                "direct_apply": "Scroll down past the login section to find direct application form"
            },
            "workday": {
                "guest_apply": "Look for 'Apply as Guest' or 'Apply without creating account' option",
                "email_continue": "Enter email and click 'Continue' without password",
                "skip_signin": "Look for small 'Skip sign in' link at bottom of login modal"
            },
            "lever": {
                "direct_form": "Scroll down - application form is usually below the login section",
                "guest_mode": "Look for 'Apply as guest' or similar bypass option"
            },
            "ashby": {
                "no_login": "Ashby typically doesn't require login - proceed with form filling",
                "direct_apply": "Click 'Application' tab if multiple tabs are present"
            },
            "smartrecruiters": {
                "guest_apply": "Look for 'Continue as guest' or 'Apply without account' button",
                "email_only": "Enter email and proceed without creating password"
            },
            "icims": {
                "new_user": "Click 'New user? Apply now' or 'Apply without account' button",
                "guest_option": "Look for guest application option below login form"
            },
            "taleo": {
                "new_candidate": "Click 'New Candidate' or 'First time applying?' button",
                "skip_login": "Click 'Continue as guest' or similar option"
            },
            "jobvite": {
                "apply_now": "Click 'Apply Now' button which bypasses login",
                "guest_apply": "Look for guest application option"
            },
            "unknown": {
                "common_bypass": "Look for: 'Apply as guest', 'Continue without account', 'Skip login', or scroll down to find direct application form",
                "email_only": "If only email is requested, enter it and proceed without password"
            }
        }
        
        return strategies.get(platform, strategies["unknown"])
    
    @staticmethod
    def generate_bypass_prompt(platform: str, page_text: str) -> str:
        """
        Generate detailed prompt for bypassing login.
        
        Args:
            platform: ATS platform name
            page_text: Current page text
            
        Returns:
            Bypass instruction prompt
        """
        strategies = LoginBypassHandler.get_bypass_strategies(platform)
        
        prompt = f"""
🚫 LOGIN WALL DETECTED - BYPASS REQUIRED

Platform: {platform.upper()}

CRITICAL: DO NOT CREATE AN ACCOUNT OR LOG IN!

Try these strategies IN ORDER:

"""
        
        for i, (strategy_name, instruction) in enumerate(strategies.items(), 1):
            prompt += f"{i}. {instruction}\n"
        
        prompt += """

BYPASS SUCCESS INDICATORS:
✅ Application form fields are now visible (name, email, resume upload)
✅ URL changed to /apply or /application
✅ "Sign in" text is no longer prominently displayed

BYPASS FAILURE INDICATORS:
❌ Still showing password field as required
❌ "Create account" is the only option (no guest/skip option)
❌ Modal popup blocking entire page with no close button

If ALL bypass attempts fail:
- Report this as a login blocker (not your failure)
- Return done with success=False and impossible_task=True
"""
        
        return prompt


class LoginHandler:
    """
    Main handler coordinating login detection and bypass.
    """
    
    def __init__(self):
        self.detector = LoginDetector()
        self.bypass_handler = LoginBypassHandler()
    
    def check_and_handle_login(self, page_text: str, url: str) -> Tuple[bool, str, str]:
        """
        Check for login requirement and return bypass instructions if needed.
        
        Args:
            page_text: Current page text content
            url: Current URL
            
        Returns:
            (needs_bypass, platform, bypass_prompt)
        """
        requires_login, login_platform, reason = self.detector.detect_login_requirement(page_text, url)
        
        # Always detect platform from URL (even if no login detected)
        detected_platform = self.detector.detect_ats_platform(url) or ""
        
        if not requires_login:
            logger.info("✅ No login wall detected - proceeding with application")
            return False, detected_platform, ""
        
        logger.warning(f"🚫 {reason}")
        logger.info(f"   Preparing bypass strategies for {login_platform}...")
        
        bypass_prompt = self.bypass_handler.generate_bypass_prompt(login_platform, page_text)
        
        return True, login_platform, bypass_prompt
    
    def log_bypass_attempt(self, platform: str, success: bool):
        """Log the result of a bypass attempt."""
        if success:
            logger.info(f"✅ Successfully bypassed {platform} login wall")
        else:
            logger.warning(f"⚠️  Failed to bypass {platform} login - may be impossible task")


# Convenience function for quick integration
def detect_and_bypass_login(page_text: str, url: str) -> Tuple[bool, str, str]:
    """
    Quick function to detect login and get bypass instructions.
    
    Args:
        page_text: Current page text
        url: Current URL
        
    Returns:
        (needs_bypass, platform, bypass_prompt)
        
    Example:
        needs_bypass, platform, prompt = detect_and_bypass_login(page_text, url)
        if needs_bypass:
            # Inject prompt into agent instructions
            enhanced_prompt = base_prompt + "\\n\\n" + prompt
    """
    handler = LoginHandler()
    return handler.check_and_handle_login(page_text, url)
