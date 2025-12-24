#!/usr/bin/env python3
"""
Send Fest Pop gifts - handles expanded gift panel
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def send_fest_pop(username: str, quantity: int, cps: float = 3.0):
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🎈 ENVOI DE FEST POP - {username:<43} ║
╠══════════════════════════════════════════════════════════════════════╣
║   Quantité: {quantity:<15,}  Vitesse: {cps} CPS                      ║
║   Durée estimée: ~{quantity/cps/60:.0f} minutes                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=30)
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

    # Find and click Fest Pop location
    print("🔍 Recherche de Fest Pop...")

    # Get Fest Pop position
    fest_pop_pos = await page.evaluate("""
        () => {
            const elements = document.querySelectorAll('*');
            for (const el of elements) {
                if (el.innerText?.trim() === 'Fest Pop' && el.offsetParent) {
                    const rect = el.getBoundingClientRect();
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                }
            }
            return null;
        }
    """)

    if not fest_pop_pos:
        print("❌ Fest Pop non trouvé!")
        await browser.close()
        await playwright.stop()
        return

    print(f"✅ Fest Pop trouvé à ({fest_pop_pos['x']:.0f}, {fest_pop_pos['y']:.0f})")

    # Send gifts
    print(f"\n🚀 ENVOI DE {quantity:,} FEST POP...")
    print("─" * 60)

    delay = 1.0 / cps
    sent = 0
    failed = 0

    for i in range(quantity):
        try:
            # Click on Fest Pop using JavaScript for speed
            result = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.innerText?.trim() === 'Fest Pop' && el.offsetParent) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if result:
                sent += 1
            else:
                failed += 1
                # Try to reopen panel if closed
                if failed % 10 == 0:
                    try:
                        more = page.locator('text="More"').last
                        if await more.count() > 0:
                            await more.click()
                            await asyncio.sleep(0.5)
                    except:
                        pass

        except Exception as e:
            failed += 1

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
