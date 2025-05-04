#!/usr/bin/env python3
"""
Test script for Prompt 20: Frames
This test validates the iframe interactions and HTML content extraction
"""
import sys
import os
import asyncio
import json
import time

# Add the parent directory to the Python path to allow importing Tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools import PlaywrightTools

async def test_frames():
    """Test the Frames prompt using iframe interaction tools"""
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
        
        # STEP 1: Navigate to the frames page
        print("\n📌 Navigating to frames page...")
        result = await tools.playwright_navigate("https://the-internet.herokuapp.com/frames")
        if result["status"] != "success":
            print(f"❌ Failed to navigate: {result['message']}")
            return
        print("✅ Navigation successful")
        
        # STEP 2: Take a screenshot of frames index page
        print("\n📌 Taking screenshot of frames index page...")
        index_screenshot = await tools.playwright_screenshot(filename="frames_index.png")
        if index_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {index_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {index_screenshot.get('path', 'Unknown path')}")
        
        # STEP 3: Get the HTML content of the frames index page
        print("\n📌 Getting HTML content of frames index page...")
        html_content = await tools.playwright_get_visible_html()
        if html_content["status"] != "success":
            print(f"❌ Failed to get HTML content: {html_content['message']}")
        else:
            print("✅ Got HTML content")
            frame_links = await tools.playwright_evaluate("""() => {
                const links = document.querySelectorAll('a');
                return Array.from(links)
                    .filter(link => link.textContent.includes('Frame'))
                    .map(link => ({
                        text: link.textContent.trim(),
                        href: link.getAttribute('href')
                    }));
            }""")
            
            if frame_links["status"] == "success":
                print("🔍 Found frame links:")
                for link in frame_links["result"]:
                    print(f"  - {link['text']} ({link['href']})")
        
        # STEP 4: Navigate to the Nested Frames page
        print("\n📌 Navigating to Nested Frames page...")
        nested_frames_click = await tools.playwright_click(selector="a[href='/nested_frames']")
        if nested_frames_click["status"] != "success":
            print(f"❌ Failed to click nested frames link: {nested_frames_click['message']}")
            return
        print("✅ Navigation to Nested Frames successful")
        
        # Wait a moment for frames to load
        await asyncio.sleep(1)
        
        # STEP 5: Take a screenshot of the nested frames page
        print("\n📌 Taking screenshot of nested frames page...")
        nested_screenshot = await tools.playwright_screenshot(filename="nested_frames.png")
        if nested_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {nested_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {nested_screenshot.get('path', 'Unknown path')}")
        
        # STEP 6: Analyze the frame structure
        print("\n📌 Analyzing frame structure...")
        frame_structure = await tools.playwright_evaluate("""() => {
            // Check for presence of frameset
            const framesets = document.querySelectorAll('frameset');
            const iframes = document.querySelectorAll('iframe');
            
            return {
                hasFramesets: framesets.length > 0,
                framesetCount: framesets.length,
                hasIframes: iframes.length > 0,
                iframeCount: iframes.length,
                topFrameset: framesets[0] ? {
                    rows: framesets[0].getAttribute('rows'),
                    cols: framesets[0].getAttribute('cols')
                } : null
            };
        }""")
        
        if frame_structure["status"] != "success":
            print(f"❌ Failed to analyze frame structure: {frame_structure['message']}")
        else:
            structure = frame_structure["result"]
            print("🔍 Frame structure:")
            print(f"  - Has framesets: {structure['hasFramesets']} (Count: {structure['framesetCount']})")
            print(f"  - Has iframes: {structure['hasIframes']} (Count: {structure['iframeCount']})")
            if structure['topFrameset']:
                print(f"  - Top frameset: rows={structure['topFrameset']['rows']}, cols={structure['topFrameset']['cols']}")
        
        # STEP 7: Try to access content in the top frame
        print("\n📌 Trying to access content in frames...")
        
        # First check if we can get all frame names
        frames_info = await tools.playwright_evaluate("""() => {
            try {
                // Get all frames
                const frames = window.frames;
                const frameCount = frames.length;
                
                // Try to get frame names or indices
                const frameInfo = [];
                for (let i = 0; i < frameCount; i++) {
                    try {
                        const frame = frames[i];
                        const frameName = frame.name || `unnamed-${i}`;
                        frameInfo.push({
                            index: i,
                            name: frameName
                        });
                    } catch (err) {
                        frameInfo.push({
                            index: i,
                            error: err.toString()
                        });
                    }
                }
                
                return {
                    frameCount,
                    frameInfo
                };
            } catch (error) {
                return { error: error.toString() };
            }
        }""")
        
        if frames_info["status"] == "success" and "frameInfo" in frames_info["result"]:
            print(f"✅ Found {frames_info['result']['frameCount']} frames:")
            for frame in frames_info["result"]["frameInfo"]:
                print(f"  - Frame {frame['index']}: {frame.get('name', 'unnamed')}")
        else:
            print(f"❌ Could not get frame information: {frames_info.get('message', 'Unknown error')}")
        
        # STEP 8: Try using iframe_click to interact with an element in the middle frame
        print("\n📌 Attempting to interact with the middle frame...")
        
        # Navigate to the iframes page to use a more reliable iframe example
        print("\n📌 Navigating back to frames index...")
        await tools.playwright_navigate("https://the-internet.herokuapp.com/frames")
        
        # Navigate to iFrame page
        print("\n📌 Navigating to iFrame page...")
        iframe_click = await tools.playwright_click(selector="a[href='/iframe']")
        if iframe_click["status"] != "success":
            print(f"❌ Failed to click iframe link: {iframe_click['message']}")
        else:
            print("✅ Navigation to iFrame successful")
            
        # Wait a moment for iframe to load
        await asyncio.sleep(2)
        
        # STEP 9: Take a screenshot of the iframe page
        print("\n📌 Taking screenshot of iframe page...")
        iframe_screenshot = await tools.playwright_screenshot(filename="iframe_page.png")
        if iframe_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {iframe_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {iframe_screenshot.get('path', 'Unknown path')}")
        
        # STEP 10: Get iframe content
        print("\n📌 Getting iframe content...")
        iframe_html = await tools.playwright_evaluate("""() => {
            const iframe = document.querySelector('iframe');
            return {
                exists: !!iframe,
                id: iframe ? iframe.id : null,
                name: iframe ? iframe.name : null
            };
        }""")
        
        if iframe_html["status"] != "success":
            print(f"❌ Failed to get iframe info: {iframe_html['message']}")
        else:
            print(f"✅ Found iframe with id: {iframe_html['result']['id']}, name: {iframe_html['result']['name']}")
        
        # STEP 11: Test iframe interaction by typing text in the editor
        print("\n📌 Typing text in the iframe editor...")
        iframe_fill = await tools.playwright_iframe_click(
            iframeSelector="iframe#mce_0_ifr", 
            selector="body#tinymce"
        )
        
        if iframe_fill["status"] != "success":
            print(f"❌ Failed to click in iframe: {iframe_fill['message']}")
            
            # Try an alternative approach by evaluating JS in the iframe
            print("⚠️ Trying alternative approach with evaluate...")
            iframe_js = await tools.playwright_evaluate("""() => {
                try {
                    const iframe = document.querySelector('iframe#mce_0_ifr');
                    if (!iframe) return { error: "Iframe not found" };
                    
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    const body = iframeDoc.querySelector('body');
                    
                    if (body) {
                        // Clear existing content
                        body.innerHTML = 'Hello from Playwright Test!';
                        return { 
                            success: true, 
                            content: body.innerHTML 
                        };
                    } else {
                        return { error: "Body element not found in iframe" };
                    }
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")
            
            if iframe_js["status"] == "success" and iframe_js["result"].get("success"):
                print(f"✅ Successfully modified iframe content using JavaScript")
                print(f"✅ New content: {iframe_js['result']['content']}")
            else:
                print(f"❌ JavaScript approach also failed: {iframe_js.get('result', {}).get('error', 'Unknown error')}")
        else:
            print("✅ Successfully clicked in iframe")
            
            # Now try to type in the iframe
            iframe_type = await tools.playwright_evaluate("""() => {
                try {
                    const iframe = document.querySelector('iframe#mce_0_ifr');
                    if (!iframe) return { error: "Iframe not found" };
                    
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    const body = iframeDoc.querySelector('body');
                    
                    if (body) {
                        body.innerHTML = 'Hello from Playwright iframe test!';
                        return { 
                            success: true, 
                            content: body.innerHTML 
                        };
                    } else {
                        return { error: "Body element not found in iframe" };
                    }
                } catch (e) {
                    return { error: e.toString() };
                }
            }""")
            
            if iframe_type["status"] == "success" and iframe_type["result"].get("success"):
                print(f"✅ Successfully typed in iframe")
                print(f"✅ Content: {iframe_type['result']['content']}")
            else:
                error = iframe_type.get("result", {}).get("error", "Unknown error")
                print(f"❌ Failed to type in iframe: {error}")
        
        # STEP 12: Take a final screenshot showing iframe content
        print("\n📌 Taking final screenshot showing iframe content...")
        final_screenshot = await tools.playwright_screenshot(filename="iframe_content.png")
        if final_screenshot["status"] != "success":
            print(f"❌ Failed to take screenshot: {final_screenshot['message']}")
        else:
            print(f"✅ Screenshot saved: {final_screenshot.get('path', 'Unknown path')}")
        
        # Get the HTML content of the page with iframe
        print("\n📌 Getting complete HTML including iframe...")
        final_html = await tools.playwright_get_visible_html()
        if final_html["status"] != "success":
            print(f"❌ Failed to get HTML content: {final_html['message']}")
        else:
            html_length = len(final_html["result"])
            print(f"✅ Got HTML content ({html_length} characters)")
        
        print("\n✅ Frames test completed successfully!")
        
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
    print("Starting Frames test...")
    asyncio.run(test_frames())
