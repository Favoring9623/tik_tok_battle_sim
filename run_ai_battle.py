#!/usr/bin/env python3
"""
Run AI Battle Controller - Full integration with gift sending

Usage:
    python run_ai_battle.py @streamer smart
    python run_ai_battle.py @streamer aggressive --gift "Rose"
    python run_ai_battle.py @streamer sniper --duration 300
"""

import asyncio
import sys
import argparse
from datetime import datetime

from playwright.async_api import async_playwright

# Add parent to path for imports
sys.path.insert(0, '.')

from core.ai_battle_controller import (
    AIBattleController,
    AIConfig,
    AIStrategy,
    AIDecision,
    BattleScore
)
from core.gift_sender import TikTokGiftSender


def print_header(config: AIConfig, duration: int):
    """Print startup header."""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   AI BATTLE CONTROLLER                                               ║
╠══════════════════════════════════════════════════════════════════════╣
║   Target: @{config.target_streamer:<25}                              ║
║   Strategy: {config.strategy.value:<20}                              ║
║   Gift: {config.gift_name:<20}                                       ║
║   Duration: {duration}s                                              ║
╠══════════════════════════════════════════════════════════════════════╣
║   Strategies:                                                        ║
║   - aggressive: Full pressure constantly                             ║
║   - defensive: Only sends when behind                                ║
║   - sniper: Saves and strikes at the end                             ║
║   - smart: Adapts to situation (recommended)                         ║
║   - conservative: Minimal spending                                   ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def print_decision(decision: AIDecision, score: BattleScore, stats: dict):
    """Print AI decision in real-time."""
    gap_color = "\033[92m" if score.gap > 0 else ("\033[91m" if score.gap < 0 else "\033[93m")
    reset = "\033[0m"

    status = "SEND" if decision.should_send else "WAIT"
    status_color = "\033[92m" if decision.should_send else "\033[90m"

    print(f"""
┌──────────────────────────────────────────────────────────────────────┐
│ {datetime.now().strftime('%H:%M:%S')} | Battle: {'ACTIVE' if score.battle_active else 'INACTIVE':8} | Time: {score.time_remaining:3}s remaining
├──────────────────────────────────────────────────────────────────────┤
│ SCORE: {score.our_score:>10,} vs {score.opponent_score:<10,}
│ GAP:   {gap_color}{score.gap:>+10,}{reset}  ({score.gap_percentage:+.1f}%)
├──────────────────────────────────────────────────────────────────────┤
│ DECISION: {status_color}{status:4}{reset} | Urgency: {decision.urgency:8} | CPS: {decision.cps}
│ REASON: {decision.reason[:55]}
├──────────────────────────────────────────────────────────────────────┤
│ STATS: Sent {stats.get('gifts_sent', 0):,} gifts | Decisions: {stats.get('decisions_made', 0)}
└──────────────────────────────────────────────────────────────────────┘""")


async def run_ai_battle(
    username: str,
    strategy: str = "smart",
    gift_name: str = "Fest Pop",
    duration: int = 300,
    demo_mode: bool = False
):
    """Run the AI battle controller."""

    username = username.lstrip("@")

    # Parse strategy
    try:
        strat = AIStrategy(strategy.lower())
    except ValueError:
        print(f"Unknown strategy: {strategy}")
        print("Available: aggressive, defensive, sniper, smart, conservative")
        return

    # Create config
    config = AIConfig(
        strategy=strat,
        target_streamer=username,
        gift_name=gift_name,
        max_total_gifts=10000,
        max_gifts_per_minute=500
    )

    print_header(config, duration)

    if demo_mode:
        print("\n DEMO MODE - No gifts will be sent\n")
    else:
        input("\n>>> Press Enter to start AI battle (Ctrl+C to abort) <<<\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state="data/tiktok_session/state.json",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        # Navigate to stream
        print(f"Connecting to @{username}...")
        try:
            await page.goto(
                f"https://www.tiktok.com/@{username}/live",
                wait_until="domcontentloaded",
                timeout=30000
            )
        except Exception as e:
            print(f"Navigation warning: {e}")
        await asyncio.sleep(5)

        # Create gift sender (unless demo mode)
        gift_sender = None
        if not demo_mode:
            gift_sender = TikTokGiftSender()
            gift_sender._playwright = p
            gift_sender._browser = browser
            gift_sender._context = context
            gift_sender._page = page
            gift_sender._is_connected = True
            gift_sender._current_streamer = username

        # Create controller
        controller = AIBattleController(page, config, gift_sender)

        # Callback to display decisions
        def on_decision(decision, score):
            print_decision(decision, score, controller.stats)

        controller.on_decision(on_decision)

        try:
            print(f"\n AI Battle starting in 3 seconds...\n")
            await asyncio.sleep(3)

            stats = await controller.run_battle_ai(duration=duration)

            # Final summary
            print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   BATTLE FINISHED                                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║   Total gifts sent: {stats['gifts_sent']:>10,}                       ║
║   Failed attempts:  {stats['gifts_failed']:>10}                       ║
║   Decisions made:   {stats['decisions_made']:>10}                       ║
╚══════════════════════════════════════════════════════════════════════╝
            """)

        except KeyboardInterrupt:
            print("\n\n Stopping AI battle...")
            controller.stop()

        finally:
            # Save session
            await context.storage_state(path="data/tiktok_session/state.json")
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description="AI Battle Controller")
    parser.add_argument("username", help="Target streamer username")
    parser.add_argument("strategy", nargs="?", default="smart",
                       choices=["aggressive", "defensive", "sniper", "smart", "conservative"],
                       help="AI strategy (default: smart)")
    parser.add_argument("--gift", "-g", default="Fest Pop",
                       help="Gift to send (default: Fest Pop)")
    parser.add_argument("--duration", "-d", type=int, default=300,
                       help="Battle duration in seconds (default: 300)")
    parser.add_argument("--demo", action="store_true",
                       help="Demo mode - no gifts sent")

    args = parser.parse_args()

    asyncio.run(run_ai_battle(
        username=args.username,
        strategy=args.strategy,
        gift_name=args.gift,
        duration=args.duration,
        demo_mode=args.demo
    ))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Usage: python run_ai_battle.py <username> [strategy] [options]

Examples:
    python run_ai_battle.py @liznogalh smart
    python run_ai_battle.py @streamer aggressive --gift "Rose"
    python run_ai_battle.py @streamer sniper --duration 300
    python run_ai_battle.py @streamer smart --demo

Strategies:
    aggressive   - Full pressure constantly
    defensive    - Only sends when behind
    sniper       - Saves and strikes at the end
    smart        - Adapts to situation (recommended)
    conservative - Minimal spending
        """)
    else:
        main()
