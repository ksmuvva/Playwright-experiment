#!/usr/bin/env python3
"""
MCP Tools - Collection of browser automation tools for the MCP protocol
Includes code generation and browser automation tools used by the MCP agent.
"""
import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, CDPSession, TimeoutError as PlaywrightTimeoutError

# Configure logging
logger = logging.getLogger("mcp_tools")

class CodeGenSession:
    """Represents a code generation session."""
    def __init__(self, session_id: str, name: str, language: str):
        self.session_id = session_id
        self.name = name
        self.language = language
        self.code = ""
        self.created_at = asyncio.get_event_loop().time()
        self.updated_at = self.created_at
    
    def update(self, code: str):
        """Update the code in the session."""
        self.code = code
        self.updated_at = asyncio.get_event_loop().time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "language": self.language,
            "code": self.code,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class PlaywrightTools:
    """Collection of Playwright browser automation tools."""
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = []
        self.codegen_sessions = {}  # Map of session_id to CodeGenSession
        self.console_logs = []
        self.browser_initialized = False  # Track if browser is initialized
    
    # === Helper Methods ===
    
    async def initialize(self):
        """Initialize Playwright without launching a browser."""
        try:
            # Launch Playwright but don't create a browser yet
            self.playwright = await async_playwright().start()
            logger.info("Playwright initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            return False
    
    async def _ensure_browser_initialized(self):
        """Ensure browser is initialized before using it."""
        if not self.browser_initialized:
            try:
                # Launch browser based on environment configuration
                # Get browser type from environment or default to chromium
                browser_type = os.getenv("BROWSER_TYPE", "chromium").lower()
                
                # Select the appropriate browser engine
                if browser_type == "firefox":
                    browser_engine = self.playwright.firefox
                    logger.info("Using Firefox browser engine")
                elif browser_type == "webkit":
                    browser_engine = self.playwright.webkit
                    logger.info("Using WebKit browser engine")
                else:
                    # Default to chromium
                    browser_engine = self.playwright.chromium
                    logger.info("Using Chromium browser engine")
                
                # Get headless mode from environment or default to False
                headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
                
                # Launch the selected browser
                self.browser = await browser_engine.launch(
                    headless=headless
                    # Note: user_data_dir is not supported in newer versions of Playwright
                )
                
                # Get viewport size from environment variables with defaults
                viewport_width = int(os.getenv("VIEWPORT_WIDTH", 1425))
                viewport_height = int(os.getenv("VIEWPORT_HEIGHT", 776))
                viewport_size = {"width": viewport_width, "height": viewport_height}
                logger.info(f"Using viewport size from environment: {viewport_width}x{viewport_height}")
                
                # Get user agent from environment or use default
                user_agent = os.getenv("USER_AGENT", 
                             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                self.context = await self.browser.new_context(
                    viewport=viewport_size,
                    user_agent=user_agent
                )
                self.browser_initialized = True
                logger.info(f"Browser initialized with viewport size {viewport_size}")
                
                # Create a page if needed
                if len(self.pages) == 0:
                    page = await self.context.new_page()
                    
                    # Set viewport directly on the page as well to ensure it's applied
                    await page.set_viewport_size(viewport_size)
                    
                    self.pages.append(page)
                    logger.info(f"Created new page with viewport size {viewport_size}")
                
                # For truly maximizing the window, use multiple approaches
                try:
                    # 1. Try CDP method first to set exact window size instead of maximizing
                    viewport_width = int(os.getenv("VIEWPORT_WIDTH", 1425))
                    viewport_height = int(os.getenv("VIEWPORT_HEIGHT", 776))
                    cdp_session = await self.pages[0].context.new_cdp_session(self.pages[0])
                    await cdp_session.send('Browser.setWindowBounds', {
                        'windowId': 1,
                        'bounds': {'width': viewport_width, 'height': viewport_height}
                    })
                    logger.info(f"Browser window set to {viewport_width}x{viewport_height} via CDP")
                except Exception as e:
                    # Log the error but continue - viewport size should still be set correctly
                    logger.warning(f"Could not set window size via CDP: {e}")
                    logger.info("Continuing with viewport size set in context only")
                    
                    # 2. Try JavaScript approach if CDP fails
                    try:
                        # Try to set window size using JavaScript
                        viewport_width = int(os.getenv("VIEWPORT_WIDTH", 1425))
                        viewport_height = int(os.getenv("VIEWPORT_HEIGHT", 776))
                        await self.pages[0].evaluate(f"""() => {{
                            window.resizeTo({viewport_width}, {viewport_height});
                        }}""")
                        logger.info(f"Attempted to set window size to {viewport_width}x{viewport_height} with JavaScript")
                    except Exception:
                        # Just continue if this also fails
                        pass
                        
                    # 3. Try setting viewport directly using CSS viewport meta tag
                    try:
                        viewport_width = int(os.getenv("VIEWPORT_WIDTH", 1425))
                        viewport_height = int(os.getenv("VIEWPORT_HEIGHT", 776))
                        await self.pages[0].evaluate(f"""() => {{
                            // Create or update viewport meta tag for exact dimensions
                            let viewport = document.querySelector('meta[name="viewport"]');
                            if (!viewport) {{
                                viewport = document.createElement('meta');
                                viewport.name = 'viewport';
                                document.head.appendChild(viewport);
                            }}
                            viewport.content = 'width={viewport_width}, height={viewport_height}';
                        }}""")
                        logger.info("Set viewport size using meta viewport tag")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error initializing browser: {e}")
                # Reset initialization state to allow retry
                self.browser_initialized = False
                raise

    async def _get_page(self, page_index: int) -> Optional[Page]:
        """Get a page by index, creating one if necessary."""
        if page_index < 0:
            return None
        
        # Ensure browser is initialized
        await self._ensure_browser_initialized()
        
        # Create new pages if needed
        while len(self.pages) <= page_index:
            new_page = await self.context.new_page()
            # Set up console log listeners
            new_page.on("console", lambda msg: self.console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": asyncio.get_event_loop().time()
            }))
            self.pages.append(new_page)
        
        return self.pages[page_index]
    
    async def cleanup(self):
        """Cleanup resources but maintain browser persistence."""
        try:
            # Close pages but keep the browser context and session alive
            for page in self.pages:
                if page and not page.is_closed():
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {e}")
            
            # Clear the pages list but don't close the context or browser
            self.pages = []
                
            if self.browser_initialized:
                logger.info("Keeping browser session alive")
            
            if self.playwright:
                logger.info("Playwright session remains active")
            
            logger.info("Tools cleaned up (browser session remains open for persistence)")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # === Code Generation Tool Implementations ===

    async def start_codegen_session(self, session_name: str, language: str) -> Dict[str, Any]:
        """Start a new code generation session."""
        session_id = f"session_{len(self.codegen_sessions) + 1}"
        session = CodeGenSession(session_id, session_name, language)
        self.codegen_sessions[session_id] = session
        
        return {
            "status": "success",
            "message": f"Code generation session started: {session_name}",
            "session": session.to_dict()
        }

    async def end_codegen_session(self, session_id: str) -> Dict[str, Any]:
        """End a code generation session."""
        if session_id not in self.codegen_sessions:
            return {
                "status": "error",
                "message": f"Session not found: {session_id}"
            }
        
        session = self.codegen_sessions.pop(session_id)
        
        return {
            "status": "success",
            "message": f"Code generation session ended: {session.name}",
            "session": session.to_dict()
        }

    async def get_codegen_session(self, session_id: str) -> Dict[str, Any]:
        """Get the current state of a code generation session."""
        if session_id not in self.codegen_sessions:
            return {
                "status": "error",
                "message": f"Session not found: {session_id}"
            }
        
        session = self.codegen_sessions[session_id]
        
        return {
            "status": "success",
            "session": session.to_dict()
        }

    async def clear_codegen_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a code generation session."""
        if session_id not in self.codegen_sessions:
            return {
                "status": "error",
                "message": f"Session not found: {session_id}"
            }
        
        session = self.codegen_sessions[session_id]
        session.update("")
        
        return {
            "status": "success",
            "message": f"Code generation session cleared: {session.name}",
            "session": session.to_dict()
        }

    # === Browser Automation Tool Implementations ===

    async def playwright_navigate(self, url: str, wait_for_load: bool = True, 
                                 capture_screenshot: bool = False, page_index: int = 0) -> Dict[str, Any]:
        """Navigate to a URL."""
        try:
            # Make sure the URL has http/https prefix
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Get or create the page
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            try:
                # Check if page is still valid
                if not page.is_closed():
                    print(f"Navigating to {url}...")
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                        
                    status = response.status if response else None
                    
                    # Get the title and URL after navigation
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url}",
                        "title": title,
                        "url": current_url
                    }
                else:
                    # Page is closed, create a new one
                    print("Page is closed, creating a new one...")
                    page = await self.context.new_page()
                    self.pages[page_index] = page
                    
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                        
                    status = response.status if response else None
                    
                    # Get the title and URL after navigation
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url} with new page",
                        "title": title,
                        "url": current_url
                    }
            except Exception as e:
                # If the page is closed or any other error, create a new one
                print(f"Error navigating with existing page: {e}")
                print("Creating a new page and trying again...")
                
                # Create a new page and try again
                try:
                    page = await self.context.new_page()
                    # Replace the page in the pages list
                    if page_index < len(self.pages):
                        self.pages[page_index] = page
                    else:
                        self.pages.append(page)
                    
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                    
                    status = response.status if response else None
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url} with new page (after error)",
                        "title": title,
                        "url": current_url
                    }
                except Exception as e2:
                    return {"status": "error", "message": f"Error navigating to {url} even with new page: {str(e2)}"}
            
            if capture_screenshot:
                screenshot_path = f"screenshot_{asyncio.get_event_loop().time()}.png"
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_screenshot(self, filename: str = None, selector: str = "", page_index: int = 0, path: str = None) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            filename: Path to save the screenshot (alternative to path)
            selector: Optional selector to screenshot a specific element
            page_index: Index of the page to screenshot
            path: Path to save the screenshot (alternative to filename)
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Handle the parameter naming conflict - prefer path if provided
            actual_filename = path if path is not None else filename
            
            if actual_filename is None:
                actual_filename = f"screenshot_{int(time.time())}.png"
            
            # Ensure png extension
            if not actual_filename.endswith(".png"):
                actual_filename += ".png"
            
            logger.info(f"Taking screenshot: {actual_filename}")
            
            if selector:
                element = await page.wait_for_selector(selector, state="visible")
                if not element:
                    return {"status": "error", "message": f"Element not found: {selector}"}
                
                await element.screenshot(path=actual_filename)
            else:
                await page.screenshot(path=actual_filename)
            
            return {
                "status": "success",
                "message": f"Screenshot saved to {actual_filename}",
                "filename": actual_filename
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_click(self, selector: str, page_index: int = 0, 
                              capture_screenshot: bool = False, fallback: bool = True) -> Dict[str, Any]:
        """
        Click on an element with fallback strategies.
        
        Args:
            selector: CSS/XPath selector to locate the element
            page_index: Index of the page to operate on
            capture_screenshot: Whether to capture screenshots
            fallback: Whether to attempt fallback strategies if direct click fails
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Common selectors for cookie accept buttons if the given selector doesn't work
            common_cookie_selectors = [
                selector,  # Try the provided selector first
                "#accept-cookies", 
                ".cookie-accept", 
                "[aria-label='Accept cookies']", 
                "[aria-label='Accept All']",
                "[aria-label='Accept all']",
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('Accept all')",
                "button:has-text('I accept')",
                "button:has-text('Allow all')",
                "button:has-text('Allow cookies')"
            ]
            
            # If this is likely a cookie consent button
            if "cookie" in selector.lower() or "accept" in selector.lower() or "consent" in selector.lower():
                logger.info(f"Looks like a cookie button. Trying various selectors...")
                
                # Try each selector
                for cookie_selector in common_cookie_selectors:
                    try:
                        logger.info(f"Trying selector: {cookie_selector}")
                        # Wait a short time for each selector
                        is_visible = await page.is_visible(cookie_selector, timeout=1000)
                        if is_visible:
                            logger.info(f"Found visible element with selector: {cookie_selector}")
                            await page.click(cookie_selector)
                            
                            result = {
                                "status": "success",
                                "message": f"Clicked on {cookie_selector}",
                                "selector_used": cookie_selector
                            }
                            
                            if capture_screenshot:
                                screenshot_path = f"click_{asyncio.get_event_loop().time()}.png"
                                await page.screenshot(path=screenshot_path)
                                result["screenshot"] = screenshot_path
                                
                            return result
                    except Exception as selector_error:
                        # Continue to the next selector
                        continue
                
                # If we get here, none of the selectors worked
                if not fallback:
                    return {"status": "error", "message": f"Could not find any cookie consent button to click"}
                
                # Try to extract text from selector and use smart_click as fallback
                logger.info("Cookie button selectors failed, trying smart_click fallback")
                try:
                    # Extract text from selector if it contains text pattern
                    if ":has-text('" in selector:
                        text = selector.split(":has-text('")[1].split("'")[0]
                    elif "text=" in selector:
                        text = selector.split("text=")[1]
                        if text.startswith("'") and "'" in text[1:]:
                            text = text.split("'")[1]
                    else:
                        text = "Accept"  # Default text for cookie buttons
                    
                    return await self.playwright_smart_click(
                        text=text,
                        element_type="button",
                        page_index=page_index,
                        capture_screenshot=capture_screenshot
                    )
                except Exception as fallback_error:
                    return {"status": "error", "message": f"Both direct selectors and smart_click fallback failed: {str(fallback_error)}"}
            
            # For non-cookie buttons, try the provided selector
            logger.info(f"Waiting for selector to be visible: {selector}")
            try:
                await page.wait_for_selector(selector, state="visible", timeout=5000)
                await page.click(selector)
                
                result = {
                    "status": "success",
                    "message": f"Clicked on {selector}",
                    "selector_used": selector
                }
                
                if capture_screenshot:
                    screenshot_path = f"click_{asyncio.get_event_loop().time()}.png"
                    await page.screenshot(path=screenshot_path)
                    result["screenshot"] = screenshot_path
                    
                return result
            except Exception as direct_click_error:
                logger.info(f"Direct click failed: {str(direct_click_error)}")
                if not fallback:
                    return {"status": "error", "message": str(direct_click_error)}
                
                # Try fallback to smart_click
                logger.info("Direct click failed, attempting smart_click fallback")
                try:
                    # Extract potential text from the selector
                    text = None
                    if ":has-text('" in selector:
                        text = selector.split(":has-text('")[1].split("'")[0]
                    elif "text=" in selector:
                        parts = selector.split("text=")
                        if len(parts) > 1:
                            text = parts[1]
                            if text.startswith("'") and "'" in text[1:]:
                                text = text.split("'")[1]
                    
                    # If we can't extract text, try multi_strategy_locate
                    if not text:
                        logger.info("No text to extract, trying multi_strategy_locate")
                        result = await self.playwright_multi_strategy_locate(
                            description=selector,
                            action="click",
                            page_index=page_index,
                            capture_screenshot=capture_screenshot
                        )
                        
                        if result["status"] == "success":
                            result["message"] = f"Clicked using multi-strategy fallback"
                            result["original_selector"] = selector
                            return result
                    
                    # If we have text, try smart_click
                    if text:
                        logger.info(f"Extracted text '{text}' from selector, trying smart_click")
                        result = await self.playwright_smart_click(
                            text=text,
                            page_index=page_index,
                            capture_screenshot=capture_screenshot
                        )
                        
                        if result["status"] == "success":
                            result["message"] = f"Clicked using smart_click fallback"
                            result["original_selector"] = selector
                            return result
                    
                    # If all fallbacks failed
                    return {
                        "status": "error", 
                        "message": f"All click methods failed for selector: {selector}",
                        "original_error": str(direct_click_error)
                    }
                except Exception as fallback_error:
                    return {
                        "status": "error", 
                        "message": f"Both direct click and fallbacks failed: {str(fallback_error)}",
                        "original_error": str(direct_click_error)
                    }
            
        except Exception as e:
            logger.error(f"Error in playwright_click: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def playwright_click_and_switch_tab(self, selector: str, page_index: int = 0,
                                            capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element that opens a new tab and switch to it."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for the element to be visible
            await page.wait_for_selector(selector, state="visible")
            
            # Get the current number of pages
            initial_pages_count = len(self.pages)
            
            # Start listening for new pages
            async with page.expect_popup() as popup_info:
                await page.click(selector)
            
            # Get the new page
            new_page = await popup_info.value
            self.pages.append(new_page)
            new_page_index = len(self.pages) - 1
            
            # Set up console log listeners for the new page
            new_page.on("console", lambda msg: self.console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": asyncio.get_event_loop().time()
            }))
            
            # Wait for the new page to load
            await new_page.wait_for_load_state("networkidle")
            
            result = {
                "status": "success",
                "message": f"Clicked on {selector} and switched to new tab",
                "new_page_index": new_page_index,
                "title": await new_page.title(),
                "url": new_page.url
            }
            
            if capture_screenshot:
                screenshot_path = f"new_tab_{asyncio.get_event_loop().time()}.png"
                await new_page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_iframe_click(self, iframe_selector: str, element_selector: str,
                                     page_index: int = 0, capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element inside an iframe."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for iframe
            iframe = await page.wait_for_selector(iframe_selector)
            if not iframe:
                return {"status": "error", "message": f"Iframe not found: {iframe_selector}"}
            
            # Get the content frame
            frame = await iframe.content_frame()
            if not frame:
                return {"status": "error", "message": "Could not access iframe content"}
            
            # Click the element within the iframe
            await frame.wait_for_selector(element_selector, state="visible")
            await frame.click(element_selector)
            
            result = {
                "status": "success",
                "message": f"Clicked on {element_selector} inside iframe {iframe_selector}"
            }
            
            if capture_screenshot:
                screenshot_path = f"iframe_click_{asyncio.get_event_loop().time()}.png"
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_hover(self, selector: str, page_index: int = 0,
                              capture_screenshot: bool = False) -> Dict[str, Any]:
        """Hover over an element."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.wait_for_selector(selector, state="visible")
            await page.hover(selector)
            
            result = {
                "status": "success",
                "message": f"Hovered over {selector}"
            }
            
            if capture_screenshot:
                screenshot_path = f"hover_{asyncio.get_event_loop().time()}.png"
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_fill(self, selector: str, text: str, page_index: int = 0) -> Dict[str, Any]:
        """Fill a form field."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # First attempt - standard fill approach
            try:
                await page.wait_for_selector(selector, state="visible", timeout=5000)
                await page.fill(selector, text)
                
                return {
                    "status": "success",
                    "message": f"Filled {selector} with text",
                    "strategy_used": "standard_fill"
                }
            except PlaywrightTimeoutError:
                # If standard approach fails, try the next approach
                logger.info(f"Standard fill approach failed for '{selector}', trying with multi-strategy locate")
                
                # Try with multi-strategy locate
                multi_strategy_result = await self.playwright_multi_strategy_locate(
                    description=f"input field {selector.replace('[name=', '').replace(']', '')}",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if multi_strategy_result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Filled input using multi-strategy approach",
                        "strategy_used": "multi_strategy",
                        "details": multi_strategy_result
                    }
                
                # Try with vision locator 
                logger.info(f"Multi-strategy approach failed, trying with vision locator")
                vision_result = await self.playwright_vision_locator(
                    text="search", 
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if vision_result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Filled input using vision locator",
                        "strategy_used": "vision_locator",
                        "details": vision_result
                    }
                
                # Try with accessibility tree
                logger.info(f"Vision locator approach failed, trying with accessibility tree")
                a11y_result = await self.playwright_accessibility_locator(
                    description=f"search input field",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if a11y_result["status"] == "success" and a11y_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Filled input using accessibility locator",
                        "strategy_used": "accessibility_locator",
                        "details": a11y_result
                    }
                
                # Try with JavaScript evaluate as last resort
                logger.info(f"All specialized locators failed, trying with JavaScript as last resort")
                js_result = await self.playwright_js_locate(
                    description=f"search input",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if js_result["status"] == "success" and js_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Filled input using JavaScript locator",
                        "strategy_used": "js_locate",
                        "details": js_result
                    }
                
                # If all approaches fail, try some common selectors for search inputs
                common_search_selectors = [
                    "input[type='search']",
                    "input[type='text']",
                    "input.search-box",
                    "input.searchbox",
                    "input.gLFyf",  # Google search class
                    ".search-input",
                    "#search-input",
                    "[aria-label='Search']",
                    "[placeholder*='Search']",
                    "[placeholder*='search']"
                ]
                
                for common_selector in common_search_selectors:
                    try:
                        if await page.is_visible(common_selector, timeout=1000):
                            await page.fill(common_selector, text)
                            return {
                                "status": "success",
                                "message": f"Filled {common_selector} with text using common selector patterns",
                                "strategy_used": "common_selectors"
                            }
                    except Exception:
                        continue
                
                # If we reach here, all approaches failed
                return {
                    "status": "error",
                    "message": f"Failed to fill text. All approaches failed.",
                    "selector_tried": selector,
                    "text": text
                }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_select(self, selector: str, value: str, page_index: int = 0) -> Dict[str, Any]:
        """Select an option from a dropdown."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.wait_for_selector(selector, state="visible")
            await page.select_option(selector, value)
            
            return {
                "status": "success",
                "message": f"Selected value '{value}' in {selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_evaluate(self, script: str, page_index: int = 0, arg: Any = None) -> Dict[str, Any]:
        """
        Evaluate JavaScript in the page context.
        
        Args:
            script: JavaScript code to execute. For code with return statements, wrap it in a function.
            page_index: Index of the page to operate on
            arg: Optional argument to pass to the evaluated function
            
        Note:
            There are two ways to use this method:
            1. Direct expressions without 'return': "document.title" or "5+5"
            2. Function format: "() => { return document.title; }" or "function() { return 5+5; }"
            
            Invalid: "return document.title" (return outside of a function is not allowed)
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Check if the script contains a return statement without being in a function
            if "return " in script and not ("() =>" in script or "function" in script):
                logger.warning(f"Script contains a return statement outside a function: {script}")
                # Automatically wrap the script in a function
                wrapped_script = f"() => {{ {script} }}"
                logger.info(f"Wrapped script in function: {wrapped_script}")
                result = await page.evaluate(wrapped_script, arg)
            else:
                result = await page.evaluate(script, arg)
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error evaluating script: {str(e)}")
            logger.error(f"Problematic script: {script}")
            
            # Provide more helpful error message
            error_msg = str(e)
            if "Illegal return statement" in error_msg:
                error_msg += "\nJavaScript return statements must be inside a function. Use '() => { return value; }' format or remove 'return'."
            
            return {
                "status": "error", 
                "message": error_msg,
                "script": script  # Include the problematic script for debugging
            }

    async def playwright_console_logs(self, page_index: int = 0, count: int = 10) -> Dict[str, Any]:
        """Get console logs from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Get the most recent logs for this page
            page_logs = [log for log in self.console_logs if log.get("page_index", 0) == page_index]
            recent_logs = page_logs[-count:] if count < len(page_logs) else page_logs
            
            return {
                "status": "success",
                "logs": recent_logs
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_close(self, page_index: int = 0) -> Dict[str, Any]:
        """Close a page."""
        if page_index < 0 or page_index >= len(self.pages):
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Close the page
            await self.pages[page_index].close()
            
            # Remove from list
            self.pages.pop(page_index)
            
            return {
                "status": "success",
                "message": f"Closed page at index {page_index}",
                "remaining_pages": len(self.pages)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_expect_response(self, url_pattern: str, timeout_ms: int = 30000,
                                        page_index: int = 0) -> Dict[str, Any]:
        """Wait for a specific HTTP response."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for response
            async with page.expect_response(url_pattern, timeout=timeout_ms) as response_info:
                response = await response_info.value
            
            # Get response details
            status = response.status
            headers = await response.all_headers()
            
            return {
                "status": "success",
                "message": f"Received response from {response.url}",
                "response_status": status,
                "headers": headers
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_assert_response(self, url_pattern: str, status_code: int = 200,
                                        page_index: int = 0) -> Dict[str, Any]:
        """Assert that a response matches expectations."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create a callback to collect the responses
            matching_responses = []
            
            def handle_response(response):
                if url_pattern in response.url:
                    matching_responses.append(response)
            
            # Start listening for responses
            page.on("response", handle_response)
            
            # Wait a bit to collect responses
            await asyncio.sleep(2)
            
            # Stop listening
            page.remove_listener("response", handle_response)
            
            # Check matches
            if not matching_responses:
                return {
                    "status": "error",
                    "message": f"No responses matching {url_pattern} found"
                }
            
            # Check status codes
            success = all(response.status == status_code for response in matching_responses)
            
            return {
                "status": "success" if success else "error",
                "message": f"Response assertion {'passed' if success else 'failed'}",
                "expected_status": status_code,
                "actual_statuses": [response.status for response in matching_responses],
                "urls": [response.url for response in matching_responses]
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_custom_user_agent(self, user_agent: str, page_index: int = 0) -> Dict[str, Any]:
        """Set a custom user agent."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.set_extra_http_headers({"User-Agent": user_agent})
            
            return {
                "status": "success",
                "message": f"Set custom user agent: {user_agent}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_text(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible text from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            text = await page.text_content(selector)
            
            return {
                "status": "success",
                "text": text
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_html(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible HTML from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            html = await page.inner_html(selector)
            
            return {
                "status": "success",
                "html": html
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_back(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate back in the browser history."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.go_back()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated back",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_forward(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate forward in the browser history."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.go_forward()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated forward",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_drag(self, source_selector: str, target_selector: str,
                             page_index: int = 0) -> Dict[str, Any]:
        """Drag an element to another position."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for elements
            await page.wait_for_selector(source_selector, state="visible")
            await page.wait_for_selector(target_selector, state="visible")
            
            # Perform drag and drop
            await page.drag_and_drop(source_selector, target_selector)
            
            return {
                "status": "success",
                "message": f"Dragged {source_selector} to {target_selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_press_key(self, key: str, page_index: int = 0) -> Dict[str, Any]:
        """Press a key."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.keyboard.press(key)
            
            return {
                "status": "success",
                "message": f"Pressed key: {key}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_save_as_pdf(self, filename: str, page_index: int = 0) -> Dict[str, Any]:
        """Save the page as PDF."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            
            await page.pdf(path=filename)
            
            return {
                "status": "success",
                "message": f"Saved page as PDF: {filename}",
                "filename": filename
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)} 

    async def playwright_smart_click(self, text: str = None, selector: str = None, element_type: str = "any", 
                                   page_index: int = 0, capture_screenshot: bool = False) -> Dict[str, Any]:
        """
        Smart click that tries multiple selector strategies based on fuzzy text matching.
        Especially useful for common UI patterns with varied terminology.
        
        Args:
            text: The text to look for (e.g., "Place Order", "Continue", "Submit")
            selector: CSS/XPath selector (alternative to text, for backward compatibility)
            element_type: Type of element to target ('button', 'link', 'any')
            page_index: Index of the page to operate on
            capture_screenshot: Whether to capture a screenshot after clicking
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Handle case where selector is provided instead of text
            if selector and not text:
                logger.info(f"Smart click received selector: {selector}")
                # Try to extract text from selector if it's a text-based selector
                if ":has-text('" in selector and "'" in selector.split(":has-text('")[1]:
                    extracted_text = selector.split(":has-text('")[1].split("'")[0]
                    text = extracted_text
                    logger.info(f"Extracted text from selector: '{text}'")
                elif ":text-is('" in selector and "'" in selector.split(":text-is('")[1]:
                    extracted_text = selector.split(":text-is('")[1].split("'")[0]
                    text = extracted_text
                    logger.info(f"Extracted text from selector: '{text}'")
                elif "text=" in selector:
                    parts = selector.split("text=")
                    if len(parts) > 1:
                        if "'" in parts[1]:
                            extracted_text = parts[1].split("'")[1] if "'" in parts[1] else parts[1]
                            text = extracted_text
                            logger.info(f"Extracted text from selector: '{text}'")
                
                # If we couldn't extract text, try using the selector directly first
                if not text:
                    try:
                        logger.info(f"Attempting direct click with selector before smart strategies: {selector}")
                        await page.click(selector)
                        result = {
                            "status": "success",
                            "message": f"Clicked element with selector: {selector}",
                            "selector_used": selector
                        }
                        
                        if capture_screenshot:
                            screenshot_path = f"smart_click_{asyncio.get_event_loop().time()}.png"
                            await page.screenshot(path=screenshot_path)
                            result["screenshot"] = screenshot_path
                            
                        return result
                    except Exception as e:
                        logger.info(f"Direct click with selector failed: {str(e)}, trying smart strategies")
                        # If direct click fails, set a generic text to continue with smart strategies
                        text = "Submit" # Default fallback text
            
            if not text:
                return {"status": "error", "message": "Either text or a valid selector must be provided"}
                
            # Create variations of the text for fuzzy matching
            text_variations = [
                text,
                text.lower(),
                text.upper(),
                text.title(),
                # Common variations for buttons
                f"Submit {text}",
                f"Confirm {text}",
                f"Place {text}",
                f"Complete {text}",
                # Common action variations
                "Submit",
                "Continue",
                "Proceed",
                "Next",
                "Confirm",
                "OK",
                "Checkout",
                "Place Order"
            ]
            
            # Generate selectors based on element type
            selectors = []
            
            if element_type == "button" or element_type == "any":
                # Button selectors
                for variation in text_variations:
                    selectors.extend([
                        f"button:has-text('{variation}')",
                        f"button:text-is('{variation}')",
                        f"button[value='{variation}']",
                        f"input[type='submit'][value='{variation}']",
                        f"[role='button']:has-text('{variation}')",
                        f".btn:has-text('{variation}')",
                        f".button:has-text('{variation}')"
                    ])
            
            if element_type == "link" or element_type == "any":
                # Link selectors
                for variation in text_variations:
                    selectors.extend([
                        f"a:has-text('{variation}')",
                        f"a:text-is('{variation}')",
                        f"[role='link']:has-text('{variation}')"
                    ])
            
            if element_type == "any":
                # General selectors for any clickable element
                for variation in text_variations:
                    selectors.extend([
                        f":has-text('{variation}'):visible",
                        f"[aria-label='{variation}']",
                        f"[title='{variation}']",
                        f"[name='{variation}']",
                        f"[data-test='{variation}']"
                    ])
            
            # Try each selector until one works
            for selector in selectors:
                try:
                    # Check if element exists and is visible
                    is_visible = await page.is_visible(selector, timeout=1000)
                    if is_visible:
                        print(f"Smart click found element with selector: {selector}")
                        await page.click(selector)
                        
                        result = {
                            "status": "success",
                            "message": f"Smart click succeeded with selector: {selector}",
                            "matched_text": text,
                            "selector_used": selector
                        }
                        
                        if capture_screenshot:
                            screenshot_path = f"smart_click_{asyncio.get_event_loop().time()}.png"
                            await page.screenshot(path=screenshot_path)
                            result["screenshot"] = screenshot_path
                            
                        return result
                except Exception:
                    # Continue to next selector if this one fails
                    continue
            
            # If we get here, none of the selectors worked, try fallback strategies
            logger.info(f"Standard smart click strategies failed for '{text}', trying advanced fallbacks")
            
            # Fallback 1: Try accessibility locator
            try:
                logger.info("Trying accessibility locator as fallback")
                a11y_result = await self.playwright_accessibility_locator(
                    description=text,
                    action="click",
                    page_index=page_index
                )
                
                if a11y_result["status"] == "success" and a11y_result.get("element_found"):
                    result = {
                        "status": "success",
                        "message": f"Clicked element using accessibility locator fallback",
                        "matched_text": text,
                        "fallback_method": "accessibility_locator"
                    }
                    
                    if capture_screenshot:
                        screenshot_path = f"smart_click_a11y_{asyncio.get_event_loop().time()}.png"
                        await page.screenshot(path=screenshot_path)
                        result["screenshot"] = screenshot_path
                        
                    return result
            except Exception as a11y_error:
                logger.info(f"Accessibility locator fallback failed: {str(a11y_error)}")
            
            # Fallback 2: Try vision locator
            try:
                logger.info("Trying vision locator as fallback")
                vision_result = await self.playwright_vision_locator(
                    text=text,
                    action="click",
                    page_index=page_index
                )
                
                if vision_result["status"] == "success":
                    result = {
                        "status": "success",
                        "message": f"Clicked element using vision locator fallback",
                        "matched_text": text,
                        "fallback_method": "vision_locator"
                    }
                    
                    if capture_screenshot:
                        screenshot_path = f"smart_click_vision_{asyncio.get_event_loop().time()}.png"
                        await page.screenshot(path=screenshot_path)
                        result["screenshot"] = screenshot_path
                        
                    return result
            except Exception as vision_error:
                logger.info(f"Vision locator fallback failed: {str(vision_error)}")
            
            # Fallback 3: Try JavaScript evaluation
            try:
                logger.info("Trying JavaScript evaluation as final fallback")
                js_result = await self.playwright_js_locate(
                    description=text,
                    action="click",
                    page_index=page_index
                )
                
                if js_result["status"] == "success" and js_result.get("element_found"):
                    result = {
                        "status": "success",
                        "message": f"Clicked element using JavaScript evaluation fallback",
                        "matched_text": text,
                        "fallback_method": "js_locate"
                    }
                    
                    if capture_screenshot:
                        screenshot_path = f"smart_click_js_{asyncio.get_event_loop().time()}.png"
                        await page.screenshot(path=screenshot_path)
                        result["screenshot"] = screenshot_path
                        
                    return result
            except Exception as js_error:
                logger.info(f"JavaScript evaluation fallback failed: {str(js_error)}")
            
            # If we get here, all strategies failed
            # Take a debug screenshot for analysis
            debug_screenshot = None
            if capture_screenshot:
                debug_screenshot = f"smart_click_failed_{asyncio.get_event_loop().time()}.png"
                await page.screenshot(path=debug_screenshot)
                
            return {
                "status": "error", 
                "message": f"Smart click failed: Could not find clickable element matching '{text}'",
                "tried_selectors": selectors[:5],  # Return first few selectors tried (limit result size)
                "fallbacks_tried": ["accessibility_locator", "vision_locator", "js_locate"],
                "debug_screenshot": debug_screenshot
            }
            
        except Exception as e:
            logger.error(f"Error in smart click: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def playwright_find_element(self, description: str, page_index: int = 0, 
                                     max_results: int = 5) -> Dict[str, Any]:
        """
        Find elements based on natural language description and return information about matches.
        
        Args:
            description: Natural language description of the element to find
            page_index: Index of the page to search in
            max_results: Maximum number of matching elements to return
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Parse description to identify key terms
            terms = description.lower().split()
            element_type = None
            
            # Try to detect element type from description
            type_indicators = {
                "button": ["button", "submit", "click"],
                "input": ["input", "field", "text box", "enter", "type"],
                "link": ["link", "anchor", "href", "navigate"],
                "image": ["image", "picture", "photo", "img"],
                "dropdown": ["dropdown", "select", "option", "menu"],
                "checkbox": ["checkbox", "check box", "tick"],
                "radio": ["radio", "radio button"],
                "form": ["form", "submit form"]
            }
            
            for etype, indicators in type_indicators.items():
                if any(indicator in description.lower() for indicator in indicators):
                    element_type = etype
                    break
            
            # Extract potential text content
            text_content = None
            text_indicators = ["text", "says", "displaying", "containing", "with text", "labeled"]
            for indicator in text_indicators:
                if indicator in description.lower():
                    parts = description.lower().split(indicator)
                    if len(parts) > 1:
                        text_content = parts[1].strip().strip('"\'')
                        break
            
            # Create selectors based on the description
            selectors = []
            
            # Type-specific selectors
            if element_type == "button":
                selectors.extend([
                    "button",
                    "input[type='submit']",
                    "input[type='button']",
                    "[role='button']",
                    ".btn",
                    ".button"
                ])
            elif element_type == "input":
                selectors.extend([
                    "input[type='text']",
                    "input:not([type='submit']):not([type='button']):not([type='checkbox']):not([type='radio'])",
                    "textarea",
                    "[role='textbox']"
                ])
            elif element_type == "link":
                selectors.extend([
                    "a",
                    "[role='link']"
                ])
            elif element_type == "image":
                selectors.extend([
                    "img",
                    "svg",
                    "canvas",
                    "[role='img']"
                ])
            elif element_type == "dropdown":
                selectors.extend([
                    "select",
                    "[role='combobox']",
                    "[role='listbox']"
                ])
            elif element_type == "checkbox":
                selectors.extend([
                    "input[type='checkbox']",
                    "[role='checkbox']"
                ])
            elif element_type == "radio":
                selectors.extend([
                    "input[type='radio']",
                    "[role='radio']"
                ])
            
            # If no specific type is identified, use generic selectors
            if not element_type or not selectors:
                selectors = ["button", "a", "input", "select", "[role='button']", "[role='link']"]
            
            # Add text content refinement if available
            if text_content:
                text_selectors = []
                for selector in selectors:
                    text_selectors.append(f"{selector}:has-text('{text_content}')")
                    text_selectors.append(f"{selector}[placeholder*='{text_content}']")
                    text_selectors.append(f"{selector}[aria-label*='{text_content}']")
                    text_selectors.append(f"{selector}[title*='{text_content}']")
                selectors = text_selectors
            
            # Find matching elements
            elements = []
            for selector in selectors:
                try:
                    matches = await page.query_selector_all(selector)
                    for match in matches:
                        if len(elements) >= max_results:
                            break
                            
                        # Get properties for this element
                        tag_name = await page.evaluate("el => el.tagName?.toLowerCase()", match)
                        text = await page.evaluate("el => el.textContent?.trim() || el.value || ''", match)
                        placeholder = await page.evaluate("el => el.placeholder || ''", match)
                        aria_label = await page.evaluate("el => el.getAttribute('aria-label') || ''", match)
                        is_visible = await match.is_visible()
                        is_enabled = await page.evaluate("el => !el.disabled", match)
                        
                        # Create selector that uniquely identifies this element
                        unique_selector = await page.evaluate("el => {" + """
                            const getUniquePath = (el) => {
                                if (el.id) return `#${el.id}`;
                                if (el.className && typeof el.className === 'string') {
                                    const classes = el.className.split(' ').filter(c => c).join('.');
                                    if (classes) return `${el.tagName.toLowerCase()}.${classes}`;
                                }
                                return el.tagName.toLowerCase();
                            };
                            return getUniquePath(arguments[0]);
                        """ + "}", match)
                        
                        # Skip duplicates (elements we've already found with different selectors)
                        if any(e["unique_selector"] == unique_selector for e in elements):
                            continue
                            
                        elements.append({
                            "tag": tag_name,
                            "text": text[:50] + ("..." if len(text) > 50 else ""),
                            "placeholder": placeholder,
                            "aria_label": aria_label,
                            "is_visible": is_visible,
                            "is_enabled": is_enabled,
                            "selector": selector,
                            "unique_selector": unique_selector
                        })
                        
                except Exception:
                    # Continue to next selector if this one fails
                    continue
                    
                if len(elements) >= max_results:
                    break
            
            return {
                "status": "success" if elements else "error",
                "message": f"Found {len(elements)} elements matching '{description}'",
                "elements": elements,
                "element_type_detected": element_type
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_adaptive_action(self, action: str, primary_selector: str, 
                                        fallback_selectors: List[str] = None, text_input: str = "", 
                                        page_index: int = 0) -> Dict[str, Any]:
        """
        Perform actions with fallback strategies, trying multiple approaches when primary fails.
        
        Args:
            action: Action to perform ('click', 'fill', 'hover', 'select')
            primary_selector: Main selector to try first
            fallback_selectors: List of fallback selectors to try if primary fails
            text_input: Text to input (for 'fill' or 'select' actions)
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        # Default fallback selectors if none provided
        if not fallback_selectors:
            fallback_selectors = []
        
        # Add all selectors to try
        selectors_to_try = [primary_selector] + fallback_selectors
        
        # Track errors for debugging
        errors = []
        
        try:
            # Try each selector until one works
            for selector in selectors_to_try:
                try:
                    # Check if element exists and is visible
                    is_visible = await page.is_visible(selector, timeout=2000)
                    if not is_visible:
                        errors.append(f"Element not visible: {selector}")
                        continue
                    
                    # Execute the requested action
                    if action == "click":
                        await page.click(selector)
                    elif action == "fill":
                        await page.fill(selector, text_input)
                    elif action == "hover":
                        await page.hover(selector)
                    elif action == "select":
                        await page.select_option(selector, text_input)
                    else:
                        return {
                            "status": "error",
                            "message": f"Unsupported action: {action}"
                        }
                    
                    # Action succeeded
                    return {
                        "status": "success",
                        "message": f"Adaptive {action} succeeded with selector: {selector}",
                        "selector_used": selector,
                        "attempted_selectors": selectors_to_try.index(selector) + 1  # How many we tried
                    }
                    
                except Exception as e:
                    # Record the error and continue to next selector
                    errors.append(f"Error with {selector}: {str(e)}")
                    continue
            
            # If we get here, none of the selectors worked
            return {
                "status": "error",
                "message": f"Adaptive {action} failed: Could not perform action with any selector",
                "selectors_tried": selectors_to_try,
                "errors": errors[:5]  # Return first few errors for debugging (limit result size)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Advanced Inspection and Debug Tools ===

    async def playwright_inspector(self, selector: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Launch Playwright Inspector for debugging element selection issues.
        Helps identify why elements aren't being found with standard selectors.
        
        Args:
            selector: Optional selector to highlight in the inspector
            page_index: Index of the page to inspect
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # We can't directly launch the Playwright Inspector programmatically,
            # but we can provide debugging information about the selector
            
            # Capture page info
            url = page.url
            title = await page.title()
            
            # Check if selector exists (if provided)
            selector_info = {}
            if selector:
                try:
                    # Check if selector exists
                    element = await page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        selector_info = {
                            "exists": True,
                            "is_visible": is_visible,
                            "attributes": await page.evaluate("""(el) => {
                                const attrs = {};
                                for (const attr of el.attributes) {
                                    attrs[attr.name] = attr.value;
                                }
                                return attrs;
                            }""", element),
                            "bounding_box": await element.bounding_box(),
                            "tag_name": await page.evaluate("el => el.tagName", element),
                            "inner_text": await element.inner_text()
                        }
                    else:
                        selector_info = {
                            "exists": False,
                            "message": f"Element with selector '{selector}' not found"
                        }
                except Exception as e:
                    selector_info = {
                        "exists": False,
                        "error": str(e)
                    }
            
            # Get page structure info
            page_structure = await page.evaluate("""() => {
                function getBasicDOMInfo(element, depth = 0, maxDepth = 3) {
                    if (depth > maxDepth) return { tag: '...', truncated: true };
                    
                    const children = Array.from(element.children).map(child => 
                        getBasicDOMInfo(child, depth + 1, maxDepth)
                    );
                    
                    return {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || undefined,
                        className: element.className || undefined,
                        children: children.length > 0 ? children : undefined
                    };
                }
                
                return getBasicDOMInfo(document.body);
            }""")
            
            # Get console messages
            console_messages = self.console_logs[-20:] if self.console_logs else []
            
            # Take a screenshot for reference
            screenshot_path = f"inspector_debug_{int(time.time())}.png"
            await page.screenshot(path=screenshot_path)
            
            return {
                "status": "success",
                "message": "Collected debugging information for page inspection",
                "url": url,
                "title": title,
                "selector_info": selector_info,
                "page_structure_sample": page_structure,
                "console_messages": console_messages,
                "screenshot": screenshot_path,
                "debugging_tip": "For interactive debugging, run Playwright with the --inspector flag"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_cdp_evaluate(self, script: str, page_index: int = 0) -> Dict[str, Any]:
        """
        Execute Chrome DevTools Protocol commands for advanced debugging and interaction.
        Useful when standard Playwright methods fail to locate or interact with elements.
        
        Args:
            script: JavaScript to execute via CDP
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create a CDP session with the page
            cdp_session = await page.context.new_cdp_session(page)
            
            # Execute the provided JavaScript
            result = await cdp_session.send('Runtime.evaluate', {
                'expression': script,
                'returnByValue': True,
                'awaitPromise': True
            })
            
            if 'exceptionDetails' in result:
                return {
                    "status": "error",
                    "message": "Script execution failed",
                    "error": result['exceptionDetails']
                }
            
            return {
                "status": "success",
                "message": "CDP script executed successfully",
                "result": result.get('result', {}).get('value')
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_devtools_info(self, page_index: int = 0) -> Dict[str, Any]:
        """
        Collect debugging information that would be available in Chrome DevTools UI.
        Provides insights into page structure, network activity, and console messages.
        
        Args:
            page_index: Index of the page to analyze
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create a CDP session
            cdp_session = await page.context.new_cdp_session(page)
            
            # Collect information from various DevTools domains
            
            # Get DOM structure
            dom_result = await cdp_session.send('DOM.getDocument', {
                'depth': 3,  # Limit depth to avoid huge responses
                'pierce': False
            })
            
            # Get performance metrics
            performance = await cdp_session.send('Performance.getMetrics')
            
            # Get network requests
            network_result = await page.evaluate("""() => {
                const resources = performance.getEntriesByType('resource');
                return resources.map(r => ({
                    name: r.name,
                    entryType: r.entryType,
                    startTime: r.startTime,
                    duration: r.duration,
                    initiatorType: r.initiatorType
                })).slice(0, 20); // Limit to 20 entries
            }""")
            
            # Get console messages
            console_messages = self.console_logs[-10:] if self.console_logs else []
            
            # Take a screenshot
            screenshot_path = f"devtools_debug_{int(time.time())}.png"
            await page.screenshot(path=screenshot_path)
            
            return {
                "status": "success",
                "message": "Collected Chrome DevTools debugging information",
                "url": page.url,
                "dom_sample": dom_result['root'],
                "performance_metrics": performance['metrics'],
                "network_requests": network_result,
                "console_messages": console_messages,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Advanced Locator Strategy Tools ===

    async def playwright_accessibility_locator(self, description: str, action: str = "find", 
                                              text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Use accessibility tree to locate elements based on semantic roles and labels.
        More resilient to DOM structure changes than standard selectors.
        
        Args:
            description: Description of the element to find (e.g., "Submit button", "Search field")
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Get accessibility tree from the page
            accessibility_tree = await page.accessibility.snapshot()
            
            # Extract words from description
            keywords = description.lower().split()
            
            # Helper function to search the tree recursively
            def search_tree(node, depth=0, path=""):
                matches = []
                score = 0
                
                # Calculate match score for this node
                node_text = (node.get('name', '') + ' ' + node.get('role', '')).lower()
                for keyword in keywords:
                    if keyword in node_text:
                        score += 1
                
                # If this node matches, add it to results
                if score > 0:
                    matches.append({
                        'node': node,
                        'score': score,
                        'path': path,
                        'depth': depth
                    })
                
                # Search children recursively
                for i, child in enumerate(node.get('children', [])):
                    child_matches = search_tree(child, depth + 1, f"{path}/{i}")
                    matches.extend(child_matches)
                
                return matches
            
            # Search the accessibility tree
            all_matches = search_tree(accessibility_tree)
            
            # Sort matches by score (highest first)
            all_matches.sort(key=lambda x: (-x['score'], x['depth']))
            
            if not all_matches:
                return {
                    "status": "error",
                    "message": f"No elements matching '{description}' found in accessibility tree"
                }
            
            # Get best match
            best_match = all_matches[0]
            
            # Try to find corresponding DOM element
            element = None
            try:
                # Try using role and name for ARIA elements
                if best_match['node'].get('role') and best_match['node'].get('name'):
                    selector = f"[role='{best_match['node']['role']}'][aria-label='{best_match['node']['name']}']"
                    element = await page.query_selector(selector)
                
                # If that fails, try using the computed path
                if not element and 'computed' in best_match['node']:
                    selector = best_match['node']['computed']
                    element = await page.query_selector(selector)
                
                # As a last resort, try searching by text content
                if not element and best_match['node'].get('name'):
                    selector = f":text-is('{best_match['node']['name']}')"
                    element = await page.query_selector(selector)
            except Exception:
                # If we can't find the element, we'll return the a11y info without performing an action
                pass
            
            # Perform the requested action if we found an element
            action_result = None
            if element and action != "find":
                if action == "click":
                    await element.click()
                    action_result = "Clicked element"
                elif action == "fill" and text_input:
                    await element.fill(text_input)
                    action_result = f"Filled element with '{text_input}'"
            
            # Get the node from best match
            node = best_match['node']
            
            return {
                "status": "success",
                "message": f"Found element using accessibility tree: {node.get('role')} '{node.get('name')}'",
                "element_found": element is not None,
                "action_performed": action_result,
                "element_details": {
                    "role": node.get('role'),
                    "name": node.get('name'),
                    "value": node.get('value'),
                    "description": node.get('description')
                },
                "match_score": best_match['score'],
                "all_matches_count": len(all_matches)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_vision_locator(self, text: str, exact: bool = False, 
                                       action: str = "find", text_input: str = "", 
                                       page_index: int = 0) -> Dict[str, Any]:
        """
        Locate elements by visual text content using Playwright's getByText/getByRole functions.
        Useful for interacting with elements that are visually identifiable but lack good selectors.
        
        Args:
            text: Visible text to locate
            exact: Whether to match the exact text or allow partial matches
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Try different approaches to locate the element
            element = None
            method_used = None
            
            # Try by text (most direct approach)
            try:
                if exact:
                    element = page.get_by_text(text, exact=True)
                else:
                    element = page.get_by_text(text)
                
                # Check if element exists
                if await element.count() > 0:
                    method_used = "get_by_text"
                else:
                    element = None
            except Exception:
                # Continue to next approach
                pass
            
            # Try by role with name
            if not element:
                try:
                    # Try common interactive roles
                    for role in ["button", "link", "checkbox", "radio", "textbox", "combobox"]:
                        role_element = page.get_by_role(role, name=text, exact=exact)
                        if await role_element.count() > 0:
                            element = role_element
                            method_used = f"get_by_role({role})"
                            break
                except Exception:
                    # Continue to next approach
                    pass
            
            # Try by label
            if not element:
                try:
                    label_element = page.get_by_label(text, exact=exact)
                    if await label_element.count() > 0:
                        element = label_element
                        method_used = "get_by_label"
                except Exception:
                    # Continue to next approach
                    pass
            
            # Try by placeholder
            if not element:
                try:
                    placeholder_element = page.get_by_placeholder(text, exact=exact)
                    if await placeholder_element.count() > 0:
                        element = placeholder_element
                        method_used = "get_by_placeholder"
                except Exception:
                    # Continue to next approach
                    pass
            
            if not element:
                return {
                    "status": "error",
                    "message": f"No elements with text '{text}' found"
                }
            
            # Get element properties
            element_count = await element.count()
            is_visible = await element.first.is_visible() if element_count > 0 else False
            
            # Perform the requested action
            action_result = None
            if is_visible and action != "find":
                if action == "click":
                    await element.first.click()
                    action_result = "Clicked element"
                elif action == "fill" and text_input:
                    await element.first.fill(text_input)
                    action_result = f"Filled element with '{text_input}'"
            
            # Take a screenshot with the element highlighted
            screenshot_path = None
            if is_visible:
                try:
                    # Highlight the element with a red border
                    await page.evaluate("""(selector) => {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            el.style.border = '2px solid red';
                        }
                    }""", element.first.evaluate("el => CSS.escape(el.outerHTML)"))
                    
                    screenshot_path = f"vision_locator_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path)
                    
                    # Remove the highlight
                    await page.evaluate("""(selector) => {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            el.style.border = '';
                        }
                    }""", element.first.evaluate("el => CSS.escape(el.outerHTML)"))
                except Exception:
                    # If highlighting fails, just continue
                    pass
            
            return {
                "status": "success",
                "message": f"Found element with text '{text}' using {method_used}",
                "method_used": method_used,
                "element_count": element_count,
                "is_visible": is_visible,
                "action_performed": action_result,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_js_locate(self, description: str, action: str = "find", 
                                  text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Use JavaScript evaluation to locate elements when standard methods fail.
        Leverages custom JS to find elements based on various attributes and properties.
        
        Args:
            description: Description of element to find
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create a JS function to find elements based on multiple criteria
            result = await page.evaluate("""(description) => {
                const searchText = description.toLowerCase();
                const keywords = searchText.split(/\\s+/);
                
                function getTextAndAttributesContent(el) {
                    let content = (el.innerText || el.textContent || '').toLowerCase();
                    
                    // Add attribute values to the content
                    const attributesToCheck = ['id', 'name', 'placeholder', 'title', 'aria-label', 'alt', 'role'];
                    for (const attr of attributesToCheck) {
                        if (el.hasAttribute(attr)) {
                            content += ' ' + el.getAttribute(attr).toLowerCase();
                        }
                    }
                    
                    return content;
                }
                
                function scoreElement(el) {
                    const content = getTextAndAttributesContent(el);
                    
                    let score = 0;
                    // Check for each keyword in the content
                    for (const keyword of keywords) {
                        if (content.includes(keyword)) {
                            score += 1;
                        }
                    }
                    
                    // Bonus for interactive elements
                    const tagName = el.tagName.toLowerCase();
                    if (tagName === 'button' || tagName === 'a' || 
                        tagName === 'input' || tagName === 'select') {
                        score += 0.5;
                    }
                    
                    // Bonus for visible elements
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            score += 0.5;
                        }
                    }
                    
                    return score;
                }
                
                // Find all elements
                const allElements = document.querySelectorAll('*');
                
                // Score each element
                const scoredElements = [];
                for (const el of allElements) {
                    const score = scoreElement(el);
                    if (score > 0) {
                        scoredElements.push({
                            score,
                            element: {
                                tagName: el.tagName.toLowerCase(),
                                id: el.id || undefined,
                                className: el.className || undefined,
                                textContent: (el.innerText || el.textContent || '').slice(0, 50),
                                attributes: Object.fromEntries(
                                    Array.from(el.attributes)
                                    .map(attr => [attr.name, attr.value])
                                ),
                                isVisible: (el.offsetWidth > 0 && el.offsetHeight > 0),
                                xpath: getXPath(el)
                            }
                        });
                    }
                }
                
                // Sort by score (highest first)
                scoredElements.sort((a, b) => b.score - a.score);
                
                // Get top results
                const topResults = scoredElements.slice(0, 5);
                
                // Function to get element XPath
                function getXPath(element) {
                    if (!element) return '';
                    
                    // Use id if available
                    if (element.id) {
                        return `//*[@id="${element.id}"]`;
                    }
                    
                    const parts = [];
                    let current = element;
                    
                    while (current && current.nodeType === Node.ELEMENT_NODE) {
                        let index = 0;
                        let sibling = current.previousSibling;
                        
                        while (sibling) {
                            if (sibling.nodeType === Node.ELEMENT_NODE && 
                                sibling.tagName === current.tagName) {
                                index++;
                            }
                            sibling = sibling.previousSibling;
                        }
                        
                        const tagName = current.tagName.toLowerCase();
                        const position = index > 0 ? `[${index + 1}]` : '';
                        parts.unshift(`${tagName}${position}`);
                        
                        current = current.parentNode;
                    }
                    
                    return '/' + parts.join('/');
                }
                
                return {
                    totalMatches: scoredElements.length,
                    topMatches: topResults
                };
            }""", description)
            
            if not result or result['totalMatches'] == 0:
                return {
                    "status": "error",
                    "message": f"No elements matching '{description}' found via JavaScript evaluation"
                }
            
            # Get the best match
            best_match = result['topMatches'][0]
            
            # Try to interact with the element using its XPath
            xpath = best_match['element']['xpath']
            element = None
            
            try:
                element = await page.wait_for_selector(f"xpath={xpath}", timeout=1000)
            except PlaywrightTimeoutError:
                # If XPath fails, try with CSS selector if we have an ID or class
                el_info = best_match['element']
                if el_info['id']:
                    try:
                        element = await page.wait_for_selector(f"#{el_info['id']}", timeout=1000)
                    except PlaywrightTimeoutError:
                        pass
                
                if not element and el_info['className'] and isinstance(el_info['className'], str):
                    class_name = el_info['className'].split(' ')[0]  # Use first class
                    try:
                        element = await page.wait_for_selector(f".{class_name}", timeout=1000)
                    except PlaywrightTimeoutError:
                        pass
            
            # Perform action if element is found
            action_result = None
            if element and action != "find":
                if action == "click":
                    await element.click()
                    action_result = "Clicked element"
                elif action == "fill" and text_input:
                    await element.fill(text_input)
                    action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found element matching '{description}' using JavaScript evaluation",
                "element_found": element is not None,
                "action_performed": action_result,
                "match_score": best_match['score'],
                "element_details": best_match['element'],
                "xpath": xpath,
                "total_matches": result['totalMatches']
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_multi_strategy_locate(self, description: str, action: str = "click", 
                                             text_input: str = "", page_index: int = 0,
                                             capture_screenshot: bool = False) -> Dict[str, Any]:
        """
        Comprehensive tool that tries multiple locator strategies in sequence until one works.
        Combines all advanced strategies for maximum reliability.
        
        Args:
            description: Description of element to find
            action: Action to perform ('click', 'fill', 'select', 'hover')
            text_input: Text to input if action requires it
            page_index: Index of the page to operate on
            capture_screenshot: Whether to capture screenshots during the process
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        attempts = []
        
        try:
            # 1. Try standard selectors first
            standard_selectors = [
                # Try exact text match
                f"text={description}",
                # Try contains text
                f"text='{description}'",
                # Try button with text
                f"button:has-text('{description}')",
                # Try link with text
                f"a:has-text('{description}')",
                # Try input with placeholder
                f"input[placeholder*='{description}']",
                # Try element with aria-label
                f"[aria-label*='{description}']",
                # Try label with text
                f"label:has-text('{description}')"
            ]
            
            for selector in standard_selectors:
                try:
                    attempt = {"strategy": "standard_selector", "selector": selector}
                    element = await page.wait_for_selector(selector, timeout=1000)
                    
                    if element:
                        # Element found, perform action
                        if action == "click":
                            await element.click()
                        elif action == "fill":
                            await element.fill(text_input)
                        elif action == "hover":
                            await element.hover()
                        elif action == "select":
                            await element.select_option(text_input)
                        
                        attempt["result"] = "success"
                        attempts.append(attempt)
                        
                        # Take screenshot if requested
                        screenshot_path = None
                        if capture_screenshot:
                            screenshot_path = f"multi_strategy_{int(time.time())}.png"
                            await page.screenshot(path=screenshot_path)
                        
                        return {
                            "status": "success",
                            "message": f"Located element using standard selector: {selector}",
                            "strategy_used": "standard_selector",
                            "selector_used": selector,
                            "action_performed": action,
                            "screenshot": screenshot_path
                        }
                    
                except Exception as e:
                    attempt["result"] = "failed"
                    attempt["error"] = str(e)
                    attempts.append(attempt)
            
            # 2. Try Playwright's locator API (getBy methods)
            try:
                attempt = {"strategy": "locator_api", "description": description}
                
                # Try different getBy methods
                methods = [
                    {"name": "getByText", "locator": page.get_by_text(description)},
                    {"name": "getByRole_button", "locator": page.get_by_role("button", name=description)},
                    {"name": "getByRole_link", "locator": page.get_by_role("link", name=description)},
                    {"name": "getByLabel", "locator": page.get_by_label(description)},
                    {"name": "getByPlaceholder", "locator": page.get_by_placeholder(description)},
                    {"name": "getByAltText", "locator": page.get_by_alt_text(description)},
                    {"name": "getByTitle", "locator": page.get_by_title(description)}
                ]
                
                for method in methods:
                    locator = method["locator"]
                    if await locator.count() > 0:
                        # Element found, perform action
                        if action == "click":
                            await locator.click()
                        elif action == "fill":
                            await locator.fill(text_input)
                        elif action == "hover":
                            await locator.hover()
                        
                        attempt["result"] = "success"
                        attempt["method"] = method["name"]
                        attempts.append(attempt)
                        
                        # Take screenshot if requested
                        screenshot_path = None
                        if capture_screenshot:
                            screenshot_path = f"multi_strategy_{int(time.time())}.png"
                            await page.screenshot(path=screenshot_path)
                        
                        return {
                            "status": "success",
                            "message": f"Located element using locator API: {method['name']}",
                            "strategy_used": "locator_api",
                            "method_used": method["name"],
                            "action_performed": action,
                            "screenshot": screenshot_path
                        }
                
                attempt["result"] = "failed"
                attempt["error"] = "No matching elements found with locator API"
                attempts.append(attempt)
                
            except Exception as e:
                attempt["result"] = "failed"
                attempt["error"] = str(e)
                attempts.append(attempt)
            
            # 3. Try accessibility tree based location
            try:
                attempt = {"strategy": "accessibility_tree", "description": description}
                
                a11y_result = await self.playwright_accessibility_locator(
                    description=description,
                    action=action,
                    text_input=text_input,
                    page_index=page_index
                )
                
                if a11y_result["status"] == "success" and a11y_result.get("element_found"):
                    attempt["result"] = "success"
                    attempts.append(attempt)
                    
                    # Take screenshot if requested
                    screenshot_path = None
                    if capture_screenshot:
                        screenshot_path = f"multi_strategy_{int(time.time())}.png"
                        await page.screenshot(path=screenshot_path)
                    
                    return {
                        "status": "success",
                        "message": f"Located element using accessibility tree",
                        "strategy_used": "accessibility_tree",
                        "element_details": a11y_result.get("element_details"),
                        "action_performed": action,
                        "screenshot": screenshot_path
                    }
                
                attempt["result"] = "failed"
                attempt["error"] = "No matching elements found in accessibility tree"
                attempts.append(attempt)
                
            except Exception as e:
                attempt["result"] = "failed"
                attempt["error"] = str(e)
                attempts.append(attempt)
            
            # 4. Try JavaScript-based location
            try:
                attempt = {"strategy": "javascript", "description": description}
                
                js_result = await self.playwright_js_locate(
                    description=description,
                    action=action,
                    text_input=text_input,
                    page_index=page_index
                )
                
                if js_result["status"] == "success" and js_result.get("element_found"):
                    attempt["result"] = "success"
                    attempts.append(attempt)
                    
                    # Take screenshot if requested
                    screenshot_path = None
                    if capture_screenshot:
                        screenshot_path = f"multi_strategy_{int(time.time())}.png"
                        await page.screenshot(path=screenshot_path)
                    
                    return {
                        "status": "success",
                        "message": f"Located element using JavaScript evaluation",
                        "strategy_used": "javascript",
                        "element_details": js_result.get("element_details"),
                        "action_performed": action,
                        "screenshot": screenshot_path
                    }
                
                attempt["result"] = "failed"
                attempt["error"] = "No matching elements found via JavaScript"
                attempts.append(attempt)
                
            except Exception as e:
                attempt["result"] = "failed"
                attempt["error"] = str(e)
                attempts.append(attempt)
            
            # If we got here, all strategies failed
            
            # Take a final screenshot to help with debugging
            debug_screenshot = None
            if capture_screenshot:
                debug_screenshot = f"multi_strategy_failed_{int(time.time())}.png"
                await page.screenshot(path=debug_screenshot)
            
            # Collect information about the page to help debug why nothing worked
            page_info = {
                "url": page.url,
                "title": await page.title(),
                "content_snippet": await page.evaluate("() => document.body.innerText.substring(0, 500)")
            }
            
            return {
                "status": "error",
                "message": f"Failed to locate element matching '{description}' with any strategy",
                "attempted_strategies": [a["strategy"] for a in attempts],
                "detailed_attempts": attempts,
                "page_info": page_info,
                "debug_screenshot": debug_screenshot,
                "suggestion": "Try using more specific description or inspect the page manually"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)} 

    async def playwright_auto_execute(self, action: str, target: str, value: str = "", 
                               page_index: int = 0, max_attempts: int = 3, 
                               capture_screenshot: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Meta-tool that automatically tries multiple approaches to perform an action.
        Handles fallbacks between different tools based on context and previous failures.
        
        This is the recommended entry point for all browser automation actions as it
        incorporates a complete fallback chain that maximizes success rates.
        
        Args:
            action: Action to perform ('navigate', 'click', 'fill', 'press_key', 'screenshot', etc.)
            target: Target description or selector (or filename for 'screenshot' action)
            value: Value to use (text for fill, key for press_key, etc.)
            page_index: Index of the page to operate on
            max_attempts: Maximum number of retry attempts for each strategy
            capture_screenshot: Whether to capture screenshots during execution
            **kwargs: Additional keyword arguments to pass to the specific tool
                      For screenshot action, you can pass 'selector' to screenshot a specific element
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        attempts = []
        logger.info(f"Auto-executing action '{action}' on target '{target}'")
        
        try:
            # First attempt: Map action to corresponding tool and try it directly
            primary_tool_name = f"playwright_{action}"
            primary_tool = getattr(self, primary_tool_name, None)
            
            if not primary_tool:
                logger.error(f"Unknown action: {action}. No tool named {primary_tool_name} found.")
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}. No tool named {primary_tool_name} found."
                }
            
            # Configure arguments based on action type
            if action == "navigate":
                tool_args = {"url": target, "page_index": page_index, "capture_screenshot": capture_screenshot}
            elif action == "click":
                tool_args = {
                    "selector": target, 
                    "page_index": page_index, 
                    "capture_screenshot": capture_screenshot,
                    "fallback": True  # Enable fallbacks in playwright_click
                }
            elif action == "fill":
                tool_args = {"selector": target, "text": value, "page_index": page_index}
            elif action == "press_key":
                tool_args = {"key": target, "page_index": page_index}
            elif action == "select":
                tool_args = {"selector": target, "value": value, "page_index": page_index}
            elif action == "screenshot":
                # Use 'filename' instead of 'path' for screenshot
                tool_args = {
                    "filename": target if target else f"screenshot_{int(time.time())}.png", 
                    "page_index": page_index
                }
                # Add selector if provided in kwargs
                if "selector" in kwargs:
                    tool_args["selector"] = kwargs["selector"]
            elif action == "smart_click":
                # Handle smart_click specially to accommodate both text and selector
                if target.startswith(":has-text") or target.startswith("[aria-label") or target.startswith("#") or target.startswith("."):
                    # This looks like a selector
                    tool_args = {
                        "selector": target, 
                        "page_index": page_index, 
                        "capture_screenshot": capture_screenshot
                    }
                else:
                    # Treat as text
                    tool_args = {
                        "text": target, 
                        "page_index": page_index, 
                        "capture_screenshot": capture_screenshot
                    }
            else:
                # Generic fallback for other actions
                tool_args = {"selector": target, "page_index": page_index, "capture_screenshot": capture_screenshot}
                if value:
                    tool_args["text"] = value
                    
            # Merge any additional kwargs
            tool_args.update({k: v for k, v in kwargs.items() if k not in tool_args})
            
            # Log the attempt
            logger.info(f"Attempting direct {action} with target '{target}'")
            attempt = {"strategy": "direct", "tool": primary_tool_name, "arguments": tool_args}
            
            # Try direct tool first
            try:
                # Check if we have a valid method
                if not hasattr(self, primary_tool_name):
                    logger.error(f"Tool {primary_tool_name} does not exist")
                    attempt["result"] = "error"
                    attempt["error"] = f"Tool {primary_tool_name} does not exist"
                    attempts.append(attempt)
                    raise AttributeError(f"Tool {primary_tool_name} does not exist")
                
                # Get the method and verify it's callable
                method = getattr(self, primary_tool_name)
                if not callable(method):
                    logger.error(f"Tool {primary_tool_name} is not callable")
                    attempt["result"] = "error"
                    attempt["error"] = f"Tool {primary_tool_name} is not callable"
                    attempts.append(attempt)
                    raise TypeError(f"Tool {primary_tool_name} is not callable")
                
                # Execute the method with the prepared arguments
                result = await method(**tool_args)
                
                if result.get("status") == "success":
                    logger.info(f"Direct {action} with {primary_tool_name} successful")
                    attempt["result"] = "success"
                    attempts.append(attempt)
                    return {
                        "status": "success",
                        "message": f"Action '{action}' completed successfully with direct tool",
                        "tool_used": primary_tool_name,
                        "details": result
                    }
                else:
                    logger.info(f"Direct {action} with {primary_tool_name} failed: {result.get('message')}")
                    attempt["result"] = "failed"
                    attempt["error"] = result.get("message", "Unknown error")
                    attempts.append(attempt)
            except Exception as e:
                logger.error(f"Error executing {primary_tool_name}: {str(e)}")
                attempt["result"] = "error"
                attempt["error"] = str(e)
                attempts.append(attempt)
            
            # Second attempt: Try with advanced tool variants
            advanced_attempts = []
            
            # Smart click for anything that needs to click
            if action == "click":
                try:
                    smart_click_result = await self.playwright_smart_click(
                        text=target.replace(":has-text('", "").replace("')", ""),
                        page_index=page_index
                    )
                    advanced_attempts.append({
                        "strategy": "smart_click",
                        "result": smart_click_result.get("status"),
                        "details": smart_click_result
                    })
                    if smart_click_result.get("status") == "success":
                        return {
                            "status": "success",
                            "message": f"Action '{action}' completed successfully with smart_click",
                            "tool_used": "playwright_smart_click",
                            "details": smart_click_result
                        }
                except Exception as e:
                    advanced_attempts.append({
                        "strategy": "smart_click",
                        "result": "error",
                        "error": str(e)
                    })
            
            # Multi-strategy locate for any action
            description = target
            if target.startswith("[") and "]" in target:
                # Extract meaningful description from selector
                description = target.split("[")[1].split("]")[0].replace("name=", "").replace("'", "")
            
            try:
                multi_strategy_result = await self.playwright_multi_strategy_locate(
                    description=description,
                    action=action,
                    text_input=value,
                    page_index=page_index,
                    capture_screenshot=True
                )
                advanced_attempts.append({
                    "strategy": "multi_strategy_locate",
                    "result": multi_strategy_result.get("status"),
                    "details": multi_strategy_result
                })
                if multi_strategy_result.get("status") == "success":
                    return {
                        "status": "success",
                        "message": f"Action '{action}' completed successfully with multi-strategy locate",
                        "tool_used": "playwright_multi_strategy_locate",
                        "details": multi_strategy_result
                    }
            except Exception as e:
                advanced_attempts.append({
                    "strategy": "multi_strategy_locate",
                    "result": "error",
                    "error": str(e)
                })
            
            # Vision locator for UI interactions
            try:
                vision_result = await self.playwright_vision_locator(
                    text=description,
                    action=action if action in ["click", "fill"] else "find",
                    text_input=value,
                    page_index=page_index
                )
                advanced_attempts.append({
                    "strategy": "vision_locator",
                    "result": vision_result.get("status"),
                    "details": vision_result
                })
                if vision_result.get("status") == "success":
                    return {
                        "status": "success",
                        "message": f"Action '{action}' completed successfully with vision locator",
                        "tool_used": "playwright_vision_locator", 
                        "details": vision_result
                    }
            except Exception as e:
                advanced_attempts.append({
                    "strategy": "vision_locator", 
                    "result": "error",
                    "error": str(e)
                })
            
            # JavaScript evaluation as last resort
            try:
                js_result = await self.playwright_js_locate(
                    description=description,
                    action=action if action in ["click", "fill"] else "find",
                    text_input=value,
                    page_index=page_index
                )
                advanced_attempts.append({
                    "strategy": "js_locate",
                    "result": js_result.get("status"),
                    "details": js_result
                })
                if js_result.get("status") == "success" and js_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Action '{action}' completed successfully with JavaScript locate",
                        "tool_used": "playwright_js_locate",
                        "details": js_result
                    }
            except Exception as e:
                advanced_attempts.append({
                    "strategy": "js_locate",
                    "result": "error", 
                    "error": str(e)
                })
            
            # If we get here, all strategies failed
            # Take a debug screenshot
            screenshot_path = f"auto_execute_failed_{int(time.time())}.png"
            await page.screenshot(path=screenshot_path)
            
            return {
                "status": "error",
                "message": f"All strategies failed for action '{action}' on target '{target}'",
                "attempts": attempts + advanced_attempts,
                "debug_screenshot": screenshot_path,
                "suggestion": "Check the page structure and try with a different selector or action"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)} 