#!/usr/bin/env python3
"""
Test script for Prompt 13: Dynamic Controls
This test validates multiple tools including click, fill, and waiting for dynamic elements
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_dynamic_controls():
    """Test the Dynamic Controls prompt using multiple tools"""
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
        
        # STEP 1: Navigate to the dynamic controls page
        print("\n📌 Navigating to dynamic controls page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/dynamic_controls")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot of the initial state
        print("\n📌 Taking screenshot of initial state...")
        initial_screenshot = await tools.playwright_screenshot(filename="dynamic_controls_initial.png")
        if initial_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {initial_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {initial_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Verify the checkbox is present
        print("\n📌 Verifying checkbox exists...")
        checkbox_check = await tools.playwright_evaluate("""() => {
            const checkbox = document.querySelector('#checkbox');
            return {
                exists: !!checkbox,
                isVisible: !!checkbox && window.getComputedStyle(checkbox).display !== 'none'
            };
        }""")
        
        if checkbox_check["status"] != "success":
            print(f"❌ Failed to check for checkbox: {checkbox_check['message']}")
            return
            
        if not checkbox_check["result"]["exists"] or not checkbox_check["result"]["isVisible"]:
            print("❌ Checkbox not found or not visible")
            return
            
        print("✅ Checkbox exists and is visible")
        
        # STEP 4: Click the Remove button
        print("\n📌 Clicking 'Remove' button...")
        remove_click = await tools.playwright_click(selector="button:has-text('Remove')")
        
        if remove_click["status"] != "success":
            print(f"❌ Failed to click Remove button: {remove_click['message']}")
            return
            
        print("✅ Clicked Remove button")
        
        # STEP 5: Wait for loading animation to disappear
        print("\n📌 Waiting for loading animation...")
        # Using evaluate to check when loading is complete
        for i in range(10):  # Try for a maximum of 10 seconds
            loading_check = await tools.playwright_evaluate("""() => {
                return document.querySelector('#loading') === null || 
                       window.getComputedStyle(document.querySelector('#loading')).display === 'none';
            }""")
            
            if loading_check["status"] == "success" and loading_check["result"]:
                print("✅ Loading completed")
                break
                
            await asyncio.sleep(1)
            print("⏳ Still loading...")
        else:
            print("⚠️ Loading did not complete within expected time")
        
        # STEP 6: Take a screenshot after checkbox removal
        print("\n📌 Taking screenshot after checkbox removal...")
        removed_screenshot = await tools.playwright_screenshot(filename="dynamic_controls_removed.png")
        if removed_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {removed_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {removed_screenshot.get('path', 'Unknown path')}")
        
        # STEP 7: Verify checkbox is gone
        checkbox_gone = await tools.playwright_evaluate("""() => {
            const checkbox = document.querySelector('#checkbox');
            return {
                exists: !!checkbox,
                isVisible: !!checkbox && window.getComputedStyle(checkbox).display !== 'none',
                message: document.querySelector('#message')?.textContent || 'No message'
            };
        }""")
        
        if checkbox_gone["status"] != "success":
            print(f"❌ Failed to check if checkbox is gone: {checkbox_gone['message']}")
        else:
            if not checkbox_gone["result"]["exists"] or not checkbox_gone["result"]["isVisible"]:
                print(f"✅ Checkbox successfully removed! Message: {checkbox_gone['result']['message']}")
            else:
                print("❌ Checkbox still exists and is visible")
        
        # STEP 8: Click Add button to bring back checkbox
        print("\n📌 Clicking 'Add' button...")
        add_click = await tools.playwright_click(selector="button:has-text('Add')")
        
        if add_click["status"] != "success":
            print(f"❌ Failed to click Add button: {add_click['message']}")
        else:
            print("✅ Clicked Add button")
        
        # STEP 9: Wait for loading animation to disappear again
        print("\n📌 Waiting for loading animation...")
        for i in range(10):  # Try for a maximum of 10 seconds
            loading_check = await tools.playwright_evaluate("""() => {
                return document.querySelector('#loading') === null || 
                       window.getComputedStyle(document.querySelector('#loading')).display === 'none';
            }""")
            
            if loading_check["status"] == "success" and loading_check["result"]:
                print("✅ Loading completed")
                break
                
            await asyncio.sleep(1)
            print("⏳ Still loading...")
        else:
            print("⚠️ Loading did not complete within expected time")
        
        # STEP 10: Take a screenshot after checkbox is added back
        print("\n📌 Taking screenshot after checkbox added back...")
        added_screenshot = await tools.playwright_screenshot(filename="dynamic_controls_added.png")
        if added_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {added_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {added_screenshot.get('path', 'Unknown path')}")
        
        # STEP 11: Check that the checkbox is back
        checkbox_back = await tools.playwright_evaluate("""() => {
            const checkbox = document.querySelector('#checkbox');
            return {
                exists: !!checkbox,
                isVisible: !!checkbox && window.getComputedStyle(checkbox).display !== 'none',
                message: document.querySelector('#message')?.textContent || 'No message'
            };
        }""")
        
        if checkbox_back["status"] != "success":
            print(f"❌ Failed to check if checkbox is back: {checkbox_back['message']}")
        else:
            if checkbox_back["result"]["exists"] and checkbox_back["result"]["isVisible"]:
                print(f"✅ Checkbox successfully added back! Message: {checkbox_back['result']['message']}")
            else:
                print("❌ Checkbox was not added back")
        
        # STEP 12: Enable the input field
        print("\n📌 Clicking 'Enable' button...")
        enable_click = await tools.playwright_click(selector="button:has-text('Enable')")
        
        if enable_click["status"] != "success":
            print(f"❌ Failed to click Enable button: {enable_click['message']}")
        else:
            print("✅ Clicked Enable button")
        
        # STEP 13: Wait for loading animation to disappear
        print("\n📌 Waiting for loading animation...")
        for i in range(10):  # Try for a maximum of 10 seconds
            loading_check = await tools.playwright_evaluate("""() => {
                return document.querySelector('#loading') === null || 
                       window.getComputedStyle(document.querySelector('#loading')).display === 'none';
            }""")
            
            if loading_check["status"] == "success" and loading_check["result"]:
                print("✅ Loading completed")
                break
                
            await asyncio.sleep(1)
            print("⏳ Still loading...")
        else:
            print("⚠️ Loading did not complete within expected time")
        
        # STEP 14: Take a screenshot after input field is enabled
        print("\n📌 Taking screenshot after input field is enabled...")
        enabled_screenshot = await tools.playwright_screenshot(filename="dynamic_controls_enabled.png")
        if enabled_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {enabled_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {enabled_screenshot.get('path', 'Unknown path')}")
        
        # STEP 15: Type "Hello" in the input field
        print("\n📌 Typing 'Hello' in the input field...")
        type_result = await tools.playwright_fill(selector="#input-example input", text="Hello")
        
        if type_result["status"] != "success":
            print(f"❌ Failed to type in input field: {type_result['message']}")
        else:
            print("✅ Successfully typed 'Hello' in the input field")
        
        # STEP 16: Take final screenshot
        print("\n📌 Taking final screenshot...")
        final_screenshot = await tools.playwright_screenshot(filename="dynamic_controls_final.png")
        if final_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {final_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {final_screenshot.get('path', 'Unknown path')}")
        
        # STEP 17: Verify input field content
        input_check = await tools.playwright_evaluate("""() => {
            const input = document.querySelector('#input-example input');
            return {
                exists: !!input,
                enabled: !!input && !input.disabled,
                value: input.value
            };
        }""")
        
        if input_check["status"] != "success":
            print(f"❌ Failed to check input field: {input_check['message']}")
        else:
            if (input_check["result"]["exists"] and 
                input_check["result"]["enabled"] and 
                input_check["result"]["value"] == "Hello"):
                print("✅ Input field is enabled and contains 'Hello'")
            else:
                print(f"❌ Input field validation failed: {input_check['result']}")
        
        print("\n✅ Dynamic Controls test completed successfully!")
        
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
    print("Starting Dynamic Controls test...")
    asyncio.run(test_dynamic_controls())
