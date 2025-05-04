"""
Base utilities and common classes for MCP Tools
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

class PlaywrightBase:
    """Base class for Playwright automation."""
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = []
        self.console_logs = []
        self.browser_initialized = False  # Track if browser is initialized
        
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
        """
        Ensure browser is initialized before using it.
        This method preserves existing browser sessions if they're still valid.
        """
        # Check if browser or context is closed or missing in a version-compatible way
        needs_initialization = False
        
        # Check if browser is missing
        if not self.browser or not self.context:
            logger.info("Browser or context is missing - initialization needed")
            needs_initialization = True
        else:
            # Check if browser is closed
            try:
                if hasattr(self.browser, 'is_closed') and self.browser.is_closed():
                    logger.info("Browser is closed - initialization needed")
                    needs_initialization = True
            except Exception as e:
                logger.warning(f"Error checking browser state: {e}")
                # Be conservative - assume initialization is needed if we can't check
                needs_initialization = True
        
        # If browser is still alive, just update the initialization flag
        if self.browser and self.context and not needs_initialization:
            logger.info("Browser is still alive - using existing session")
            self.browser_initialized = True
            # Just ensure our pages array is reset
            self.pages = []
            return
        
        # Only reinitialize if needed
        if needs_initialization:
            try:
                # Clean up any existing resources that might be in an inconsistent state
                try:
                    if self.context:
                        # Check if context has closed method before trying to use it
                        if hasattr(self.context, 'is_closed') and not self.context.is_closed():
                            await self.context.close()
                        else:
                            # Fallback: try to close without checking
                            try:
                                await self.context.close()
                            except:
                                pass
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
                
                try:
                    if self.browser:
                        # Check if browser has closed method before trying to use it
                        if hasattr(self.browser, 'is_closed') and not self.browser.is_closed():
                            await self.browser.close()
                        else:
                            # Fallback: try to close without checking
                            try:
                                await self.browser.close()
                            except:
                                pass
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
                    
                # Reset state before creating new resources
                self.pages = []
                self.browser_initialized = False
                
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
                
                # Create a browser context with the configured viewport
                self.context = await self.browser.new_context(
                    viewport=viewport_size,
                    accept_downloads=True
                )
                
                # Setup event listeners for console logs
                self.context.on("console", lambda msg: self._handle_console_log(msg))
                
                self.browser_initialized = True
                logger.info("Browser initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize browser: {e}")
                raise

    async def _get_page(self, page_index: int) -> Optional[Page]:
        """Get a page by index, creating one if necessary."""
        if page_index < 0:
            logger.error(f"Invalid page index: {page_index}")
            return None
        
        # Ensure browser is initialized
        await self._ensure_browser_initialized()
        
        # Create new pages if needed
        while len(self.pages) <= page_index:
            new_page = await self.context.new_page()
            self.pages.append(new_page)
            logger.info(f"Created new page at index {len(self.pages) - 1}")
        
        return self.pages[page_index]
    
    async def cleanup(self):
        """Cleanup resources but maintain browser persistence."""
        try:
            # Close all pages but keep the browser running
            for page in self.pages:
                await page.close()
                
            self.pages = []
            logger.info("Closed all pages")
            
            # Don't close the browser to enable persistent sessions
            return {"status": "success", "message": "Cleaned up browser resources"}
            
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
            return {"status": "error", "message": str(e)}
    
    async def reset_pages(self):
        """
        Reset pages array without closing any actual browser resources.
        This is the safest option for between-command cleanup to ensure browser persistence.
        """
        try:
            # Just reset the pages array without touching browser resources
            self.pages = []
            logger.info("Reset pages array while preserving browser session")
            
            # Ensure browser state is marked as still initialized
            self.browser_initialized = True if self.browser else False
            
            return {"status": "success", "message": "Reset pages array while preserving browser session"}
            
        except Exception as e:
            logger.error(f"Failed to reset pages: {e}")
            return {"status": "error", "message": str(e)}
            
    def _handle_console_log(self, msg):
        """Handle console log message from browser."""
        self.console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "time": asyncio.get_event_loop().time()
        })
        logger.info(f"Browser console {msg.type}: {msg.text}")
