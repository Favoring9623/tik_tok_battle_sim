#!/usr/bin/env python3
"""
Send Fest Pop gifts - TURBO VERSION
Optimized for maximum speed (5-8 CPS)
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def send_fest_pop_turbo(username: str, quantity: int, cps: float = 6.0):
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🚀 FEST POP TURBO - {username:<46} ║
╠══════════════════════════════════════════════════════════════════════╣
║   Quantité: {quantity:<15,}  Vitesse: {cps} CPS (TURBO)              ║
║   Durée estimée: ~{quantity/cps/60:.1f} minutes                                     ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=0)  # No slow_mo for speed
    context = await browser.new_context(
        storage_state="data/tiktok_session/state.json",
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()

    username = username.lstrip("@")
    print(f"🔴 Navigation vers @{username}...")
    await page.goto(f"https://www.tiktok.com/@{username}/live")
    await asyncio.sleep(3)
    print("✅ Connecté au live")

    # Open gift panel
    print("📦 Ouverture du panneau...")
    try:
        more_btn = page.locator('text="More"').last
        await more_btn.click()
        await asyncio.sleep(1.5)
    except:
        pass

    # Find Fest Pop
    print("🔍 Recherche Fest Pop...")
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
                                const r = img.getBoundingClientRect();
                                return {x: r.x + r.width/2, y: r.y + r.height/2};
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
        print("❌ Fest Pop non trouvé!")
        await browser.close()
        await playwright.stop()
        return

    fest_x, fest_y = fest_info['x'], fest_info['y']
    print(f"✅ Fest Pop: ({fest_x:.0f}, {fest_y:.0f})")

    # Select Fest Pop and find Send button
    await page.mouse.click(fest_x, fest_y)
    await asyncio.sleep(0.3)

    send_pos = await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.trim() === 'Send') {
                    let el = walker.currentNode.parentElement;
                    if (el && el.offsetParent) {
                        const r = el.getBoundingClientRect();
                        return {x: r.x + r.width/2, y: r.y + r.height/2};
                    }
                }
            }
            return null;
        }
    """)

    if not send_pos:
        print("❌ Bouton Send non trouvé!")
        await browser.close()
        await playwright.stop()
        return

    send_x, send_y = send_pos['x'], send_pos['y']
    print(f"✅ Send: ({send_x:.0f}, {send_y:.0f})")

    print(f"\n🚀 ENVOI TURBO DE {quantity:,} FEST POP...")
    print("─" * 60)

    delay = 1.0 / cps
    sent = 0
    failed = 0
    reselect_every = 100  # Re-select less often for speed

    # Pre-move mouse to Send button area
    await page.mouse.move(send_x, send_y)

    for i in range(quantity):
        try:
            # Re-select Fest Pop periodically
            if i > 0 and i % reselect_every == 0:
                await page.mouse.click(fest_x, fest_y)
                await asyncio.sleep(0.15)
                # Update Send position
                new_send = await page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body, NodeFilter.SHOW_TEXT, null, false
                        );
                        while (walker.nextNode()) {
                            if (walker.currentNode.textContent.trim() === 'Send') {
                                let el = walker.currentNode.parentElement;
                                if (el && el.offsetParent) {
                                    const r = el.getBoundingClientRect();
                                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                                }
                            }
                        }
                        return null;
                    }
                """)
                if new_send:
                    send_x, send_y = new_send['x'], new_send['y']

            # Fast click on Send
            await page.mouse.click(send_x, send_y)
            sent += 1

        except:
            failed += 1

        # Progress every 50
        if (i + 1) % 50 == 0:
            progress = (i + 1) / quantity * 100
            bar_filled = int(progress / 2.5)
            bar = "█" * bar_filled + "░" * (40 - bar_filled)
            print(f"\r  [{bar}] {progress:>5.1f}% | {sent:,}/{quantity:,} | Échecs: {failed}", end="", flush=True)

        await asyncio.sleep(delay)

    print(f"\n\n{'═' * 60}")
    print("📊 RÉSULTAT TURBO")
    print("═" * 60)
    print(f"   ✅ Envoyés: {sent:,}")
    print(f"   ❌ Échecs: {failed}")
    print(f"   ⚡ Vitesse: {cps} CPS")
    if sent + failed > 0:
        print(f"   📈 Taux réussite: {sent/(sent+failed)*100:.1f}%")
    print("═" * 60)

    await context.storage_state(path="data/tiktok_session/state.json")
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "@christ9817"
    quantity = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    cps = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0

    asyncio.run(send_fest_pop_turbo(username, quantity, cps))
