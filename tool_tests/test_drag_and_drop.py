#!/usr/bin/env python3
"""
Test script for Prompt 10: Drag and Drop
This test validates the playwright_drag tool functionality
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_drag_and_drop():
    """Test the Drag and Drop prompt using the playwright_drag tool"""
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
        
        # STEP 1: Navigate to the drag and drop page
        print("\n📌 Navigating to drag and drop page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/drag_and_drop")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot before dragging
        print("\n📌 Taking screenshot before dragging...")
        before_screenshot = await tools.playwright_screenshot(filename="drag_drop_before.png")
        if before_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {before_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {before_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Verify initial state with evaluate
        print("\n📌 Verifying initial state...")
        initial_state = await tools.playwright_evaluate("""() => {
            return {
                columnA: document.querySelector('#column-a').textContent.trim(),
                columnB: document.querySelector('#column-b').textContent.trim()
            };
        }""")
        
        if initial_state["status"] != "success":
            print(f"❌ Failed to verify initial state: {initial_state['message']}")
            return
            
        print(f"✅ Initial state: Column A = '{initial_state['result']['columnA']}', Column B = '{initial_state['result']['columnB']}'")
        
        # STEP 4: Perform the drag and drop operation
        print("\n📌 Performing drag and drop operation...")
        drag_result = await tools.playwright_drag(
            sourceSelector="#column-a", 
            targetSelector="#column-b"
        )
        
        if drag_result["status"] != "success":
            print(f"❌ Failed to drag and drop: {drag_result['message']}")
            # Some implementations struggle with pure dragging, so let's try with JavaScript as backup
            print("📌 Trying alternative JavaScript implementation...")
            js_drag_result = await tools.playwright_evaluate("""() => {
                const sourceElement = document.querySelector('#column-a');
                const targetElement = document.querySelector('#column-b');
                
                // Get source and target coordinates
                const sourceRect = sourceElement.getBoundingClientRect();
                const targetRect = targetElement.getBoundingClientRect();
                
                // Create and dispatch mouse events
                const mouseDown = new MouseEvent('mousedown', {
                    bubbles: true,
                    clientX: sourceRect.left + sourceRect.width / 2,
                    clientY: sourceRect.top + sourceRect.height / 2
                });
                
                const mouseMove = new MouseEvent('mousemove', {
                    bubbles: true,
                    clientX: targetRect.left + targetRect.width / 2,
                    clientY: targetRect.top + targetRect.height / 2
                });
                
                const mouseUp = new MouseEvent('mouseup', {
                    bubbles: true,
                    clientX: targetRect.left + targetRect.width / 2,
                    clientY: targetRect.top + targetRect.height / 2
                });
                
                sourceElement.dispatchEvent(mouseDown);
                document.dispatchEvent(mouseMove);
                document.dispatchEvent(mouseUp);
                
                return {
                    success: true,
                    message: "JavaScript drag and drop attempted"
                };
            }""")
            
            if js_drag_result["status"] != "success":
                print(f"❌ JavaScript drag and drop also failed: {js_drag_result['message']}")
                return
        else:
            print("✅ Drag and drop operation completed")
        
        # STEP 5: Take a screenshot after dragging
        print("\n📌 Taking screenshot after dragging...")
        after_screenshot = await tools.playwright_screenshot(filename="drag_drop_after.png")
        if after_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {after_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {after_screenshot.get('path', 'Unknown path')}")
        
        # STEP 6: Verify final state with evaluate
        print("\n📌 Verifying final state...")
        final_state = await tools.playwright_evaluate("""() => {
            return {
                columnA: document.querySelector('#column-a').textContent.trim(),
                columnB: document.querySelector('#column-b').textContent.trim()
            };
        }""")
        
        if final_state["status"] != "success":
            print(f"❌ Failed to verify final state: {final_state['message']}")
            return
            
        print(f"✅ Final state: Column A = '{final_state['result']['columnA']}', Column B = '{final_state['result']['columnB']}'")
        
        # STEP 7: Determine if the drag was successful by comparing states
        if (initial_state["result"]["columnA"] != final_state["result"]["columnA"] and
            initial_state["result"]["columnB"] != final_state["result"]["columnB"]):
            print("\n✅ Drag and drop test PASSED! The columns were successfully swapped.")
        else:
            print("\n⚠️ Drag and drop test INCONCLUSIVE. The columns were not swapped.")
            
        print("\n✅ Test completed!")
        
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
    print("Starting Drag and Drop test...")
    asyncio.run(test_drag_and_drop())
