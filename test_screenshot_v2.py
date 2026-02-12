"""
Test screenshot capture methods with browser-use library
This script tests the correct methods available on BrowserSession
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from browser_use import Agent, Browser, ChatGoogle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "logs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def test_screenshot_methods():
    """Test different screenshot capture methods"""
    
    print("=" * 80)
    print("SCREENSHOT CAPTURE TEST - BrowserSession Methods")
    print("=" * 80)
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize LLM
    print("🔧 Initializing Gemini LLM...")
    llm = ChatGoogle(
        model="gemini-3-flash-preview",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    print("✅ LLM initialized")
    print()
    
    # Create browser
    print("🌐 Creating browser instance...")
    browser = Browser()
    print("✅ Browser created")
    print()
    
    # Create and run agent
    TASK = "Navigate to https://jobs.smartrecruiters.com/renesaselectronics/744000106536395 and wait 2 seconds"
    print(f"🎯 Task: {TASK}")
    
    print("🤖 Creating agent...")
    agent = Agent(task=TASK, llm=llm, browser=browser)
    print("✅ Agent created")
    print()
    
    print("▶️  Running agent...")
    result = await agent.run()
    print("✅ Agent completed  ")
    print()
    
    # ========================================================================
    # Testing screenshot methods - Using Playwright pages before browser reset
    # CRITICAL: Must use browser.new_page() to get Playwright Page objects
    # ========================================================================
    
    print("=" * 80)
    print("TESTING BROWSER SESSION SCREENSHOT METHODS")
    print("=" * 80)
    print()
    
    # Method 1: Create new page and navigate
    print("📸 Method 1: browser.new_page() + navigate + screenshot")
    try:
        page = await browser.new_page()
        await page.goto("https://jobs.smartrecruiters.com/renesaselectronics/744000106536395", 
                       wait_until='domcontentloaded', timeout=30000)
        screenshot_path = SCREENSHOTS_DIR / f"method1_new_page_{timestamp}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        await page.close()
        print(f"✅ SUCCESS: {screenshot_path}")
        print(f"   File size: {screenshot_path.stat().st_size} bytes")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Method 2: browser.take_screenshot() - Direct method
    print("📸 Method 2: browser.take_screenshot()")
    try:
        screenshot_bytes = await browser.take_screenshot()
        if screenshot_bytes:
            screenshot_path = SCREENSHOTS_DIR / f"method2_take_screenshot_{timestamp}.png"
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot_bytes)
            print(f"✅ SUCCESS: {screenshot_path}")
            print(f"   File size: {screenshot_path.stat().st_size} bytes")
        else:
            print("❌ FAILED: take_screenshot() returned no data")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Method 3: Get current page from browser context (what the main code tries)
    print("📸 Method 3: Access pages from browser internals")
    try:
        # This is what job_application_automation.py tries
        current_page = None
        
        # Check if browser has contexts (Playwright style)
        if hasattr(browser, '_playwright_browser') or hasattr(browser, 'playwright_browser'):
            pw_browser = getattr(browser, '_playwright_browser', getattr(browser, 'playwright_browser', None))
            if pw_browser:
                contexts = pw_browser.contexts
                if contexts:
                    pages = contexts[0].pages
                    if pages:
                        current_page = pages[-1]
                        print(f"   Found page through playwright_browser.contexts")
        
        if current_page:
            screenshot_path = SCREENSHOTS_DIR / f"method3_pw_contexts_{timestamp}.png"
            await current_page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"✅ SUCCESS: {screenshot_path}")
            print(f"   File size: {screenshot_path.stat().st_size} bytes")
        else:
            print("❌ FAILED: Could not access playwright browser contexts")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Close browser properly
    print("🛑 Closing browser...")
    await browser.stop()
    print("✅ Browser closed")
    print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    
    # Summary
    print("📊 SUMMARY:")
    print("Check the logs/screenshots/ directory for generated screenshots")
    screenshots = list(SCREENSHOTS_DIR.glob(f"*{timestamp}*.png"))
    print(f"Screenshots found: {len(screenshots)}")
    for ss in screenshots:
        print(f"  - {ss.name} ({ss.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(test_screenshot_methods())
