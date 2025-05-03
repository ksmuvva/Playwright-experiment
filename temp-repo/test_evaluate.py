#!/usr/bin/env python3
"""
Test script for testing the playwright_evaluate function with different return scenarios.
"""
import sys
import asyncio
import json
from playwright.async_api import async_playwright
from exp_tools import PlaywrightTools

async def test_evaluate():
    """Test different cases of playwright_evaluate."""
    pw = None
    tools = None
    
    try:
        pw = await async_playwright().start()
        
        # Initialize our PlaywrightTools with the existing playwright instance
        tools = PlaywrightTools()
        tools.playwright = pw  # Set the playwright property
        
        # Set up a browser and page
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Store the resources in the tools object
        tools.browser = browser
        tools.context = context
        tools.pages = [page]
        tools.browser_initialized = True
        
        # Navigate to a test page
        await page.goto("https://the-internet.herokuapp.com/broken_images")
        
        print("\n========== TEST 1: Script with leading 'return' ==========")
        script1 = "return Array.from(document.querySelectorAll('img')).map(img => { return { src: img.src, broken: img.naturalWidth === 0 }; });"
        print(f"Script: {script1}")
        result1 = await tools.playwright_evaluate(script1)
        print(f"Status: {result1['status']}")
        print(f"Message: {result1['message']}")
        
        # Format the result for better readability
        print("Results:")
        if result1['status'] == 'success' and result1['result'] is not None:
            for i, img in enumerate(result1['result']):
                print(f"  Image {i+1}: {img['src']} - {'Broken' if img['broken'] else 'OK'}")
        else:
            print(f"  No valid results: {result1.get('result', 'None')}")
        
        print("\n========== TEST 2: Script with array operation but no leading 'return' ==========")
        script2 = "Array.from(document.querySelectorAll('img')).map(img => { return { src: img.src, broken: img.naturalWidth === 0 }; });"
        print(f"Script: {script2}")
        result2 = await tools.playwright_evaluate(script2)
        print(f"Status: {result2['status']}")
        print(f"Message: {result2['message']}")
        
        # Format the result for better readability
        print("Results:")
        if result2['status'] == 'success' and result2['result'] is not None:
            for i, img in enumerate(result2['result']):
                print(f"  Image {i+1}: {img['src']} - {'Broken' if img['broken'] else 'OK'}")
        else:
            print(f"  No valid results: {result2.get('result', 'None')}")
        
        print("\n========== TEST 3: Script with already wrapped function ==========")
        script3 = "() => { return Array.from(document.querySelectorAll('img')).map(img => { return { src: img.src, broken: img.naturalWidth === 0 }; }); }"
        print(f"Script: {script3}")
        result3 = await tools.playwright_evaluate(script3)
        print(f"Status: {result3['status']}")
        print(f"Message: {result3['message']}")
        
        # Format the result for better readability
        print("Results:")
        if result3['status'] == 'success' and result3['result'] is not None:
            for i, img in enumerate(result3['result']):
                print(f"  Image {i+1}: {img['src']} - {'Broken' if img['broken'] else 'OK'}")
        else:
            print(f"  No valid results: {result3.get('result', 'None')}")
        
        print("\nAll tests completed successfully!")
    finally:
        # Clean up resources
        if tools and hasattr(tools, 'cleanup'):
            try:
                await tools.cleanup()
            except Exception as e:
                print(f"Error during cleanup: {e}", file=sys.stderr)
        if pw:
            try:
                await pw.stop()
            except Exception as e:
                print(f"Error stopping playwright: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Simple asyncio run with error handling
    try:
        asyncio.run(test_evaluate())
    except Exception as e:
        print(f"Error in test: {e}", file=sys.stderr)
        sys.exit(1) 