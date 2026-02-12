"""
Test screenshot capture methods to identify which approach works with browser-use.
"""
import asyncio
from pathlib import Path
from datetime import datetime
from browser_use import Browser, Agent, ChatGoogle
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup paths
SCREENSHOTS_DIR = Path(__file__).parent / "logs" / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)

async def test_screenshot_methods():
    """Test all screenshot capture methods."""
    print("=" * 80)
    print("SCREENSHOT CAPTURE TEST")
    print("=" * 80)
    print()
    
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
    browser = Browser(cross_origin_iframes=True)
    print("✅ Browser created")
    print()
    
    # Create simple navigation task
    test_url = "https://jobs.smartrecruiters.com/renesaselectronics/744000106536395-software-engineering-intern"
    task = f"Navigate to {test_url} and wait 2 seconds"
    
    print(f"🎯 Task: {task}")
    print()
    
    # Create agent
    print("🤖 Creating agent...")
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser
    )
    print("✅ Agent created")
    print()
    
    # Run agent
    print("▶️  Running agent...")
    result = await agent.run()
    print("✅ Agent completed")
    print()
    
    # Now test screenshot capture methods
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 80)
    print("TESTING SCREENSHOT METHODS")
    print("=" * 80)
    print()
    
    # Method 1: agent.browser
    print("📸 Method 1: agent.browser.context.pages")
    try:
        if hasattr(agent, 'browser'):
            if hasattr(agent.browser, 'context') and agent.browser.context:
                pages = agent.browser.context.pages
                if pages and len(pages) > 0:
                    current_page = pages[-1]
                    screenshot_path = SCREENSHOTS_DIR / f"method1_{timestamp}.png"
                    await current_page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"✅ SUCCESS: {screenshot_path}")
                    print(f"   File size: {screenshot_path.stat().st_size} bytes")
                else:
                    print("❌ FAILED: No pages found")
            else:
                print("❌ FAILED: No context attribute or context is None")
        else:
            print("❌ FAILED: Agent has no browser attribute")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Method 2: browser.contexts
    print("📸 Method 2: browser.contexts[0].pages")
    try:
        if hasattr(browser, 'contexts'):
            contexts = browser.contexts
            if contexts and len(contexts) > 0:
                pages = contexts[0].pages
                if pages and len(pages) > 0:
                    current_page = pages[-1]
                    screenshot_path = SCREENSHOTS_DIR / f"method2_{timestamp}.png"
                    await current_page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"✅ SUCCESS: {screenshot_path}")
                    print(f"   File size: {screenshot_path.stat().st_size} bytes")
                else:
                    print("❌ FAILED: No pages in context")
            else:
                print("❌ FAILED: No contexts found")
        else:
            print("❌ FAILED: Browser has no contexts attribute")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Method 3: browser.context (singular)
    print("📸 Method 3: browser.context.pages")
    try:
        if hasattr(browser, 'context'):
            if browser.context:
                pages = browser.context.pages
                if pages and len(pages) > 0:
                    current_page = pages[-1]
                    screenshot_path = SCREENSHOTS_DIR / f"method3_{timestamp}.png"
                    await current_page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"✅ SUCCESS: {screenshot_path}")
                    print(f"   File size: {screenshot_path.stat().st_size} bytes")
                else:
                    print("❌ FAILED: No pages found")
            else:
                print("❌ FAILED: browser.context is None")
        else:
            print("❌ FAILED: Browser has no context attribute")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Method 4: Direct playwright access
    print("📸 Method 4: browser.playwright_browser.contexts")
    try:
        if hasattr(browser, 'playwright_browser'):
            pw_browser = browser.playwright_browser
            if pw_browser:
                contexts = pw_browser.contexts
                if contexts and len(contexts) > 0:
                    pages = contexts[0].pages
                    if pages and len(pages) > 0:
                        current_page = pages[-1]
                        screenshot_path = SCREENSHOTS_DIR / f"method4_{timestamp}.png"
                        await current_page.screenshot(path=str(screenshot_path), full_page=True)
                        print(f"✅ SUCCESS: {screenshot_path}")
                        print(f"   File size: {screenshot_path.stat().st_size} bytes")
                    else:
                        print("❌ FAILED: No pages found")
                else:
                    print("❌ FAILED: No contexts found")
            else:
                print("❌ FAILED: playwright_browser is None")
        else:
            print("❌ FAILED: Browser has no playwright_browser attribute")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    print()
    
    # Debug: Print browser object structure
    print("=" * 80)
    print("DEBUG: Browser Object Structure")
    print("=" * 80)
    print()
    print(f"browser type: {type(browser)}")
    print(f"browser attributes: {dir(browser)}")
    print()
    if hasattr(agent, 'browser'):
        print(f"agent.browser type: {type(agent.browser)}")
        print(f"agent.browser attributes: {dir(agent.browser)}")
    print()
    
    # Close browser
    print("🛑 Closing browser...")
    await browser.close()
    print("✅ Browser closed")
    print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_screenshot_methods())
