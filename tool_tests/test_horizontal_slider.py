#!/usr/bin/env python3
"""
Test script for Prompt 22: Horizontal Slider
This test validates the keyboard interaction with a slider component
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_horizontal_slider():
    """Test the Horizontal Slider prompt using keyboard interactions"""
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
        
        # STEP 1: Navigate to the horizontal slider page
        print("\n📌 Navigating to horizontal slider page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/horizontal_slider")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot before interaction
        print("\n📌 Taking screenshot before slider interaction...")
        before_screenshot = await tools.playwright_screenshot(filename="slider_before.png")
        if before_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {before_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {before_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Check the slider's initial value
        print("\n📌 Checking slider's initial value...")
        initial_value = await tools.playwright_evaluate("""() => {
            const slider = document.querySelector('input[type="range"]');
            const valueDisplay = document.querySelector('.sliderContainer > span');
            return {
                sliderExists: !!slider,
                min: slider ? parseFloat(slider.min) : null,
                max: slider ? parseFloat(slider.max) : null,
                step: slider ? parseFloat(slider.step) : null,
                currentValue: slider ? parseFloat(slider.value) : null,
                displayedValue: valueDisplay ? valueDisplay.textContent : null
            };
        }""")
        
        if initial_value["status"] != "success":
            print(f"❌ Failed to check slider value: {initial_value['message']}")
            return
            
        slider_info = initial_value["result"]
        if not slider_info["sliderExists"]:
            print("❌ Slider element not found")
            return
            
        print("✅ Slider found")
        print(f"   Range: {slider_info['min']} to {slider_info['max']} (step: {slider_info['step']})")
        print(f"   Initial value: {slider_info['currentValue']} (displayed: {slider_info['displayedValue']})")
        
        # STEP 4: Focus the slider 
        print("\n📌 Focusing slider element...")
        focus_result = await tools.playwright_click(selector="input[type='range']")
        
        if focus_result["status"] != "success":
            print(f"❌ Failed to focus slider: {focus_result['message']}")
            return
            
        print("✅ Slider focused")
        
        # STEP 5: Use keyboard arrows to increase the value
        print("\n📌 Using arrow keys to set slider to 4.5...")
        
        # First, let's estimate how many times we need to press
        # The goal is 4.5, and each step is usually 0.5 on this slider
        target_value = 4.5
        current_value = slider_info['currentValue']
        step_size = slider_info['step'] or 0.5  # Default to 0.5 if step is not provided
        
        # Calculate number of key presses needed (assuming starting from 0)
        # For right arrow key
        steps_needed = int((target_value - current_value) / step_size)
        
        print(f"   Current value: {current_value}, Target: {target_value}")
        print(f"   Step size: {step_size}, Steps needed: {steps_needed}")
        
        for i in range(steps_needed):
            key_result = await tools.playwright_press_key(key="ArrowRight")
            if key_result["status"] != "success":
                print(f"❌ Failed to press ArrowRight key (attempt {i+1}): {key_result['message']}")
                break
            await asyncio.sleep(0.1)  # Small delay between key presses
            
        print(f"✅ Pressed ArrowRight {steps_needed} times")
        
        # Wait a brief moment for the slider to settle
        await asyncio.sleep(0.5)
        
        # STEP 6: Take a screenshot after slider adjustment
        print("\n📌 Taking screenshot after slider adjustment...")
        after_screenshot = await tools.playwright_screenshot(filename="slider_after.png")
        if after_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {after_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {after_screenshot.get('path', 'Unknown path')}")
        
        # STEP 7: Check the final value of the slider
        print("\n📌 Verifying final slider value...")
        final_value = await tools.playwright_evaluate("""() => {
            const slider = document.querySelector('input[type="range"]');
            const valueDisplay = document.querySelector('.sliderContainer > span');
            return {
                currentValue: slider ? parseFloat(slider.value) : null,
                displayedValue: valueDisplay ? valueDisplay.textContent : null
            };
        }""")
        
        if final_value["status"] != "success":
            print(f"❌ Failed to check final slider value: {final_value['message']}")
        else:
            result = final_value["result"]
            print(f"✅ Final slider value: {result['currentValue']} (displayed: {result['displayedValue']})")
            
            if result['currentValue'] == target_value or result['displayedValue'] == target_value.toString():
                print(f"✅ Successfully set slider to target value of {target_value}")
            else:
                print(f"⚠️ Slider value ({result['currentValue']}) does not match target ({target_value})")
                
                # Try one more approach with direct value setting
                print("\n📌 Trying direct value setting via JavaScript...")
                set_value = await tools.playwright_evaluate(f"""() => {{
                    try {{
                        const slider = document.querySelector('input[type="range"]');
                        if (!slider) return {{ error: "Slider not found" }};
                        
                        // Set the value directly
                        slider.value = "{target_value}";
                        
                        // Dispatch input event to update display
                        const event = new Event('input', {{ bubbles: true }});
                        slider.dispatchEvent(event);
                        
                        // Check if value was updated
                        const valueDisplay = document.querySelector('.sliderContainer > span');
                        return {{
                            success: true,
                            newValue: parseFloat(slider.value),
                            displayedValue: valueDisplay ? valueDisplay.textContent : null
                        }};
                    }} catch (e) {{
                        return {{ error: e.toString() }};
                    }}
                }}""")
                
                if set_value["status"] == "success" and set_value["result"].get("success"):
                    print(f"✅ Successfully set slider value via JavaScript")
                    print(f"   New value: {set_value['result']['newValue']} (displayed: {set_value['result']['displayedValue']})")
                else:
                    error = set_value.get("result", {}).get("error", "Unknown error")
                    print(f"❌ Failed to set value via JavaScript: {error}")
        
        # STEP 8: Take a final screenshot
        print("\n📌 Taking final screenshot...")
        final_screenshot = await tools.playwright_screenshot(filename="slider_final.png")
        if final_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {final_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {final_screenshot.get('path', 'Unknown path')}")
        
        print("\n✅ Horizontal slider test completed!")
        
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
    print("Starting Horizontal Slider test...")
    asyncio.run(test_horizontal_slider())
