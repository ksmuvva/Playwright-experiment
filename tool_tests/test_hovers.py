#!/usr/bin/env python3
"""
Test script for Prompt 23: Hovers
This test validates the playwright_hover tool functionality
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_hovers():
    """Test the Hovers prompt using the playwright_hover tool"""
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
        
        # STEP 1: Navigate to the hovers page
        print("\n📌 Navigating to hovers page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/hovers")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot before hovering
        print("\n📌 Taking screenshot before hovering...")
        before_screenshot = await tools.playwright_screenshot(filename="hovers_before.png")
        if before_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {before_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {before_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Get number of user figures
        print("\n📌 Getting number of user figures...")
        user_figures_result = await tools.playwright_evaluate("""() => {
            return document.querySelectorAll('.figure').length;
        }""")
        
        if user_figures_result["status"] != "success":
            print(f"❌ Failed to get user figures: {user_figures_result['message']}")
            return
            
        num_figures = user_figures_result["result"]
        print(f"✅ Found {num_figures} user figures")
        
        # STEP 4: Hover over each figure and capture screenshots
        for i in range(1, num_figures + 1):
            print(f"\n📌 Testing hover on user figure {i}...")
            
            # Construct the selector for the current figure
            figure_selector = f".figure:nth-child({i*2})"  # Adjusted for page structure
            
            # Hover over the figure
            hover_result = await tools.playwright_hover(selector=figure_selector)
            
            if hover_result["status"] != "success":
                print(f"❌ Failed to hover over figure {i}: {hover_result['message']}")
                continue
                
            print(f"✅ Hover successful on figure {i}")
            
            # Take screenshot showing the hover effect
            hover_screenshot = await tools.playwright_screenshot(filename=f"hover_figure_{i}.png")
            
            if hover_screenshot["status"] != "success":
                print(f"❌ Failed to take screenshot: {hover_screenshot['message']}")
            else:
                print(f"✅ Screenshot saved: {hover_screenshot.get('path', 'Unknown path')}")
            
            # Extract the visible information using evaluate
            info_result = await tools.playwright_evaluate(f"""() => {{
                const figure = document.querySelector('{figure_selector}');
                if (!figure) return {{ error: 'Figure not found' }};
                
                const caption = figure.querySelector('.figcaption');
                if (!caption) return {{ error: 'Caption not visible' }};
                
                return {{
                    name: caption.querySelector('h5')?.textContent || 'No name',
                    link: caption.querySelector('a')?.textContent || 'No link',
                    href: caption.querySelector('a')?.getAttribute('href') || 'No URL'
                }};
            }}""")
            
            if info_result["status"] != "success":
                print(f"❌ Failed to get hover information: {info_result['message']}")
                continue
                
            info = info_result["result"]
            if "error" in info:
                print(f"⚠️ Could not find hover information: {info['error']}")
                continue
                
            print(f"ℹ️ Hover information for figure {i}:")
            print(f"  Name: {info['name']}")
            print(f"  Link text: {info['link']}")
            print(f"  Link URL: {info['href']}")
        
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
    print("Starting Hovers test...")
    asyncio.run(test_hovers())
