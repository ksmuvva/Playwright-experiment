#!/usr/bin/env python3
"""
Advanced MCP Server/Client - AI-powered browser automation agent
Uses MCP SDK to communicate with a Playwright server and converts
natural language commands to structured browser automation actions.

This is an experimental prototype with server, client, and tools in one file.
"""
import asyncio
import json
import os
import logging
import tempfile
import base64
import traceback  # Add import for traceback module
from typing import Any, Dict, List, Optional, Tuple, Union
import argparse
import time
import re
import subprocess

import anthropic  # For Claude API integration
from dotenv import load_dotenv

# Import MCP SDK components
import mcp
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
# Fix imports based on what's available in the mcp package
try:
    from mcp.server import MpcServer, Tool, create_tool
except ImportError:
    # If these aren't available, try other possible names or use alternatives
    from mcp.server.fastmcp import FastMCP as MpcServer
    # Define placeholder Tool and create_tool if they don't exist
    class Tool:
        pass
        
    def create_tool(name, description, function, parameters):
        """Create a tool function wrapper."""
        return function

from mcp.server.stdio import stdio_server

# Import tools from our modular structure
try:
    from Tools import PlaywrightTools  # Main integrated tools class
    from Tools.CodeGeneration.codegen import CodeGenSession  # Code generation session class
    print("Successfully imported tools from modular Tools package")
