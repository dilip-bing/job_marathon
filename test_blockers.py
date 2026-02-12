"""
Test suite for login_handler.py and blocker_handler.py

This file contains comprehensive test cases for all blocker types and
all ATS platform detections. Run this before integrating into main code.

Author: Dilip Kumar
Date: February 12, 2026
"""

from login_handler import detect_and_bypass_login, LoginHandler, LoginDetector
from blocker_handler import check_for_blockers, BlockerType, BlockerDetector

# ═══════════════════════════════════════════════════════════════════════════
# BLOCKER DETECTION TEST CASES
# ═══════════════════════════════════════════════════════════════════════════

def test_email_verification_blocker():
    """Test Case 1: Email Verification Detection"""
    print("\n🧪 Test 1: Email Verification Blocker")
    
    test_cases = [
        """
        To continue, please enter the 8-character verification code 
        that was sent to your email address.
        """,
        """
        We've sent a verification code to your email. Please check your 
        inbox and enter the code below to proceed.
        """,
        """
        Verify your email address by entering the code we just sent you.
        """
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == True, f"Email verification #{i} not detected"
        assert blocker_type == BlockerType.EMAIL_VERIFICATION, f"Wrong blocker type #{i}"
        assert is_impossible == True, f"Should be impossible #{i}"
        print(f"  ✅ Email verification variant #{i} detected correctly")
    
    print("  ✅ ALL Email verification tests passed")


def test_captcha_blocker():
    """Test Case 2: CAPTCHA Detection"""
    print("\n🧪 Test 2: CAPTCHA Blocker")
    
    test_cases = [
        "Please verify you're not a robot by completing the reCAPTCHA below.",
        "Complete the CAPTCHA challenge to continue.",
        "I'm not a robot checkbox required.",
        "Verify you are human by solving the CAPTCHA."
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == True, f"CAPTCHA #{i} not detected"
        assert blocker_type == BlockerType.CAPTCHA, f"Wrong blocker type #{i}"
        assert is_impossible == True, f"Should be impossible #{i}"
        print(f"  ✅ CAPTCHA variant #{i} detected correctly")
    
    print("  ✅ ALL CAPTCHA tests passed")


def test_expired_job_blocker():
    """Test Case 3: Expired Job Detection"""
    print("\n🧪 Test 3: Expired Job Blocker")
    
    test_cases = [
        "This job has expired and is no longer accepting applications.",
        "Sorry, this position is no longer available.",
        "The job posting you are looking for has been removed.",
        "This opportunity is no longer accepting applications."
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == True, f"Expired job #{i} not detected"
        assert blocker_type == BlockerType.EXPIRED_JOB, f"Wrong blocker type #{i}"
        assert is_impossible == True, f"Should be impossible #{i}"
        print(f"  ✅ Expired job variant #{i} detected correctly")
    
    print("  ✅ ALL Expired job tests passed")


def test_phone_verification_blocker():
    """Test Case 4: Phone Verification Detection"""
    print("\n🧪 Test 4: Phone Verification Blocker")
    
    test_cases = [
        "Please verify your phone number by entering the SMS code we sent you.",
        "Enter the 6-digit code sent to your mobile phone.",
        "Verify your phone number to continue with your application."
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == True, f"Phone verification #{i} not detected"
        assert blocker_type == BlockerType.PHONE_VERIFICATION, f"Wrong blocker type #{i}"
        assert is_impossible == True, f"Should be impossible #{i}"
        print(f"  ✅ Phone verification variant #{i} detected correctly")
    
    print("  ✅ ALL Phone verification tests passed")


def test_video_interview_blocker():
    """Test Case 5: Video Interview Detection (Soft Blocker)"""
    print("\n🧪 Test 5: Video Interview Blocker (Soft)")
    
    test_cases = [
        "This position requires a HireVue video interview as part of the application.",
        "You will be asked to record video responses to interview questions.",
        "One-way video interview required for this role."
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == False, f"Video interview #{i} should be soft blocker (not hard blocked)"
        # Soft blockers don't block, they just warn
        print(f"  ✅ Video interview variant #{i} correctly identified as soft blocker")
    
    print("  ✅ ALL Video interview tests passed")


def test_assessment_blocker():
    """Test Case 6: Assessment Detection (Soft Blocker)"""
    print("\n🧪 Test 6: Assessment Blocker (Soft)")
    
    test_cases = [
        "A coding challenge is required for this position.",
        "You will need to complete a technical assessment as part of this application.",
        "Skills assessment required before proceeding."
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == False, f"Assessment #{i} should be soft blocker"
        print(f"  ✅ Assessment variant #{i} correctly identified as soft blocker")
    
    print("  ✅ ALL Assessment tests passed")


def test_clean_page():
    """Test Case 7: Clean Page (No Blockers)"""
    print("\n🧪 Test 7: Clean Page (No Blockers)")
    
    test_cases = [
        """
        Please fill out the application form below.
        First Name: ___
        Last Name: ___
        Email: ___
        Phone: ___
        """,
        """
        Submit Your Application
        We're excited to learn more about you! Please complete all required fields.
        """,
        """
        Application Form
        All fields marked with * are required.
        """
    ]
    
    for i, page_text in enumerate(test_cases, 1):
        is_blocked, blocker_type, reason, is_impossible = check_for_blockers(
            page_text, "https://example.com"
        )
        
        assert is_blocked == False, f"Clean page #{i} should have no blockers"
        assert blocker_type.value == "none", f"Should be NONE blocker type #{i}"
        assert is_impossible == False, f"Should not be impossible #{i}"
        print(f"  ✅ Clean page #{i} correctly identified as blocker-free")
    
    print("  ✅ ALL Clean page tests passed")


# ═══════════════════════════════════════════════════════════════════════════
# LOGIN DETECTION TEST CASES
# ═══════════════════════════════════════════════════════════════════════════

def test_greenhouse_login_detection():
    """Test Case 8: Greenhouse Login Detection"""
    print("\n🧪 Test 8: Greenhouse Login Detection")
    
    test_cases = [
        {
            "page_text": "Sign in to continue your application. Already have an account? Log in",
            "url": "https://jobs.greenhouse.io/company/jobs/12345"
        },
        {
            "page_text": "Create an account or sign in to save your progress",
            "url": "https://job-boards.greenhouse.io/company/job"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"Greenhouse login #{i} not detected"
        assert platform == "greenhouse", f"Wrong platform #{i}: {platform}"
        assert len(bypass_prompt) > 0, f"Bypass prompt empty #{i}"
        assert "email" in bypass_prompt.lower() or "guest" in bypass_prompt.lower(), \
            f"Bypass prompt doesn't contain expected strategies #{i}"
        print(f"  ✅ Greenhouse variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL Greenhouse tests passed")


def test_workday_login_detection():
    """Test Case 9: Workday Login Detection"""
    print("\n🧪 Test 9: Workday Login Detection")
    
    test_cases = [
        {
            "page_text": "Sign in to save your progress and apply faster",
            "url": "https://company.wd5.myworkdayjobs.com/careers/job/12345"
        },
        {
            "page_text": "Create Account or Sign In to continue",
            "url": "https://example.wd1.myworkdayjobs.com/External"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"Workday login #{i} not detected"
        assert platform == "workday", f"Wrong platform #{i}: {platform}"
        assert "guest" in bypass_prompt.lower() or "skip" in bypass_prompt.lower(), \
            f"Bypass prompt doesn't contain expected strategies #{i}"
        print(f"  ✅ Workday variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL Workday tests passed")


def test_lever_login_detection():
    """Test Case 10: Lever Login Detection"""
    print("\n🧪 Test 10: Lever Login Detection")
    
    test_cases = [
        {
            "page_text": "Sign in to track your application status",
            "url": "https://jobs.lever.co/company/job-id"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"Lever login #{i} not detected"
        assert platform == "lever", f"Wrong platform #{i}: {platform}"
        print(f"  ✅ Lever variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL Lever tests passed")


def test_icims_login_detection():
    """Test Case 11: iCIMS Login Detection"""
    print("\n🧪 Test 11: iCIMS Login Detection")
    
    test_cases = [
        {
            "page_text": "Please log in to your career account",
            "url": "https://careers.company.com/jobs/12345"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"iCIMS login #{i} not detected"
        assert platform == "icims", f"Wrong platform #{i}: {platform}"
        print(f"  ✅ iCIMS variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL iCIMS tests passed")


def test_ashby_login_detection():
    """Test Case 12: Ashby Login Detection"""
    print("\n🧪 Test 12: Ashby Login Detection")
    
    test_cases = [
        {
            "page_text": "Sign in to continue with your application",
            "url": "https://jobs.ashbyhq.com/company/job-id"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"Ashby login #{i} not detected"
        assert platform == "ashby", f"Wrong platform #{i}: {platform}"
        print(f"  ✅ Ashby variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL Ashby tests passed")


def test_smartrecruiters_login_detection():
    """Test Case 13: SmartRecruiters Login Detection"""
    print("\n🧪 Test 13: SmartRecruiters Login Detection")
    
    test_cases = [
        {
            "page_text": "Create an account or sign in to apply",
            "url": "https://jobs.smartrecruiters.com/company/job-id"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"SmartRecruiters login #{i} not detected"
        assert platform == "smartrecruiters", f"Wrong platform #{i}: {platform}"
        print(f"  ✅ SmartRecruiters variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL SmartRecruiters tests passed")


def test_taleo_login_detection():
    """Test Case 14: Taleo Login Detection"""
    print("\n🧪 Test 14: Taleo Login Detection")
    
    test_cases = [
        {
            "page_text": "Sign in to your Taleo account",
            "url": "https://company.taleo.net/careersection/job"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"Taleo login #{i} not detected"
        assert platform == "taleo", f"Wrong platform #{i}: {platform}"
        print(f"  ✅ Taleo variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL Taleo tests passed")


def test_jobvite_login_detection():
    """Test Case 15: Jobvite Login Detection"""
    print("\n🧪 Test 15: Jobvite Login Detection")
    
    test_cases = [
        {
            "page_text": "Sign in to your Jobvite account to continue",
            "url": "https://jobs.jobvite.com/company/job"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == True, f"Jobvite login #{i} not detected"
        assert platform == "jobvite", f"Wrong platform #{i}: {platform}"
        print(f"  ✅ Jobvite variant #{i} detected with bypass strategies")
    
    print("  ✅ ALL Jobvite tests passed")


def test_no_login_required():
    """Test Case 16: No Login Required"""
    print("\n🧪 Test 16: No Login Required")
    
    test_cases = [
        {
            "page_text": "Please fill out the application form below. All fields are required.",
            "url": "https://example.com/careers/apply"
        },
        {
            "page_text": "Submit your application. We look forward to hearing from you!",
            "url": "https://jobs.example.com/job/12345"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        needs_bypass, platform, bypass_prompt = detect_and_bypass_login(
            test_case["page_text"], test_case["url"]
        )
        
        assert needs_bypass == False, f"False positive on clean page #{i}"
        assert platform == "", f"Should be empty string platform #{i}, got: {platform}"
        assert bypass_prompt == "", f"Should have empty bypass prompt #{i}"
        print(f"  ✅ Clean page #{i} correctly identified as no login required")
    
    print("  ✅ ALL No Login Required tests passed")


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TEST (Real-world Example)
# ═══════════════════════════════════════════════════════════════════════════

def test_real_world_scenario():
    """Test Case 17: Real-world Combined Scenario"""
    print("\n🧪 Test 17: Real-world Combined Scenario")
    
    # Scenario 1: Greenhouse job with email verification required
    page_text_1 = """
    Sign in to continue your application.
    
    Please enter the 8-character verification code sent to your email
    to verify your account.
    """
    url_1 = "https://jobs.greenhouse.io/company/job/12345"
    
    # Should detect blocker first (higher priority)
    is_blocked, blocker_type, reason, is_impossible = check_for_blockers(page_text_1, url_1)
    assert is_blocked == True
    assert blocker_type == BlockerType.EMAIL_VERIFICATION
    assert is_impossible == True
    print("  ✅ Scenario 1: Email verification blocker correctly prioritized over login detection")
    
    # Should still detect login (for logging purposes)
    needs_bypass, platform, bypass_prompt = detect_and_bypass_login(page_text_1, url_1)
    assert needs_bypass == True
    assert platform == "greenhouse"
    print("  ✅ Scenario 1: Login also detected but blocker takes precedence")
    
    # Scenario 2: Workday job with clean application form
    page_text_2 = """
    Application for Software Engineer
    
    Please complete the following information:
    * First Name
    * Last Name
    * Email Address
    * Phone Number
    * Resume (upload)
    """
    url_2 = "https://company.wd5.myworkdayjobs.com/careers/job/12345"
    
    is_blocked, blocker_type, reason, is_impossible = check_for_blockers(page_text_2, url_2)
    assert is_blocked == False
    print("  ✅ Scenario 2: Clean form correctly identified (no blockers)")
    
    needs_bypass, platform, bypass_prompt = detect_and_bypass_login(page_text_2, url_2)
    # Platform should be detected from URL even if no login wall in text
    assert platform == "workday"
    # But needs_bypass should be False since no login keywords in page text
    print(f"  ✅ Scenario 2: Platform detected as {platform}, bypass needed: {needs_bypass}")
    
    print("  ✅ ALL Real-world scenario tests passed")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """Run all test cases and report results."""
    print("=" * 80)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("Testing: login_handler.py and blocker_handler.py")
    print("=" * 80)
    
    tests = [
        # Blocker tests
        test_email_verification_blocker,
        test_captcha_blocker,
        test_expired_job_blocker,
        test_phone_verification_blocker,
        test_video_interview_blocker,
        test_assessment_blocker,
        test_clean_page,
        
        # Login detection tests
        test_greenhouse_login_detection,
        test_workday_login_detection,
        test_lever_login_detection,
        test_icims_login_detection,
        test_ashby_login_detection,
        test_smartrecruiters_login_detection,
        test_taleo_login_detection,
        test_jobvite_login_detection,
        test_no_login_required,
        
        # Integration test
        test_real_world_scenario,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  ❌ FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"  ❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nHandlers are working correctly and ready for integration!")
        print("\nNext steps:")
        print("1. Review INTEGRATION_GUIDE.py for integration instructions")
        print("2. Modify job_application_automation.py with handler calls")
        print("3. Update batch_apply.py to track blocker statistics")
        print("4. Run integration test with real job URLs")
        print("=" * 80)
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please review the failures above and fix before integrating.")
        print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
