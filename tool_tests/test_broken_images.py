#!/usr/bin/env python3
"""
Test script for Prompt 4: Broken Images
This test validates the playwright_evaluate tool for checking broken images
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_broken_images():
    """Test the Broken Images prompt using the playwright_evaluate tool"""
    tools = None
    
    try:
        print("Initializing PlaywrightTools...")
        tools = PlaywrightTools()
        await tools.initialize()
        
        # Verify browser and page are available
        print("Verifying browser and page...")
        browser_ok, page = await tools.verify_browser_page()
        if not browser_ok or not page:
            print("❌ Failed to initialize browser and page")
            return
            
        print("✅ Browser and page initialized successfully")
        
        # STEP 1: Navigate to the broken images page
        print("\n📌 Navigating to broken images page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/broken_images")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Use playwright_evaluate to check all images on the page
        print("\n📌 Evaluating image status...")
        script = """() => { 
            return Array.from(document.querySelectorAll('img')).map(img => { 
                return { 
                    src: img.src, 
                    broken: img.naturalWidth === 0,
                    alt: img.alt || 'No alt text',
                    dimensions: img.naturalWidth ? `${img.naturalWidth}x${img.naturalHeight}` : 'Unknown'
                }; 
            });
        }"""
        
        result = await tools.playwright_evaluate(script)
        
        if result["status"] != "success":
            print(f"❌ Failed to evaluate images: {result['message']}")
            return
            
        # STEP 3: Process and display results
        print("\n📊 Image Analysis Results:")
        images = result["result"]
        working_images = [img for img in images if not img["broken"]]
        broken_images = [img for img in images if img["broken"]]
        
        print(f"✅ Working images: {len(working_images)}")
        for i, img in enumerate(working_images):
            print(f"  {i+1}. {img['src']} - {img['dimensions']}")
            
        print(f"❌ Broken images: {len(broken_images)}")
        for i, img in enumerate(broken_images):
            print(f"  {i+1}. {img['src']}")
        
        # STEP 4: Take a screenshot for verification
        print("\n📌 Taking screenshot...")
        screenshot_result = await tools.playwright_screenshot(filename="broken_images_test.png")
        if screenshot_result["status"] != "success":
            print(f"❌ Failed to take screenshot: {screenshot_result['message']}")
        else:
            print(f"✅ Screenshot saved: {screenshot_result.get('path', 'Unknown path')}")
            
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up resources
        print("\nCleaning up resources...")
        if tools:
            try:
                await tools.cleanup_all()
                print("✅ Cleanup completed successfully")
            except Exception as e:
                print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    print("Starting Broken Images test...")
    asyncio.run(test_broken_images())