except Exception as e:
    print(f"Error importing from Tools package: {e}")
    print("Traceback:")
    import traceback
    traceback.print_exc()
    
    # Define placeholder classes as last resort
    class PlaywrightTools:
        def __init__(self):
            self.playwright = None
            self.browser = None
            self.context = None
            self.pages = []
            self.browser_initialized = False
            self.active_page_index = 0
            print("Using placeholder PlaywrightTools implementation")
            
        async def is_browser_alive(self):
            """
            Check if the browser is still responsive and available.
            Returns True if the browser is alive, False otherwise.
            """
            if not self.browser:
                print("Browser validation failed: Browser object doesn't exist")
                self.browser_initialized = False
                return False
            
            try:
                # Attempt a simple operation to verify browser is responsive
                try:
                    # Check browser connection status - will throw if browser is closed
                    version = await self.browser.version()
                    print(f"Browser check succeeded: Browser version {version}")
                    return True
                except Exception as browser_error:
                    print(f"Browser connection check failed: {browser_error}")
                    # If we get here, the browser connection failed
                    self.browser_initialized = False
                    return False
            except Exception as e:
                print(f"Browser check failed with exception: {e}")
                # Reset state since browser is no longer valid
                self.browser_initialized = False
                self.browser = None  # Clear the reference to release memory
                return False
            
        async def initialize(self):
            """Initialize Playwright without launching a browser yet."""
            try:
                from playwright.async_api import async_playwright
                self.playwright = await async_playwright().start()
                print("✅ Playwright initialized")
                return True
            except Exception as e:
                print(f"❌ Failed to initialize Playwright: {e}")
                return False
                
        async def verify_browser_page(self, page_index=0):
            """
            Verify browser and page are alive, and recover if needed.
            Returns tuple (browser_ok, page) where:
            - browser_ok: True if browser is ready to use
            - page: The page object if available, None otherwise
            """
            import traceback  # Import traceback module for error reporting
            
            print(f"⏱️ Verifying browser and page state...")
            
            # First check browser existence and initialization state
            if not self.browser_initialized or not self.browser:
                print("📢 Browser not initialized or doesn't exist - initializing now")
                browser_alive = False
            else:
                # Check if the existing browser is still alive
                print("📢 Checking if existing browser is still responsive...")
                browser_alive = await self.is_browser_alive()
                
                if not browser_alive:
                    print("📢 Browser is not responsive - will reinitialize")
                else:
                    print("📢 Browser is responsive - proceeding with checks")
            
            # Initialize/reinitialize browser if needed
            if not browser_alive:
                # Browser needs initialization or recovery
                try:
                    # Initialize Playwright if not already initialized
                    if not self.playwright:
                        print("🚀 Starting Playwright...")
                        from playwright.async_api import async_playwright
                        self.playwright = await async_playwright().start()
                    
                    # Launch browser
                    print("🚀 Launching browser...")
                    self.browser = await self.playwright.chromium.launch(headless=False)
                    
                    # Create context with viewport
                    viewport_size = {"width": 1280, "height": 720}
                    self.context = await self.browser.new_context(
                        viewport=viewport_size,
                        accept_downloads=True
                    )
                    
                    self.browser_initialized = True
                    print("✅ Browser initialized successfully")
                except Exception as e:
                    print(f"❌ Failed to initialize browser: {e}")
                    return False, None
            
            # Create or get page
            page = None
            try:
                if len(self.pages) > page_index and self.pages[page_index]:
                    page = self.pages[page_index]
                else:
                    # Create new page
                    page = await self.context.new_page()
                    # Make sure pages list is long enough
                    while len(self.pages) <= page_index:
                        self.pages.append(None)
                    self.pages[page_index] = page
            except Exception as e:
                print(f"❌ Failed to get/create page: {e}")
                return True, None  # Browser ok but page failed
                
            return True, page
                
        async def playwright_navigate(self, url, wait_until="load", timeout=30000):
            """Navigate to a URL in the browser."""
            try:
                # Verify browser and page
                browser_ok, page = await self.verify_browser_page()
                if not browser_ok or not page:
                    return {"status": "error", "message": "Failed to verify browser/page"}
                
                print(f"🌐 Navigating to: {url}")
                # Perform the navigation
                response = await page.goto(url, wait_until=wait_until, timeout=timeout)
                
                result = {
                    "status": "success",
                    "message": f"Successfully navigated to {url}",
                    "title": await page.title(),
                    "url": page.url
                }
                
                # If response is available, add status info
                if response:
                    result["status_code"] = response.status
                    result["status_text"] = response.status_text
                
                return result
                
            except Exception as e:
                print(f"❌ Navigation failed: {e}")
                return {"status": "error", "message": f"Navigation failed: {str(e)}"}
                
        async def playwright_click(self, selector):
            """Click on an element specified by selector."""
            try:
                # Verify browser and page
                browser_ok, page = await self.verify_browser_page()
                if not browser_ok or not page:
                    return {"status": "error", "message": "Failed to verify browser/page"}
                
                print(f"🖱️ Clicking element: {selector}")
                await page.click(selector)
                
                return {
                    "status": "success",
                    "message": f"Successfully clicked on {selector}"
                }
                
            except Exception as e:
                print(f"❌ Click failed: {e}")
                return {"status": "error", "message": f"Click failed: {str(e)}"}
                
        async def playwright_get_visible_text(self, selector=None):
            """Extract visible text from the page or a specific element."""
            try:
                # Verify browser and page
                browser_ok, page = await self.verify_browser_page()
                if not browser_ok or not page:
                    return {"status": "error", "message": "Failed to verify browser/page"}
                
                if selector:
                    # Get text from specific element
                    print(f"📄 Getting text from element: {selector}")
                    element = await page.query_selector(selector)
                    if not element:
                        return {
                            "status": "error", 
                            "message": f"Element not found: {selector}"
                        }
                    
                    text = await element.text_content()
                    return {
                        "status": "success",
                        "message": f"Successfully extracted text from {selector}",
                        "text": text.strip()
                    }
                else:
                    # Get text from entire page body
                    print("📄 Getting text from entire page")
                    body = await page.query_selector("body")
                    if not body:
                        return {
                            "status": "error",
                            "message": "Could not find body element"
                        }
                    
                    text = await body.text_content()
                    return {
                        "status": "success",
                        "message": "Successfully extracted page text",
                        "text": text.strip()
                    }
                    
            except Exception as e:
                print(f"❌ Text extraction failed: {e}")
                return {"status": "error", "message": f"Text extraction failed: {str(e)}"}
                
        async def cleanup(self):
            """Cleanup resources but maintain browser persistence."""
            try:
                # Close all pages but keep the browser running
                for page in self.pages:
                    if page:
                        try:
                            await page.close()
                        except Exception:
                            pass
                self.pages = []
                self.active_page_index = 0
                print("Cleaned up pages while preserving browser session")
                return {"status": "success", "message": "Cleaned up browser resources"}
            except Exception as e:
                print(f"Failed to cleanup: {e}")
                return {"status": "error", "message": str(e)}

        async def cleanup_all(self):
            """
            Clean up all resources including browser and playwright.
            Ensures proper state tracking even if cleanup fails.
            """
            try:
                # Close all pages
                for page in self.pages:
                    if page:
                        try:
                            await page.close()
                        except Exception:
                            pass
                    
                self.pages = []
                
                # Close browser context
                if self.context:
                    try:
                        await self.context.close()
                    except Exception:
                        pass
                    self.context = None
                
                # Close browser
                if self.browser:
                    try:
                        await self.browser.close()
                    except Exception:
                        pass
                    self.browser = None
                
                # Close playwright
                if self.playwright:
                    try:
                        await self.playwright.stop()
                    except Exception:
                        pass
                    self.playwright = None
                    
                # Always update state regardless of whether operations succeeded
                self.browser_initialized = False
                print("Fully cleaned up all browser resources")
                return {"status": "success", "message": "Fully cleaned up all browser resources"}
                
            except Exception as e:
                print(f"Error in cleanup_all: {e}")
                # Still mark as not initialized even if cleanup failed
                self.browser_initialized = False
                self.browser = None
                self.context = None
                self.playwright = None
                return {"status": "error", "message": str(e)}
                
    class CodeGenSession:
        pass

# Import Playwright dependencies
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, CDPSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_agent")

# Load environment variables
load_dotenv()

