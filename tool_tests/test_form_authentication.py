#!/usr/bin/env python3
"""
Test script for Prompt 19: Form Authentication
This test validates form authentication and browser navigation history
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_form_authentication():
    """Test the Form Authentication prompt and browser history navigation"""
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
        
        # STEP 1: Navigate to the login page
        print("\n📌 Navigating to login page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/login")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation to login page successful")
        
        # STEP 2: Take a screenshot of login page
        print("\n📌 Taking screenshot of login page...")
        login_screenshot = await tools.playwright_screenshot(filename="login_page.png")
        if login_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {login_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {login_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Try login with wrong credentials (test:test)
        print("\n📌 Attempting login with incorrect credentials (test:test)...")
        
        # Fill username
        username_fill = await tools.playwright_fill(selector="#username", text="test")
        if username_fill["status"] != "success":
            print(f"❌ Failed to fill username: {username_fill['message']}")
            return
        print("✅ Filled username field")
        
        # Fill password
        password_fill = await tools.playwright_fill(selector="#password", text="test")
        if password_fill["status"] != "success":
            print(f"❌ Failed to fill password: {password_fill['message']}")
            return
        print("✅ Filled password field")
        
        # Click login button
        login_click = await tools.playwright_click(selector="button[type='submit']")
        if login_click["status"] != "success":
            print(f"❌ Failed to click login button: {login_click['message']}")
            return
        print("✅ Clicked login button")
        
        # Wait brief moment for error message
        await asyncio.sleep(1)
        
        # STEP 4: Take a screenshot of error message
        print("\n📌 Taking screenshot after invalid login attempt...")
        error_screenshot = await tools.playwright_screenshot(filename="login_error.png")
        if error_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {error_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {error_screenshot.get('path', 'Unknown path')}")
        
        # STEP 5: Verify error message is displayed
        print("\n📌 Checking for error message...")
        error_check = await tools.playwright_evaluate("""() => {
            const flashMessage = document.getElementById('flash');
            return {
                exists: !!flashMessage,
                isVisible: !!flashMessage && window.getComputedStyle(flashMessage).display !== 'none',
                text: flashMessage ? flashMessage.textContent.trim() : '',
                isError: flashMessage ? flashMessage.classList.contains('error') : false
            };
        }""")
        
        if error_check["status"] != "success":
            print(f"❌ Failed to check for error message: {error_check['message']}")
        else:
            if error_check["result"]["isError"]:
                print(f"✅ Error message displayed: '{error_check['result']['text']}'")
            else:
                print(f"❌ Error message not displayed properly")
        
        # STEP 6: Try login with correct credentials (tomsmith:SuperSecretPassword!)
        print("\n📌 Attempting login with correct credentials (tomsmith:SuperSecretPassword!)...")
        
        # Fill username
        username_fill = await tools.playwright_fill(selector="#username", text="tomsmith")
        if username_fill["status"] != "success":
            print(f"❌ Failed to fill username: {username_fill['message']}")
            return
        print("✅ Filled username field")
        
        # Fill password
        password_fill = await tools.playwright_fill(selector="#password", text="SuperSecretPassword!")
        if password_fill["status"] != "success":
            print(f"❌ Failed to fill password: {password_fill['message']}")
            return
        print("✅ Filled password field")
        
        # Click login button
        login_click = await tools.playwright_click(selector="button[type='submit']")
        if login_click["status"] != "success":
            print(f"❌ Failed to click login button: {login_click['message']}")
            return
        print("✅ Clicked login button")
        
        # Wait brief moment for success message
        await asyncio.sleep(1)
        
        # STEP 7: Take a screenshot after successful login
        print("\n📌 Taking screenshot after successful login...")
        success_screenshot = await tools.playwright_screenshot(filename="login_success.png")
        if success_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {success_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {success_screenshot.get('path', 'Unknown path')}")
        
        # STEP 8: Verify success message is displayed
        print("\n📌 Checking for success message...")
        success_check = await tools.playwright_evaluate("""() => {
            const flashMessage = document.getElementById('flash');
            const secureArea = document.querySelector('h2');
            return {
                flashExists: !!flashMessage,
                flashText: flashMessage ? flashMessage.textContent.trim() : '',
                isSuccess: flashMessage ? flashMessage.classList.contains('success') : false,
                isSecureArea: secureArea ? secureArea.textContent.includes('Secure Area') : false,
                url: window.location.href
            };
        }""")
        
        if success_check["status"] != "success":
            print(f"❌ Failed to check for success: {success_check['message']}")
        else:
            result = success_check["result"]
            if result["isSuccess"] and result["isSecureArea"]:
                print(f"✅ Successfully logged in! Now in Secure Area.")
                print(f"✅ Success message: '{result['flashText']}'")
                print(f"✅ Current URL: {result['url']}")
            else:
                print(f"❌ Login success not confirmed. Current URL: {result['url']}")
        
        # STEP 9: Logout
        print("\n📌 Clicking logout button...")
        logout_click = await tools.playwright_click(selector="a.button[href='/logout']")
        if logout_click["status"] != "success":
            print(f"❌ Failed to click logout button: {logout_click['message']}")
        else:
            print("✅ Clicked logout button")
            
        # Wait brief moment for redirection
        await asyncio.sleep(1)
        
        # STEP 10: Take a screenshot after logout
        print("\n📌 Taking screenshot after logout...")
        logout_screenshot = await tools.playwright_screenshot(filename="after_logout.png")
        if logout_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {logout_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {logout_screenshot.get('path', 'Unknown path')}")
        
        # STEP 11: Verify we are back at login page
        print("\n📌 Verifying we're back at login page...")
        login_page_check = await tools.playwright_evaluate("""() => {
            const loginForm = document.getElementById('login');
            return {
                hasForm: !!loginForm,
                url: window.location.href,
                isLoginPage: window.location.href.includes('/login')
            };
        }""")
        
        if login_page_check["status"] != "success":
            print(f"❌ Failed to verify login page: {login_page_check['message']}")
        else:
            if login_page_check["result"]["isLoginPage"]:
                print(f"✅ Successfully logged out and returned to login page")
                print(f"✅ Current URL: {login_page_check['result']['url']}")
            else:
                print(f"❌ Not on login page. Current URL: {login_page_check['result']['url']}")
        
        # STEP 12: Test browser back button functionality
        print("\n📌 Testing browser back button...")
        back_result = await tools.playwright_go_back()
        if back_result["status"] != "success":
            print(f"❌ Failed to go back: {back_result['message']}")
        else:
            print("✅ Successfully navigated back")
        
        # Wait brief moment for navigation
        await asyncio.sleep(1)
        
        # STEP 13: Take a screenshot after going back
        print("\n📌 Taking screenshot after going back...")
        back_screenshot = await tools.playwright_screenshot(filename="after_go_back.png")
        if back_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {back_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {back_screenshot.get('path', 'Unknown path')}")
        
        # STEP 14: Verify we're back at the secure area
        print("\n📌 Verifying current page after back navigation...")
        page_check = await tools.playwright_evaluate("""() => {
            const heading = document.querySelector('h2');
            return {
                heading: heading ? heading.textContent.trim() : 'No heading found',
                url: window.location.href,
                isSecureArea: window.location.href.includes('/secure')
            };
        }""")
        
        if page_check["status"] != "success":
            print(f"❌ Failed to verify current page: {page_check['message']}")
        else:
            result = page_check["result"]
            print(f"ℹ️ Current heading: '{result['heading']}'")
            print(f"ℹ️ Current URL: {result['url']}")
            if result["isSecureArea"]:
                print(f"✅ Successfully verified browser history navigation - we're back at the secure area")
            else:
                print(f"❌ Browser history navigation did not work as expected")
        
        print("\n✅ Form authentication test completed successfully!")
        
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
    print("Starting Form Authentication test...")
    asyncio.run(test_form_authentication())
