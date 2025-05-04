#!/usr/bin/env python3
"""
Test Runner for Playwright Tools Tests
Runs all test scripts and collects results
"""
import sys
import os
import asyncio
import time
import importlib.util
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("playwright_test_runner")

# List of test modules to run
TEST_MODULES = [
    "test_broken_images",
    "test_drag_and_drop",
    "test_hovers",
    "test_dynamic_controls",
    "test_dropdown",
    "test_form_authentication",
    "test_frames",
    "test_context_menu",
    "test_horizontal_slider"
]

def get_test_function(module_name):
    """Import a test module and return its main test function"""
    try:
        # Construct the full path to the test module
        module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
        
        # Import the module dynamically
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the test function (assumed to start with "test_")
        for attr_name in dir(module):
            if attr_name.startswith("test_") and callable(getattr(module, attr_name)):
                return getattr(module, attr_name)
        
        raise AttributeError(f"No test function found in module {module_name}")
        
    except Exception as e:
        logger.error(f"Error importing test module {module_name}: {e}")
        return None

async def run_test(module_name):
    """Run a single test and return result"""
    logger.info(f"Running test: {module_name}")
    
    start_time = time.time()
    success = False
    error_message = None
    
    try:
        # Get the test function from the module
        test_func = get_test_function(module_name)
        if not test_func:
            raise ImportError(f"Could not load test function from {module_name}")
            
        # Run the test function
        await test_func()
        success = True
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error running test {module_name}: {e}")
        import traceback
        traceback.print_exc()
        success = False
        
    execution_time = time.time() - start_time
    
    return {
        "module": module_name,
        "success": success,
        "error": error_message,
        "execution_time": execution_time
    }

async def run_all_tests():
    """Run all tests and collect results"""
    results = []
    
    for module_name in TEST_MODULES:
        result = await run_test(module_name)
        results.append(result)
        
        # Add a small delay between tests to allow resources to be properly cleaned up
        await asyncio.sleep(2)
        
    return results

def print_test_summary(results):
    """Print a summary of the test results"""
    print("\n" + "="*60)
    print("PLAYWRIGHT TOOLS TEST SUMMARY")
    print("="*60)
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status} - {result['module']} ({result['execution_time']:.2f}s)")
        if not result["success"] and result["error"]:
            print(f"  Error: {result['error']}")
            
    successful_tests = sum(1 for r in results if r["success"])
    print("-"*60)
    print(f"Tests: {len(results)}, Passed: {successful_tests}, Failed: {len(results) - successful_tests}")
    print("="*60)

async def main():
    """Main function to run tests"""
    print(f"Starting Playwright Tools tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Running {len(TEST_MODULES)} test modules")
    
    results = await run_all_tests()
    print_test_summary(results)
    
    # Determine exit code
    all_passed = all(r["success"] for r in results)
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