# --- Configuration ---
SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", "python")
SERVER_ARGS = os.getenv("MCP_SERVER_ARGS", "playwright_server.py").split()
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-7-sonnet-20250219")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# System prompt template for the LLM
SYSTEM_PROMPT = """You are an AI assistant specialized in browser automation via the Playwright Model Context Protocol (MCP). Your primary role is to interpret natural language commands from users and convert them into precise Playwright automation instructions.

## Your Capabilities

You can help users automate browser tasks by generating tool calls for actions such as:
- Navigating to websites
- Clicking elements
- Typing text
- Pressing keys
- Waiting for elements
- Capturing screenshots
- Extracting content
- Code generation

## CRITICAL OUTPUT FORMAT REQUIREMENTS

YOU MUST RESPOND WITH PURE JSON ONLY. Your entire response must be valid JSON without ANY text before or after it.

DO NOT include any explanations, comments, or markdown formatting in your responses.
DO NOT wrap your JSON in code blocks or any other formatting.
DO NOT say things like "Here's the JSON" or "I'll help you with that".

JUST OUTPUT THE RAW JSON DIRECTLY.

## IMPORTANT GUIDELINES - READ CAREFULLY

1. **ALWAYS break down user requests into separate tool calls** - This is critical
2. For example, "go to website and click a button" MUST be converted to TWO separate tool calls:
   - First tool call: playwright_navigate to the website
   - Second tool call: playwright_click to click the button
3. **NEVER combine multiple actions into a single tool call**
4. When clicking on text links, try these selectors in this order:
   - Exact text match: "a:text('Exact Text')"
   - Contains text: "a:has-text('Partial Text')"
   - Role and name: "[role='link'][name='Link Text']"
5. **PREFER ADVANCED TOOLS over basic ones for better reliability**:
   - Use `playwright_auto_execute` for the most reliable execution with automatic fallbacks
   - Use `playwright_smart_click` instead of `playwright_click` for better success rates
   - Use `playwright_multi_strategy_locate` for complex UI interaction instead of direct methods

## TOOL SELECTION PRIORITY (from most to least preferred)

1. **Best for most cases**: 
   - `playwright_auto_execute` - Meta-tool that tries multiple approaches automatically
   
2. **Specialized tools** (prefer these over basic tools):
   - `playwright_smart_click` - For clicking anything
   - `playwright_multi_strategy_locate` - For any interaction with elements
   - `playwright_vision_locator` - For finding elements by visible text
   
3. **Basic tools** (only use when you're certain the selector is reliable):
   - `playwright_navigate` - For navigation only
   - `playwright_fill` - For entering text
   - `playwright_press_key` - For keyboard input
   - Other basic tools

## AVAILABLE TOOLS - USE ONLY THESE EXACT TOOL NAMES

- playwright_navigate - Navigate to a URL
- playwright_click - Click on an element 
- playwright_fill - Enter text into an input field (NOT playwright_type)
- playwright_press_key - Press a keyboard key (NOT playwright_press)
- playwright_screenshot - Take a screenshot
- playwright_select - Select an option from a dropdown
- playwright_hover - Hover over an element
- playwright_get_visible_text - Extract visible text from the page
- playwright_get_visible_html - Get HTML content
- playwright_smart_click - Smart click with fallback strategies
- playwright_find_element - Find elements by description
- playwright_adaptive_action - Perform actions with fallbacks
- playwright_inspector - Debug element selection issues
- playwright_multi_strategy_locate - Use multiple strategies to find elements

## Advanced Tools for Difficult Cases
- playwright_accessibility_locator - Use accessibility tree for finding elements
- playwright_vision_locator - Locate elements by visual text
- playwright_js_locate - Use JavaScript to find elements
- playwright_cdp_evaluate - Execute Chrome DevTools Protocol commands
- playwright_devtools_info - Get debugging information

## Page Interactions

For clicking on page elements:
- For links with text (like "Advanced usage"), use: `"selector": "a:has-text('Advanced usage')"`
- For buttons with text, use: `"selector": "button:has-text('Button Text')"`
- For navigation links, use: `"selector": "nav a:has-text('Link Text')"`
- For sidebar links, use: `"selector": ".sidebar a:has-text('Link Text')"`

## Response Format

When a user gives you a command, respond with JSON containing tool calls in this format:
{
  "tool_calls": [
    {
      "tool": "[tool_name]",
      "arguments": {
        // tool-specific arguments
      }
    },
    {
      "tool": "[next_tool_name]",
      "arguments": {
        // tool-specific arguments for next step
      }
    }
  ]
}

For cookie consent buttons and popups, use these common selectors:
- Cookie accept buttons: "#accept-cookies", ".cookie-accept", "[aria-label='Accept cookies']", "button:has-text('Accept')"
- Common popups: ".modal-close", ".popup-close", "button:has-text('Close')"

ONLY OUTPUT THE JSON WITH TOOL_CALLS. DO NOT INCLUDE ANY OTHER TEXT, EXPLANATIONS, OR MARKDOWN FORMATTING.
"""

