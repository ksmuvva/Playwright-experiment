# MCP Enhanced Tools

A modular Playwright automation toolkit for the Model Context Protocol (MCP), designed to enable AI agents to interact with web browsers effectively.

## Overview

This toolkit provides a comprehensive suite of browser automation tools organized into logical modules for better maintainability, readability, and extensibility. It's designed to work with the Model Context Protocol for AI-driven browser automation.

## Directory Structure

```
Tools/
├── __init__.py           - Main integration module with PlaywrightTools class
├── base.py               - Base utilities and PlaywrightBase class
├── AdvancedBrowser/      - JavaScript execution and console logs
├── BrowserControl/       - Basic navigation tools
├── CodeGeneration/       - Code generation and sessions
├── ContentExtraction/    - Screenshots, PDFs, text extraction
├── Debug/                - Debugging and testing tools
├── ElementInteraction/   - Element clicks, fills, and interactions
├── ElementLocation/      - Smart element location strategies
└── Network/              - Response handling and network control
```

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/MCP-enhanced-test.git

# Install dependencies
cd MCP-enhanced-test
pip install -r requirements.txt
```

### Basic Usage

```python
from Tools import PlaywrightTools

async def main():
    # Initialize the tools
    tools = PlaywrightTools()
    await tools.initialize()
    
    # Navigate to a website
    await tools.playwright_navigate(url="https://example.com")
    
    # Click a button
    await tools.playwright_smart_click(text="More information")
    
    # Take a screenshot
    result = await tools.playwright_screenshot()
    print(f"Screenshot saved to: {result.get('screenshot_path')}")
    
    # Clean up
    await tools.cleanup()

# Run the example
import asyncio
asyncio.run(main())
```

## Key Features

- **Modular Structure**: Organized by functionality for better maintainability
- **Smart Element Location**: Multiple strategies to find elements reliably
- **Intelligent Interaction**: Auto-execute with fallbacks for robust automation
- **Advanced Debugging**: Tools to help diagnose and fix issues
- **Code Generation**: Generate Playwright code from recorded sessions

## Main Tool Categories

### Browser Control
- Basic navigation: `playwright_navigate`, `playwright_go_back`, `playwright_go_forward`
- Window management: `playwright_close`

### Element Interaction
- Clicks: `playwright_click`, `playwright_smart_click`, `playwright_iframe_click`
- Forms: `playwright_fill`, `playwright_select`
- Advanced: `playwright_hover`, `playwright_drag`, `playwright_press_key`

### Content Extraction
- Visual: `playwright_screenshot`, `playwright_save_as_pdf`
- Text: `playwright_get_visible_text`, `playwright_get_visible_html`

### Element Location
- Smart finding: `playwright_find_element`, `playwright_multi_strategy_locate`
- Advanced location: `playwright_accessibility_locator`, `playwright_vision_locator`, `playwright_js_locate`

### Advanced Tools
- JavaScript: `playwright_evaluate`, `playwright_cdp_evaluate`, `playwright_devtools_info`
- Debugging: `playwright_debug_info`, `playwright_inspector`, `playwright_console_logs`
- Network: `playwright_expect_response`, `playwright_assert_response`

### Auto-Execution
- Intelligent execution: `playwright_auto_execute` - Tries multiple strategies to accomplish a task

## Migration

If you're upgrading from the original `exp_tools.py`, see [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details on transitioning to the modular structure.

## Testing

Run the test script to verify correct installation and functionality:

```bash
python test_modular_structure.py
```

## Documentation

For detailed documentation of the module structure, see [MODULAR_STRUCTURE.md](MODULAR_STRUCTURE.md).
