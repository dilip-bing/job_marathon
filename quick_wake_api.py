#!/usr/bin/env python3
"""Quick API wake-up - tries GET first, then POST"""

import requests
import time

print("\n🔔 Waking up Resume API...\n")

# Try 1: Simple GET to wake up server
print("Attempt 1: GET / (wake up server)")
start = time.time()
try:
    r = requests.get('https://resume-optimizer-api-fvpd.onrender.com', timeout=120)
    duration = time.time() - start
    print(f"✅ Server responded in {duration:.1f}s (Status: {r.status_code})")
except Exception as e:
    print(f"❌ Failed: {e}")

# Wait a bit
print("\nWaiting 5 seconds...\n")
time.sleep(5)

# Try 2: Test the actual endpoint
print("Attempt 2: POST /api/v1/optimize (test API)")
start = time.time()
try:
    r = requests.post(
        'https://resume-optimizer-api-fvpd.onrender.com/api/v1/optimize',
        json={"job_description": "Test", "return_format": "base64"},
        timeout=30
    )
    duration = time.time() - start
    print(f"✅ API responded in {duration:.1f}s (Status: {r.status_code})")
    
    if duration < 5:
        print(f"✅ READY - API is fully awake and fast ({duration:.1f}s)")
    else:
        print(f"⚠️  Still warming up ({duration:.1f}s)")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60)
print("Resume API wake-up complete!")
print("You can now run the batch within 10-15 minutes.")
print("="*60 + "\n")
