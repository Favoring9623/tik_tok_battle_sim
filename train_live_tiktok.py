#!/usr/bin/env python3
"""
TikTok Live Training Script - Real API Integration

This script connects to real TikTok Live streams to train and test
the battle simulation system with actual gift data.

Features:
- Single stream monitoring mode
- Two-stream battle mode
- Gift data collection for ML training
- Real-time statistics dashboard
- Leaderboard updates

Usage:
    python train_live_tiktok.py --mode single --username @username
    python train_live_tiktok.py --mode battle --creator @user1 --opponent @user2
    python train_live_tiktok.py --mode monitor --duration 300
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveBattleConnector,
    LiveGiftEvent,
    ConnectionStatus,
    TIKTOK_LIVE_AVAILABLE
)

# Check TikTokLive availability
if not TIKTOK_LIVE_AVAILABLE:
    print("ERROR: TikTokLive library not installed!")
    print("Run: pip install TikTokLive")
    sys.exit(1)

# Try to import database for leaderboard updates
try:
    from core.database import LeaderboardRepository, init_database
    DATABASE_AVAILABLE = True
    init_database()
except ImportError:
    DATABASE_AVAILABLE = False
    print("Note: Database not available, leaderboard updates disabled")


class LiveTrainingSession:
    """
    Training session that connects to real TikTok Live streams.
    Collects gift data and updates leaderboards.
    """

    def __init__(self, output_dir: str = "data/live_training"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.gift_log: List[Dict] = []
        self.stats = {
            'total_gifts': 0,
            'total_coins': 0,
            'total_points': 0,
            'unique_gifters': set(),
            'gift_types': {},
            'start_time': None,
            'streams_connected': [],
        }

    def log_gift(self, event: LiveGiftEvent, stream_type: str = "single"):
        """Log a gift event for training data."""
        gift_data = {
            'timestamp': event.timestamp.isoformat(),
            'stream_type': stream_type,
            'team': event.team,
            'username': event.username,
            'user_id': event.user_id,
            'gift_name': event.gift_name,
            'gift_id': event.gift_id,
            'coin_value': event.coin_value,
            'repeat_count': event.repeat_count,
            'total_coins': event.total_coins,
            'total_points': event.total_points,
        }
        self.gift_log.append(gift_data)

        # Update stats
        self.stats['total_gifts'] += event.repeat_count
        self.stats['total_coins'] += event.total_coins
        self.stats['total_points'] += event.total_points
        self.stats['unique_gifters'].add(event.username)

        gift_name = event.gift_name
        if gift_name not in self.stats['gift_types']:
            self.stats['gift_types'][gift_name] = {'count': 0, 'coins': 0}
        self.stats['gift_types'][gift_name]['count'] += event.repeat_count
        self.stats['gift_types'][gift_name]['coins'] += event.total_coins

        # Update leaderboard if database available
        if DATABASE_AVAILABLE:
            try:
                LeaderboardRepository.update_gifter_stats(
                    username=event.username,
                    coins_spent=event.total_coins,
                    gifts_sent=event.repeat_count
                )
            except Exception as e:
                print(f"Leaderboard update error: {e}")

    def save_session(self):
        """Save session data to JSON file."""
        output_file = self.output_dir / f"session_{self.session_id}.json"

        # Convert datetime objects for JSON serialization
        start_time = self.stats.get('start_time')
        duration = (datetime.now() - start_time).total_seconds() if start_time else 0

        session_data = {
            'session_id': self.session_id,
            'stats': {
                'total_gifts': self.stats['total_gifts'],
                'total_coins': self.stats['total_coins'],
                'total_points': self.stats['total_points'],
                'unique_gifters': list(self.stats['unique_gifters']),
                'gift_types': self.stats['gift_types'],
                'streams_connected': self.stats['streams_connected'],
                'start_time': start_time.isoformat() if start_time else None,
                'duration_seconds': duration
            },
            'gifts': self.gift_log
        }

        with open(output_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\nSession saved to: {output_file}")
        return output_file

    def print_stats(self):
        """Print current session statistics."""
        print("\n" + "=" * 60)
        print("SESSION STATISTICS")
        print("=" * 60)
        print(f"Total Gifts:     {self.stats['total_gifts']:,}")
        print(f"Total Coins:     {self.stats['total_coins']:,}")
        print(f"Total Points:    {self.stats['total_points']:,}")
        print(f"Unique Gifters:  {len(self.stats['unique_gifters'])}")
        print(f"Streams:         {', '.join(self.stats['streams_connected'])}")

        if self.stats['gift_types']:
            print("\nTop Gift Types:")
            sorted_gifts = sorted(
                self.stats['gift_types'].items(),
                key=lambda x: x[1]['coins'],
                reverse=True
            )[:5]
            for gift_name, data in sorted_gifts:
                print(f"  {gift_name}: {data['count']}x ({data['coins']:,} coins)")

        print("=" * 60)


async def single_stream_mode(username: str, duration: int, session: LiveTrainingSession):
    """
    Monitor a single TikTok Live stream.

    Args:
        username: TikTok username to monitor
        duration: Duration in seconds (0 = until stream ends)
        session: Training session instance
    """
    print("\n" + "=" * 60)
    print(f"SINGLE STREAM MODE")
    print(f"Monitoring: @{username}")
    print(f"Duration: {'Until stream ends' if duration == 0 else f'{duration} seconds'}")
    print("=" * 60 + "\n")

    connector = TikTokLiveConnector(username)
    session.stats['streams_connected'].append(username)
    session.stats['start_time'] = datetime.now()

    def on_gift(event: LiveGiftEvent):
        session.log_gift(event, "single")
        print(f"🎁 {event.username}: {event.gift_name} x{event.repeat_count} "
              f"({event.total_coins:,} coins, {event.total_points:,} pts)")

    def on_connect(unique_id: str):
        print(f"\n✅ Connected to @{unique_id}")
        print("Waiting for gifts... (Press Ctrl+C to stop)\n")

    def on_disconnect(unique_id: str):
        print(f"\n❌ Disconnected from @{unique_id}")

    connector.on_gift(on_gift)
    connector.on_connect(on_connect)
    connector.on_disconnect(on_disconnect)

    try:
        if duration > 0:
            # Run for specified duration
            task = asyncio.create_task(connector.connect(auto_reconnect=True))
            await asyncio.sleep(duration)
            await connector.disconnect()
            task.cancel()
        else:
            # Run until stream ends or Ctrl+C
            await connector.connect(auto_reconnect=False)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await connector.disconnect()
        session.print_stats()


async def battle_mode(creator: str, opponent: str, duration: int, session: LiveTrainingSession):
    """
    Run a live battle between two TikTok streams.

    Args:
        creator: First TikTok username
        opponent: Second TikTok username
        duration: Battle duration in seconds
        session: Training session instance
    """
    print("\n" + "=" * 60)
    print(f"⚔️  LIVE BATTLE MODE")
    print(f"Creator:  @{creator}")
    print(f"Opponent: @{opponent}")
    print(f"Duration: {duration} seconds")
    print("=" * 60 + "\n")

    battle = LiveBattleConnector(creator, opponent, duration)
    session.stats['streams_connected'] = [creator, opponent]
    session.stats['start_time'] = datetime.now()

    creator_connected = False
    opponent_connected = False

    def on_creator_connect(unique_id: str):
        nonlocal creator_connected
        creator_connected = True
        print(f"✅ Creator @{unique_id} connected")
        check_battle_ready()

    def on_opponent_connect(unique_id: str):
        nonlocal opponent_connected
        opponent_connected = True
        print(f"✅ Opponent @{unique_id} connected")
        check_battle_ready()

    def check_battle_ready():
        if creator_connected and opponent_connected:
            print("\n🚀 Both streams connected! Battle is LIVE!\n")

    def on_gift(event: LiveGiftEvent, creator_score: int, opponent_score: int):
        session.log_gift(event, "battle")

        team_emoji = "🔵" if event.team == "creator" else "🔴"
        print(f"{team_emoji} {event.username}: {event.gift_name} x{event.repeat_count}")
        print(f"   Score: Creator {creator_score:,} | Opponent {opponent_score:,}")

        # Show score bar
        total = creator_score + opponent_score or 1
        creator_pct = int((creator_score / total) * 30)
        opponent_pct = 30 - creator_pct
        print(f"   [{'█' * creator_pct}{'░' * opponent_pct}]\n")

    def on_battle_end(winner: str, creator_score: int, opponent_score: int):
        print("\n" + "=" * 60)
        print("🏆 BATTLE ENDED!")
        print("=" * 60)

        if winner == "creator":
            print(f"Winner: 🔵 @{creator}")
        elif winner == "opponent":
            print(f"Winner: 🔴 @{opponent}")
        else:
            print("Result: TIE!")

        print(f"\nFinal Scores:")
        print(f"  🔵 Creator (@{creator}):  {creator_score:,}")
        print(f"  🔴 Opponent (@{opponent}): {opponent_score:,}")
        print(f"  Difference: {abs(creator_score - opponent_score):,}")
        print("=" * 60)

    battle.creator_connector.on_connect(on_creator_connect)
    battle.opponent_connector.on_connect(on_opponent_connect)
    battle.on_gift(on_gift)
    battle.on_battle_end(on_battle_end)

    try:
        print("Connecting to streams...")
        result = await battle.start_battle()

        # Save battle result
        session.gift_log.append({
            'type': 'battle_result',
            'timestamp': datetime.now().isoformat(),
            'winner': result['winner'],
            'creator_score': result['creator_score'],
            'opponent_score': result['opponent_score'],
        })

    except KeyboardInterrupt:
        print("\nBattle interrupted!")
        await battle.end_battle()
    finally:
        session.print_stats()


async def monitor_mode(duration: int, session: LiveTrainingSession):
    """
    Monitor multiple streams for popular live battles.
    Discovers and tracks active streams.
    """
    print("\n" + "=" * 60)
    print("📺 MONITOR MODE")
    print(f"Duration: {duration} seconds")
    print("=" * 60)
    print("\nThis mode requires manual input of usernames.")
    print("Enter TikTok usernames to monitor (comma-separated):")

    usernames_input = input("> ").strip()
    if not usernames_input:
        print("No usernames provided. Exiting.")
        return

    usernames = [u.strip().lstrip('@') for u in usernames_input.split(',')]
    print(f"\nMonitoring {len(usernames)} streams: {', '.join(usernames)}")

    session.stats['streams_connected'] = usernames
    session.stats['start_time'] = datetime.now()

    connectors = []

    for username in usernames:
        connector = TikTokLiveConnector(username)

        def make_handlers(uname):
            def on_gift(event: LiveGiftEvent):
                session.log_gift(event, "monitor")
                print(f"[@{uname}] 🎁 {event.username}: {event.gift_name} x{event.repeat_count}")

            def on_connect(unique_id: str):
                print(f"✅ Connected to @{unique_id}")

            return on_gift, on_connect

        gift_handler, connect_handler = make_handlers(username)
        connector.on_gift(gift_handler)
        connector.on_connect(connect_handler)
        connectors.append(connector)

    try:
        # Connect to all streams
        tasks = [asyncio.create_task(c.connect(auto_reconnect=True)) for c in connectors]

        # Wait for duration
        await asyncio.sleep(duration)

        # Disconnect all
        for connector in connectors:
            await connector.disconnect()

        for task in tasks:
            task.cancel()

    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        for connector in connectors:
            try:
                await connector.disconnect()
            except:
                pass
        session.print_stats()


def find_live_streams():
    """
    Helper to find currently live TikTok streams.
    Returns a list of suggested usernames.
    """
    print("\n" + "=" * 60)
    print("🔍 FIND LIVE STREAMS")
    print("=" * 60)
    print("""
