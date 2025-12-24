#!/usr/bin/env python3
"""
Investigate why gifts aren't being sent - check balance before/after clicks
"""

import asyncio
from playwright.async_api import async_playwright

async def investigate():
    print("=== INVESTIGATION: POURQUOI LES CADEAUX NE SONT PAS ENVOYÉS ===\n")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=100)
    context = await browser.new_context(
        storage_state="data/tiktok_session/state.json",
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()

    print("1. Navigation vers le live...")
    await page.goto("https://www.tiktok.com/@christ9817/live")
    await asyncio.sleep(5)

    print("2. Ouverture du panneau de cadeaux...")
    try:
        more_btn = page.locator('text="More"').last
        await more_btn.click()
        await asyncio.sleep(2)
    except:
        print("   Panneau peut-être déjà ouvert")

    # Screenshot before
    await page.screenshot(path="investigate_before.png")
    print("   Screenshot: investigate_before.png")

    # Try to read balance
    print("\n3. Lecture du solde...")
    balance_info = await page.evaluate("""
        () => {
            // Look for balance display (usually shows coin count)
            const elements = document.querySelectorAll('*');
            const results = [];
            for (const el of elements) {
                const text = el.innerText?.trim() || '';
                // Look for numbers that could be balance
                if (/^\\d{1,3}(,\\d{3})*$/.test(text) || /^\\d+$/.test(text)) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.y < 400) {
                        results.push({
                            text: text,
                            x: rect.x,
                            y: rect.y,
                            tag: el.tagName,
                            class: el.className?.slice?.(0, 50) || ''
                        });
                    }
                }
            }
            return results.slice(0, 10);
        }
    """)
    print("   Éléments numériques trouvés:")
    for item in balance_info:
        print(f"      '{item['text']}' at ({item['x']:.0f}, {item['y']:.0f})")

    # Find Fest Pop position
    print("\n4. Recherche de Fest Pop...")
    fest_info = await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    let el = node.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (el && el.className?.includes?.('flex') &&
                            el.className?.includes?.('items-center')) {
                            const img = el.querySelector('img');
                            if (img) {
                                const imgRect = img.getBoundingClientRect();
                                return {
                                    imgX: imgRect.x + imgRect.width/2,
                                    imgY: imgRect.y + imgRect.height/2,
                                    containerClass: el.className
                                };
                            }
                        }
                        el = el?.parentElement;
                    }
                }
            }
            return null;
        }
    """)

    if not fest_info:
        print("   Fest Pop non trouvé!")
        await browser.close()
        return

    click_x, click_y = fest_info['imgX'], fest_info['imgY']
    print(f"   Fest Pop trouvé à ({click_x:.0f}, {click_y:.0f})")

    # Test different click methods
    print("\n5. TEST DE DIFFÉRENTES MÉTHODES DE CLIC...")

    print("\n   === Méthode A: Mouse click simple ===")
    await page.mouse.click(click_x, click_y)
    await asyncio.sleep(2)
    await page.screenshot(path="investigate_after_click_A.png")
    print("   Screenshot: investigate_after_click_A.png")

    print("\n   === Méthode B: Double click ===")
    await page.mouse.dblclick(click_x, click_y)
    await asyncio.sleep(2)
    await page.screenshot(path="investigate_after_click_B.png")
    print("   Screenshot: investigate_after_click_B.png")

    print("\n   === Méthode C: Click via evaluate sur l'image ===")
    await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    let el = node.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (el && el.className?.includes?.('flex')) {
                            const img = el.querySelector('img');
                            if (img) {
                                img.click();
                                return true;
                            }
                        }
                        el = el?.parentElement;
                    }
                }
            }
            return false;
        }
    """)
    await asyncio.sleep(2)
    await page.screenshot(path="investigate_after_click_C.png")
    print("   Screenshot: investigate_after_click_C.png")

    print("\n   === Méthode D: Click sur le container entier ===")
    await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    let el = node.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (el && el.className?.includes?.('flex') &&
                            el.className?.includes?.('items-center')) {
                            el.click();
                            return true;
                        }
                        el = el?.parentElement;
                    }
                }
            }
            return false;
        }
    """)
    await asyncio.sleep(2)
    await page.screenshot(path="investigate_after_click_D.png")
    print("   Screenshot: investigate_after_click_D.png")

    print("\n   === Méthode E: dispatchEvent MouseEvent ===")
    await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    let el = node.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (el && el.className?.includes?.('flex')) {
                            const img = el.querySelector('img');
                            if (img) {
                                const event = new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                });
                                img.dispatchEvent(event);
                                return true;
                            }
                        }
                        el = el?.parentElement;
                    }
                }
            }
            return false;
        }
    """)
    await asyncio.sleep(2)
    await page.screenshot(path="investigate_after_click_E.png")
    print("   Screenshot: investigate_after_click_E.png")

    # Check for any popup/dialog
    print("\n6. Vérification des popups/dialogs...")
    dialogs = await page.evaluate("""
        () => {
            const results = [];
            // Look for modal/dialog elements
            const modals = document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="Modal"], [class*="popup"], [class*="Popup"]');
            for (const m of modals) {
                if (m.offsetParent !== null) {
                    results.push({
                        tag: m.tagName,
                        class: m.className?.slice?.(0, 60),
                        text: m.innerText?.slice?.(0, 100)
                    });
                }
            }
            return results;
        }
    """)

    if dialogs:
        print("   Dialogs/popups trouvés:")
        for d in dialogs:
            print(f"      <{d['tag']}> {d['class']}: {d['text']}")
    else:
        print("   Aucun dialog trouvé")

    print("\n7. Garder le navigateur ouvert 60s pour inspection manuelle...")
    print("   Vérifiez les screenshots générés et testez manuellement dans le navigateur")
    await asyncio.sleep(60)

    await context.storage_state(path="data/tiktok_session/state.json")
    await browser.close()
    await playwright.stop()

    print("\n=== FIN DE L'INVESTIGATION ===")
    print("Screenshots générés:")
    print("  - investigate_before.png")
    print("  - investigate_after_click_A.png (mouse click)")
    print("  - investigate_after_click_B.png (double click)")
    print("  - investigate_after_click_C.png (JS click sur img)")
    print("  - investigate_after_click_D.png (JS click sur container)")
    print("  - investigate_after_click_E.png (dispatchEvent)")

if __name__ == "__main__":
    asyncio.run(investigate())
