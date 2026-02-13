import requests
import time

print("Testing Resume API...")
print("URL: https://resume-optimizer-api-fvpd.onrender.com")
print("")

# Test 1: Simple GET request to wake up server
print("Test 1: Waking up server (GET /)...")
start = time.time()
try:
    r = requests.get('https://resume-optimizer-api-fvpd.onrender.com', timeout=60)
    duration = time.time() - start
    print(f'✅ API is UP! Status: {r.status_code}, Response time: {duration:.1f}s')
    if duration > 15:
        print(f'⚠️  Long response time ({duration:.1f}s) - Server was sleeping (cold start)')
except requests.exceptions.Timeout:
    print('❌ API TIMEOUT (>60s) - Server is sleeping or overloaded')
except Exception as e:
    print(f'❌ API ERROR: {e}')

print("")

# Test 2: Check API endpoint
print("Test 2: Testing API optimize endpoint (POST /api/v1/optimize)...")
start = time.time()
try:
    payload = {
        "job_description": "Test job description for API health check",
        "return_format": "base64"
    }
    
    # Note: This will fail without API key, but we can see if it responds
    r = requests.post(
        'https://resume-optimizer-api-fvpd.onrender.com/api/v1/optimize',
        json=payload,
        timeout=60
    )
    duration = time.time() - start
    print(f'Response: Status {r.status_code}, Response time: {duration:.1f}s')
    
    if r.status_code == 401:
        print('✅ API is functional (returned 401 - authentication required)')
    elif r.status_code == 200:
        print('✅ API is functional (returned 200 - success)')
    else:
        print(f'⚠️  API returned unexpected status: {r.status_code}')
        print(f'Response: {r.text[:200]}')
        
except requests.exceptions.Timeout:
    print('❌ API TIMEOUT (>60s) - Server is not responding')
except Exception as e:
    print(f'❌ API ERROR: {e}')

print("")
print("=" * 60)
print("Summary:")
print("If both tests show long response times (>15s), the API server")
print("was sleeping and took time to wake up (Render.com free tier).")
print("This causes workers to hang when multiple hit it simultaneously.")
print("=" * 60)
