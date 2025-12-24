#!/usr/bin/env python3
"""
Live Tournament Runner - Best-of-X TikTok Battle Tournaments

Run real-time tournaments between two TikTok Live streams.

Usage:
    python run_live_tournament.py --creator @user1 --opponent @user2 --format bo3
    python run_live_tournament.py --creator @user1 --opponent @user2 --format bo5 --round-duration 180
    python run_live_tournament.py --creator @user1 --opponent @user2 --format bo7 --break-time 30
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.live_tournament_engine import (
    LiveTournamentEngine,
    TournamentFormat,
    TournamentState,
    RoundResult,
    TIKTOK_LIVE_AVAILABLE
)

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    """Print a header line."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_round_header(round_num: int, series_score: str):
    """Print round header."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'─'*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}  🎮 ROUND {round_num}  │  Series: {series_score}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*60}{Colors.END}\n")


def print_gift(team: str, username: str, gift_name: str, count: int, coins: int, points: int):
    """Print gift event."""
    if team == "creator":
        color = Colors.BLUE
        emoji = "🔵"
    else:
        color = Colors.RED
        emoji = "🔴"

    print(f"  {emoji} {color}{username}{Colors.END}: {gift_name} x{count} "
          f"({Colors.YELLOW}{coins:,} coins{Colors.END}, {Colors.GREEN}+{points:,} pts{Colors.END})")


def print_score_bar(creator_score: int, opponent_score: int, time_remaining: int):
    """Print visual score bar."""
    total = creator_score + opponent_score or 1
    creator_pct = int((creator_score / total) * 40)
    opponent_pct = 40 - creator_pct

    bar = f"{Colors.BLUE}{'█' * creator_pct}{Colors.END}{Colors.RED}{'█' * opponent_pct}{Colors.END}"

    print(f"\r  [{bar}] "
          f"{Colors.BLUE}{creator_score:,}{Colors.END} vs "
          f"{Colors.RED}{opponent_score:,}{Colors.END} "
          f"│ ⏱️  {time_remaining}s  ", end='', flush=True)


def print_round_result(result: RoundResult, creator_name: str, opponent_name: str):
    """Print round result."""
    print(f"\n\n{Colors.BOLD}{'─'*60}{Colors.END}")
    print(f"{Colors.BOLD}  🏁 ROUND {result.round_number} COMPLETE{Colors.END}")
    print(f"{'─'*60}")

    winner_color = Colors.BLUE if result.winner == "creator" else Colors.RED
    winner_name = creator_name if result.winner == "creator" else opponent_name

    print(f"\n  {Colors.BLUE}@{creator_name}{Colors.END}: {result.creator_score:,}")
    print(f"  {Colors.RED}@{opponent_name}{Colors.END}: {result.opponent_score:,}")
    print(f"\n  🏆 Winner: {winner_color}{result.winner.upper()} (@{winner_name}){Colors.END}")

    if result.top_gifter:
        print(f"  ⭐ MVP Gifter: {result.top_gifter} ({result.top_gift_amount:,} coins)")

    print(f"  📊 Total Gifts: {result.gift_count}")
    print(f"{'─'*60}\n")


def print_tournament_result(winner: str, stats: dict, creator_name: str, opponent_name: str):
    """Print final tournament result."""
    winner_name = creator_name if winner == "creator" else opponent_name
    winner_color = Colors.BLUE if winner == "creator" else Colors.RED

    print_header("🏆 TOURNAMENT COMPLETE 🏆")

    print(f"  {Colors.BOLD}Champion:{Colors.END} {winner_color}@{winner_name}{Colors.END}")
    print(f"  {Colors.BOLD}Series:{Colors.END} {stats['series_score']}")
    print()
    print(f"  {Colors.BOLD}Total Points:{Colors.END}")
    print(f"    {Colors.BLUE}@{creator_name}{Colors.END}: {stats['total_creator_score']:,}")
    print(f"    {Colors.RED}@{opponent_name}{Colors.END}: {stats['total_opponent_score']:,}")
    print()
    print(f"  {Colors.BOLD}Statistics:{Colors.END}")
    print(f"    Rounds Played: {stats['rounds_played']}")
    print(f"    Total Gifts: {stats['total_gifts']}")
    print(f"    Total Coins: {stats['total_coins']:,}")

    print("\n  📊 Round-by-Round:")
    for r in stats['rounds']:
        winner_indicator = "🔵" if r['winner'] == "creator" else "🔴"
        print(f"    Round {r['round_number']}: {r['creator_score']:,} - {r['opponent_score']:,} {winner_indicator}")

    print(f"\n{'='*60}\n")


async def run_tournament(
    creator: str,
    opponent: str,
    format: TournamentFormat,
    round_duration: int,
    break_duration: int,
    output_file: str = None
):
    """Run a live tournament."""

    print_header(f"LIVE TOURNAMENT - Best of {format.value}")

    print(f"  {Colors.BLUE}🔵 Creator:{Colors.END}  @{creator}")
    print(f"  {Colors.RED}🔴 Opponent:{Colors.END} @{opponent}")
    print(f"  ⏱️  Round Duration: {round_duration}s")
    print(f"  ⏸️  Break Time: {break_duration}s")
    print(f"  🎯 Wins Needed: {(format.value // 2) + 1}")
    print()

    # Create tournament
    tournament = LiveTournamentEngine(
        creator_username=creator,
        opponent_username=opponent,
        format=format,
        round_duration=round_duration,
        break_duration=break_duration
    )

    # Register callbacks
    def on_round_start(round_num, stats):
        print_round_header(round_num, stats['series_score'])

    def on_gift(event, round_num, creator_score, opponent_score):
        print_gift(
            event.team,
            event.username,
            event.gift_name,
            event.repeat_count,
            event.total_coins,
            event.total_points
        )

    last_update = [0]

    def on_score_update(round_num, creator_score, opponent_score, time_remaining):
        # Only update every 5 seconds to reduce noise
        if time_remaining % 5 == 0 or time_remaining <= 10:
            print_score_bar(creator_score, opponent_score, time_remaining)

    def on_round_end(result, stats):
        print_round_result(result, creator, opponent)

    def on_break_start(next_round, break_seconds):
        print(f"\n  ⏸️  {Colors.YELLOW}Break time - {break_seconds}s until Round {next_round}{Colors.END}\n")

    def on_tournament_end(winner, stats):
        print_tournament_result(winner, stats, creator, opponent)

        # Save results if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"  📁 Results saved to: {output_file}\n")

    tournament.on_round_start(on_round_start)
    tournament.on_gift(on_gift)
    tournament.on_score_update(on_score_update)
    tournament.on_round_end(on_round_end)
    tournament.on_break_start(on_break_start)
    tournament.on_tournament_end(on_tournament_end)

    print(f"  {Colors.YELLOW}Connecting to streams...{Colors.END}\n")

    try:
        result = await tournament.start()
        return result
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.RED}Tournament cancelled by user{Colors.END}\n")
        await tournament.stop()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Run a Best-of-X TikTok Live Tournament",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Best of 3 tournament with 2-minute rounds
  python run_live_tournament.py -c @user1 -o @user2 -f bo3 -r 120

  # Best of 5 tournament with 3-minute rounds and 30s breaks
  python run_live_tournament.py -c @user1 -o @user2 -f bo5 -r 180 -b 30

  # Best of 7 tournament, save results to file
  python run_live_tournament.py -c @user1 -o @user2 -f bo7 --output results.json
        """
    )

    parser.add_argument(
        '-c', '--creator',
        required=True,
        help='Creator TikTok username'
    )
    parser.add_argument(
        '-o', '--opponent',
        required=True,
        help='Opponent TikTok username'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['bo3', 'bo5', 'bo7'],
        default='bo3',
        help='Tournament format (default: bo3)'
    )
    parser.add_argument(
        '-r', '--round-duration',
        type=int,
        default=120,
        help='Round duration in seconds (default: 120)'
    )
    parser.add_argument(
        '-b', '--break-time',
        type=int,
        default=20,
        help='Break time between rounds in seconds (default: 20)'
    )
    parser.add_argument(
        '--output',
        help='Output file for tournament results (JSON)'
    )

    args = parser.parse_args()

    if not TIKTOK_LIVE_AVAILABLE:
        print(f"{Colors.RED}Error: TikTokLive library not installed{Colors.END}")
        print("Run: pip install TikTokLive")
        sys.exit(1)

    # Parse format
    format_map = {
        'bo3': TournamentFormat.BEST_OF_3,
        'bo5': TournamentFormat.BEST_OF_5,
        'bo7': TournamentFormat.BEST_OF_7,
    }
    tournament_format = format_map[args.format]

    # Clean usernames
    creator = args.creator.lstrip('@')
    opponent = args.opponent.lstrip('@')

    # Run tournament
    try:
        result = asyncio.run(run_tournament(
            creator=creator,
            opponent=opponent,
            format=tournament_format,
            round_duration=args.round_duration,
            break_duration=args.break_time,
            output_file=args.output
        ))

        if result:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
