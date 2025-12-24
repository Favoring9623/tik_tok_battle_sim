#!/usr/bin/env python3
"""
Test clicking on TikTok gifts using different methods.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright


async def test_click_gift():
    """Test various methods to click on a gift."""

    print("🔍 Testing gift click methods...")

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=False,
        slow_mo=200,
    )

    session_path = Path("data/tiktok_session/state.json")
    context = await browser.new_context(
        storage_state=str(session_path),
        viewport={"width": 1280, "height": 800},
    )

    page = await context.new_page()

    # Navigate to live
    await page.goto("https://www.tiktok.com/@liznogalh/live")
    print("✅ Page loaded")

    await asyncio.sleep(5)

    # Take screenshot before
    await page.screenshot(path="data/before_click.png")
    print("📸 Screenshot saved: before_click.png")

    # ===== TEST METHODS =====

    gift_name = "Rose"
    methods_tried = []

    # Method 1: get_by_text exact
    print(f"\n🔍 Method 1: get_by_text('{gift_name}', exact=True)")
    try:
        locator = page.get_by_text(gift_name, exact=True)
        count = await locator.count()
        print(f"   Found: {count} elements")
        if count > 0:
            box = await locator.first.bounding_box()
            print(f"   Bounding box: {box}")
            await locator.first.click()
            print("   ✅ Clicked!")
            methods_tried.append(("get_by_text exact", True))
            await asyncio.sleep(2)
        else:
            methods_tried.append(("get_by_text exact", False))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        methods_tried.append(("get_by_text exact", False))

    # Method 2: get_by_text partial
    print(f"\n🔍 Method 2: get_by_text('{gift_name}', exact=False)")
    try:
        locator = page.get_by_text(gift_name, exact=False)
        count = await locator.count()
        print(f"   Found: {count} elements")
        if count > 0:
            for i in range(min(count, 3)):
                el = locator.nth(i)
                text = await el.inner_text()
                box = await el.bounding_box()
                print(f"   [{i}] text='{text[:30]}' box={box}")
            methods_tried.append(("get_by_text partial", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        methods_tried.append(("get_by_text partial", False))

    # Method 3: Query selector with class patterns
    print(f"\n🔍 Method 3: Query selector for gift containers")
    try:
        # Find all potential gift containers
        containers = await page.query_selector_all('div[class*="flex"][class*="col"][class*="center"]')
        print(f"   Found: {len(containers)} potential containers")

        for i, container in enumerate(containers[:10]):
            try:
                text = await container.inner_text()
                visible = await container.is_visible()
                if visible and len(text) < 50:
                    print(f"   [{i}] visible={visible} text='{text}'")
                    if "rose" in text.lower():
                        print(f"   ⭐ Found Rose container!")
                        await container.click()
                        print("   ✅ Clicked Rose container!")
                        methods_tried.append(("container search", True))
                        await asyncio.sleep(2)
                        break
            except:
                pass
    except Exception as e:
        print(f"   ❌ Error: {e}")
        methods_tried.append(("container search", False))

    # Method 4: Click by coordinates (based on screenshot layout)
    print(f"\n🔍 Method 4: Click by coordinates")
    try:
        # In the screenshot, Rose appears at approximately:
        # - X: around 230 (first gift in the bar)
        # - Y: around 550 (bottom gift bar)
        # Viewport is 1280x800

        # Gift bar positions (approximate from screenshot)
        gift_positions = {
            "Rose": (230, 550),
            "Fest Party": (330, 550),
            "Fest Cheers": (430, 550),
            "Sunset": (530, 550),
            "More": (600, 550),
        }

        if gift_name in gift_positions:
            x, y = gift_positions[gift_name]
            print(f"   Clicking at ({x}, {y})")
            await page.mouse.click(x, y)
            print("   ✅ Clicked by coordinates!")
            methods_tried.append(("coordinates", True))
            await asyncio.sleep(2)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        methods_tried.append(("coordinates", False))

    # Method 5: Evaluate JavaScript to find and click
    print(f"\n🔍 Method 5: JavaScript evaluation")
    try:
        result = await page.evaluate(f"""
            () => {{
                // Find elements containing 'Rose' text
                const elements = document.body.querySelectorAll('*');
                for (const el of elements) {{
                    if (el.textContent && el.textContent.trim() === 'Rose' && el.offsetParent !== null) {{
                        console.log('Found:', el);
                        el.click();
                        return {{'found': true, 'tag': el.tagName, 'class': el.className}};
                    }}
                }}
                return {{'found': false}};
            }}
        """)
        print(f"   Result: {result}")
        if result.get('found'):
            print("   ✅ Clicked via JS!")
            methods_tried.append(("javascript", True))
            await asyncio.sleep(2)
        else:
            methods_tried.append(("javascript", False))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        methods_tried.append(("javascript", False))

    # Take screenshot after
    await page.screenshot(path="data/after_click.png")
    print("\n📸 Screenshot saved: after_click.png")

    # Summary
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES MÉTHODES")
    print("=" * 50)
    for method, success in methods_tried:
        status = "✅" if success else "❌"
        print(f"   {status} {method}")

    print("\n⏳ Keeping browser open for 30s for manual inspection...")
    await asyncio.sleep(30)

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_click_gift())
