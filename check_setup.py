"""
Pre-flight check script to verify everything is ready for batch processing.
"""

import json
import os
from pathlib import Path
import glob

def check_mark(condition):
    return "✅" if condition else "❌"

def preflight_check():
    """Run all pre-flight checks."""
    
    print("=" * 80)
    print("BATCH APPLICATION SYSTEM - PRE-FLIGHT CHECK")
    print("=" * 80)
    print()
    
    all_good = True
    
    # Check 1: company_list.json exists
    print("📋 Checking company_list.json...")
    company_list_path = Path("company_list.json")
    exists = company_list_path.exists()
    print(f"   {check_mark(exists)} Company list file exists")
    
    if exists:
        try:
            with open(company_list_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            count = len(companies)
            print(f"   ✅ Found {count} jobs to process")
            
            # Validate structure
            valid_jobs = 0
            for company in companies:
                if 'name' in company and 'apply_link' in company:
                    valid_jobs += 1
            
            if valid_jobs == count:
                print(f"   ✅ All {count} jobs have required fields (name, apply_link)")
            else:
                print(f"   ⚠️  Warning: {count - valid_jobs} jobs missing required fields")
                all_good = False
                
        except Exception as e:
            print(f"   ❌ Error reading company_list.json: {e}")
            all_good = False
    else:
        print("   ❌ company_list.json not found")
        all_good = False
    
    print()
    
    # Check 2: user_profile.json exists
    print("👤 Checking user_profile.json...")
    user_profile_path = Path("user_profile.json")
    exists = user_profile_path.exists()
    print(f"   {check_mark(exists)} User profile file exists")
    
    if exists:
        try:
            with open(user_profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Check key fields
            has_personal = 'personal_info' in profile
            has_email = profile.get('personal_info', {}).get('email')
            has_name = profile.get('personal_info', {}).get('full_name')
            
            print(f"   {check_mark(has_personal)} Has personal_info section")
            print(f"   {check_mark(has_name)} Has full name")
            print(f"   {check_mark(has_email)} Has email")
            
            if not (has_personal and has_email and has_name):
                all_good = False
                
        except Exception as e:
            print(f"   ❌ Error reading user_profile.json: {e}")
            all_good = False
    else:
        print("   ❌ user_profile.json not found")
        all_good = False
    
    print()
    
    # Check 3: form_responses.yaml exists
    print("📝 Checking form_responses.yaml...")
    form_responses_path = Path("form_responses.yaml")
    exists = form_responses_path.exists()
    print(f"   {check_mark(exists)} Form responses file exists")
    
    if not exists:
        print("   ⚠️  Optional but recommended for better form filling")
    
    print()
    
    # Check 4: generated_documents directory
    print("📄 Checking generated_documents...")
    docs_dir = Path("generated_documents")
    exists = docs_dir.exists()
    print(f"   {check_mark(exists)} Directory exists")
    
    if exists:
        # Check for resume files
        resume_files = glob.glob(str(docs_dir / "dilip_kumar_tc_resume_*.docx"))
        cover_letter_files = glob.glob(str(docs_dir / "dilip_kumar_tc_cover_letter_*.docx"))
        
        has_resume = len(resume_files) > 0
        has_cover_letter = len(cover_letter_files) > 0
        
        print(f"   {check_mark(has_resume)} Has resume files ({len(resume_files)} found)")
        print(f"   {check_mark(has_cover_letter)} Has cover letter files ({len(cover_letter_files)} found)")
        
        if not has_resume:
            print("   ⚠️  No resumes found - will need to generate on first run")
            print("   💡 Tip: Run without --skip-generation first, or it will fail")
    else:
        print("   ⚠️  Directory will be created automatically")
    
    print()
    
    # Check 5: logs directory
    print("📊 Checking logs...")
    logs_dir = Path("logs")
    exists = logs_dir.exists()
    print(f"   {check_mark(exists)} Logs directory {'exists' if exists else 'will be created'}")
    
    company_logs_dir = Path("logs/company_logs")
    exists = company_logs_dir.exists()
    print(f"   {check_mark(exists)} Company logs directory {'exists' if exists else 'will be created'}")
    
    print()
    
    # Check 6: Required Python files
    print("🐍 Checking Python scripts...")
    required_files = [
        "job_application_automation.py",
        "batch_apply.py",
        "view_summary.py"
    ]
    
    for filename in required_files:
        exists = Path(filename).exists()
        print(f"   {check_mark(exists)} {filename}")
        if not exists:
            all_good = False
    
    print()
    
    # Check 7: Dependencies (optional check)
    print("📦 Checking Python packages...")
    try:
        import browser_use
        print("   ✅ browser-use installed")
    except ImportError:
        print("   ❌ browser-use not installed")
        print("      Run: pip install -r requirements.txt")
        all_good = False
    
    try:
        import yaml
        print("   ✅ pyyaml installed")
    except ImportError:
        print("   ❌ pyyaml not installed")
        print("      Run: pip install -r requirements.txt")
        all_good = False
    
    try:
        import requests
        print("   ✅ requests installed")
    except ImportError:
        print("   ❌ requests not installed")
        print("      Run: pip install -r requirements.txt")
        all_good = False
    
    print()
    print("=" * 80)
    
    if all_good:
        print("✅ ALL CHECKS PASSED - Ready to start batch processing!")
        print()
        print("Next steps:")
        print("  1. Review company_list.json")
        print("  2. Run: python batch_apply.py --skip-generation")
        print("  3. Monitor progress (takes ~2-3 hours for 37 jobs)")
        print("  4. View results: python view_summary.py")
    else:
        print("⚠️  SOME CHECKS FAILED - Please fix the issues above")
        print()
        print("Common fixes:")
        print("  - Missing files: Create them from examples")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - No resumes: Run batch_apply.py without --skip-generation first")
    
    print("=" * 80)
    print()
    
    return all_good

if __name__ == "__main__":
    preflight_check()
