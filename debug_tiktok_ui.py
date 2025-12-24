#!/usr/bin/env python3
"""
Debug TikTok Live UI
====================

Analyze the TikTok Live page to find gift panel selectors.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright


async def debug_live_ui(username: str):
    """Debug TikTok Live UI and find gift button selectors."""

    print(f"🔍 Debugging TikTok Live UI for @{username}...")

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=False,
        slow_mo=100,
    )

    # Load saved session
    session_path = Path("data/tiktok_session/state.json")
    if session_path.exists():
        context = await browser.new_context(
            storage_state=str(session_path),
            viewport={"width": 1280, "height": 800},
        )
        print("✅ Session chargée")
    else:
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        print("⚠️ Pas de session sauvegardée")

    page = await context.new_page()

    # Navigate to live
    username = username.lstrip("@")
    await page.goto(f"https://www.tiktok.com/@{username}/live")
    print(f"✅ Page chargée: @{username}/live")

    # Wait for page to fully load
    await asyncio.sleep(5)

    # Take screenshot
    screenshot_path = Path("data/debug_tiktok_live.png")
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"📸 Screenshot saved: {screenshot_path}")

    # Find all clickable elements
    print("\n" + "=" * 60)
    print("🔍 ANALYSE DES ÉLÉMENTS INTERACTIFS")
    print("=" * 60)

    # Look for gift-related elements
    gift_keywords = ['gift', 'cadeau', 'send', 'envoyer', 'coin', 'rose', 'fest']

    print("\n🎁 Éléments liés aux cadeaux:")
    print("-" * 60)

    # Search by various attributes
    for keyword in gift_keywords:
        elements = await page.query_selector_all(f'[class*="{keyword}" i], [data-e2e*="{keyword}" i], [aria-label*="{keyword}" i]')
        if elements:
            print(f"\n  Keyword '{keyword}': {len(elements)} éléments trouvés")
            for i, el in enumerate(elements[:5]):
                try:
                    tag = await el.evaluate("el => el.tagName")
                    classes = await el.evaluate("el => el.className")
                    text = await el.inner_text()
                    visible = await el.is_visible()
                    print(f"    [{i}] <{tag}> visible={visible}")
                    print(f"        class: {classes[:80]}...")
                    if text and len(text) < 50:
                        print(f"        text: {text}")
                except:
                    pass

    # Find all buttons
    print("\n\n🔘 Tous les boutons visibles:")
    print("-" * 60)

    buttons = await page.query_selector_all('button, [role="button"]')
    for i, btn in enumerate(buttons[:20]):
        try:
            visible = await btn.is_visible()
            if visible:
                text = await btn.inner_text()
                classes = await btn.evaluate("el => el.className")
                aria = await btn.get_attribute("aria-label") or ""
                print(f"  [{i}] text='{text[:30]}' aria='{aria[:30]}' class={classes[:50]}...")
        except:
            pass

    # Find SVG icons (often gift icons)
    print("\n\n🎨 Icônes SVG (possibles boutons cadeaux):")
    print("-" * 60)

    svgs = await page.query_selector_all('svg')
    print(f"  {len(svgs)} SVG trouvés")

    # Look for specific TikTok Live elements
    print("\n\n📺 Éléments spécifiques TikTok Live:")
    print("-" * 60)

    live_selectors = [
        '[data-e2e="live-gift-button"]',
        '[data-e2e="gift-btn"]',
        '[data-e2e="send-gift-btn"]',
        '[class*="DuxifyGift"]',
        '[class*="gift-panel"]',
        '[class*="GiftContainer"]',
        '[class*="LiveRoom"]',
        '[class*="BottomBar"]',
        '#gift-panel',
        '.gift-button',
    ]

    for selector in live_selectors:
        try:
            el = await page.query_selector(selector)
            if el:
                visible = await el.is_visible()
                print(f"  ✅ {selector} - visible={visible}")
            else:
                print(f"  ❌ {selector} - non trouvé")
        except Exception as e:
            print(f"  ⚠️ {selector} - erreur: {e}")

    # Dump page HTML structure for analysis
    print("\n\n📄 Structure HTML (bottom area):")
    print("-" * 60)

    # Get the bottom part of the live stream (where controls usually are)
    bottom_html = await page.evaluate("""
        () => {
            const elements = document.querySelectorAll('[class*="bottom" i], [class*="control" i], [class*="action" i]');
            return Array.from(elements).map(el => ({
                tag: el.tagName,
                class: el.className,
                id: el.id,
                children: el.children.length
            })).slice(0, 10);
        }
    """)

    for item in bottom_html:
        print(f"  <{item['tag']}> id='{item['id']}' children={item['children']}")
        print(f"    class: {item['class'][:80]}...")

    # Interactive debugging
    print("\n\n" + "=" * 60)
    print("🖱️ MODE INTERACTIF")
    print("=" * 60)
    print("""
Le navigateur reste ouvert pour inspection manuelle.

INSTRUCTIONS:
1. Ouvre les DevTools (F12)
2. Clique sur l'onglet "Elements"
3. Utilise l'outil de sélection (Ctrl+Shift+C)
4. Clique sur le bouton cadeau
5. Note le sélecteur CSS

Appuie sur Entrée pour fermer...
    """)

    try:
        input()
    except:
        await asyncio.sleep(60)

    await browser.close()
    await playwright.stop()
    print("🔌 Navigateur fermé")


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "@liznogalh"
    asyncio.run(debug_live_ui(username))
