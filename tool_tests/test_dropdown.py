#!/usr/bin/env python3
"""
Test script for Prompt 11: Dropdown
This test validates the playwright_select tool functionality
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_dropdown():
    """Test the Dropdown prompt using the playwright_select tool"""
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
        
        # STEP 1: Navigate to the dropdown page
        print("\n📌 Navigating to dropdown page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/dropdown")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot before selection
        print("\n📌 Taking screenshot before dropdown selection...")
        before_screenshot = await tools.playwright_screenshot(filename="dropdown_before.png")
        if before_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {before_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {before_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Verify dropdown is present
        print("\n📌 Verifying dropdown exists...")
        dropdown_check = await tools.playwright_evaluate("""() => {
            const dropdown = document.getElementById('dropdown');
            return {
                exists: !!dropdown,
                isVisible: !!dropdown && window.getComputedStyle(dropdown).display !== 'none',
                options: dropdown ? Array.from(dropdown.options).map(opt => ({
                    value: opt.value,
                    text: opt.textContent,
                    selected: opt.selected
                })) : []
            };
        }""")
        
        if dropdown_check["status"] != "success":
            print(f"❌ Failed to check for dropdown: {dropdown_check['message']}")
            return
            
        if not dropdown_check["result"]["exists"] or not dropdown_check["result"]["isVisible"]:
            print("❌ Dropdown not found or not visible")
            return
            
        print("✅ Dropdown exists and is visible")
        print("🔍 Available options:")
        for option in dropdown_check["result"]["options"]:
            status = "✓ Selected" if option["selected"] else "□ Not selected"
            print(f"  - Value: '{option['value']}', Text: '{option['text']}' ({status})")
        
        # STEP 4: Select "Option 2" using playwright_select
        print("\n📌 Selecting 'Option 2' from dropdown...")
        select_result = await tools.playwright_select(selector="#dropdown", value="2")
        
        if select_result["status"] != "success":
            print(f"❌ Failed to select option: {select_result['message']}")
            return
            
        print("✅ Option selection successful")
        
        # STEP 5: Take a screenshot after selection
        print("\n📌 Taking screenshot after dropdown selection...")
        after_screenshot = await tools.playwright_screenshot(filename="dropdown_after.png")
        if after_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {after_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {after_screenshot.get('path', 'Unknown path')}")
        
        # STEP 6: Verify selected option with evaluate
        print("\n📌 Verifying selected option...")
        selection_check = await tools.playwright_evaluate("""() => {
            const dropdown = document.getElementById('dropdown');
            const selectedOption = dropdown.options[dropdown.selectedIndex];
            return {
                value: selectedOption.value,
                text: selectedOption.textContent,
                isOption2: selectedOption.value === '2' && selectedOption.textContent.trim() === 'Option 2'
            };
        }""")
        
        if selection_check["status"] != "success":
            print(f"❌ Failed to verify selection: {selection_check['message']}")
            return
            
        result = selection_check["result"]
        if result["isOption2"]:
            print(f"✅ Successfully selected Option 2 (value: {result['value']}, text: {result['text']})")
        else:
            print(f"❌ Failed to select Option 2. Current selection: value: {result['value']}, text: {result['text']}")
        
        print("\n✅ Dropdown test completed successfully!")
        
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
    print("Starting Dropdown test...")
    asyncio.run(test_dropdown())
