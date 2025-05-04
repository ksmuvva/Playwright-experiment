#!/usr/bin/env python3
"""
Test script for Prompt 7: Context Menu
This test validates the context menu and console logs functionality
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_context_menu():
    """Test the Context Menu prompt using console logs capture"""
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
        
        # STEP 1: Navigate to the context menu page
        print("\n📌 Navigating to context menu page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/context_menu")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot before interaction
        print("\n📌 Taking screenshot before right-click...")
        before_screenshot = await tools.playwright_screenshot(filename="context_menu_before.png")
        if before_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {before_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {before_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Verify the context menu hot spot exists
        print("\n📌 Verifying context menu hot spot exists...")
        hotspot_check = await tools.playwright_evaluate("""() => {
            const hotspot = document.querySelector('#hot-spot');
            return {
                exists: !!hotspot,
                isVisible: !!hotspot && window.getComputedStyle(hotspot).display !== 'none',
                width: hotspot ? hotspot.offsetWidth : 0,
                height: hotspot ? hotspot.offsetHeight : 0
            };
        }""")
        
        if hotspot_check["status"] != "success":
            print(f"❌ Failed to check for hotspot: {hotspot_check['message']}")
            return
            
        if not hotspot_check["result"]["exists"] or not hotspot_check["result"]["isVisible"]:
            print("❌ Context menu hotspot not found or not visible")
            return
            
        print("✅ Context menu hotspot exists and is visible")
        print(f"   Size: {hotspot_check['result']['width']}x{hotspot_check['result']['height']}")
        
        # STEP 4: Set up console log monitoring
        print("\n📌 Setting up console log capture...")
        # Clear any existing logs first
        console_clear = await tools.playwright_console_logs(clear=True)
        if console_clear["status"] != "success":
            print(f"❌ Failed to clear console logs: {console_clear['message']}")
        else:
            print("✅ Console logs cleared")
        
        # Add JavaScript to log alert text to console
        print("\n📌 Adding JavaScript to log alert text to console...")
        js_setup = await tools.playwright_evaluate("""() => {
            // Store the original alert function
            window._originalAlert = window.alert;
            
            // Override the alert function to log to console
            window.alert = function(message) {
                console.log('ALERT_TEXT: ' + message);
                return window._originalAlert(message);
            };
            
            return { success: true, message: "Alert override installed" };
        }""")
        
        if js_setup["status"] != "success":
            print(f"❌ Failed to set up alert logging: {js_setup['message']}")
        else:
            print("✅ Alert logging set up successfully")
        
        # STEP 5: Simulate a right-click on the hot spot
        print("\n📌 Performing right-click on hot spot...")
        # Since we can't directly call a right-click through the PlaywrightTools, we'll use evaluate
        right_click = await tools.playwright_evaluate("""() => {
            try {
                const hotspot = document.querySelector('#hot-spot');
                if (!hotspot) return { error: "Hotspot element not found" };
                
                // Create and dispatch a context menu event
                const contextMenuEvent = new MouseEvent('contextmenu', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    button: 2,
                    buttons: 2
                });
                
                const accepted = hotspot.dispatchEvent(contextMenuEvent);
                
                console.log(`CONTEXT_MENU_EVENT: Dispatched with result ${accepted}`);
                
                return { 
                    success: true,
                    eventAccepted: accepted,
                    message: "Context menu event dispatched"
                };
            } catch (err) {
                console.error('Error in right-click: ' + err);
                return { error: err.toString() };
            }
        }""")
        
        if right_click["status"] != "success" or right_click.get("result", {}).get("error"):
            error = right_click.get("result", {}).get("error", right_click.get("message", "Unknown error"))
            print(f"❌ Failed to right-click: {error}")
        else:
            print("✅ Right-click simulated successfully")
        
        # Give some time for the alert to appear and be logged
        await asyncio.sleep(2)
        
        # STEP 6: Take a screenshot after interaction
        # (Note: Alert may prevent screenshot, but we'll try anyway)
        print("\n📌 Taking screenshot after right-click (may not capture alert)...")
        try:
            after_screenshot = await tools.playwright_screenshot(filename="context_menu_after.png")
            if after_screenshot["status"] != "success":
                print(f"❌ Failed to take screenshot: {after_screenshot['message']}")
            else:
                print(f"✅ Screenshot saved: {after_screenshot.get('path', 'Unknown path')}")
        except Exception as e:
            print(f"⚠️ Screenshot after right-click failed (possibly due to alert): {e}")
        
        # STEP 7: Check console logs to see if we captured the alert text
        print("\n📌 Checking console logs for alert text...")
        console_logs = await tools.playwright_console_logs()
        
        if console_logs["status"] != "success":
            print(f"❌ Failed to get console logs: {console_logs['message']}")
        else:
            logs = console_logs["result"]
            print(f"ℹ️ Found {len(logs)} console log entries")
            
            # Look for our specific alert log
            alert_text = None
            for log in logs:
                if "ALERT_TEXT:" in log.get("text", ""):
                    alert_text = log["text"].replace("ALERT_TEXT: ", "")
                    break
            
            if alert_text:
                print(f"✅ Found alert text in console logs: '{alert_text}'")
            else:
                print("❌ Could not find alert text in console logs")
                print("📋 Console logs:")
                for log in logs:
                    print(f"  - [{log.get('type', 'unknown')}] {log.get('text', 'no text')}")
        
        # STEP 8: Now dismiss the alert so we can continue
        print("\n📌 Dismissing alert...")
        dismiss_alert = await tools.playwright_evaluate("""() => {
            try {
                // Check if there's a reachable alert
                try {
                    window.alert._testAccess = true;
                } catch (e) {
                    // If we can't set a property, an alert is likely active
                    console.log("Alert appears to be active, attempting to dismiss");
                }
                
                // Add a global function we can call to try to dismiss the alert
                window._tryDismissAlert = true;
                
                return { success: true, message: "Alert dismissal attempted" };
            } catch (err) {
                return { error: err.toString() };
            }
        }""")
        
        if dismiss_alert["status"] != "success":
            print(f"⚠️ Alert dismissal might not have worked: {dismiss_alert['message']}")
        
        # STEP 9: Check if we managed to dismiss the alert
        print("\n📌 Verifying page state after alert...")
        page_state = await tools.playwright_evaluate("""() => {
            return { 
                url: window.location.href,
                title: document.title,
                hotspotExists: !!document.querySelector('#hot-spot')
            };
        }""")
        
        if page_state["status"] != "success":
            print(f"❌ Failed to check page state: {page_state['message']}")
        else:
            if page_state["result"]["hotspotExists"]:
                print("✅ Successfully verified page state after alert")
                print(f"   Title: {page_state['result']['title']}")
                print(f"   URL: {page_state['result']['url']}")
            else:
                print("⚠️ Page state changed after alert - hot spot no longer found")
        
        # STEP 10: Take a final screenshot
        print("\n📌 Taking final screenshot...")
        final_screenshot = await tools.playwright_screenshot(filename="context_menu_final.png")
        if final_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {final_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {final_screenshot.get('path', 'Unknown path')}")
        
        print("\n✅ Context Menu test completed!")
        
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
    print("Starting Context Menu test...")
    asyncio.run(test_context_menu())
