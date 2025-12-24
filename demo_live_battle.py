#!/usr/bin/env python3
"""
Demo: Live TikTok Battle

Connect to TWO real TikTok Live streams and run a battle
based on actual gifts received!

Usage:
    python demo_live_battle.py @creator1 @opponent

Features:
- Real-time gift tracking from TikTok Live
- Phase system (Boosts, x5 Gloves)
- Live score updates
- Web dashboard support
"""

import asyncio
import sys
import signal
from datetime import datetime

# Add project to path
sys.path.insert(0, '.')

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveGiftEvent,
    TIKTOK_LIVE_AVAILABLE
)
from core.live_battle_engine import LiveBattleEngine, BattleMode


def print_banner():
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🎮 TIKTOK LIVE BATTLE - REAL-TIME GIFT COMPETITION 🎮          ║
║                                                                  ║
║   Connect to actual TikTok Live streams and compete!             ║
║   Gifts received = Battle Points                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def print_status_bar(state: dict):
    """Print current battle status."""
    creator_score = state['creator_score']
    opponent_score = state['opponent_score']
    time_remaining = state['time_remaining']
    phase = state['current_phase']
    multiplier = state['current_multiplier']

    # Determine leader
    if creator_score > opponent_score:
        leader = f"@{state['creator_username']} +{creator_score - opponent_score:,}"
    elif opponent_score > creator_score:
        leader = f"@{state['opponent_username']} +{opponent_score - creator_score:,}"
    else:
        leader = "TIE"

    # Phase emoji
    phase_display = {
        'normal': '⏱️',
        'boost1': '🔥 BOOST #1',
        'boost2': '🔥 BOOST #2',
        'x5': '🥊 x5 ACTIVE',
        'final_30s': '⚡ FINAL 30s',
        'final_5s': '💀 FINAL 5s'
    }.get(phase, '⏱️')

    print(f"\r[{time_remaining:03d}s] {phase_display} (x{multiplier}) | "
          f"Creator: {creator_score:,} | Opponent: {opponent_score:,} | "
          f"Leader: {leader}     ", end='', flush=True)


async def run_live_battle(creator: str, opponent: str, duration: int):
    """Run a live battle between two TikTok users."""
    print(f"\n🎬 Initializing battle: @{creator} vs @{opponent}")
    print(f"⏱️  Duration: {duration} seconds\n")

    engine = LiveBattleEngine(
        creator_username=creator,
        opponent_username=opponent,
        battle_duration=duration,
        mode=BattleMode.LIVE
    )

    # Gift tracking
    gift_log = []

    def on_gift(event: LiveGiftEvent, creator_score: int, opponent_score: int):
        """Handle gift events."""
        team_emoji = "🟢" if event.team == "creator" else "🔴"
        gift_log.append({
            'time': datetime.now(),
            'team': event.team,
            'user': event.username,
            'gift': event.gift_name,
            'count': event.repeat_count,
            'coins': event.total_coins
        })

        # Print gift notification
        print(f"\n{team_emoji} {event.username}: {event.gift_name} x{event.repeat_count} "
              f"({event.total_coins:,} coins)")
        print_status_bar(engine.get_state())

    def on_phase(phase: str, multiplier: float):
        """Handle phase changes."""
        phase_names = {
            'normal': 'Normal Phase',
            'boost1': '🔥 BOOST #1 ACTIVATED!',
            'boost2': '🔥 BOOST #2 ACTIVATED!',
            'x5': '🥊 x5 GLOVE ACTIVATED!',
            'final_30s': '⚡ FINAL 30 SECONDS!',
            'final_5s': '💀 FINAL 5 SECONDS!'
        }
        print(f"\n\n{'='*50}")
        print(f"   {phase_names.get(phase, phase)} (x{multiplier})")
        print(f"{'='*50}\n")

    def on_end(winner: str, result: dict):
        """Handle battle end."""
        print(f"\n\n{'='*60}")
        print(f"   🏆 BATTLE COMPLETE!")
        print(f"{'='*60}")
        print(f"\n   Winner: {'@' + result['creator_username'] if winner == 'creator' else '@' + result['opponent_username'] if winner == 'opponent' else 'TIE'}")
        print(f"\n   Final Scores:")
        print(f"   🟢 @{result['creator_username']}: {result['creator_score']:,} pts")
        print(f"   🔴 @{result['opponent_username']}: {result['opponent_score']:,} pts")
        print(f"\n   Total Gifts: Creator={result['creator_gifts']}, Opponent={result['opponent_gifts']}")

        if result['top_creator_gifters']:
            print(f"\n   🟢 Top Creator Supporters:")
            for user, coins in list(result['top_creator_gifters'].items())[:3]:
                print(f"      • {user}: {coins:,} coins")

        if result['top_opponent_gifters']:
            print(f"\n   🔴 Top Opponent Supporters:")
            for user, coins in list(result['top_opponent_gifters'].items())[:3]:
                print(f"      • {user}: {coins:,} coins")

        print(f"\n{'='*60}\n")

    # Register callbacks
    engine.on_gift(on_gift)
    engine.on_phase_change(on_phase)
    engine.on_battle_end(on_end)

    # Handle Ctrl+C
    def signal_handler(sig, frame):
        print("\n\n⚠️  Battle interrupted! Stopping...")
        asyncio.create_task(engine.stop_battle())

    signal.signal(signal.SIGINT, signal_handler)

    # Start battle
    print("🔌 Connecting to TikTok Live streams...")
    print("   (Make sure both users are currently LIVE)\n")

    try:
        await engine.start_live_battle()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCommon issues:")
        print("  • User is not currently live")
        print("  • Username is incorrect")
        print("  • Network/proxy issues")
        raise


