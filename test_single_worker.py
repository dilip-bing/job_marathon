#!/usr/bin/env python3
"""Test a single worker to diagnose hanging issue."""

import asyncio
import json
from job_worker import JobWorker

# Test data
job_data = {
    "name": "Smith+Nephew - Software/Electrical R&D Intern",
    "apply_link": "https://smithnephew.wd5.myworkdayjobs.com/en-US/External/job/Andover-MA/R-D-Intern--Software-Electrical--Andover--MA-_R87990",
    "date_posted": "Feb 07"
}

config = {
    "skip_generation": True,  # Use skip mode to test faster
    "headless": True,
    "timeout_minutes": 30
}

async def main():
    """Run a single worker."""
    worker = JobWorker(job_data, config, job_index=0)
    worker.setup_logging()
    
    print("=" * 80)
    print("STARTING WORKER TEST")
    print("=" * 80)
    
    result = await worker.run()
    
    print("\n" + "=" * 80)
    print("WORKER RESULT:")
    print(json.dumps(result, indent=2))
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(main())
