#!/usr/bin/env python3
"""
AI vs Live Streamer Battle

Run a battle where our AI team competes against a real TikTok Live streamer.
The AI agents simulate gifting while we monitor the real stream's gifts.

Usage:
    # Single challenge match (2 min)
    python run_ai_vs_live.py --target @username --duration 120

    # Best-of-3 tournament
    python run_ai_vs_live.py --target @username --format bo3

    # Best-of-5 with custom round duration
    python run_ai_vs_live.py --target @username --format bo5 --duration 180

    # Custom AI team
    python run_ai_vs_live.py --target @username --team "NovaWhale,PixelPixie"
"""

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai_vs_live_engine import (
    AIvsLiveEngine,
    AIBattleMode,
    TournamentFormat,
    TIKTOK_LIVE_AVAILABLE
)
from core.tiktok_battle_config import (
    TIKTOK_BATTLE_CONFIG,
    TOURNAMENT_CONFIG,
    BATTLE_DURATION_SECONDS,
    VICTORY_LAP_SECONDS,
)


# ANSI colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_round_start(round_num: int, series: str):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'─'*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}  🎮 ROUND {round_num}  │  Series: {series}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*60}{Colors.END}\n")


def print_ai_gift(gift_data: dict, ai_score: int, live_score: int):
    agent = gift_data['agent']
    emoji = gift_data['emoji']
    gift = gift_data['gift_name']
    points = gift_data['points']
    mult = gift_data.get('multiplier', 1.0)

    mult_str = f" (x{mult})" if mult > 1 else ""
    print(f"  🔵 {emoji} {Colors.BLUE}{agent}{Colors.END}: {gift}{mult_str} "
          f"{Colors.GREEN}+{points:,} pts{Colors.END}")


def print_live_gift(event, live_score: int, ai_score: int):
    print(f"  🔴 {Colors.RED}{event.username}{Colors.END}: {event.gift_name} x{event.repeat_count} "
          f"({Colors.YELLOW}{event.total_coins:,} coins{Colors.END}, "
          f"{Colors.GREEN}+{event.total_points:,} pts{Colors.END})")


def print_score_update(ai_score: int, live_score: int, time_left: int, round_num: int):
    total = ai_score + live_score or 1
    ai_pct = int((ai_score / total) * 40)
    live_pct = 40 - ai_pct

    bar = f"{Colors.BLUE}{'█' * ai_pct}{Colors.END}{Colors.RED}{'█' * live_pct}{Colors.END}"

    print(f"\r  [{bar}] "
          f"{Colors.BLUE}AI {ai_score:,}{Colors.END} vs "
          f"{Colors.RED}{live_score:,} Live{Colors.END} "
          f"│ ⏱️  {time_left}s  ", end='', flush=True)


def print_round_result(result, stats: dict):
    print(f"\n\n{Colors.BOLD}{'─'*60}{Colors.END}")
    print(f"{Colors.BOLD}  🏁 ROUND {result.round_number} COMPLETE{Colors.END}")
    print(f"{'─'*60}")

    winner_color = Colors.BLUE if result.winner == "ai" else Colors.RED
    winner_text = "AI TEAM" if result.winner == "ai" else "LIVE STREAM"

    print(f"\n  {Colors.BLUE}AI Team{Colors.END}: {result.ai_score:,} ({result.ai_gifts} gifts)")
    print(f"  {Colors.RED}Live{Colors.END}: {result.live_score:,} ({result.live_gifts} gifts)")
    print(f"\n  🏆 Winner: {winner_color}{winner_text}{Colors.END}")
    print(f"  ⭐ Top AI Agent: {result.top_ai_agent}")
    print(f"  ⭐ Top Live Gifter: {result.top_live_gifter}")
    print(f"  📊 Series: AI {stats['ai_wins']} - {stats['live_wins']} Live")
    print(f"{'─'*60}\n")


def print_final_result(winner: str, stats: dict):
    print_header("🏆 BATTLE COMPLETE 🏆")

    winner_color = Colors.BLUE if winner == "ai" else Colors.RED
    winner_text = "AI TEAM" if winner == "ai" else f"@{stats['target_streamer']}"

    print(f"  {Colors.BOLD}Champion:{Colors.END} {winner_color}{winner_text}{Colors.END}")
    print(f"  {Colors.BOLD}Series:{Colors.END} {stats['series_score']}")
    print()

    print(f"  {Colors.BOLD}Total Points:{Colors.END}")
    print(f"    {Colors.BLUE}AI Team{Colors.END}: {stats['total_ai_score']:,}")
    print(f"    {Colors.RED}Live Stream{Colors.END}: {stats['total_live_score']:,}")
    print()

    print(f"  {Colors.BOLD}AI Team Performance:{Colors.END}")
    for agent in stats['ai_team']:
        print(f"    {agent['emoji']} {agent['name']}: {agent['gifts']} gifts, "
              f"{agent['points']:,} pts ({agent['coins_spent']:,} coins)")
    print()

    print(f"  {Colors.BOLD}Round-by-Round:{Colors.END}")
    for r in stats['rounds']:
        winner_icon = "🔵" if r['winner'] == "ai" else "🔴"
        print(f"    Round {r['round']}: AI {r['ai_score']:,} - {r['live_score']:,} Live {winner_icon}")

    print(f"\n{'='*60}\n")


