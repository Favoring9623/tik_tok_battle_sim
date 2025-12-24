#!/usr/bin/env python3
"""
Direct Gift Sender - Non-Interactive
=====================================

Send gifts directly without interactive menu.

Usage:
    python send_gifts_now.py @username 100
    python send_gifts_now.py @username 100 --gift "Fest Pop" --cps 5
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.tiktok_gift_sender import TikTokGiftSender, SenderSession


def print_progress(session: SenderSession):
    """Print progress bar."""
    width = 40
    filled = int(width * session.progress / 100)
    bar = "█" * filled + "░" * (width - filled)

    print(f"\r  [{bar}] {session.progress:>5.1f}% | "
          f"{session.sent:,}/{session.total_quantity:,} | "
          f"Échecs: {session.failed}", end="", flush=True)


async def send_gifts(
    target: str,
    quantity: int,
    gift: str = "Fest Pop",
    cps: float = 5.0,
    headless: bool = False
):
    """Send gifts to a live stream."""

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🎁 ENVOI DE CADEAUX - {target:<45} ║
╠══════════════════════════════════════════════════════════════════════╣
║   Cadeau: {gift:<20}  Quantité: {quantity:<20,}  ║
║   Vitesse: {cps} CPS            Durée estimée: ~{quantity/cps:.0f}s{' '*15}║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    async with TikTokGiftSender(
        headless=headless,
        slow_mo=30,
        on_progress=print_progress
    ) as sender:

        # Check login
        print("🔍 Vérification connexion...")
        if not await sender.is_logged_in():
            print("❌ Non connecté! Lance d'abord:")
            print("   python run_auto_clicker_live.py --login")
            return None

        print("✅ Connecté à TikTok")

        # Go to live
        print(f"🔴 Navigation vers {target}...")
        if not await sender.go_to_live(target):
            print(f"❌ {target} n'est pas en live")
            return None

        print(f"✅ Connecté au live de {target}")

        # Countdown
        print("\n⏳ Démarrage dans 3 secondes...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            await asyncio.sleep(1)

        # Send gifts
        print(f"\n🚀 ENVOI DE {quantity:,}x {gift}...")
        print("─" * 60)

        session = await sender.send_burst(gift, quantity, cps)

        print(f"\n\n{'═' * 60}")
        print("📊 RÉSULTAT")
        print("═" * 60)
        print(f"   ✅ Envoyés: {session.sent:,}")
        print(f"   ❌ Échecs: {session.failed}")
        total = session.sent + session.failed
        if total > 0:
            print(f"   📈 Taux réussite: {session.sent/total*100:.1f}%")
        else:
            print(f"   📈 Taux réussite: N/A")
        import time
        duration = time.time() - session.start_time
        print(f"   ⏱️  Durée: {duration:.1f}s")
        print("═" * 60)

        return session


def main():
    parser = argparse.ArgumentParser(description="Send TikTok gifts directly")
    parser.add_argument("target", help="Target username (e.g., @liznogalh)")
    parser.add_argument("quantity", type=int, help="Number of gifts to send")
    parser.add_argument("--gift", default="Fest Pop", help="Gift name (default: Fest Pop)")
    parser.add_argument("--cps", type=float, default=5.0, help="Clicks per second (default: 5)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    args = parser.parse_args()

    asyncio.run(send_gifts(
        target=args.target,
        quantity=args.quantity,
        gift=args.gift,
        cps=args.cps,
        headless=args.headless
    ))


if __name__ == "__main__":
    main()
