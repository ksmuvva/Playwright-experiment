#!/usr/bin/env python3
"""
Direct test for playwright_evaluate function
"""
import sys
import os
import asyncio
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Tools import PlaywrightTools

async def test_direct_evaluate():
    """Directly test the playwright_evaluate function"""
    tools = PlaywrightTools()
    
    try:
        print(f"[{time.time()}] Initializing browser...")
        await tools.initialize()
        
        print(f"[{time.time()}] Navigating to example.com...")
        await tools.playwright_navigate("https://example.com")
        
        # Test the simplest possible evaluation
        print(f"[{time.time()}] Testing simple document.title evaluation...")
        result = await tools.playwright_evaluate("document.title")
        print(f"Result: {result}")
        
        if result.get("status") == "success":
            print("✅ TEST PASSED: Successfully executed evaluate!")
        else:
            print(f"❌ TEST FAILED: {result.get('message', 'Unknown error')}")
            
    finally:
        print(f"[{time.time()}] Cleaning up...")
        await tools.cleanup_all()
        print(f"[{time.time()}] Done!")

if __name__ == "__main__":
    print(f"[{time.time()}] Starting direct evaluate test...")
    asyncio.run(test_direct_evaluate())
    print(f"[{time.time()}] Test complete!")
