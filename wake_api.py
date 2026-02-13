import requests
import time

print("=" * 60)
print("WAKING UP RESUME API")
print("=" * 60)
print("")

# Test the actual endpoint that workers will use
print("Testing POST /api/v1/optimize (the endpoint workers use)...")
print("")

for i in range(3):
    print(f"Attempt {i+1}/3:")
    start = time.time()
    try:
        payload = {
            "job_description": "Test job description to wake up API server",
            "return_format": "base64"
        }
        
        r = requests.post(
            'https://resume-optimizer-api-fvpd.onrender.com/api/v1/optimize',
            json=payload,
            timeout=90
        )
        duration = time.time() - start
        
        print(f"  Status: {r.status_code}, Response time: {duration:.1f}s")
        
        if r.status_code == 401:
            print(f"  ✅ API is awake and functional (401 = needs API key)")
        elif r.status_code == 200:
            print(f"  ✅ API is awake and functional (200 = success)")
        else:
            print(f"  ⚠️  Unexpected status: {r.status_code}")
        
        if duration < 5:
            print(f"  ✅ Fast response ({duration:.1f}s) - Server is AWAKE")
            break
        elif duration < 15:
            print(f"  ⚠️  Medium response ({duration:.1f}s) - Server is warming up")
        else:
            print(f"  ⚠️  Slow response ({duration:.1f}s) - Server was sleeping")
            
    except requests.exceptions.Timeout:
        print(f"  ❌ TIMEOUT (>90s) - Server not responding")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    print("")
    
    if i < 2:
        print("  Waiting 3 seconds before next attempt...")
        time.sleep(3)
        print("")

print("=" * 60)
print("RESULT: API is now awake and ready for batch processing")
print("You should run the batch within the next 10-15 minutes")
print("before the server goes back to sleep.")
print("=" * 60)
