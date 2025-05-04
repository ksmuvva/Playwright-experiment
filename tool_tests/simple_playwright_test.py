#!/usr/bin/env python3
"""
Simple test for Playwright tools initialization
"""
import sys
import os
import asyncio

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from Tools import PlaywrightTools
    print("Successfully imported PlaywrightTools")
except Exception as e:
    print(f"Error importing PlaywrightTools: {e}")
    sys.exit(1)

async def main():
    """Test PlaywrightTools initialization"""
    try:
        print("Creating PlaywrightTools instance...")
        tools = PlaywrightTools()
        
        print("Initializing browser...")
        await tools.initialize()
        
        print("Verifying browser and page...")
        browser_ok, page = await tools.verify_browser_page()
        print(f"Browser verification result: {browser_ok}")
        
        if browser_ok and page:
            print("Browser and page are ready!")
            
            # Try a simple navigation
            print("Testing navigation...")
            await tools.playwright_navigate("https://example.com")
            print("Navigation successful!")
            
            # Try a simple evaluation 
            print("Testing evaluate...")
            result = await tools.playwright_evaluate("document.title")
            print(f"Evaluate result: {result}")
        
        # Clean up
        print("Cleaning up...")
        await tools.cleanup_all()
        print("Cleanup complete!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting simple Playwright test...")
    asyncio.run(main())
    print("Test complete!")
