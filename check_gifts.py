#!/usr/bin/env python3
"""Check available gifts on a live stream"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def check_gifts(username: str):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=50)
    context = await browser.new_context(
        storage_state="data/tiktok_session/state.json",
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()

    username = username.lstrip("@")
    print(f"Navigation vers @{username}...")
    await page.goto(f"https://www.tiktok.com/@{username}/live")
    await asyncio.sleep(5)

    # Open More panel
    try:
        more_btn = page.locator('text="More"').last
        await more_btn.click()
        await asyncio.sleep(2)
        print("Panneau ouvert")
    except:
        print("Panneau peut-être déjà ouvert")

    # Screenshot
    await page.screenshot(path=f"{username}_gifts.png")
    print(f"Screenshot: {username}_gifts.png")

    # Find all gift names
    gifts = await page.evaluate("""
        () => {
            const results = [];
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            const giftNames = ['Rose', 'Fest Pop', 'Fest Cheers', 'Fest Party', 'Doughnut',
                              'Money Gun', 'GG', 'Ice Cream Cone', 'Paper Crane', 'Finger Heart',
                              'TikTok', 'Rosa', 'Balloon', 'Heart', 'Sun Cream'];

            while (walker.nextNode()) {
                const text = walker.currentNode.textContent.trim();
                if (giftNames.includes(text)) {
                    const el = walker.currentNode.parentElement;
                    if (el && el.offsetParent) {
                        const rect = el.getBoundingClientRect();
                        results.push({name: text, x: rect.x, y: rect.y});
                    }
                }
            }
            return results;
        }
    """)

    print("\nCadeaux trouvés:")
    for g in gifts:
        print(f"  - {g['name']} at ({g['x']:.0f}, {g['y']:.0f})")

    if not any(g['name'] == 'Fest Pop' for g in gifts):
        print("\n⚠️ Fest Pop NON disponible sur ce live")
        print("   (Fest Pop est réservé aux lives participant à Live Fest)")

    await asyncio.sleep(10)
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "@christ9817"
    asyncio.run(check_gifts(username))
