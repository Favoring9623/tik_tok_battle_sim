#!/usr/bin/env python3
"""
Live Auto-Clicker for TikTok Live Fest
======================================

Interactive tool to send gifts automatically on TikTok Live.

Usage:
    python run_auto_clicker_live.py                    # Interactive mode
    python run_auto_clicker_live.py --test             # Test browser setup
    python run_auto_clicker_live.py --target @user     # Direct to user's live
    python run_auto_clicker_live.py --login            # Force re-login

WARNING: This may violate TikTok's Terms of Service.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.tiktok_gift_sender import TikTokGiftSender, SenderSession


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🖱️  TIKTOK LIVE AUTO-CLICKER                                      ║
║                                                                      ║
║   Envoi automatique de cadeaux pour Live Fest                       ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║   ⚠️  ATTENTION: Utilisation à vos risques et périls                ║
║   Cet outil peut entraîner la suspension de votre compte TikTok     ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def print_progress(session: SenderSession):
    """Print progress bar."""
    width = 40
    filled = int(width * session.progress / 100)
    bar = "█" * filled + "░" * (width - filled)
    elapsed = session.start_time

    print(f"\r  [{bar}] {session.progress:>5.1f}% | "
          f"{session.sent:,}/{session.total_quantity:,} | "
          f"Failed: {session.failed}", end="", flush=True)


async def run_interactive(target: str = None):
    """Run in interactive mode."""
    print_banner()

    async with TikTokGiftSender(
        headless=False,
        slow_mo=50,
        on_progress=print_progress
    ) as sender:

        # Check/perform login
        print("\n🔍 Vérification de la connexion...")

        if not await sender.is_logged_in():
            print("\n❌ Non connecté à TikTok")
            print("📱 Veuillez vous connecter dans la fenêtre du navigateur...")
            print("   (QR code, téléphone ou email)")
            print("   ⏳ Timeout: 3 minutes\n")

            if not await sender.login(timeout=180):
                print("❌ Échec de la connexion")
                return

        print("✅ Connecté à TikTok!\n")

        # Navigate to target if specified
        if target:
            print(f"🔴 Navigation vers {target}...")
            if not await sender.go_to_live(target):
                print(f"❌ {target} n'est pas en live actuellement")
                target = None

        # Main loop
        while True:
            print("\n" + "═" * 60)
            print("📋 MENU PRINCIPAL")
            print("═" * 60)
            print("  1. 🔴 Aller sur un live")
            print("  2. 🎁 Envoyer des cadeaux (quantité manuelle)")
            print("  3. 🚀 Mode BURST (auto-clicker rapide)")
            print("  4. 📦 Lots pré-définis")
            print("  5. 🚪 Quitter")
            print("═" * 60)

            try:
                choice = input("\n👉 Choix (1-5): ").strip()
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir!")
                break

            if choice == "1":
                username = input("   Nom d'utilisateur (@...): ").strip()
                if username:
                    if await sender.go_to_live(username):
                        print(f"   ✅ Connecté au live de {username}")
                    else:
                        print(f"   ❌ {username} n'est pas en live")

            elif choice == "2":
                print("\n   🎁 ENVOI MANUEL")
                print("   ─" * 25)

                gift = input("   Cadeau [Fest Pop]: ").strip() or "Fest Pop"
                qty_str = input("   Quantité [10]: ").strip() or "10"

                try:
                    qty = int(qty_str)
                except ValueError:
                    print("   ❌ Quantité invalide")
                    continue

                print(f"\n   🚀 Envoi de {qty}x {gift}...")
                print("   " + "─" * 50)

                session = await sender.send_gift(gift, qty, delay_ms=500)

                print(f"\n\n   ✅ Terminé!")
                print(f"   📊 Envoyés: {session.sent} | Échecs: {session.failed}")

            elif choice == "3":
                print("\n   🚀 MODE BURST (Auto-Clicker)")
                print("   ─" * 25)

                gift = input("   Cadeau [Fest Pop]: ").strip() or "Fest Pop"
                qty_str = input("   Quantité [100]: ").strip() or "100"
                cps_str = input("   Clicks/seconde [5]: ").strip() or "5"

                try:
                    qty = int(qty_str)
                    cps = float(cps_str)
                except ValueError:
                    print("   ❌ Valeurs invalides")
                    continue

                duration = qty / cps
                print(f"\n   ⚡ Burst: {qty}x {gift} @ {cps} CPS")
                print(f"   ⏱️  Durée estimée: {duration:.1f} secondes")
                print("   " + "─" * 50)

                confirm = input("   Confirmer? (o/N): ").strip().lower()
                if confirm != 'o':
                    print("   ❌ Annulé")
                    continue

                session = await sender.send_burst(gift, qty, cps)

                print(f"\n\n   ✅ Burst terminé!")
                print(f"   📊 Envoyés: {session.sent} | Échecs: {session.failed}")

            elif choice == "4":
                print("\n   📦 LOTS PRÉ-DÉFINIS")
                print("   ─" * 25)
                print("   a. Micro   - 10 Fest Pop")
                print("   b. Small   - 100 Fest Pop")
                print("   c. Medium  - 1,000 Fest Pop")
                print("   d. Large   - 5,000 Fest Pop")
                print("   e. Mega    - 10,000 Fest Pop")

                lot = input("\n   Choisir lot (a-e): ").strip().lower()

                lots = {
                    'a': ('Fest Pop', 10, 2),
                    'b': ('Fest Pop', 100, 5),
                    'c': ('Fest Pop', 1000, 10),
                    'd': ('Fest Pop', 5000, 10),
                    'e': ('Fest Pop', 10000, 10),
                }

                if lot not in lots:
                    print("   ❌ Lot invalide")
                    continue

                gift, qty, cps = lots[lot]
                duration = qty / cps

                print(f"\n   📦 Lot sélectionné: {qty:,}x {gift}")
                print(f"   ⏱️  Durée: ~{duration:.0f} secondes ({duration/60:.1f} min)")

                confirm = input("   Confirmer? (o/N): ").strip().lower()
                if confirm != 'o':
                    print("   ❌ Annulé")
                    continue

                session = await sender.send_burst(gift, qty, cps)

                print(f"\n\n   ✅ Lot terminé!")
                print(f"   📊 Envoyés: {session.sent} | Échecs: {session.failed}")

            elif choice == "5":
                print("\n👋 Au revoir!")
                break

            else:
                print("   ❌ Option invalide")


async def run_test():
    """Test browser setup."""
    print_banner()
    print("🧪 Test de configuration...\n")

    async with TikTokGiftSender(headless=False) as sender:
        print("✅ Navigateur démarré")

        await sender._page.goto("https://www.tiktok.com")
        print("✅ TikTok chargé")

        logged_in = await sender.is_logged_in()
        status = "Connecté" if logged_in else "Non connecté"
        icon = "✅" if logged_in else "⚠️"
        print(f"{icon} Statut: {status}")

        if not logged_in:
            print("\n💡 Pour vous connecter, lancez:")
            print("   python run_auto_clicker_live.py --login")

        print("\n✅ Test terminé (fermeture dans 5s...)")
        await asyncio.sleep(5)


async def run_login():
    """Force login flow."""
    print_banner()
    print("🔐 Mode connexion...\n")

    # Delete existing session
    session_file = Path("data/tiktok_session/state.json")
    if session_file.exists():
        session_file.unlink()
        print("🗑️  Session précédente supprimée")

    async with TikTokGiftSender(headless=False) as sender:
        print("📱 Connectez-vous dans la fenêtre du navigateur...")
        print("   Utilisez QR code, téléphone ou email")
        print("   ⏳ Timeout: 3 minutes\n")

        if await sender.login(timeout=180):
            print("\n✅ Connexion réussie! Session sauvegardée.")
        else:
            print("\n❌ Échec de la connexion")


def main():
    parser = argparse.ArgumentParser(description="TikTok Live Auto-Clicker")
    parser.add_argument("--test", action="store_true", help="Test browser setup")
    parser.add_argument("--login", action="store_true", help="Force re-login")
    parser.add_argument("--target", type=str, help="Go directly to user's live (e.g., @username)")

    args = parser.parse_args()

    if args.test:
        asyncio.run(run_test())
    elif args.login:
        asyncio.run(run_login())
    else:
        asyncio.run(run_interactive(args.target))


if __name__ == "__main__":
    main()
