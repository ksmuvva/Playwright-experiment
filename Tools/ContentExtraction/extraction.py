"""
Content Extraction Tools for MCP - Extract content, take screenshots, and save PDFs
"""
from typing import Dict, Any, Optional
import time

from ..base import PlaywrightBase, logger

class ContentExtractionTools(PlaywrightBase):
    """Tools for extracting content and capturing visual state."""
    
    async def playwright_screenshot(self, filename: str = None, selector: str = "", 
                                  page_index: int = 0, path: str = None, full_page: bool = False, 
                                  output_path: str = None) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            filename: Path to save the screenshot (alternative to path/output_path)
            selector: Optional selector to screenshot a specific element
            page_index: Index of the page to screenshot
            path: Path to save the screenshot (alternative to filename)
            full_page: Whether to take a screenshot of the full scrollable page
            output_path: Path to save the screenshot (alternative to filename/path)
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Handle all parameter options for the output path (output_path, path, filename)
            actual_filename = output_path if output_path else (path if path else filename)
            if not actual_filename:
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
                # Pass the full_page parameter to control if we capture the entire page
                await page.screenshot(path=actual_filename, full_page=full_page)
            
            return {
                "status": "success",
                "message": f"Screenshot saved to {actual_filename}",
                "filename": actual_filename
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
                filename = f"{filename}.pdf"
                
            await page.pdf(path=filename)
            
            return {
                "status": "success",
                "message": f"Saved page as PDF: {filename}",
                "filename": filename
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_get_visible_text(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible text from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            element = await page.query_selector(selector)
            if not element:
                return {"status": "error", "message": f"Element not found: {selector}"}
                
            text_content = await element.text_content()
            
            return {
                "status": "success",
                "text": text_content,
                "length": len(text_content)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_get_visible_html(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get HTML content of the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            element = await page.query_selector(selector)
            if not element:
                return {"status": "error", "message": f"Element not found: {selector}"}
                
            html_content = await element.inner_html()
            
            return {
                "status": "success",
                "html": html_content,
                "length": len(html_content)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
