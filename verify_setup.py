"""
═══════════════════════════════════════════════════════════════════════════════
ENVIRONMENT VERIFICATION SCRIPT
═══════════════════════════════════════════════════════════════════════════════

Run this script to verify your environment is properly configured before
running the job application automation.

Author: Dilip Kumar
Date: February 11, 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import json
from pathlib import Path

print("═" * 80)
print("JOB APPLICATION AUTOMATION - ENVIRONMENT VERIFICATION")
print("═" * 80)
print()

# Track issues
issues = []
warnings = []

# ═══════════════════════════════════════════════════════════════════════════
# 1. Check Python Version
# ═══════════════════════════════════════════════════════════════════════════

print("1. Checking Python version...")
python_version = sys.version_info
if python_version.major >= 3 and python_version.minor >= 9:
    print(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
else:
    print(f"   ❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (need 3.9+)")
    issues.append("Python version too old (need 3.9+)")

# ═══════════════════════════════════════════════════════════════════════════
# 2. Check Required Packages
# ═══════════════════════════════════════════════════════════════════════════

print("2. Checking required packages...")
required_packages = [
    "browser_use",
    "playwright",
    "requests",
    "langchain",
]

for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
        print(f"   ✅ {package} installed")
    except ImportError:
        print(f"   ❌ {package} NOT installed")
        issues.append(f"Package '{package}' not installed")

# ═══════════════════════════════════════════════════════════════════════════
# 3. Check Configuration Files
# ═══════════════════════════════════════════════════════════════════════════

print("3. Checking configuration files...")

# Check user_profile.json
user_profile_path = Path("user_profile.json")
if user_profile_path.exists():
    print(f"   ✅ user_profile.json exists")
    
    # Validate JSON
    try:
        with open(user_profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        # Check required fields
        personal_info = profile.get("personal_info", {})
        if not personal_info.get("full_name"):
            warnings.append("user_profile.json: full_name is empty")
        if not personal_info.get("email"):
            warnings.append("user_profile.json: email is empty")
        if not personal_info.get("phone"):
            warnings.append("user_profile.json: phone is empty")
        
        print(f"   ✅ user_profile.json is valid JSON")
        print(f"      Name: {personal_info.get('full_name', 'NOT SET')}")
        print(f"      Email: {personal_info.get('email', 'NOT SET')}")
        
    except json.JSONDecodeError:
        print(f"   ❌ user_profile.json has invalid JSON")
        issues.append("user_profile.json contains invalid JSON")
        
else:
    print(f"   ❌ user_profile.json NOT found")
    issues.append("user_profile.json file missing")

# Check config.py
config_path = Path("config.py")
if config_path.exists():
    print(f"   ✅ config.py exists")
else:
    print(f"   ❌ config.py NOT found")
    issues.append("config.py file missing")

# ═══════════════════════════════════════════════════════════════════════════
# 4. Check API Keys
# ═══════════════════════════════════════════════════════════════════════════

print("4. Checking API configuration...")

try:
    import config
    
    if config.RESUME_API_KEY and config.RESUME_API_KEY != "YOUR_API_KEY_HERE":
        print(f"   ✅ Resume API key configured")
    else:
        print(f"   ❌ Resume API key NOT configured")
        issues.append("Resume API key not set in config.py")
    
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY != "YOUR_GEMINI_KEY_HERE":
        print(f"   ✅ Gemini API key configured")
    else:
        print(f"   ❌ Gemini API key NOT configured")
        issues.append("Gemini API key not set in config.py")
        
except ImportError:
    print(f"   ❌ Cannot import config.py")
    issues.append("config.py cannot be imported")

# ═══════════════════════════════════════════════════════════════════════════
# 5. Check Directories
# ═══════════════════════════════════════════════════════════════════════════

print("5. Checking directories...")

directories = [
    "generated_documents",
    "logs"
]

for dir_name in directories:
    dir_path = Path(dir_name)
    if dir_path.exists():
        print(f"   ✅ {dir_name}/ exists")
    else:
        print(f"   ⚠️  {dir_name}/ NOT found (will be created automatically)")
        warnings.append(f"{dir_name}/ directory will be auto-created")

# ═══════════════════════════════════════════════════════════════════════════
# 6. Test API Connection (Optional)
# ═══════════════════════════════════════════════════════════════════════════

print("6. Testing API connectivity...")

try:
    import requests
    
    # Test Resume API health
    try:
        print(f"   ⏳ Testing Resume API (may take up to 120 seconds on cold start)...")
        response = requests.get(
            "https://resume-optimizer-api-fvpd.onrender.com/health",
            timeout=120
        )
        if response.status_code == 200:
            print(f"   ✅ Resume API is reachable")
        else:
            print(f"   ⚠️  Resume API returned status {response.status_code}")
            warnings.append("Resume API might be having issues")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Cannot reach Resume API: {str(e)}")
        warnings.append("Resume API connection failed (check internet or cold start timeout)")
        
except ImportError:
    print(f"   ⚠️  Cannot test API (requests not installed)")

# ═══════════════════════════════════════════════════════════════════════════
# 7. Check Playwright
# ═══════════════════════════════════════════════════════════════════════════

print("7. Checking Playwright browsers...")

try:
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            browser.close()
            print(f"   ✅ Playwright browsers installed")
        except Exception as e:
            print(f"   ❌ Playwright browsers NOT installed")
            issues.append("Run: playwright install")
            
except Exception as e:
    print(f"   ⚠️  Cannot check Playwright: {str(e)}")
    warnings.append("Playwright check failed")

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

print()
print("═" * 80)
print("VERIFICATION SUMMARY")
print("═" * 80)

if not issues and not warnings:
    print("✅ ALL CHECKS PASSED!")
    print()
    print("Your environment is ready to run job application automation.")
    print()
    print("Next steps:")
    print("  1. Update user_profile.json with your information")
    print("  2. Set JOB_URL in job_application_automation.py")
    print("  3. Run: python job_application_automation.py")
    
elif issues:
    print("❌ CRITICAL ISSUES FOUND:")
    for issue in issues:
        print(f"   • {issue}")
    print()
    print("Please fix these issues before running the automation.")
    
if warnings:
    print()
    print("⚠️  WARNINGS:")
    for warning in warnings:
        print(f"   • {warning}")
    print()
    print("These are not critical but should be reviewed.")

print()
print("═" * 80)

# Exit with error code if there are critical issues
if issues:
    sys.exit(1)
else:
    sys.exit(0)
