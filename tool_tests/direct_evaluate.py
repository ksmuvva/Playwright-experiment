#!/usr/bin/env python3
"""
Minimal test script for playwright_evaluate without using the Tools package.
"""
import sys
import os
import asyncio
from playwright.async_api import async_playwright

async def test_playwright_evaluate():
    """Test the playwright_evaluate functionality directly without using the Tools package."""
    playwright = None
    browser = None
    
    try:
        print("Starting Playwright...")
        playwright = await async_playwright().start()
        
        print("Launching browser...")
        browser = await playwright.chromium.launch(headless=False)
        
        print("Creating context and page...")
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to test page...")
        await page.goto("https://example.com")
        
        print("\nRunning evaluate test...")
        script = "document.title"
        result = await page.evaluate(script)
        print(f"Result: {result}")
        
        print("Test completed successfully!")
        
    finally:
        print("\nCleaning up resources...")
        if browser:
            try:
                await browser.close()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}", file=sys.stderr)
        if playwright:
            try:
                await playwright.stop()
                print("Playwright stopped successfully")
            except Exception as e:
                print(f"Error stopping playwright: {e}", file=sys.stderr)

if __name__ == "__main__":
    try:
        print("Starting test...")
        asyncio.run(test_playwright_evaluate())
    except Exception as e:
        print(f"Error in test: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