class PlaywrightMCPServer:
    """MCP Server implementation for Playwright."""
    def __init__(self):
        """Initialize the server."""
        self.server = None
        self.tools_instance = PlaywrightTools()
    
    async def start(self):
        """Start the Playwright server."""
        try:
            # Initialize the tools
            tools_initialized = await self.tools_instance.initialize()
            if not tools_initialized:
                logger.error("Failed to initialize tools")
                return False
            
            # Set up the MPC Server with tools
            self.server = MpcServer(
                name="Playwright MCP Server",
                version="0.1.0",
                description="Server for Playwright browser automation",
                tools=self._create_tools()
            )
            
            logger.info("Playwright MCP Server started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def _create_tools(self) -> List[Tool]:
        """Create and return a list of tools using the PlaywrightTools instance."""
        tools = []
        
        # Get all method names from tools_instance
        tool_methods = [name for name in dir(self.tools_instance) 
                       if callable(getattr(self.tools_instance, name)) 
                       and not name.startswith('_')]
        
        print(f"Found {len(tool_methods)} potential tool methods in PlaywrightTools")
        print(f"Available methods: {[m for m in tool_methods]}")
        
        # Create tools for all tool methods
        for method_name in tool_methods:
            # Skip internal methods and non-tool methods
            if method_name.startswith("playwright_"):
                # Get the method object
                method = getattr(self.tools_instance, method_name)
                
                # Get parameter info from type hints and docstring
                parameters = {}
                try:
                    import inspect
                    sig = inspect.signature(method)
                    
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                            
                        param_type = "string"  # Default type
                        
                        # Try to determine parameter type from annotation
                        if param.annotation != inspect.Parameter.empty:
                            if param.annotation == str:
                                param_type = "string"
                            elif param.annotation == int:
                                param_type = "integer"
                            elif param.annotation == bool:
                                param_type = "boolean"
                            elif param.annotation == dict or param.annotation == Dict:
                                param_type = "object"
                            elif param.annotation == list or param.annotation == List:
                                param_type = "array"
                        
                        # Get description from docstring if possible
                        param_desc = f"Parameter for {method_name}"
                        
                        # Add parameter definition
                        parameters[param_name] = {
                            "type": param_type,
                            "description": param_desc
                        }
                    
                    # Extract description from method docstring
                    description = method.__doc__ or f"Tool for {method_name}"
                    description = description.strip().split("\n")[0]  # Get first line
                    
                    # Create the tool
                    tools.append(create_tool(
                        name=method_name,
                        description=description,
                        function=method,
                        parameters=parameters
                    ))
                    
                    print(f"Created tool wrapper for {method_name}")
                except Exception as e:
                    print(f"Error creating tool for {method_name}: {str(e)}")
                    continue
        
        print(f"Created {len(tools)} tool wrappers from PlaywrightTools")
        return tools

    async def stop(self):
        """Stop the server and cleanup resources."""
        try:
            await self.tools_instance.cleanup()
            logger.info("Playwright MCP Server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

class MCPClient:
    """Advanced MCP Client that communicates with a Playwright server."""
    def __init__(self):
        """Initialize the MCP client."""
        self.session = None
        self.tools = []
        self.last_plan = None
        self.server_params = StdioServerParameters(
            command=SERVER_COMMAND,
            args=SERVER_ARGS,
            env=os.environ.copy()
        )
        
        # Initialize LLM client
        if not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set. LLM integration will not work.")
            self.llm_client = None
        else:
            try:
                self.llm_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.llm_client = None

    async def connect(self) -> bool:
        """Connect to the MCP server and initialize session."""
        try:
            logger.info(f"Connecting to server: {SERVER_COMMAND} {' '.join(SERVER_ARGS)}")
            reader, writer = await stdio_client(self.server_params)
            
            self.session = ClientSession(
                reader, 
                writer, 
                sampling_callback=self.handle_sampling_message
            )
            
            # Initialize the session
            init_response = await self.session.initialize()
            logger.info(f"Connected to server: {init_response.serverInfo.name} v{init_response.serverInfo.version}")
            
            # Get available tools
            await self.discover_tools()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False

    async def discover_tools(self) -> None:
        """Discover available tools from the server."""
        if not self.session:
            logger.error("Session not initialized")
            return
        
        try:
            self.tools = await self.session.list_tools()
            logger.info(f"Discovered {len(self.tools)} tools")
            for tool in self.tools:
                logger.info(f"  - {tool.name}: {tool.description}")
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")

    async def handle_sampling_message(
        self, params: types.CreateMessageRequestParams
    ) -> types.CreateMessageResult:
        """
        Handle sampling messages from the server.
        This is called when the server needs LLM input.
        """
        logger.info("Server requested LLM input")
        
        if not self.llm_client:
            logger.error("LLM client not initialized")
            return types.CreateMessageResult(
                role="assistant",
                content=types.TextContent(type="text", text="Error: LLM client not initialized"),
                model=LLM_MODEL,
                stopReason="error"
            )
        
        # Convert MCP messages to Claude format
        claude_messages = []
        
        # Process each message - without system message
        for msg in params.messages:
            # Skip if not user or assistant message
            if msg.role not in ["user", "assistant"]:
                continue
                
            content_blocks = []
            
            # Handle text content
            if isinstance(msg.content, types.TextContent):
                content_blocks.append({"type": "text", "text": msg.content.text})
            # Handle list content (multiple blocks)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, types.TextContent):
                        content_blocks.append({"type": "text", "text": block.text})
                    # Handle other content types if needed
            
            if content_blocks:
                claude_messages.append({"role": msg.role, "content": content_blocks})
        
        try:
            # Call Claude API with system as a separate parameter
            logger.info(f"Calling Claude API ({LLM_MODEL})")
            response = await asyncio.to_thread(
                self.llm_client.messages.create,
                model=LLM_MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,  # System as top-level parameter
                messages=claude_messages
            )
            
            # Process Claude's response
            if response.content and response.content[0].type == "text":
                raw_text = response.content[0].text
                logger.info("Received response from Claude")
                
                try:
                    # Clean up the raw text by removing Markdown code block formatting if present
                    cleaned_text = raw_text
                    # If the text starts with ```json or ``` and ends with ```, remove those markers
                    if cleaned_text.strip().startswith("```") and cleaned_text.strip().endswith("```"):
                        # Remove the opening ```json or ``` line
                        cleaned_text = re.sub(r'^```(?:json)?\s*\n', '', cleaned_text.strip())
                        # Remove the closing ```
                        cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text)
                    
                    # Parse JSON plan
                    plan_data = json.loads(cleaned_text)
                    if isinstance(plan_data, dict) and "tool_calls" in plan_data:
                        self.last_plan = plan_data["tool_calls"]
                        self.plan_ready_for_execution = True  # Set flag to indicate plan is ready
                        logger.info(f"Parsed plan with {len(self.last_plan)} tool calls")
                        
                        # Log the plan details for debugging
                        for i, tool_call in enumerate(self.last_plan):
                            logger.info(f"  Tool call {i+1}: {tool_call.get('tool')}")
                        
                        # Return text content acknowledging the plan
                        return types.CreateMessageResult(
                            role="assistant",
                            content=types.TextContent(
                                type="text",
                                text=f"Generated plan with {len(self.last_plan)} tool calls"
                            ),
                            model=LLM_MODEL,
                            stopReason="end_turn"
                        )
                    else:
                        logger.error("Response not in expected format")
                        return types.CreateMessageResult(
                            role="assistant",
                            content=types.TextContent(
                                type="text",
                                text="Error: LLM response not in expected format"
                            ),
                            model=LLM_MODEL,
                            stopReason="error"
                        )
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON response")
                    return types.CreateMessageResult(
                        role="assistant",
                        content=types.TextContent(
                            type="text",
                            text=f"Error: Failed to parse LLM response as JSON: {raw_text}"
                        ),
                        model=LLM_MODEL,
                        stopReason="error"
                    )
            else:
                logger.error("Unexpected response format from Claude")
                return types.CreateMessageResult(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text="Error: Unexpected response format from LLM"
                    ),
                    model=LLM_MODEL,
                    stopReason="error"
                )
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return types.CreateMessageResult(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text=f"Error communicating with LLM: {e}"
                ),
                model=LLM_MODEL,
                stopReason="error"
            )

    async def execute_plan(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a plan by calling tools on the server."""
        if not self.session:
            logger.error("Session not initialized")
            return []
        
        results = []
        
        for i, tool_call in enumerate(tool_calls):
            try:
                tool_name = tool_call.get("tool")
                if not tool_name:
                    logger.error(f"Tool call {i} missing 'tool' field")
                    continue
                
                arguments = tool_call.get("arguments", {})
                
                # Check if tool exists
                if not any(t.name == tool_name for t in self.tools):
                    logger.error(f"Tool '{tool_name}' not available")
                    results.append({
                        "tool": tool_name,
                        "status": "failed",
                        "error": f"Tool '{tool_name}' not available"
                    })
                    continue
                
                logger.info(f"Executing tool call {i+1}/{len(tool_calls)}: {tool_name}")
                result = await self.session.call_tool(tool_name, arguments=arguments)
                
                # Add result to results list
                results.append({
                    "tool": tool_name,
                    "status": "completed" if "error" not in str(result) else "failed",
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Error executing tool call {i+1}: {e}")
                results.append({
                    "tool": tool_call.get("tool", "unknown"),
                    "status": "failed",
                    "error": str(e)
                })
        
        return results

    async def process_natural_language(self, prompt: str, server: PlaywrightMCPServer = None) -> Dict[str, Any]:
        """Process a natural language prompt and execute the resulting plan."""
        if not self.session:
            logger.error("Session not initialized")
            return {"status": "error", "message": "Session not initialized"}
        
        if not self.llm_client:
            logger.error("LLM client not initialized")
            return {"status": "error", "message": "LLM client not initialized"}
        
        if not server:
            logger.error("Server not provided")
            return {"status": "error", "message": "Server not provided"}
        
        # Create message to send to the LLM
        try:
            # Get the actual available tools for dynamic system prompt
            available_tools = [m for m in dir(server.tools_instance) 
                             if callable(getattr(server.tools_instance, m)) 
                             and not m.startswith('_')]
            
            # Create a dynamic system prompt with the exact available tools
            dynamic_system_prompt = SYSTEM_PROMPT
            
            # Add a timestamp to force refresh of tool information
            timestamp = int(time.time())
            dynamic_system_prompt += f"\n\n## CURRENTLY AVAILABLE TOOLS (timestamp: {timestamp})\n"
            
            for tool in sorted(available_tools):
                if tool.startswith("playwright_"):
                    # Get the docstring if available
                    doc = getattr(server.tools_instance, tool).__doc__
                    short_doc = doc.strip().split("\n")[0] if doc else f"Tool for {tool}"
                    dynamic_system_prompt += f"- {tool} - {short_doc}\n"
            
            # Call LLM directly
            logger.info(f"Calling Claude API with prompt: {prompt}")
            response = await asyncio.to_thread(
                self.llm_client.messages.create,
                model=LLM_MODEL,
                max_tokens=MAX_TOKENS,
                system=dynamic_system_prompt,  # Use dynamic system prompt with actual available tools
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ]
            )
            
            # Process response
            if not response.content or response.content[0].type != "text":
                logger.error("Invalid response from LLM")
                return {"status": "error", "message": "Invalid response from LLM"}
            
            raw_text = response.content[0].text
            
            try:
                # Clean up the raw text by removing Markdown code block formatting if present
                cleaned_text = raw_text
                # If the text starts with ```json or ``` and ends with ```, remove those markers
                if cleaned_text.strip().startswith("```") and cleaned_text.strip().endswith("```"):
                    # Remove the opening ```json or ``` line
                    cleaned_text = re.sub(r'^```(?:json)?\s*\n', '', cleaned_text.strip())
                    # Remove the closing ```
                    cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text)
                
                # Parse JSON plan
                plan_data = json.loads(cleaned_text)
                
                if not isinstance(plan_data, dict) or "tool_calls" not in plan_data:
                    logger.error("Invalid plan format")
                    return {
                        "status": "error", 
                        "message": "Invalid plan format",
                        "raw_response": raw_text
                    }
                
                tool_calls = plan_data["tool_calls"]
                logger.info(f"Generated plan with {len(tool_calls)} tool calls")
                
                # Execute each tool call sequentially
                results = []
                success_count = 0
                error_recovery_attempts = 0
                max_recovery_attempts = 2
                
                i = 0
                while i < len(tool_calls):
                    tool_call = tool_calls[i]
                    tool_name = tool_call.get("tool")
                    arguments = tool_call.get("arguments", {})
                    
                    print(f"\n⚙️  Step {i+1}/{len(tool_calls)}: {tool_name}")
                    print(f"   Parameters: {json.dumps(arguments, indent=2)}")
                    
                    # Get method from server's tools_instance
                    tool_method = getattr(server.tools_instance, tool_name, None)
                    
                    # Try to recover from missing tools by finding similar tools
                    if not tool_method:
                        error_msg = f"Tool not found: {tool_name}"
                        print(f"❌ {error_msg}")
                        
                        # Suggest a similar tool name if possible
                        available_tools = [m for m in dir(server.tools_instance) 
                                         if callable(getattr(server.tools_instance, m)) 
                                         and not m.startswith('_')
                                         and m.startswith('playwright_')]
                        
                        # Find the closest matching tool name
                        closest_match = None
                        min_distance = float('inf')
                        
                        for available_tool in available_tools:
                            # Simple string distance calculation
                            distance = sum(1 for a, b in zip(tool_name, available_tool) if a != b)
                            distance += abs(len(tool_name) - len(available_tool))
                            
                            if distance < min_distance:
                                min_distance = distance
                                closest_match = available_tool
                        
                        # Automatic tool correction for known mistakes
                        auto_corrections = {
                            "playwright_type": "playwright_fill",
                            "playwright_press": "playwright_press_key",
                            "playwright_input": "playwright_fill",
                            "playwright_search": "playwright_fill",
                        }
                        
                        # Check if we can auto-correct this tool
                        if tool_name in auto_corrections:
                            correct_tool = auto_corrections[tool_name]
                            print(f"🔄 Auto-correcting to {correct_tool}")
                            
                            # Update tool name and get the method
                            tool_name = correct_tool
                            tool_method = getattr(server.tools_instance, tool_name, None)
                            
                            # Update the tool call for result tracking
                            tool_call["tool"] = tool_name
                            
                        elif closest_match and min_distance <= 5:  # Only suggest if reasonably close
                            print(f"💡 Did you mean: {closest_match}?")
                            
                            # Auto-fallback if we have a very close match
                            if min_distance <= 3 and error_recovery_attempts < max_recovery_attempts:
                                print(f"🔄 Auto-fallback to {closest_match}")
                                tool_name = closest_match
                                tool_method = getattr(server.tools_instance, closest_match, None)
                                
                                # Update the tool call for result tracking
                                tool_call["tool"] = tool_name
                                error_recovery_attempts += 1
                            else:
                                # Try the auto_execute meta-tool as fallback for any action
                                action = tool_name.replace("playwright_", "")
                                target = arguments.get("selector", arguments.get("url", ""))
                                value = arguments.get("text", arguments.get("key", ""))
                                
                                if hasattr(server.tools_instance, "playwright_auto_execute"):
                                    print(f"🔄 Falling back to playwright_auto_execute for {action}")
                                    tool_method = getattr(server.tools_instance, "playwright_auto_execute")
                                    arguments = {
                                        "action": action,
                                        "target": target,
                                        "value": value,
                                        "page_index": arguments.get("page_index", 0)
                                    }
                                    tool_name = "playwright_auto_execute"
                                    tool_call["tool"] = tool_name
                                else:
                                    print(f"   Available tools in server: {[m for m in dir(server.tools_instance) if callable(getattr(server.tools_instance, m)) and not m.startswith('_') and m.startswith('playwright_')]}")
                        results.append({
                            "tool": tool_name,
                            "status": "failed",
                            "error": error_msg
                        })
                        i += 1  # Move to next step
                        continue
                        
                    # Call the tool and wait for it to complete
                    try:
                        print(f"   Executing {tool_name}...")
                        
                        # Visual progress indicator for long-running operations
                        is_browser_operation = tool_name.startswith("playwright_") and tool_name not in ["playwright_debug_info", "playwright_get_visible_text"]
                        progress_task = None
                        
                        if is_browser_operation:
                            # Start a progress indicator for browser operations
                            async def show_progress():
                                symbols = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
                                i = 0
                                while True:
                                    print(f"\r   {symbols[i]} Processing...", end="", flush=True)
                                    i = (i + 1) % len(symbols)
                                    await asyncio.sleep(0.2)
                                
                            progress_task = asyncio.create_task(show_progress())
                        
                        # Execute the tool
                        start_time = time.time()
                        result = await tool_method(**arguments)
                        end_time = time.time()
                        execution_time = round(end_time - start_time, 2)
                        
                        # Stop the progress indicator if it's running
                        if progress_task:
                            progress_task.cancel()
                            try:
                                await progress_task
                            except asyncio.CancelledError:
                                pass
                            print("\r                          ", end="\r")  # Clear the progress indicator
                        
                        # Add to results
                        success = result.get("status") == "success"
                        results.append({
                            "tool": tool_name,
                            "status": "completed" if success else "failed",
                            "execution_time": execution_time,
                            "result": result
                        })
                        
                        status_icon = "✅" if success else "❌"
                        print(f"   {status_icon} {result.get('message', '')} (in {execution_time}s)")
                        
                        if success:
                            success_count += 1
                        # Wait a bit between actions to let the page settle
                        if i < len(tool_calls) - 1:
                                await asyncio.sleep(1.5)  # Slightly longer wait to ensure page is ready
                        else:
                            # If this tool failed, we might want to stop the sequence for critical operations
                            print(f"⚠️  Warning: Step {i+1} failed: {result.get('error', result.get('message', 'Unknown error'))}")
                            if tool_name == "playwright_navigate":
                                # Navigation is critical, ask if user wants to retry or continue
                                retry = input("   Navigation failed. Retry? (y/n): ").lower() == 'y'
                                if retry:
                                    i -= 1  # Retry the same step
                                    continue
                                # Continue with next steps anyway
                    except Exception as tool_error:
                        error_msg = str(tool_error)
                        print(f"❌ Error executing {tool_name}: {error_msg}")
                        results.append({
                            "tool": tool_name,
                            "status": "failed",
                            "error": error_msg
                        })
                        # For critical errors in navigation, offer to retry
                        if tool_name == "playwright_navigate":
                            retry = input("   Critical error in navigation. Retry? (y/n): ").lower() == 'y'
                            if retry:
                                i -= 1  # Retry the same step
                    
                    # Increment the loop counter to move to the next step
                    i += 1
                
                # Print summary
                print("\n📋 Execution summary:")
                for i, result in enumerate(results):
                    status = "✅" if result["status"] == "completed" else "❌"
                    print(f"   {status} Step {i+1}: {result['tool']}")
                
                if success_count == 0:
                    print("\n❌ All steps failed. Please check your command and try again.")
                elif success_count < len(tool_calls):
                    print(f"\n⚠️ Some steps failed ({success_count}/{len(tool_calls)} succeeded). You may want to try again.")
                else:
                    print("\n✅ All steps completed successfully!")
                
                print("\nReady for next command...")
                
                return {
                    "status": "success",
                    "plan": tool_calls,
                    "results": results
                }
                
            except json.JSONDecodeError as json_error:
                logger.error(f"Failed to parse JSON: {json_error}")
                return {"status": "error", "message": f"Failed to parse LLM response as JSON: {json_error}"}
        except Exception as e:
            logger.error(f"Error processing natural language prompt: {e}")
            return {"status": "error", "message": str(e)}

async def run_integrated():
    """Run both client and server in the same process."""
    server = None
    try:
        # Start server
        print("\n🚀 Starting AI-powered browser automation...\n")
        server = PlaywrightMCPServer()
        started = await server.start()
        if not started:
            logger.error("Failed to start server. Exiting.")
            return
        print("✅ Server started successfully")
            
        # Create client
        client = MCPClient()
        print("✅ Client initialized\n")

        # Interactive prompt loop
        print("\n=== MCP AI Browser Automation Client ===")
        print("Enter natural language commands or 'exit' to quit.")
        print("Example: 'Navigate to google.com and search for Playwright automation'")
        print("=============================================")
        
        running = True
        while running:
            try:
                # Reset browser state flag before each command
                # This ensures we'll do a fresh browser validation
                if hasattr(server.tools_instance, "browser_initialized"):
                    print("\n🔍 Checking browser health before new command...")
                    # Explicitly verify browser is still working
                    browser_alive = False
                    try:
                        if server.tools_instance.browser:
                            browser_alive = await server.tools_instance.is_browser_alive()
                        else:
                            print("Browser object doesn't exist - will be initialized when needed")
                    except Exception as e:
                        print(f"Error checking browser health: {e}")
                        browser_alive = False
                        
                    if not browser_alive and server.tools_instance.browser_initialized:
                        print("⚠️ Browser has been closed - will be reinitialized automatically")
                        # Reset all browser state to force reinitialization
                        server.tools_instance.browser_initialized = False
                        server.tools_instance.browser = None
                        server.tools_instance.context = None
                        server.tools_instance.pages = []
                    elif browser_alive:
                        print("✅ Browser is healthy and ready for commands")
                        
                user_input = input("\n>> Enter command: ").strip()
                
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting application...")
                    running = False
                    continue
                
                if not user_input:
                    continue
                
                print(f"\n🔍 Processing: \"{user_input}\"")
                print("⏳ Generating automation plan...")
                
                # Execute the plan using the client
                try:
                    result = await client.process_natural_language(user_input, server)
                    if result["status"] == "error":
                        print(f"❌ Error: {result['message']}")
                except Exception as plan_error:
                    print(f"❌ Error processing command: {plan_error}")
                    import traceback
                    traceback.print_exc()
                
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted by user")
                running = False
            except Exception as e:
                print(f"❌ Error: {e}")
                # Reset browser state on unhandled errors
                if hasattr(server.tools_instance, "browser_initialized"):
                    server.tools_instance.browser_initialized = False
    
    except ModuleNotFoundError as e:
        print(f"❌ Missing required module: {e}")
        print("Make sure all dependencies are installed. Run:")
        print("pip install playwright anthropic python-dotenv mcp")
        print("python -m playwright install chromium")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close server if it was initialized
        if server:
            print("\n🛑 Stopping server...")
            try:
                await server.stop()
                print("✅ Server fully stopped")
            except Exception as stop_error:
                print(f"❌ Error stopping server: {stop_error}")
        print("Exiting integrated mode.")

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP AI Browser Automation")
    parser.add_argument('--test', action='store_true', help='Run a simple test to check configuration')
    parser.add_argument('--command', type=str, help='Run a specific command and exit')
    parser.add_argument('--keep-browser', action='store_true', help='Keep browser open after command execution')
    args = parser.parse_args()
    
    # Add keep-browser option to the test and command modes as well
    if args.test:
        print("Running in test mode to verify configuration...")
        try:
            # Test Playwright
            print("Testing Playwright installation...")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("✅ Playwright is working")
            
            # Test browser
            await page.goto("https://example.com")
            title = await page.title()
            print(f"✅ Browser navigation works, page title: {title}")
            
            # Clean up - but only if not keeping browser open
            if not args.keep_browser:
                await context.close()
                await browser.close()
                await playwright.stop()
                print("✅ Browser closed")
            else:
                print("✅ Browser session remains open as requested")
            
            # Test Anthropic API if available
            if ANTHROPIC_API_KEY:
                print("Testing Anthropic API...")
                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                response = await asyncio.to_thread(
                    client.messages.create,
                    model=LLM_MODEL,
                    max_tokens=10,
                    messages=[
                        {"role": "user", "content": "Say hello"}
                    ]
                )
                print(f"✅ Anthropic API is working, response: {response.content[0].text}")
            else:
                print("⚠️ ANTHROPIC_API_KEY not set, skipping API test")
                
            print("\nAll tests completed successfully!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        return
    
    elif args.command:
        # Run a single command and exit
        try:
            # Initialize server
            server = PlaywrightMCPServer()
            await server.start()
            
            print(f"Running command: {args.command}")
            
            # ... (rest of the command execution logic)
            
            # Clean up only if not keeping browser open
            if not args.keep_browser:
                await server.stop()
                print("Browser closed")
            else:
                print("Browser session remains open as requested")
        except Exception as e:
            print(f"Error executing command: {e}")
        return
    
    # Default: run interactive mode
    print("Starting MCP Client/Server in integrated mode...")
    await run_integrated()

if __name__ == "__main__":
    try:
        import time  # Import time module for timestamps
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")