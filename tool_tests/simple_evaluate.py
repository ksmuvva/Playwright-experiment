#!/usr/bin/env python3
"""
Simplified test script for testing the playwright_evaluate function.
"""
import sys
import os
import asyncio
import json

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_evaluate():
    """Test different cases of playwright_evaluate."""
    tools = None
    
    try:
        print("Initializing PlaywrightTools...")
        # Initialize the PlaywrightTools class properly
        tools = PlaywrightTools()
        await tools.initialize()  # Initialize using the class's own method
        
        # Verify browser and page are available
        print("Verifying browser and page...")
        browser_ok, page = await tools.verify_browser_page()
        if not browser_ok or not page:
            print("Failed to initialize browser and page")
            return
            
        print("Browser and page initialized successfully")
        
        # Navigate to a test page
        print("Navigating to test page...")
        await page.goto("https://example.com")
        
        print("Running playwright_evaluate test...")
        script = "document.title"
        result = await tools.playwright_evaluate(script)
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            print(f"Result: {result['result']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
            
        print("Test completed successfully!")
        
    finally:
        # Clean up resources
        print("\nCleaning up resources...")
        if tools and hasattr(tools, 'cleanup_all'):
            try:
                await tools.cleanup_all()
                print("Cleanup completed successfully")
            except Exception as e:
                print(f"Error during cleanup: {e}", file=sys.stderr)
        elif tools and hasattr(tools, 'browser') and tools.browser:
            try:
                await tools.browser.close()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Simple asyncio run with error handling
    try:
        print("Starting test_evaluate...")
        asyncio.run(test_evaluate())
    except Exception as e:
        print(f"Error in test: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
