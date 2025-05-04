#!/usr/bin/env python3
"""
Test script for testing different formats with the playwright_evaluate method.
"""
import sys
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def test_evaluate_formats():
    """Test different script formats with playwright_evaluate."""
    from Tools import PlaywrightTools
    
    tools = None
    try:
        logger.info("Creating and initializing PlaywrightTools")
        tools = PlaywrightTools()
        await tools.initialize()
        
        logger.info("Verifying browser and page")
        browser_ok, page = await tools.verify_browser_page()
        if not browser_ok or not page:
            logger.error(f"Browser verification failed")
            return
            
        logger.info("Navigating to test page")
        await tools.playwright_navigate("https://example.com")
        
        # Test cases with different script formats
        test_cases = [
            {
                "name": "Simple property access",
                "script": "document.title",
                "expected_result_type": "string"
            },
            {
                "name": "Script with return statement",
                "script": "return document.title;",
                "expected_result_type": "string"
            },
            {
                "name": "Arrow function",
                "script": "() => document.title",
                "expected_result_type": "string" 
            },
            {
                "name": "Function with return",
                "script": "function() { return document.title; }",
                "expected_result_type": "string"
            },
            {
                "name": "DOM manipulation",
                "script": "document.body.style.backgroundColor = \"#f0f0f0\"; return \"changed\";",
                "expected_result_type": "string"
            },
            {
                "name": "Array operation",
                "script": "Array.from(document.querySelectorAll(\"p\")).map(p => p.textContent)",
                "expected_result_type": "array"
            }
        ]
        
        # Run each test case
        for i, test_case in enumerate(test_cases):
            logger.info(f"\nTEST CASE {i+1}: {test_case['name']}")
            logger.info(f"Script: {test_case['script']}")
            
            try:
                result = await tools.playwright_evaluate(test_case["script"])
                logger.info(f"Status: {result['status']}")
                
                if result['status'] == 'success':
                    if 'result' in result:
                        result_type = type(result['result']).__name__
                        logger.info(f"Result type: {result_type} (expected: {test_case['expected_result_type']})")
                        logger.info(f"Result: {result['result']}")
                    else:
                        logger.warning("No 'result' field in response")
                else:
                    logger.error(f"Error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Exception: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info("\nAll tests completed")
        
    finally:
        logger.info("Cleaning up resources")
        if tools:
            try:
                await tools.cleanup_all()
                logger.info("Cleanup completed successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_evaluate_formats())
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        import traceback
        traceback.print_exc()
