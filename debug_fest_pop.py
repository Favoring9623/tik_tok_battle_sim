#!/usr/bin/env python3
"""
Debug Fest Pop clicking - find the correct element to click
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_fest_pop():
    print("Starting debug session...")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=50)
    context = await browser.new_context(
        storage_state="data/tiktok_session/state.json",
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()

    # Navigate to live
    print("Navigating to @christ9817...")
    await page.goto("https://www.tiktok.com/@christ9817/live")
    await asyncio.sleep(5)
    print("Connected!")

    # Open gift panel
    print("Opening gift panel...")
    try:
        more_btn = page.locator('text="More"').last
        await more_btn.click()
        await asyncio.sleep(2)
        print("Panel opened")
    except Exception as e:
        print(f"Error: {e}")

    # Take screenshot
    await page.screenshot(path="debug_gift_panel.png")
    print("Screenshot saved: debug_gift_panel.png")

    # Analyze DOM structure around Fest Pop
    print("\n=== ANALYZING FEST POP STRUCTURE ===\n")

    analysis = await page.evaluate("""
        () => {
            const results = [];
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );

            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    let el = node.parentElement;
                    let depth = 0;
                    const chain = [];

                    while (el && depth < 10) {
                        const rect = el.getBoundingClientRect();
                        chain.push({
                            tag: el.tagName,
                            class: el.className?.slice?.(0, 80) || '',
                            id: el.id || '',
                            hasOnClick: !!el.onclick,
                            isButton: el.tagName === 'BUTTON' || el.role === 'button',
                            clickable: el.style.cursor === 'pointer' ||
                                      window.getComputedStyle(el).cursor === 'pointer',
                            rect: {x: rect.x.toFixed(0), y: rect.y.toFixed(0),
                                   w: rect.width.toFixed(0), h: rect.height.toFixed(0)},
                            depth: depth
                        });
                        el = el.parentElement;
                        depth++;
                    }
                    results.push(chain);
                }
            }
            return results;
        }
    """)

    print("Found Fest Pop elements:")
    for i, chain in enumerate(analysis):
        print(f"\n--- Instance {i+1} ---")
        for item in chain:
            click_indicator = "CLICKABLE" if item['clickable'] or item['isButton'] else ""
            print(f"  [{item['depth']}] <{item['tag']}> class='{item['class'][:50]}' " +
                  f"rect=({item['rect']['x']},{item['rect']['y']}) {item['rect']['w']}x{item['rect']['h']} {click_indicator}")

    # Find all gift-like clickable elements in the panel
    print("\n=== GIFT PANEL BUTTONS ===\n")

    buttons = await page.evaluate("""
        () => {
            const results = [];
            // Look for clickable containers with images and prices
            const containers = document.querySelectorAll('[class*="gift"], [class*="Gift"], [data-e2e*="gift"]');

            for (const el of containers) {
                if (el.offsetParent) {
                    const rect = el.getBoundingClientRect();
                    const text = el.innerText?.trim().slice(0, 30) || '';
                    results.push({
                        tag: el.tagName,
                        class: el.className?.slice?.(0, 60) || '',
                        text: text,
                        rect: {x: rect.x.toFixed(0), y: rect.y.toFixed(0)}
                    });
                }
            }
            return results.slice(0, 20);
        }
    """)

    for btn in buttons:
        print(f"  <{btn['tag']}> '{btn['text']}' at ({btn['rect']['x']},{btn['rect']['y']}) class={btn['class'][:40]}")

    # Try different click strategies
    print("\n=== TESTING CLICK STRATEGIES ===\n")

    # Strategy 1: Click on parent div with proper class
    print("Strategy 1: Click parent container of Fest Pop text...")
    result1 = await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );

            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    // Go up to find clickable container
                    let el = node.parentElement;
                    for (let i = 0; i < 8; i++) {
                        if (el && (el.className?.includes?.('gift') ||
                                   el.className?.includes?.('Gift') ||
                                   window.getComputedStyle(el).cursor === 'pointer')) {
                            el.click();
                            return {success: true, tag: el.tagName, class: el.className};
                        }
                        el = el?.parentElement;
                    }
                }
            }
            return {success: false};
        }
    """)
    print(f"  Result: {result1}")
    await asyncio.sleep(1)

    # Strategy 2: Find by position and dispatch mouse events
    print("\nStrategy 2: Find gift image near 'Fest Pop' and use mouse events...")

    fest_pop_info = await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );

            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    const rect = node.parentElement.getBoundingClientRect();
                    // Gift image is usually above or to the left of text
                    return {x: rect.x + rect.width/2, y: rect.y - 20};
                }
            }
            return null;
        }
    """)

    if fest_pop_info:
        print(f"  Fest Pop text at ({fest_pop_info['x']:.0f}, {fest_pop_info['y']:.0f})")
        print(f"  Clicking slightly above (on gift image)...")
        await page.mouse.click(fest_pop_info['x'], fest_pop_info['y'])
        await asyncio.sleep(1)

    # Strategy 3: Use locator with force
    print("\nStrategy 3: Playwright locator with force click...")
    try:
        # Look for any element containing "Fest Pop" and has a sibling image
        fest_locator = page.locator('div:has-text("Fest Pop")').first
        box = await fest_locator.bounding_box()
        if box:
            print(f"  Found div at ({box['x']:.0f}, {box['y']:.0f})")
            await fest_locator.click(force=True)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"  Error: {e}")

    # Strategy 4: Direct mouse click at known position
    print("\nStrategy 4: Direct mouse events at (564, 483)...")
    await page.mouse.move(564, 483)
    await page.mouse.down()
    await page.mouse.up()
    await asyncio.sleep(1)

    # Take final screenshot
    await page.screenshot(path="debug_after_clicks.png")
    print("\nScreenshot saved: debug_after_clicks.png")

    print("\n=== INTERACTIVE MODE ===")
    print("Browser will stay open for 60 seconds for manual testing...")
    print("Try clicking Fest Pop manually to see the correct behavior.")
    await asyncio.sleep(60)

    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_fest_pop())
