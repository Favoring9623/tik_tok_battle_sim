#!/usr/bin/env python3
"""
Send Fest Pop gifts - V2 with Send button click
Workflow: Click gift to select -> Click Send button
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def send_fest_pop(username: str, quantity: int, cps: float = 3.0):
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🎈 ENVOI DE FEST POP V2 - {username:<40} ║
╠══════════════════════════════════════════════════════════════════════╣
║   Quantité: {quantity:<15,}  Vitesse: {cps} CPS                      ║
║   Durée estimée: ~{quantity/cps/60:.0f} minutes                                      ║
║   Méthode: Select + Send button                                     ║
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
        print(f"⚠️ Panneau peut-être déjà ouvert: {e}")

    # Find Fest Pop position
    print("🔍 Recherche de Fest Pop...")
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

    if not fest_info:
        print("❌ Fest Pop non trouvé!")
        await browser.close()
        await playwright.stop()
        return

    fest_x, fest_y = fest_info['clickX'], fest_info['clickY']
    print(f"✅ Fest Pop trouvé à ({fest_x:.0f}, {fest_y:.0f})")

    # Test: Select Fest Pop and click Send
    print("\n🧪 Test: sélection + Send...")
    await page.mouse.click(fest_x, fest_y)
    await asyncio.sleep(0.5)

    # Find and click Send button
    send_clicked = await page.evaluate("""
        () => {
            // Look for Send button
            const buttons = document.querySelectorAll('button, div[role="button"]');
            for (const btn of buttons) {
                if (btn.innerText?.trim() === 'Send' && btn.offsetParent) {
                    btn.click();
                    return true;
                }
            }
            // Also try by text
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Send') {
                    let el = node.parentElement;
                    if (el && el.offsetParent) {
                        el.click();
                        return true;
                    }
                }
            }
            return false;
        }
    """)

    if send_clicked:
        print("✅ Bouton Send cliqué!")
    else:
        print("⚠️ Bouton Send non trouvé, essai avec position fixe...")
        # Send button appears below the selected gift
        # From screenshot, it's around (420, 357) when Fest Pop is selected
        await page.mouse.click(420, 357)

    await asyncio.sleep(1)
    print("   Vérifiez si 1 Fest Pop a été envoyé")

    print("\n⏳ Démarrage dans 3 secondes... (Ctrl+C pour annuler)")
    await asyncio.sleep(3)

    # Send gifts
    print(f"\n🚀 ENVOI DE {quantity:,} FEST POP...")
    print("─" * 60)

    # For faster sending, we need to:
    # 1. Keep Fest Pop selected
    # 2. Spam click on Send button

    # First, find Send button position after selecting Fest Pop
    await page.mouse.click(fest_x, fest_y)
    await asyncio.sleep(0.3)

    send_pos = await page.evaluate("""
        () => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            while (walker.nextNode()) {
                const node = walker.currentNode;
                if (node.textContent.trim() === 'Send') {
                    let el = node.parentElement;
                    if (el && el.offsetParent) {
                        const rect = el.getBoundingClientRect();
                        return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                    }
                }
            }
            return null;
        }
    """)

    if send_pos:
        send_x, send_y = send_pos['x'], send_pos['y']
        print(f"✅ Bouton Send trouvé à ({send_x:.0f}, {send_y:.0f})")
    else:
        print("⚠️ Send non trouvé, utilisation position estimée")
        send_x, send_y = 420, 357

    delay = 1.0 / cps
    sent = 0
    failed = 0
    reselect_interval = 50  # Re-select Fest Pop every N clicks

    for i in range(quantity):
        try:
            # Periodically re-select Fest Pop to keep it selected
            if i % reselect_interval == 0:
                await page.mouse.click(fest_x, fest_y)
                await asyncio.sleep(0.2)
                # Re-find Send button in case position changed
                new_send = await page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body, NodeFilter.SHOW_TEXT, null, false
                        );
                        while (walker.nextNode()) {
                            const node = walker.currentNode;
                            if (node.textContent.trim() === 'Send') {
                                let el = node.parentElement;
                                if (el && el.offsetParent) {
                                    const rect = el.getBoundingClientRect();
                                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                                }
                            }
                        }
                        return null;
                    }
                """)
                if new_send:
                    send_x, send_y = new_send['x'], new_send['y']

            # Click Send button
            await page.mouse.click(send_x, send_y)
            sent += 1

        except Exception as e:
            failed += 1
            # Try to recover
            if failed % 10 == 0:
                try:
                    more = page.locator('text="More"').last
                    if await more.count() > 0:
                        await more.click()
                        await asyncio.sleep(1)
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
