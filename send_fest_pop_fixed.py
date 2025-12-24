#!/usr/bin/env python3
"""
Send Fest Pop gifts - FIXED version with correct click coordinates
"""

import asyncio
import sys
from playwright.async_api import async_playwright

# Fest Pop position from debug:
# DIV at (511,420), IMG at (544,432)
# Click on the image center: (544 + 20, 432 + 20) = (564, 452)
FEST_POP_CLICK_POS = (564, 452)

async def send_fest_pop(username: str, quantity: int, cps: float = 3.0):
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🎈 ENVOI DE FEST POP (FIXED) - {username:<36} ║
╠══════════════════════════════════════════════════════════════════════╣
║   Quantité: {quantity:<15,}  Vitesse: {cps} CPS                      ║
║   Durée estimée: ~{quantity/cps/60:.0f} minutes                                      ║
║   Position clic: ({FEST_POP_CLICK_POS[0]}, {FEST_POP_CLICK_POS[1]})                                    ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=20)
    context = await browser.new_context(
        storage_state="data/tiktok_session/state.json",
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()

    # Navigate to live
    username = username.lstrip("@")
    print(f"🔴 Navigation vers @{username}...")
    await page.goto(f"https://www.tiktok.com/@{username}/live")
    await asyncio.sleep(4)
    print("✅ Connecté au live")

    # Open gift panel by clicking "More"
    print("📦 Ouverture du panneau de cadeaux...")
    try:
        more_btn = page.locator('text="More"').last
        await more_btn.click()
        await asyncio.sleep(2)
        print("✅ Panneau ouvert")
    except Exception as e:
        print(f"⚠️ Erreur ouverture panneau: {e}")

    # Verify Fest Pop is visible and get actual position
    print("🔍 Vérification position de Fest Pop...")

    fest_info = await page.evaluate("""
        () => {
            // Method 1: Find by text content "Fest Pop" with proper structure
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );

            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Fest Pop') {
                    // Go up to find the gift container (with flex class)
                    let el = node.parentElement;
                    for (let i = 0; i < 5; i++) {
                        if (el && el.className?.includes?.('flex') &&
                            el.className?.includes?.('items-center')) {
                            const img = el.querySelector('img');
                            if (img) {
                                const imgRect = img.getBoundingClientRect();
                                const containerRect = el.getBoundingClientRect();
                                return {
                                    container: {x: containerRect.x, y: containerRect.y,
                                               w: containerRect.width, h: containerRect.height},
                                    img: {x: imgRect.x, y: imgRect.y,
                                         w: imgRect.width, h: imgRect.height},
                                    clickX: imgRect.x + imgRect.width/2,
                                    clickY: imgRect.y + imgRect.height/2
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

    if fest_info:
        click_x = fest_info['clickX']
        click_y = fest_info['clickY']
        print(f"✅ Fest Pop trouvé!")
        print(f"   Container: ({fest_info['container']['x']:.0f}, {fest_info['container']['y']:.0f})")
        print(f"   Image: ({fest_info['img']['x']:.0f}, {fest_info['img']['y']:.0f}) {fest_info['img']['w']:.0f}x{fest_info['img']['h']:.0f}")
        print(f"   Position clic: ({click_x:.0f}, {click_y:.0f})")
    else:
        print("⚠️ Fest Pop non trouvé, utilisation position par défaut")
        click_x, click_y = FEST_POP_CLICK_POS

    # Test a single click first
    print("\n🧪 Test d'un clic...")
    await page.mouse.click(click_x, click_y)
    await asyncio.sleep(1)
    print("   Vérifiez si un Fest Pop a été envoyé (1 coin déduit)")

    # Ask for confirmation
    print("\n⏳ Démarrage dans 3 secondes... (Ctrl+C pour annuler)")
    await asyncio.sleep(3)

    # Send gifts
    print(f"\n🚀 ENVOI DE {quantity:,} FEST POP...")
    print("─" * 60)

    delay = 1.0 / cps
    sent = 0
    failed = 0

    for i in range(quantity):
        try:
            # Direct mouse click at verified position
            await page.mouse.click(click_x, click_y)
            sent += 1

        except Exception as e:
            failed += 1
            # Try to reopen panel if needed
            if failed % 20 == 0:
                try:
                    more = page.locator('text="More"').last
                    if await more.count() > 0:
                        await more.click()
                        await asyncio.sleep(1)
                        # Re-find Fest Pop position
                        new_info = await page.evaluate("""
                            () => {
                                const containers = document.querySelectorAll('div[class*="gift"], div[class*="Gift"]');
                                for (const el of containers) {
                                    if (el.innerText?.includes('Fest Pop') && el.innerText?.includes('1')) {
                                        const img = el.querySelector('img');
                                        if (img) {
                                            const r = img.getBoundingClientRect();
                                            return {x: r.x + r.width/2, y: r.y + r.height/2};
                                        }
                                    }
                                }
                                return null;
                            }
                        """)
                        if new_info:
                            click_x, click_y = new_info['x'], new_info['y']
                except:
                    pass

        # Progress display
        if (i + 1) % 10 == 0:
            progress = (i + 1) / quantity * 100
            bar_filled = int(progress / 2.5)
            bar = "█" * bar_filled + "░" * (40 - bar_filled)
            print(f"\r  [{bar}] {progress:>5.1f}% | {sent:,}/{quantity:,} | Échecs: {failed}", end="", flush=True)

        await asyncio.sleep(delay)

    print(f"\n\n{'═' * 60}")
    print("📊 RÉSULTAT")
    print("═" * 60)
    print(f"   ✅ Envoyés: {sent:,}")
    print(f"   ❌ Échecs: {failed}")
    if sent + failed > 0:
        print(f"   📈 Taux réussite: {sent/(sent+failed)*100:.1f}%")
    print("═" * 60)

    await context.storage_state(path="data/tiktok_session/state.json")
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "@christ9817"
    quantity = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    cps = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0

    asyncio.run(send_fest_pop(username, quantity, cps))
