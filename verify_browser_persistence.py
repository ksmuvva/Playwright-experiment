"""
Test script to verify browser session persistence between command sequences.
"""
import asyncio

# Import only from the main experimental module to test the standalone code
import importlib.util
import sys

# Dynamically import from the experimental module
spec = importlib.util.spec_from_file_location("exp_module", "expiremental-new.py")
exp_module = importlib.util.module_from_spec(spec)
sys.modules["exp_module"] = exp_module
spec.loader.exec_module(exp_module)

# Get the PlaywrightMCPServer class
PlaywrightMCPServer = exp_module.PlaywrightMCPServer

async def test_browser_persistence():
    """Test whether the browser persists between multiple cleanup calls."""
    print("Starting browser persistence test...")
    
    # Start server
    server = PlaywrightMCPServer()
    await server.start()
    print("✅ Server started")
    
    # Get the browser object before cleanup
    if hasattr(server.tools_instance, "browser"):
        browser_id_before = id(server.tools_instance.browser)
        print(f"Browser ID before cleanup: {browser_id_before}")
    else:
        print("❌ Browser not initialized")
        return False
    
    # First cleanup - should preserve browser
    print("Performing first cleanup (should preserve browser)...")
    await server.stop(fully_exit=False)
    print("✅ First cleanup completed")
    
    # Check if browser still exists
    if hasattr(server.tools_instance, "browser") and server.tools_instance.browser:
        browser_id_after = id(server.tools_instance.browser)
        print(f"Browser ID after cleanup: {browser_id_after}")
        
        if browser_id_before == browser_id_after:
            print("✅ SUCCESS: Browser instance preserved between cleanups")
            success = True
        else:
            print("❌ FAIL: Browser instance changed (new browser created)")
            success = False
    else:
        print("❌ FAIL: Browser was closed after cleanup")
        success = False
    
    # Final full cleanup
    print("Performing final full cleanup...")
    await server.stop(fully_exit=True)
    print("✅ Final cleanup completed")
    
    return success

async def main():
    success = await test_browser_persistence()
    if success:
        print("\n✅ BROWSER PERSISTENCE FIX SUCCESSFUL! Browser sessions are now preserved between commands.")
    else:
        print("\n❌ BROWSER PERSISTENCE FIX FAILED. Browser sessions are still not being preserved.")

if __name__ == "__main__":
    asyncio.run(main())
