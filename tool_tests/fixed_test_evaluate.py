#!/usr/bin/env python3
"""
Test script for testing the playwright_evaluate function with different return scenarios.
"""
import sys
import os
import asyncio
import json

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from playwright.async_api import async_playwright
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
        await page.goto("https://the-internet.herokuapp.com/broken_images")
        
        print('\n========== TEST 1: Script with leading "return" ==========')
        script1 = 'return Array.from(document.querySelectorAll("img")).map(img => { return { src: img.src, broken: img.naturalWidth === 0 }; });'
        print(f"Script: {script1}")
        result1 = await tools.playwright_evaluate(script1)
        print(f"Status: {result1['status']}")
        if "message" in result1:
            print(f"Message: {result1['message']}")
        
        # Format the result for better readability
        print("Results:")
        if result1["status"] == "success" and "result" in result1 and result1["result"] is not None:
            for i, img in enumerate(result1["result"]):
                print(f"  Image {i+1}: {img['src']} - {'Broken' if img['broken'] else 'OK'}")
        else:
            print(f"  No valid results: {result1.get('result', 'None')}")
        
        print('\n========== TEST 2: Script with array operation but no leading "return" ==========')
        script2 = 'Array.from(document.querySelectorAll("img")).map(img => { return { src: img.src, broken: img.naturalWidth === 0 }; });'
        print(f"Script: {script2}")
        result2 = await tools.playwright_evaluate(script2)
        print(f"Status: {result2['status']}")
        if "message" in result2:
            print(f"Message: {result2['message']}")
        
        # Format the result for better readability
        print("Results:")
        if result2["status"] == "success" and "result" in result2 and result2["result"] is not None:
            for i, img in enumerate(result2["result"]):
                print(f"  Image {i+1}: {img['src']} - {'Broken' if img['broken'] else 'OK'}")
        else:
            print(f"  No valid results: {result2.get('result', 'None')}")
        
        print('\n========== TEST 3: Script with already wrapped function ==========')
        script3 = '() => { return Array.from(document.querySelectorAll("img")).map(img => { return { src: img.src, broken: img.naturalWidth === 0 }; }); }'
        print(f"Script: {script3}")
        result3 = await tools.playwright_evaluate(script3)
        print(f"Status: {result3['status']}")
        if "message" in result3:
            print(f"Message: {result3['message']}")
        
        # Format the result for better readability
        print("Results:")
        if result3["status"] == "success" and "result" in result3 and result3["result"] is not None:
            for i, img in enumerate(result3["result"]):
                print(f"  Image {i+1}: {img['src']} - {'Broken' if img['broken'] else 'OK'}")
        else:
            print(f"  No valid results: {result3.get('result', 'None')}")
        
        print("\nAll tests completed successfully!")
        
    finally:
        # Clean up resources
        print("\nCleaning up resources...")
        if tools:
            try:
                await tools.cleanup_all()  # Use the class's own cleanup method
                print("Cleanup completed successfully")
            except Exception as e:
                print(f"Error during cleanup: {e}", file=sys.stderr)

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
