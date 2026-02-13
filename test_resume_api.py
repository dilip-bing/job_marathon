#!/usr/bin/env python3
"""Simple test of resume generation API"""

import requests
import time
from config import RESUME_API_KEY, RESUME_API_URL

print("\n" + "="*60)
print("TESTING RESUME GENERATION API")
print("="*60 + "\n")

# Check API key
if not RESUME_API_KEY:
    print("❌ ERROR: RESUME_API_KEY not set in .env file")
    print("   Add it to .env file: RESUME_API_KEY=your-key-here")
    exit(1)

# Test job description (from Alcon listing)
test_job_description = """
Embedded Software Engineering Intern
Alcon - Lake Forest, California

We are seeking a talented Embedded Software Engineering Intern to join our team.
The ideal candidate will have experience with C/C++, embedded systems, and RTOS.

Responsibilities:
- Develop and test embedded software for medical devices
- Collaborate with hardware engineers on system integration
- Write technical documentation and participate in code reviews

Requirements:
- Currently pursuing BS/MS in Computer Science, Computer Engineering, or related field
- Strong programming skills in C/C++
- Experience with embedded systems and microcontrollers
- GPA 3.5 or higher preferred
"""

print("Job Description:")
print("-" * 60)
print(test_job_description.strip())
print("-" * 60 + "\n")

print("Calling Resume API...\n")

start_time = time.time()

try:
    response = requests.post(
        f'{RESUME_API_URL}/api/v1/optimize',
        headers={'X-API-Key': RESUME_API_KEY},
        json={
            'job_description': test_job_description,
            'return_format': 'base64'
        },
        timeout=120  # 2 minutes timeout
    )
    
    duration = time.time() - start_time
    
    print(f"Response received in {duration:.1f} seconds")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS - Resume generated!")
        result = response.json()
        
        if 'resume_base64' in result:
            resume_data = result['resume_base64']
            print(f"   Resume size: {len(resume_data)} bytes (base64)")
        
        if 'cover_letter_base64' in result:
            cover_data = result['cover_letter_base64']
            print(f"   Cover letter size: {len(cover_data)} bytes (base64)")
        
        print(f"\n✅ API is WORKING and AWAKE")
        print(f"   Response time: {duration:.1f}s")
        
        if duration < 10:
            print(f"   ⚡ Fast response - server was already warm")
        elif duration < 30:
            print(f"   ✅ Good response - server is ready")
        else:
            print(f"   ⚠️  Slow response - server was cold starting")
        
    elif response.status_code == 401:
        print("\n❌ AUTHENTICATION FAILED - Invalid API key")
        print("   Check your RESUME_API_KEY environment variable")
        
    elif response.status_code == 422:
        print("\n❌ VALIDATION ERROR - Invalid request format")
        print(f"   Response: {response.text[:200]}")
        
    else:
        print(f"\n❌ UNEXPECTED STATUS: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    
except requests.exceptions.Timeout:
    duration = time.time() - start_time
    print(f"\n❌ TIMEOUT after {duration:.1f} seconds")
    print("   Server is sleeping or not responding")
    print("   This is normal for Render.com free tier")
    print("   The server may take 30-60 seconds to wake up")
    
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ CONNECTION ERROR: {e}")
    print("   Server may be down or unreachable")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "="*60 + "\n")
