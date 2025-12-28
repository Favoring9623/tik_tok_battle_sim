#!/usr/bin/env python3
"""
Budget-Constrained Battle Runner
================================

Run battles against live TikTok streams with budget constraints.
Agents learn to optimize their spending across battle phases.

Usage:
    python run_budget_battle.py -t @streamer -b 50000 -s balanced
    python run_budget_battle.py -t @streamer -b 10000 -s conservative
    python run_budget_battle.py -t @streamer -b 100000 -s aggressive
"""

import asyncio
import argparse
import sys
import os
import time
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveGiftEvent,
    TIKTOK_LIVE_AVAILABLE
)
from core.advanced_phase_system import AdvancedPhaseManager
from core.battle_engine import BattleEngine
from core.budget_manager import BudgetManager, BattlePhase, create_budget_manager
from core.battle_history import BattleHistoryDB
from agents.budget_aware_agents import (
    create_budget_aware_team,
    reset_budget_team,
    get_team_spending_report,
    BudgetAwareKinetik,
    BudgetAwareBoostResponder,
    BudgetAwareLoadoutMaster
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


class BudgetBattleEngine:
    """
    Battle engine with budget constraints.

    Features:
    - Hard budget cap (no spending beyond limit)
    - Phase-based allocation tracking
    - Spending efficiency analysis
    - Learning from budget outcomes
    """

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 50000,
        strategy: str = "balanced",
        battle_duration: int = 300,
        db_path: str = "data/budget_battles.db"
    ):
        self.target = target_streamer.lstrip("@")
        self.total_budget = total_budget
        self.strategy = strategy
        self.battle_duration = battle_duration
        self.db_path = db_path

        # Initialize components
        self.phase_manager = AdvancedPhaseManager(battle_duration=battle_duration)
        self.db = BattleHistoryDB(db_path)

        # Create budget-aware team
        self.team, self.budget = create_budget_aware_team(
            total_budget=total_budget,
            phase_manager=self.phase_manager,
            strategy=strategy,
            db=self.db
        )

        # Live connector
        self.connector = None
        self.live_score = 0
        self.ai_score = 0
        self.live_gifts = []

        # Battle state
        self.is_running = False
        self.start_time = None
        self.current_time = 0
        self._engine = None

        # Budget tracking
        self.budget_warnings = 0
        self.phases_exhausted = []

    async def connect(self) -> bool:
        """Connect to live stream."""
        print(f"\n{Colors.YELLOW}🔌 Connecting to @{self.target}...{Colors.END}")

        try:
            self.connector = TikTokLiveConnector(self.target)

            def on_gift(event: LiveGiftEvent):
                self.live_score += event.total_points
                self.live_gifts.append({
                    'time': time.time() - self.start_time if self.start_time else 0,
                    'user': event.username,
                    'gift': event.gift_name,
                    'coins': event.total_coins,
                    'points': event.total_points
                })
                # Update engine score
                if self._engine:
                    self._engine.score_tracker.opponent_score = self.live_score
                self.phase_manager.opponent_score = self.live_score

                print(f"\n  🔴 {Colors.RED}{event.username}{Colors.END}: {event.gift_name} "
                      f"x{event.repeat_count} ({Colors.YELLOW}{event.total_coins:,} coins{Colors.END}, "
                      f"{Colors.GREEN}+{event.total_points:,} pts{Colors.END})")
                self._print_battle_status()

            self.connector.on_gift(on_gift)

            try:
                await asyncio.wait_for(self.connector.connect(), timeout=15)
                print(f"{Colors.GREEN}✅ Connected to @{self.target}{Colors.END}\n")
                return True
            except asyncio.TimeoutError:
                print(f"{Colors.YELLOW}⚠️ Stream may be paused, continuing anyway...{Colors.END}\n")
                return True

        except Exception as e:
            print(f"{Colors.RED}❌ Connection failed: {e}{Colors.END}")
            print(f"{Colors.YELLOW}Continuing in offline mode...{Colors.END}\n")
            return True

    def _print_battle_status(self):
        """Print compact battle status with budget info."""
        total = self.ai_score + self.live_score or 1
        ai_pct = int((self.ai_score / total) * 30)
        live_pct = 30 - ai_pct

        bar = f"{Colors.BLUE}{'█' * ai_pct}{Colors.END}{Colors.RED}{'█' * live_pct}{Colors.END}"
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        remaining = max(0, self.battle_duration - elapsed)

        # Budget info
        budget_pct = (self.budget.remaining_coins / self.total_budget) * 100
        budget_color = Colors.GREEN if budget_pct > 30 else (Colors.YELLOW if budget_pct > 10 else Colors.RED)

        print(f"\r  [{bar}] {Colors.BLUE}AI {self.ai_score:,}{Colors.END} vs "
              f"{Colors.RED}{self.live_score:,} Live{Colors.END} │ "
              f"⏱️  {remaining}s │ "
              f"{budget_color}💰 {self.budget.remaining_coins:,}/{self.total_budget:,}{Colors.END}  ",
              end='', flush=True)

    async def run_battle(self):
        """Run budget-constrained battle."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'BUDGET-CONSTRAINED BATTLE'.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

        print(f"  {Colors.BLUE}🔵 AI Team (Budget-Aware):{Colors.END}")
        for agent in self.team:
            print(f"     {agent.emoji} {agent.name}")

        print(f"\n  {Colors.RED}🔴 Target:{Colors.END} @{self.target}")
        print(f"  ⏱️  Duration: {self.battle_duration}s")
        print(f"  💰 Budget: {Colors.GREEN}{self.total_budget:,} coins{Colors.END}")
        print(f"  📊 Strategy: {self.strategy}")
        print()

        # Show budget allocation
        print(f"  {Colors.YELLOW}📈 Budget Allocation:{Colors.END}")
        for phase, alloc in self.budget.allocations.items():
            pct = alloc.coins_allocated / self.total_budget * 100
            print(f"     {phase.value:12s}: {alloc.coins_allocated:>8,} coins ({pct:5.1f}%)")
        print()

        # Connect to live stream
        if not await self.connect():
            return None

        # Entry timing detection
        entry_offset = 0
        if self.live_score > 0:
            estimated_elapsed = min(self.live_score, self.battle_duration * 0.8)
            entry_offset = int(estimated_elapsed)
            print(f"{Colors.CYAN}⏱️  Detected mid-battle entry!{Colors.END}")
            print(f"   Live score: {self.live_score:,} pts → Estimated {entry_offset}s elapsed\n")

        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}  🎮 BATTLE START (Budget: {self.total_budget:,} coins){Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*70}{Colors.END}\n")

        # Create battle engine
        engine = BattleEngine(
            battle_duration=self.battle_duration,
            tick_speed=1.0,
            enable_multipliers=False,
            enable_analytics=True
        )
        self._engine = engine
        engine.score_tracker.opponent_score = self.live_score
        self.phase_manager.opponent_score = self.live_score

        self.is_running = True
        self.start_time = time.time() - entry_offset

        # Add agents
        for agent in self.team:
            engine.add_agent(agent)

        # Subscribe to gift events
        from core.event_bus import EventType

        def on_ai_gift(event):
            points = event.data.get("points", 0)
            self.ai_score += points
            self.phase_manager.creator_score = self.ai_score

            agent_name = event.source or "Agent"
            gift_name = event.data.get("gift", "Gift")

            # Get budget status
            budget_status = self.budget.get_status()

            print(f"  🔵 {Colors.BLUE}{agent_name}{Colors.END}: {gift_name} "
                  f"{Colors.GREEN}+{points:,} pts{Colors.END} "
                  f"({Colors.YELLOW}{budget_status['remaining']:,} coins left{Colors.END})")
            self._print_battle_status()

        engine.event_bus.subscribe(EventType.GIFT_SENT, on_ai_gift)

        # Track gifts for phase manager
        def record_gift(event):
            gift_name = event.data.get("gift", "Gift")
            points = event.data.get("points", 0)
            current_time = int(event.timestamp)
            self.phase_manager.record_gift(gift_name, points, "creator", current_time)

        engine.event_bus.subscribe(EventType.GIFT_SENT, record_gift)

        # Battle loop
        try:
            last_status_time = 0

            while self.is_running:
                elapsed = time.time() - self.start_time
                self.current_time = int(elapsed)
                time_remaining = self.battle_duration - self.current_time

                if elapsed >= self.battle_duration:
                    break

                # Update managers
                self.phase_manager.update(self.current_time)
                self.budget.update_battle_state(
                    time_remaining,
                    self.live_score - self.ai_score
                )

                # Phase transition announcements
                current_phase = self.budget.current_phase
                phase_budget = self.budget.get_phase_budget(current_phase)

                # Warn if phase budget is low
                if phase_budget < 100 and current_phase not in self.phases_exhausted:
                    self.phases_exhausted.append(current_phase)
                    print(f"\n⚠️  {Colors.YELLOW}{current_phase.value} budget exhausted!{Colors.END}")

                # Periodic status (every 30s)
                if self.current_time - last_status_time >= 30:
                    last_status_time = self.current_time
                    self._print_phase_status()

                # Let agents act
                engine.time_manager.current_time = self.current_time
                for agent in self.team:
                    try:
                        # Check if budget allows any action
                        if self.budget.remaining_coins >= 1:
                            agent.act(engine)
                    except Exception as e:
                        print(f"⚠️ Agent {agent.name} error: {e}")

                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.RED}Battle cancelled{Colors.END}")
        finally:
            self.is_running = False
            if self.connector:
                await self.connector.disconnect()

        # Results
        return self._show_results()

    def _print_phase_status(self):
        """Print periodic phase status."""
        phase = self.budget.current_phase
        status = self.budget.get_status()
        elapsed = self.current_time

        print(f"\n{'─'*50}")
        print(f"  📊 Status at t={elapsed}s | Phase: {phase.value}")
        print(f"     Budget: {status['remaining']:,}/{status['total']:,} "
              f"({status['utilization']*100:.1f}% used)")
        print(f"     Points: {self.ai_score:,} | Efficiency: {status['efficiency']:.2f} pts/coin")
        print(f"{'─'*50}")

    def _show_results(self) -> Dict:
        """Show battle results with spending analysis."""
        print(f"\n\n{Colors.BOLD}{'─'*70}{Colors.END}")
        print(f"{Colors.BOLD}  🏁 BATTLE COMPLETE{Colors.END}")
        print(f"{Colors.BOLD}{'─'*70}{Colors.END}\n")

        winner = "AI" if self.ai_score > self.live_score else "Live" if self.live_score > self.ai_score else "Tie"

        if winner == "AI":
            print(f"  {Colors.GREEN}{Colors.BOLD}🏆 AI TEAM WINS!{Colors.END}")
        elif winner == "Live":
            print(f"  {Colors.RED}{Colors.BOLD}🔴 LIVE WINS!{Colors.END}")
        else:
            print(f"  {Colors.YELLOW}{Colors.BOLD}🤝 TIE GAME!{Colors.END}")

        print(f"\n  {Colors.BLUE}AI Score:{Colors.END}   {self.ai_score:,}")
        print(f"  {Colors.RED}Live Score:{Colors.END} {self.live_score:,}")
        print(f"  Difference: {abs(self.ai_score - self.live_score):,}")

        # Budget analysis
        report = self.budget.get_efficiency_report()
        print(f"\n  💰 {Colors.YELLOW}Budget Analysis:{Colors.END}")
        print(f"     Total Budget:  {report['total_budget']:,} coins")
        print(f"     Total Spent:   {report['total_spent']:,} coins")
        print(f"     Remaining:     {report['remaining']:,} coins ({report['remaining']/report['total_budget']*100:.1f}%)")
        print(f"     Points Earned: {report['total_points']:,}")
        print(f"     Efficiency:    {report['overall_efficiency']:.2f} pts/coin")

        # Per-phase breakdown
        print(f"\n  📊 {Colors.CYAN}Spending by Phase:{Colors.END}")
        for phase_name, stats in report['by_phase'].items():
            if stats['spent'] > 0:
                print(f"     {phase_name:12s}: {stats['spent']:>8,} coins → {stats['points']:>8,} pts "
                      f"({stats['efficiency']:.2f} eff)")

        # Agent reports
        print(f"\n  👥 {Colors.BLUE}Agent Performance:{Colors.END}")
        for agent in self.team:
            total_agent_spent = 0
            if hasattr(agent, 'coins_spent_by_phase'):
                total_agent_spent = sum(agent.coins_spent_by_phase.values())
            elif hasattr(agent, 'get_spending_report'):
                agent_report = agent.get_spending_report()
                total_agent_spent = sum(
                    p.get('coins', 0)
                    for p in agent_report.get('by_phase', {}).values()
                )
            print(f"     {agent.emoji} {agent.name}: {total_agent_spent:,} coins spent")

        # Learning
        print(f"\n  📚 {Colors.GREEN}Learning Update:{Colors.END}")
        won = winner == "AI"
        battle_stats = {
            'points_donated': self.ai_score,
            'final_deficit': max(0, self.live_score - self.ai_score),
            'total_spent': report['total_spent'],
            'efficiency': report['overall_efficiency']
        }

        for agent in self.team:
            if hasattr(agent, 'learn_from_battle'):
                agent.learn_from_battle(won, battle_stats)

        return {
            'winner': winner,
            'ai_score': self.ai_score,
            'live_score': self.live_score,
            'budget_report': report,
            'live_gifts': self.live_gifts
        }


async def main():
    parser = argparse.ArgumentParser(description="Budget-Constrained TikTok Battle")
    parser.add_argument('-t', '--target', required=True, help='TikTok streamer username')
    parser.add_argument('-b', '--budget', type=int, default=50000, help='Total coin budget (default: 50000)')
    parser.add_argument('-s', '--strategy', default='balanced',
                       choices=['balanced', 'aggressive', 'conservative', 'snipe_heavy'],
                       help='Budget strategy')
    parser.add_argument('-d', '--duration', type=int, default=300, help='Battle duration (default: 300s)')

    args = parser.parse_args()

    engine = BudgetBattleEngine(
        target_streamer=args.target,
        total_budget=args.budget,
        strategy=args.strategy,
        battle_duration=args.duration
    )

    result = await engine.run_battle()
    return result


if __name__ == "__main__":
    if not TIKTOK_LIVE_AVAILABLE:
        print("WARNING: TikTokLive not installed, running in offline mode")

    asyncio.run(main())
