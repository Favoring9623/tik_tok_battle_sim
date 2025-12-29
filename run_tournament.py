#!/usr/bin/env python3
"""
Best of 3 Tournament Runner
============================

Runs a complete Best of 3 tournament against a TikTok streamer.
Manages 500k coins across all battles with intelligent allocation.

Features:
- Honor lap detection (2min58s between battles)
- Boost score tracking and learning
- Adaptive budget allocation
- Complete tournament statistics

Usage:
    python run_tournament.py -t @streamer -b 500000
    python run_tournament.py -t @streamer -b 500000 --strategy aggressive
"""

import asyncio
import argparse
import sys
import os
import time
from typing import Dict, Optional, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveGiftEvent,
    TIKTOK_LIVE_AVAILABLE
)
from core.advanced_phase_system import AdvancedPhaseManager
from core.battle_engine import BattleEngine
from core.budget_manager import BudgetManager, BattlePhase, create_budget_manager
from core.tournament_manager import (
    TournamentManager,
    TournamentState,
    BattleResult,
    create_tournament_manager
)
from core.battle_history import BattleHistoryDB
from agents.budget_aware_agents import (
    create_budget_aware_team,
    reset_budget_team,
)


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'
    MAGENTA = '\033[35m'


class TournamentBattleEngine:
    """
    Runs a Best of 3 tournament with budget management.

    Features:
    - Manages 500k coins across 3 potential battles
    - Detects honor lap (2min58s) between battles
    - Tracks boost performance for learning
    - Adapts strategy based on tournament state
    """

    # Honor lap detection
    HONOR_LAP_DURATION = 178  # 2min58s
    BATTLE_DURATION = 300     # 5 minutes

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 500000,
        strategy: str = "adaptive",
        db_path: str = "data/tournaments.db"
    ):
        self.target = target_streamer.lstrip("@")
        self.total_budget = total_budget
        self.strategy = strategy
        self.db_path = db_path

        # Tournament manager
        self.tournament = create_tournament_manager(total_budget, strategy)

        # Database
        self.db = BattleHistoryDB(db_path)

        # Connection
        self.connector = None

        # Battle state
        self.live_score = 0
        self.ai_score = 0
        self.live_gifts: List[Dict] = []
        self.battle_start_time = None
        self.is_running = False

        # Boost tracking
        self.current_boost_number = 0
        self.in_boost = False
        self.boost_multiplier = 1.0
        self.boost_start_time = None

        # Honor lap tracking
        self.gift_timestamps: List[float] = []
        self.last_gift_time = 0

        # Per-battle components (recreated each battle)
        self.phase_manager = None
        self.team = None
        self.budget = None
        self._engine = None

    async def connect(self) -> bool:
        """Connect to the TikTok stream."""
        print(f"\n{Colors.YELLOW}🔌 Connecting to @{self.target}...{Colors.END}")

        try:
            self.connector = TikTokLiveConnector(self.target)

            def on_gift(event: LiveGiftEvent):
                self.live_score += event.total_points
                self.live_gifts.append({
                    'time': time.time(),
                    'user': event.username,
                    'gift': event.gift_name,
                    'coins': event.total_coins,
                    'points': event.total_points
                })

                # Track gift timestamps for honor lap detection
                self.gift_timestamps.append(time.time())
                self.last_gift_time = time.time()

                # Update engine
                if self._engine:
                    self._engine.score_tracker.opponent_score = self.live_score
                if self.phase_manager:
                    self.phase_manager.opponent_score = self.live_score

                # Show gift with tournament context
                deficit = self.live_score - self.ai_score
                deficit_str = f" (Deficit: {deficit:,})" if deficit > 0 else ""

                print(f"\n  🔴 {Colors.RED}{event.username}{Colors.END}: {event.gift_name} "
                      f"x{event.repeat_count} ({Colors.YELLOW}{event.total_coins:,} coins{Colors.END}, "
                      f"{Colors.GREEN}+{event.total_points:,} pts{Colors.END}){Colors.RED}{deficit_str}{Colors.END}")
                self._print_battle_status()

            self.connector.on_gift(on_gift)

            try:
                await asyncio.wait_for(self.connector.connect(), timeout=15)
                print(f"{Colors.GREEN}✅ Connected to @{self.target}{Colors.END}\n")
                return True
            except asyncio.TimeoutError:
                print(f"{Colors.YELLOW}⚠️ Connection timeout, continuing...{Colors.END}\n")
                return True

        except Exception as e:
            print(f"{Colors.RED}❌ Connection failed: {e}{Colors.END}")
            return True

    def _setup_battle(self, battle_budget: int):
        """Set up components for a new battle."""
        # Reset scores
        self.live_score = 0
        self.ai_score = 0
        self.live_gifts = []
        self.gift_timestamps = []

        # Create phase manager
        self.phase_manager = AdvancedPhaseManager(battle_duration=self.BATTLE_DURATION)

        # Create budget-aware team with battle-specific budget
        self.team, self.budget = create_budget_aware_team(
            total_budget=battle_budget,
            phase_manager=self.phase_manager,
            strategy="balanced",  # Use balanced within each battle
            db=self.db
        )

        # Reset boost tracking
        self.current_boost_number = 0
        self.in_boost = False
        self.boost_multiplier = 1.0

    def _print_battle_status(self):
        """Print current battle status."""
        if not self.battle_start_time:
            return

        total = self.ai_score + self.live_score or 1
        ai_pct = int((self.ai_score / total) * 30)
        live_pct = 30 - ai_pct

        bar = f"{Colors.BLUE}{'█' * ai_pct}{Colors.END}{Colors.RED}{'█' * live_pct}{Colors.END}"
        elapsed = int(time.time() - self.battle_start_time)
        remaining = max(0, self.BATTLE_DURATION - elapsed)

        # Budget info
        budget_remaining = self.budget.remaining_coins if self.budget else 0
        battle_budget = self.tournament.get_battle_budget()
        budget_pct = (budget_remaining / battle_budget * 100) if battle_budget > 0 else 0
        budget_color = Colors.GREEN if budget_pct > 30 else (Colors.YELLOW if budget_pct > 10 else Colors.RED)

        # Tournament context
        tournament_str = f"{Colors.MAGENTA}[{self.tournament.stats.wins}-{self.tournament.stats.losses}]{Colors.END}"

        print(f"\r  {tournament_str} [{bar}] {Colors.BLUE}AI {self.ai_score:,}{Colors.END} vs "
              f"{Colors.RED}{self.live_score:,} Live{Colors.END} │ "
              f"⏱️ {remaining}s │ "
              f"{budget_color}💰 {budget_remaining:,}{Colors.END}  ",
              end='', flush=True)

    async def run_single_battle(self) -> BattleResult:
        """Run a single battle in the tournament."""
        # Get budget for this battle
        battle_budget = self.tournament.start_battle()

        # Setup battle components
        self._setup_battle(battle_budget)

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}  BATTLE {self.tournament.current_battle}/3{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'─'*70}{Colors.END}")

        print(f"\n  {Colors.BLUE}🔵 AI Team:{Colors.END}")
        for agent in self.team:
            print(f"     {agent.emoji} {agent.name}")
        print(f"\n  {Colors.RED}🔴 Opponent:{Colors.END} @{self.target}")
        print(f"  💰 Battle Budget: {Colors.GREEN}{battle_budget:,} coins{Colors.END}")
        print(f"  📊 Tournament: {self.tournament.stats.wins}-{self.tournament.stats.losses}")
        print()

        # Create engine
        engine = BattleEngine(
            battle_duration=self.BATTLE_DURATION,
            tick_speed=1.0,
            enable_multipliers=False,
            enable_analytics=True
        )
        self._engine = engine

        # Add agents
        for agent in self.team:
            engine.add_agent(agent)

        # Subscribe to events
        from core.event_bus import EventType

        def on_ai_gift(event):
            points = event.data.get("points", 0)
            coins = event.data.get("coins", points)  # Assume 1:1 if not specified
            self.ai_score += points

            if self.phase_manager:
                self.phase_manager.creator_score = self.ai_score

            # Record in tournament manager
            phase_name = self._get_current_phase_name()
            self.tournament.record_spend(
                coins=coins,
                points=points,
                phase=phase_name,
                in_boost=self.in_boost,
                multiplier=self.boost_multiplier
            )

            agent_name = event.source or "Agent"
            gift_name = event.data.get("gift", "Gift")

            deficit = self.live_score - self.ai_score
            if deficit > 0:
                status = f"{Colors.RED}(still -{deficit:,}){Colors.END}"
            else:
                status = f"{Colors.GREEN}(+{-deficit:,} ahead){Colors.END}"

            boost_str = f" x{self.boost_multiplier:.0f}" if self.in_boost else ""

            print(f"  🔵 {Colors.BLUE}{agent_name}{Colors.END}: {gift_name}{boost_str} "
                  f"{Colors.GREEN}+{points:,} pts{Colors.END} {status}")
            self._print_battle_status()

        engine.event_bus.subscribe(EventType.GIFT_SENT, on_ai_gift)

        # Track gifts for phase manager
        def record_gift(event):
            gift_name = event.data.get("gift", "Gift")
            points = event.data.get("points", 0)
            current_time = int(event.timestamp)
            if self.phase_manager:
                self.phase_manager.record_gift(gift_name, points, "creator", current_time)

        engine.event_bus.subscribe(EventType.GIFT_SENT, record_gift)

        # Battle loop
        self.is_running = True
        self.battle_start_time = time.time()

        try:
            while self.is_running:
                elapsed = time.time() - self.battle_start_time
                current_time = int(elapsed)
                time_remaining = self.BATTLE_DURATION - current_time

                if elapsed >= self.BATTLE_DURATION:
                    break

                # Update phase manager
                if self.phase_manager:
                    self.phase_manager.update(current_time)

                    # Track boost windows for tournament learning
                    self._track_boosts(current_time)

                # Update budget manager
                if self.budget:
                    self.budget.update_battle_state(
                        time_remaining,
                        self.live_score - self.ai_score
                    )

                # Let agents act
                engine.time_manager.current_time = current_time
                for agent in self.team:
                    try:
                        if self.budget and self.budget.remaining_coins >= 1:
                            agent.act(engine)
                    except Exception as e:
                        print(f"⚠️ Agent {agent.name} error: {e}")

                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.RED}Battle interrupted{Colors.END}")
        finally:
            self.is_running = False

        # End battle
        result = self.tournament.end_battle(self.ai_score, self.live_score)

        return result

    def _get_current_phase_name(self) -> str:
        """Get current phase name for tracking."""
        if self.in_boost:
            return f"boost_{self.current_boost_number}"
        if self.phase_manager:
            elapsed = time.time() - self.battle_start_time if self.battle_start_time else 0
            if elapsed < 30:
                return "opening"
            elif elapsed > self.BATTLE_DURATION - 30:
                return "snipe"
        return "mid_battle"

    def _track_boosts(self, current_time: int):
        """Track boost windows for tournament learning."""
        if not self.phase_manager:
            return

        # Check for Boost #1
        if self.phase_manager.boost1_active and not self.in_boost:
            self.in_boost = True
            self.current_boost_number = 1
            self.boost_multiplier = self.phase_manager.get_current_multiplier()
            self.boost_start_time = time.time()
            self.tournament.start_boost(1, self.boost_multiplier)

        # Check for Boost #2
        elif self.phase_manager.boost2_active and (not self.in_boost or self.current_boost_number == 1):
            if self.in_boost and self.current_boost_number == 1:
                # End boost 1 first
                self.tournament.end_boost()

            self.in_boost = True
            self.current_boost_number = 2
            self.boost_multiplier = self.phase_manager.get_current_multiplier()
            self.boost_start_time = time.time()
            self.tournament.start_boost(
                2,
                self.boost_multiplier
            )

        # Check for boost end
        elif self.in_boost and not (self.phase_manager.boost1_active or self.phase_manager.boost2_active):
            threshold_reached = False
            if self.current_boost_number == 2:
                threshold_reached = self.phase_manager.boost2_creator_qualified

            self.tournament.end_boost(threshold_reached)
            self.in_boost = False
            self.boost_multiplier = 1.0

    async def wait_honor_lap(self):
        """Wait for the honor lap period between battles."""
        print(f"\n{Colors.MAGENTA}{'='*70}{Colors.END}")
        print(f"{Colors.MAGENTA}  ⏱️  TOUR D'HONNEUR - {self.tournament.HONOR_LAP_DURATION}s{Colors.END}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.END}\n")

        start_time = time.time()

        # Wait with progress updates
        while True:
            elapsed = time.time() - start_time
            remaining = self.tournament.HONOR_LAP_DURATION - elapsed

            if remaining <= 0:
                break

            # Calculate gift rate for detection
            recent_gifts = [t for t in self.gift_timestamps if time.time() - t < 60]
            gift_rate = len(recent_gifts)  # Gifts per minute

            # Progress bar
            progress = int((elapsed / self.tournament.HONOR_LAP_DURATION) * 40)
            bar = f"{Colors.MAGENTA}{'█' * progress}{'░' * (40 - progress)}{Colors.END}"

            print(f"\r  [{bar}] {Colors.CYAN}{int(remaining)}s restants{Colors.END} │ "
                  f"Gifts/min: {gift_rate}  ",
                  end='', flush=True)

            # Check for early battle detection
            if self.tournament.detect_new_battle_start(
                boost_announced=False,  # Would need phase manager signal
                gift_spike=(gift_rate > 30 and elapsed > 120)
            ):
                print(f"\n\n{Colors.GREEN}🎮 New battle detected early!{Colors.END}")
                break

            await asyncio.sleep(1)

        print(f"\n\n{Colors.GREEN}✅ Tour d'honneur terminé{Colors.END}\n")

    async def run_tournament(self):
        """Run the complete Best of 3 tournament."""
        # Print tournament header
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'TOURNAMENT BEST OF 3':^70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.END}\n")

        print(f"  🎯 Opponent: {Colors.RED}@{self.target}{Colors.END}")
        print(f"  💰 Total Budget: {Colors.GREEN}{self.total_budget:,} coins{Colors.END}")
        print(f"  📊 Strategy: {self.strategy}")
        print(f"\n  💵 Budget Allocation:")
        for i, budget in enumerate(self.tournament.budget_per_battle):
            print(f"     Battle {i+1}: {budget:,} coins")
        print()

        # Connect to stream
        if not await self.connect():
            return None

        # Start tournament
        self.tournament.start_tournament()

        # Run battles
        while not self.tournament.is_tournament_complete():
            # Run battle
            result = await self.run_single_battle()

            # Check if tournament is complete
            if self.tournament.is_tournament_complete():
                break

            # Honor lap between battles
            await self.wait_honor_lap()

            # Reset for next battle but keep connection
            self.live_score = 0
            self.ai_score = 0

        # Disconnect
        if self.connector:
            await self.connector.disconnect()

        # Show final results
        return self._show_tournament_results()

    def _show_tournament_results(self) -> Dict:
        """Show complete tournament results."""
        summary = self.tournament.get_tournament_summary()

        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}  🏆 TOURNAMENT COMPLETE{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

        # Result
        if summary['result'] == "WIN":
            print(f"  {Colors.GREEN}{Colors.BOLD}🏆 TOURNAMENT WON! ({summary['wins']}-{summary['losses']}){Colors.END}")
        else:
            print(f"  {Colors.RED}{Colors.BOLD}💔 TOURNAMENT LOST ({summary['wins']}-{summary['losses']}){Colors.END}")

        # Budget summary
        print(f"\n  💰 {Colors.YELLOW}Budget Summary:{Colors.END}")
        print(f"     Total: {summary['total_budget']:,} coins")
        print(f"     Spent: {summary['coins_spent']:,} coins")
        print(f"     Remaining: {summary['coins_remaining']:,} coins")

        # Battle breakdown
        print(f"\n  📊 {Colors.CYAN}Battle Results:{Colors.END}")
        for battle in summary['battles']:
            result_emoji = "✅" if battle['result'] == "win" else "❌" if battle['result'] == "loss" else "🤝"
            print(f"     Battle {battle['number']}: {result_emoji} "
                  f"AI {battle['ai_score']:,} vs Opponent {battle['opponent_score']:,} "
                  f"(Margin: {battle['margin']:+,})")

        # Boost learning
        boost_data = summary['boost_learning']
        print(f"\n  📈 {Colors.GREEN}Boost Performance:{Colors.END}")
        print(f"     Boost #1: {boost_data['boost1']['count']} activations, "
              f"avg efficiency: {boost_data['boost1']['avg_efficiency']:.2f}")
        print(f"     Boost #2: {boost_data['boost2']['count']} activations, "
              f"threshold success: {boost_data['boost2']['threshold_success_rate']:.0%}")

        # Recommendations
        optimal = self.tournament.get_optimal_boost_allocation()
        print(f"\n  💡 {Colors.MAGENTA}Recommended Allocation (next tournament):{Colors.END}")
        print(f"     Boost #1: {optimal[1]:.0%} of battle budget")
        print(f"     Boost #2: {optimal[2]:.0%} of battle budget")

        print(f"\n{'='*70}\n")

        return summary


async def main():
    parser = argparse.ArgumentParser(description="Best of 3 Tournament")
    parser.add_argument('-t', '--target', required=True, help='TikTok streamer username')
    parser.add_argument('-b', '--budget', type=int, default=500000, help='Total tournament budget')
    parser.add_argument('--strategy', default='adaptive',
                       choices=['balanced', 'aggressive', 'conservative', 'adaptive'],
                       help='Budget allocation strategy')

    args = parser.parse_args()

    engine = TournamentBattleEngine(
        target_streamer=args.target,
        total_budget=args.budget,
        strategy=args.strategy
    )

    result = await engine.run_tournament()
    return result


if __name__ == "__main__":
    if not TIKTOK_LIVE_AVAILABLE:
        print("WARNING: TikTokLive not installed")

    asyncio.run(main())
