#!/usr/bin/env python3
"""
Train AI Agents on Live TikTok Battles

This script connects to a live TikTok stream and trains AI agents
using virtual gifts - no real spending!

Features:
- Real-time score reading from TikTok battles
- Virtual gift decisions (simulated, not sent)
- Learning from battle outcomes
- Persistent learning state across sessions

Usage:
    python train_live_agents.py @username
    python train_live_agents.py @username --strategy aggressive
    python train_live_agents.py @username --duration 600
"""

import asyncio
import sys
import argparse
from datetime import datetime

from playwright.async_api import async_playwright

sys.path.insert(0, '.')

from core.live_learning_engine import (
    LiveLearningEngine,
    TrainingMode,
    VirtualGift,
    BattleExperience
)
from core.ai_battle_controller import AIStrategy


def print_header(username: str, strategy: str, duration: int):
    """Print startup header."""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   LIVE AGENT TRAINING                                                ║
║   Train AI on Real TikTok Battles (Virtual Gifts Only)               ║
╠══════════════════════════════════════════════════════════════════════╣
║   Target: @{username:<25}                                            ║
║   Strategy: {strategy:<20}                                           ║
║   Duration: {duration}s                                              ║
╠══════════════════════════════════════════════════════════════════════╣
║   Mode: VIRTUAL GIFTS                                                ║
║   - AI makes gift decisions                                          ║
║   - NO real gifts are sent                                           ║
║   - Learning persists across sessions                                ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def on_virtual_gift(gift: VirtualGift):
    """Callback for virtual gift decisions."""
    gap_color = "\033[91m" if gift.gap < 0 else "\033[92m"
    reset = "\033[0m"

    print(f"""
┌──────────────────────────────────────────────────────────────────────┐
│ {datetime.now().strftime('%H:%M:%S')} | VIRTUAL GIFT DECISION
├──────────────────────────────────────────────────────────────────────┤
│ Gift: {gift.gift_name} ({gift.gift_cost:,} coins)
│ Reason: {gift.reason[:55]}
├──────────────────────────────────────────────────────────────────────┤
│ Score: {gift.our_score:,} vs {gift.opponent_score:,}
│ Gap: {gap_color}{gift.gap:+,}{reset} | Time: {gift.time_remaining}s
│ Would add: +{gift.would_have_points:,} points
└──────────────────────────────────────────────────────────────────────┘""")


def on_battle_end(experience: BattleExperience):
    """Callback for battle end."""
    result = "WIN" if experience.won else "LOSS"
    result_color = "\033[92m" if experience.won else "\033[91m"
    reset = "\033[0m"

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║ {result_color}BATTLE {result}{reset}
╠══════════════════════════════════════════════════════════════════════╣
║ Final Score: {experience.final_our_score:,} vs {experience.final_opponent_score:,}
║ Virtual Gifts: {len(experience.virtual_gifts)}
║ Virtual Spent: {experience.total_virtual_spent:,} coins
║ Decisions: {experience.decisions_made} ({experience.aggressive_decisions} aggressive, {experience.defensive_decisions} defensive)
╚══════════════════════════════════════════════════════════════════════╝
    """)


def on_learning_update(state: dict):
    """Callback for learning updates."""
    print(f"""
📚 LEARNING UPDATE
   Battles: {state['total_battles']}
   Win Rate: {state['win_rate']*100:.1f}%
   Recent Rewards: {sum(state.get('recent_rewards', [])[-5:])/max(len(state.get('recent_rewards', [])[-5:]), 1):.2f} avg
    """)


async def run_training(
    username: str,
    strategy: str = "smart",
    duration: int = 300
):
    """Run the live training session."""

    username = username.lstrip("@")

    # Parse strategy
    try:
        strat = AIStrategy(strategy.lower())
    except ValueError:
        print(f"Unknown strategy: {strategy}")
        print("Available: aggressive, defensive, sniper, smart, conservative")
        return

    print_header(username, strategy, duration)

    input("\n>>> Press Enter to start training (Ctrl+C to abort) <<<\n")

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

        # Create learning engine
        engine = LiveLearningEngine(
            page,
            strategy=strat,
            mode=TrainingMode.VIRTUAL_GIFTS
        )

        # Load previous learning state
        if engine.load_learning_state():
            print("\n✅ Previous learning state loaded!")
            stats = engine.get_learning_stats()
            print(f"   Battles: {stats['total_battles']}")
            print(f"   Win rate: {stats['win_rate']*100:.1f}%")
        else:
            print("\n📝 Starting fresh learning session")

        # Register callbacks
        engine.on_virtual_gift(on_virtual_gift)
        engine.on_battle_end(on_battle_end)
        engine.on_learning_update(on_learning_update)

        try:
            print(f"\n🎓 Training starting in 3 seconds...\n")
            await asyncio.sleep(3)

            stats = await engine.train_on_stream(
                username=username,
                duration=duration,
                save_experiences=True
            )

            # Save learning state
            engine.save_learning_state()

            # Final summary
            learning_stats = engine.get_learning_stats()
            print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   TRAINING SESSION COMPLETE                                          ║
╠══════════════════════════════════════════════════════════════════════╣
║   Battles observed:    {stats['battles_observed']:>10}                               ║
║   Virtual decisions:   {stats['virtual_gifts_decided']:>10}                               ║
║   Virtual coins spent: {stats['total_virtual_spent']:>10,}                               ║
╠══════════════════════════════════════════════════════════════════════╣
║   LEARNING STATE                                                     ║
║   Total battles:       {learning_stats['total_battles']:>10}                               ║
║   Win rate:            {learning_stats['win_rate']*100:>9.1f}%                               ║
╚══════════════════════════════════════════════════════════════════════╝
            """)

        except KeyboardInterrupt:
            print("\n\n⏹ Stopping training...")
            engine.stop()
            engine.save_learning_state()
            print("✅ Learning state saved!")

        finally:
            # Save session
            await context.storage_state(path="data/tiktok_session/state.json")
            await browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Train AI agents on live TikTok battles (virtual gifts only)"
    )
    parser.add_argument("username", help="Target streamer username")
    parser.add_argument(
        "strategy", nargs="?", default="smart",
        choices=["aggressive", "defensive", "sniper", "smart", "conservative"],
        help="AI strategy to train (default: smart)"
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=300,
        help="Training duration in seconds (default: 300)"
    )

    args = parser.parse_args()

    asyncio.run(run_training(
        username=args.username,
        strategy=args.strategy,
        duration=args.duration
    ))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Usage: python train_live_agents.py <username> [strategy] [options]

Examples:
    python train_live_agents.py @liznogalh
    python train_live_agents.py @streamer aggressive
    python train_live_agents.py @streamer smart --duration 600

Strategies:
    smart        - Adaptive (learns optimal approach)
    aggressive   - High-pressure gifting
    defensive    - Counter-punch when behind
    sniper       - Wait for final moments
    conservative - Minimal intervention

The AI will:
    - Watch real TikTok battles
    - Make virtual gift decisions (not sent)
    - Learn from battle outcomes
    - Save learning state for future sessions
        """)
    else:
        main()