async def run_single_stream_monitor(username: str):
    """Monitor a single TikTok Live stream with auto-reconnect."""
    print(f"\n📺 Monitoring @{username}'s stream...")
    print("   🔄 Auto-reconnect enabled (retries every 10s if stream ends)")
    print("   Press Ctrl+C to stop\n")

    connector = TikTokLiveConnector(username)

    def on_gift(event: LiveGiftEvent):
        print(f"\n🎁 {event.username}: {event.gift_name} x{event.repeat_count}")
        print(f"   Value: {event.total_coins:,} coins = {event.total_points:,} pts")

    def on_connect(uid: str):
        print(f"\n✅ Connected to @{uid}")
        print("🔴 LIVE - Waiting for gifts...\n")

    def on_disconnect(uid: str):
        print(f"\n⚠️  Disconnected from @{uid}")
        print("   Will attempt to reconnect...")

    def on_comment(username: str, comment: str):
        print(f"💬 {username}: {comment}")

    connector.on_gift(on_gift)
    connector.on_connect(on_connect)
    connector.on_disconnect(on_disconnect)
    connector.on_comment(on_comment)

    try:
        # auto_reconnect=True keeps trying if stream ends
        await connector.connect(auto_reconnect=True, reconnect_delay=10)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping monitor...")
        await connector.disconnect()
        stats = connector.get_stats()
        print(f"\n📊 Session Stats:")
        print(f"   Total gifts: {stats['total_gifts']}")
        print(f"   Total coins: {stats['total_coins']:,}")
        print(f"   Unique gifters: {stats['unique_gifters']}")


def main():
    """Main entry point."""
    print_banner()

    if not TIKTOK_LIVE_AVAILABLE:
        print("❌ TikTokLive library not installed!")
        print("   Run: pip install TikTokLive")
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) >= 3:
        creator = sys.argv[1].lstrip("@")
        opponent = sys.argv[2].lstrip("@")
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
        asyncio.run(run_live_battle(creator, opponent, duration))

    elif len(sys.argv) == 2:
        # Single stream monitor mode
        username = sys.argv[1].lstrip("@")
        asyncio.run(run_single_stream_monitor(username))

    else:
        # Interactive mode
        print("Select mode:")
        print("  1. Battle Mode (2 streams)")
        print("  2. Monitor Mode (1 stream)")
        print()

        choice = input("Choice (1/2): ").strip()

        if choice == "1":
            creator = input("Creator username: ").strip().lstrip("@")
            opponent = input("Opponent username: ").strip().lstrip("@")
            duration = int(input("Duration in seconds (default 300): ") or "300")

            if not creator or not opponent:
                print("❌ Both usernames required!")
                sys.exit(1)

            asyncio.run(run_live_battle(creator, opponent, duration))

        elif choice == "2":
            username = input("Username to monitor: ").strip().lstrip("@")

            if not username:
                print("❌ Username required!")
                sys.exit(1)

            asyncio.run(run_single_stream_monitor(username))

        else:
            print("Invalid choice")
            sys.exit(1)


if __name__ == "__main__":
    main()
