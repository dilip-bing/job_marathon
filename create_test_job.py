"""
Test script to run ONLY ONE job to verify submission is working.
"""

import json
from pathlib import Path

def create_single_job_test():
    """Create a test file with just the first job."""
    
    # Load full company list
    with open("company_list.json", 'r', encoding='utf-8') as f:
        companies = json.load(f)
    
    # Take first job
    first_job = [companies[0]]
    
    # Save to test file
    test_file = Path("test_single_job.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(first_job, f, indent=2, ensure_ascii=False)
    
    print("=" * 80)
    print("✅ SINGLE JOB TEST FILE CREATED")
    print("=" * 80)
    print()
    print(f"Test file: {test_file}")
    print(f"Job: {first_job[0]['name']}")
    print(f"URL: {first_job[0]['apply_link']}")
    print()
    print("=" * 80)
    print("TO TEST SUBMISSION:")
    print("=" * 80)
    print()
    print("Run this command:")
    print("   python batch_apply.py --company-list test_single_job.json --skip-generation")
    print()
    print("⚠️  IMPORTANT: WATCH THE BROWSER WINDOW!")
    print()
    print("During execution, observe:")
    print("   1. ✅ Form gets filled with your information")
    print("   2. ✅ Files (resume/cover letter) get uploaded")
    print("   3. ✅ Submit/Apply button gets CLICKED")
    print("   4. ✅ Confirmation/Thank you page appears")
    print()
    print("If you see all 4 steps, submissions are working! ✅")
    print("If Submit button is NOT clicked, let me know! ❌")
    print()
    print("After test, check your email for application confirmation.")
    print()
    print("=" * 80)

if __name__ == "__main__":
    create_single_job_test()