async def run_battle(args):
    """Run the AI vs Live battle."""
    target = args.target.lstrip('@')

    # Determine mode and format
    if args.simulate:
        mode = AIBattleMode.SIMULATION
        tournament_format = TournamentFormat.BEST_OF_1
        wins_needed = 1
        if args.format in ['bo3', 'bo5', 'bo7']:
            format_map = {
                'bo3': TournamentFormat.BEST_OF_3,
                'bo5': TournamentFormat.BEST_OF_5,
                'bo7': TournamentFormat.BEST_OF_7,
            }
            tournament_format = format_map[args.format]
            wins_needed = (tournament_format.value // 2) + 1
    elif args.format in ['bo3', 'bo5', 'bo7']:
        mode = AIBattleMode.TOURNAMENT
        format_map = {
            'bo3': TournamentFormat.BEST_OF_3,
            'bo5': TournamentFormat.BEST_OF_5,
            'bo7': TournamentFormat.BEST_OF_7,
        }
        tournament_format = format_map[args.format]
        wins_needed = (tournament_format.value // 2) + 1
    else:
        mode = AIBattleMode.CHALLENGE
        tournament_format = TournamentFormat.BEST_OF_1
        wins_needed = 1

    # Parse team
    ai_team = None
    if args.team:
        ai_team = [t.strip() for t in args.team.split(',')]

    print_header(f"AI vs LIVE BATTLE")

    print(f"  {Colors.RED}🔴 Target:{Colors.END}     @{target}")
    print(f"  {Colors.BLUE}🔵 AI Team:{Colors.END}    {', '.join(ai_team) if ai_team else 'Default Team'}")
    print(f"  🎮 Mode:        {mode.value.title()}")
    if mode == AIBattleMode.TOURNAMENT or (mode == AIBattleMode.SIMULATION and tournament_format.value > 1):
        print(f"  📊 Format:      Best of {tournament_format.value}")
        print(f"  🎯 Wins Needed: {wins_needed}")
    print(f"  ⏱️  Round Time:  {args.duration}s")
    print(f"  💰 AI Budget:   {args.budget:,} coins/round")
    print()

    # Create engine
    engine = AIvsLiveEngine(
        target_streamer=target,
        ai_team=ai_team,
        mode=mode,
        round_duration=args.duration,
        tournament_format=tournament_format,
        ai_budget_per_round=args.budget
    )

    # Register callbacks
    current_round = [1]

    def on_ai_gift(gift_data, ai_score, live_score):
        print_ai_gift(gift_data, ai_score, live_score)

    def on_live_gift(event, live_score, ai_score):
        print_live_gift(event, live_score, ai_score)

    def on_score_update(ai_score, live_score, time_left, round_num):
        if time_left % 5 == 0 or time_left <= 10:
            print_score_update(ai_score, live_score, time_left, round_num)

    def on_round_end(result, stats):
        print_round_result(result, stats)
        current_round[0] += 1

    def on_battle_end(winner, stats):
        print_final_result(winner, stats)

    def on_connection(connected, username):
        if connected:
            print(f"  {Colors.GREEN}✅ Connected to @{username}{Colors.END}\n")
            print_round_start(1, f"AI 0 - 0 Live")
        else:
            print(f"  {Colors.RED}❌ Disconnected from @{username}{Colors.END}")

    engine.on_ai_gift(on_ai_gift)
    engine.on_live_gift(on_live_gift)
    engine.on_score_update(on_score_update)
    engine.on_round_end(on_round_end)
    engine.on_battle_end(on_battle_end)
    engine.on_connection(on_connection)

    print(f"  {Colors.YELLOW}Connecting to @{target}...{Colors.END}\n")

    try:
        result = await engine.start_battle()
        return result
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.RED}Battle cancelled by user{Colors.END}\n")
        await engine.stop()
        return None
    except Exception as e:
        print(f"\n  {Colors.RED}Error: {e}{Colors.END}\n")
        await engine.stop()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="AI Team vs Live TikTok Streamer Battle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick challenge match
  python run_ai_vs_live.py --target @streamer --duration 60

  # Best of 3 tournament
  python run_ai_vs_live.py --target @streamer --format bo3

  # Best of 5 with custom team
  python run_ai_vs_live.py --target @streamer --format bo5 --team "NovaWhale,GlitchMancer"

  # Long rounds with big budget
  python run_ai_vs_live.py --target @streamer --format bo3 --duration 300 --budget 100000
        """
    )

    parser.add_argument(
        '-t', '--target',
        required=True,
        help='Target TikTok Live streamer username'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['single', 'bo3', 'bo5', 'bo7'],
        default='single',
        help='Battle format (default: single)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=BATTLE_DURATION_SECONDS,  # Official TikTok: 300s (5 minutes)
        help=f'Round duration in seconds (default: {BATTLE_DURATION_SECONDS} = 5 min, official TikTok duration)'
    )
    parser.add_argument(
        '--team',
        type=str,
        help='Comma-separated list of AI agents (default: full team)'
    )
    parser.add_argument(
        '--budget',
        type=int,
        default=50000,
        help='AI team budget per round in coins (default: 50000)'
    )
    parser.add_argument(
        '--simulate', '-s',
        action='store_true',
        help='Simulate live stream (no TikTok connection required)'
    )

    args = parser.parse_args()

    if not TIKTOK_LIVE_AVAILABLE:
        print(f"{Colors.RED}Error: TikTokLive library not installed{Colors.END}")
        print("Run: pip install TikTokLive")
        sys.exit(1)

    try:
        result = asyncio.run(run_battle(args))
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
