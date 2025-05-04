#!/usr/bin/env python3
"""
Simple test for Playwright evaluate functionality
"""
import sys
import os
import asyncio
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from Tools import PlaywrightTools
    print("Successfully imported PlaywrightTools")
except Exception as e:
    print(f"Error importing PlaywrightTools: {e}")
    sys.exit(1)

async def main():
    """Test PlaywrightTools evaluate functionality"""
    tools = None
    
    try:
        print(f"[{time.time()}] Creating PlaywrightTools instance...")
        tools = PlaywrightTools()
        
        print(f"[{time.time()}] Initializing browser...")
        await tools.initialize()
        
        print(f"[{time.time()}] Verifying browser and page...")
        browser_ok, page = await tools.verify_browser_page()
        print(f"[{time.time()}] Browser verification result: {browser_ok}")
        
        if not browser_ok or not page:
            print("Browser verification failed!")
            return
            
        # Try a simple navigation
        print(f"[{time.time()}] Testing navigation...")
        await tools.playwright_navigate("https://example.com")
        print(f"[{time.time()}] Navigation successful!")
        
        # Test evaluate with a simple string return
        print(f"[{time.time()}] Testing evaluate with string return...")
        script1 = "return document.title;"
        print(f"Script: {script1}")
        result1 = await tools.playwright_evaluate(script1)
        print(f"Result: {result1}")
        
        # Test evaluate without return keyword
        print(f"[{time.time()}] Testing evaluate without return keyword...")
        script2 = "document.title"
        print(f"Script: {script2}")
        result2 = await tools.playwright_evaluate(script2)
        print(f"Result: {result2}")
        
        # Test evaluate with function wrapping
        print(f"[{time.time()}] Testing evaluate with function wrapper...")
        script3 = "() => { return document.title; }"
        print(f"Script: {script3}")
        result3 = await tools.playwright_evaluate(script3)
        print(f"Result: {result3}")
        
        print(f"[{time.time()}] All tests completed successfully!")
        
    except Exception as e:
        print(f"[{time.time()}] Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if tools:
            print(f"[{time.time()}] Cleaning up...")
            try:
                await tools.cleanup_all()
                print(f"[{time.time()}] Cleanup complete!")
            except Exception as e:
                print(f"[{time.time()}] Error during cleanup: {e}")

if __name__ == "__main__":
    print(f"[{time.time()}] Starting simple Playwright test...")
    asyncio.run(main())
    print(f"[{time.time()}] Test complete!")
