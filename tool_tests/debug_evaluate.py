#!/usr/bin/env python3
"""
Debug script for testing the playwright_evaluate method in PlaywrightTools.
"""
import sys
import os
import asyncio
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def test_evaluate_debug():
    """Debug the playwright_evaluate method in PlaywrightTools."""
    from Tools import PlaywrightTools
    
    tools = None
    try:
        logger.info("Creating PlaywrightTools instance")
        tools = PlaywrightTools()
        
        logger.info("Checking if the required methods are available")
        methods_to_check = [
            "initialize", 
            "verify_browser_page", 
            "playwright_navigate", 
            "playwright_evaluate"
        ]
        
        for method_name in methods_to_check:
            if hasattr(tools, method_name):
                logger.info(f"Method {method_name} is available ✅")
            else:
                logger.error(f"Method {method_name} is NOT available ❌")
                
        logger.info("Initializing Playwright (this may take a while)")
        try:
            await tools.initialize()
            logger.info("Playwright initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Playwright: {e}")
            traceback.print_exc()
            return
            
        logger.info("Attempting to verify browser and page")
        try:
            browser_ok, page = await tools.verify_browser_page()
            if browser_ok and page:
                logger.info("Browser and page verified successfully")
            else:
                logger.error(f"Browser verification failed: ok={browser_ok}, page={page}")
                return
        except Exception as e:
            logger.error(f"Error during browser verification: {e}")
            traceback.print_exc()
            return
            
        logger.info("Navigating to a test page")
        try:
            nav_result = await tools.playwright_navigate("https://example.com")
            logger.info(f"Navigation result: {nav_result}")
        except Exception as e:
            logger.error(f"Error during navigation: {e}")
            traceback.print_exc()
            
        logger.info("Testing playwright_evaluate")
        try:
            result = await tools.playwright_evaluate("document.title")
            logger.info(f"Evaluate result: {result}")
        except Exception as e:
            logger.error(f"Error during playwright_evaluate: {e}")
            traceback.print_exc()
            
    finally:
        logger.info("Cleaning up")
        if tools and hasattr(tools, "cleanup_all"):
            try:
                await tools.cleanup_all()
                logger.info("Cleanup completed successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    try:
        logger.info("Starting debug test")
        asyncio.run(test_evaluate_debug())
        logger.info("Test completed")
    except Exception as e:
        logger.error(f"Unhandled error in test: {e}")
        traceback.print_exc()