To find live TikTok streams:

1. Open TikTok app or tiktok.com
2. Go to the LIVE tab
3. Look for streams with battle indicators
4. Note the usernames of battling creators

Popular categories for battles:
- Gaming streams
- Music/DJ streams
- Talk shows
- Talent competitions

Tips:
- Look for the VS icon indicating active battles
- Check streams with high viewer counts
- Evening hours have more active battles
""")

    username = input("\nEnter a username to test (or press Enter to skip): ").strip()
    return username.lstrip('@') if username else None


async def test_connection(username: str):
    """Test connection to a TikTok Live stream."""
    print(f"\n🔄 Testing connection to @{username}...")

    connector = TikTokLiveConnector(username)
    connected = False

    def on_connect(unique_id: str):
        nonlocal connected
        connected = True
        print(f"✅ SUCCESS! @{unique_id} is LIVE and accessible")

    connector.on_connect(on_connect)

    try:
        task = asyncio.create_task(connector.connect(auto_reconnect=False))
        await asyncio.sleep(10)  # Wait up to 10 seconds

        if not connected:
            print(f"❌ Could not connect to @{username}")
            print("   The user may not be live, or the username may be incorrect.")

        await connector.disconnect()
        task.cancel()

    except Exception as e:
        print(f"❌ Connection error: {e}")

    return connected


def main():
    parser = argparse.ArgumentParser(
        description="TikTok Live Training - Connect to real TikTok streams",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor a single stream
  python train_live_tiktok.py --mode single --username @username

  # Run a battle between two streams (5 minutes)
  python train_live_tiktok.py --mode battle --creator @user1 --opponent @user2 --duration 300

  # Monitor multiple streams
  python train_live_tiktok.py --mode monitor --duration 600

  # Find live streams helper
  python train_live_tiktok.py --mode find

  # Test connection to a stream
  python train_live_tiktok.py --mode test --username @username
        """
    )

    parser.add_argument(
        '--mode', '-m',
        choices=['single', 'battle', 'monitor', 'find', 'test'],
        default='single',
        help='Operation mode'
    )
    parser.add_argument(
        '--username', '-u',
        help='TikTok username for single/test mode'
    )
    parser.add_argument(
        '--creator', '-c',
        help='Creator username for battle mode'
    )
    parser.add_argument(
        '--opponent', '-o',
        help='Opponent username for battle mode'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=300,
        help='Duration in seconds (default: 300)'
    )
    parser.add_argument(
        '--output', '-O',
        default='data/live_training',
        help='Output directory for session data'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🎮 TIKTOK LIVE TRAINING SYSTEM")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"TikTokLive: v{TIKTOK_LIVE_AVAILABLE and 'Available' or 'Not Available'}")
    print(f"Database: {'Connected' if DATABASE_AVAILABLE else 'Not Available'}")
    print("=" * 60)

    session = LiveTrainingSession(output_dir=args.output)

    try:
        if args.mode == 'find':
            username = find_live_streams()
            if username:
                asyncio.run(test_connection(username))

        elif args.mode == 'test':
            if not args.username:
                args.username = input("Enter TikTok username to test: ").strip().lstrip('@')
            if args.username:
                asyncio.run(test_connection(args.username))

        elif args.mode == 'single':
            if not args.username:
                args.username = input("Enter TikTok username: ").strip().lstrip('@')
            if args.username:
                asyncio.run(single_stream_mode(args.username, args.duration, session))

        elif args.mode == 'battle':
            if not args.creator:
                args.creator = input("Enter Creator username: ").strip().lstrip('@')
            if not args.opponent:
                args.opponent = input("Enter Opponent username: ").strip().lstrip('@')

            if args.creator and args.opponent:
                asyncio.run(battle_mode(args.creator, args.opponent, args.duration, session))
            else:
                print("Both creator and opponent usernames are required for battle mode.")

        elif args.mode == 'monitor':
            asyncio.run(monitor_mode(args.duration, session))

    except KeyboardInterrupt:
        print("\n\nSession interrupted by user.")
    finally:
        if session.gift_log:
            session.save_session()
            print(f"\n📊 Collected {len(session.gift_log)} gift events")


if __name__ == "__main__":
    main()
