#!/usr/bin/env python3
"""
Synchronized Budget Battle Runner
=================================

Runs budget battles with REAL-TIME synchronization to live TikTok battles.
Supports mid-battle entry with known opponent scores.

Usage:
    # Join ongoing battle with known score and time remaining
    python run_synced_battle.py -t @streamer -b 50000 --live-score 31000 --time-left 54

    # Start fresh battle
    python run_synced_battle.py -t @streamer -b 100000 -d 300
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


class SyncedBattleEngine:
    """
    Battle engine with REAL-TIME synchronization.

    Key Features:
    - Accept initial opponent score for mid-battle entry
    - Sync with actual battle time remaining
    - Immediate deficit response
    - Dynamic budget reallocation based on live state
    """

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 50000,
        strategy: str = "balanced",
        battle_duration: int = 300,
        initial_live_score: int = 0,
        time_remaining: Optional[int] = None,
        db_path: str = "data/synced_battles.db"
    ):
        self.target = target_streamer.lstrip("@")
        self.total_budget = total_budget
        self.strategy = strategy
        self.battle_duration = battle_duration
        self.db_path = db_path

        # SYNC: Initial state from user input
        self.initial_live_score = initial_live_score
        self.time_remaining = time_remaining if time_remaining else battle_duration

        # Calculate elapsed time
        self.elapsed_at_start = battle_duration - self.time_remaining

        # Initialize phase manager with correct timing
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
        self.live_score = initial_live_score  # Start with known score
        self.ai_score = 0
        self.live_gifts = []

        # Battle state
        self.is_running = False
        self.start_time = None
        self.current_time = 0
        self._engine = None

        # Sync tracking
        self.sync_updates = []
        self.last_sync_time = 0

    def sync_live_score(self, new_score: int, time_left: Optional[int] = None):
        """
        CRITICAL: Update live score in real-time.
        Call this when you see the actual score on TikTok.
        """
        old_score = self.live_score
        self.live_score = new_score

        if time_left is not None:
            self.time_remaining = time_left

        # Update phase manager immediately
        self.phase_manager.opponent_score = new_score

        # Update engine if running
        if self._engine:
            self._engine.score_tracker.opponent_score = new_score

        # Log sync
        self.sync_updates.append({
            'time': time.time(),
            'old_score': old_score,
            'new_score': new_score,
            'delta': new_score - old_score
        })

        print(f"\n{Colors.CYAN}🔄 SYNC: Live score updated {old_score:,} → {new_score:,} (+{new_score - old_score:,}){Colors.END}")

        # Trigger immediate agent response if deficit is critical
        deficit = new_score - self.ai_score
        if deficit > 0:
            print(f"{Colors.RED}⚠️  DEFICIT: {deficit:,} pts behind!{Colors.END}")

    async def connect(self) -> bool:
        """Connect to live stream."""
        print(f"\n{Colors.YELLOW}🔌 Connecting to @{self.target}...{Colors.END}")

        try:
            self.connector = TikTokLiveConnector(self.target)

            def on_gift(event: LiveGiftEvent):
                # Accumulate live score from new gifts
                self.live_score += event.total_points
                self.live_gifts.append({
                    'time': time.time() - self.start_time if self.start_time else 0,
                    'user': event.username,
                    'gift': event.gift_name,
                    'coins': event.total_coins,
                    'points': event.total_points
                })

                # CRITICAL: Update engine score tracker
                if self._engine:
                    self._engine.score_tracker.opponent_score = self.live_score
                self.phase_manager.opponent_score = self.live_score

                # Show gift with deficit warning
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
            return True  # Continue anyway

    def _print_battle_status(self):
        """Print battle status with sync info."""
        total = self.ai_score + self.live_score or 1
        ai_pct = int((self.ai_score / total) * 30)
        live_pct = 30 - ai_pct

        bar = f"{Colors.BLUE}{'█' * ai_pct}{Colors.END}{Colors.RED}{'█' * live_pct}{Colors.END}"
        remaining = max(0, self.time_remaining - (time.time() - self.start_time if self.start_time else 0))

        # Budget info
        budget_pct = (self.budget.remaining_coins / self.total_budget) * 100
        budget_color = Colors.GREEN if budget_pct > 30 else (Colors.YELLOW if budget_pct > 10 else Colors.RED)

        # Deficit indicator
        deficit = self.live_score - self.ai_score
        if deficit > 0:
            deficit_str = f" {Colors.RED}(-{deficit:,}){Colors.END}"
        elif deficit < 0:
            deficit_str = f" {Colors.GREEN}(+{-deficit:,}){Colors.END}"
        else:
            deficit_str = ""

        print(f"\r  [{bar}] {Colors.BLUE}AI {self.ai_score:,}{Colors.END} vs "
              f"{Colors.RED}{self.live_score:,} Live{Colors.END}{deficit_str} │ "
              f"⏱️  {int(remaining)}s │ "
              f"{budget_color}💰 {self.budget.remaining_coins:,}{Colors.END}  ",
              end='', flush=True)

    async def run_battle(self):
        """Run synchronized battle."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'SYNCHRONIZED BUDGET BATTLE'.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

        # Show sync info
        if self.initial_live_score > 0 or self.time_remaining < self.battle_duration:
            print(f"  {Colors.YELLOW}🔄 MID-BATTLE SYNC:{Colors.END}")
            print(f"     Live Score: {Colors.RED}{self.initial_live_score:,} pts{Colors.END}")
            print(f"     Time Left:  {Colors.CYAN}{self.time_remaining}s{Colors.END}")
            print(f"     Elapsed:    {self.elapsed_at_start}s")
            print()

        print(f"  {Colors.BLUE}🔵 AI Team:{Colors.END}")
        for agent in self.team:
            print(f"     {agent.emoji} {agent.name}")

        print(f"\n  {Colors.RED}🔴 Target:{Colors.END} @{self.target}")
        print(f"  💰 Budget: {Colors.GREEN}{self.total_budget:,} coins{Colors.END}")
        print(f"  📊 Strategy: {self.strategy}")
        print()

        # Connect
        if not await self.connect():
            return None

        # Calculate if we need emergency response
        if self.initial_live_score > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}🚨 EMERGENCY MODE: Opponent at {self.initial_live_score:,} pts!{Colors.END}")
            deficit = self.initial_live_score - self.ai_score
            print(f"   Need {deficit:,} pts to catch up!")
            print()

            # Reallocate budget for emergency
            self._reallocate_for_emergency()

        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}  🎮 BATTLE SYNCED ({self.time_remaining}s remaining){Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*70}{Colors.END}\n")

        # Create engine
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
        self.start_time = time.time()

        # Add agents
        for agent in self.team:
            engine.add_agent(agent)

        # Subscribe to events
        from core.event_bus import EventType

        def on_ai_gift(event):
            points = event.data.get("points", 0)
            self.ai_score += points
            self.phase_manager.creator_score = self.ai_score

            agent_name = event.source or "Agent"
            gift_name = event.data.get("gift", "Gift")

            deficit = self.live_score - self.ai_score
            if deficit > 0:
                status = f"{Colors.RED}(still -{deficit:,}){Colors.END}"
            else:
                status = f"{Colors.GREEN}(+{-deficit:,} ahead){Colors.END}"

            print(f"  🔵 {Colors.BLUE}{agent_name}{Colors.END}: {gift_name} "
                  f"{Colors.GREEN}+{points:,} pts{Colors.END} {status}")
            self._print_battle_status()

        engine.event_bus.subscribe(EventType.GIFT_SENT, on_ai_gift)

        # Record gifts for phase manager
        def record_gift(event):
            gift_name = event.data.get("gift", "Gift")
            points = event.data.get("points", 0)
            current_time = int(event.timestamp)
            self.phase_manager.record_gift(gift_name, points, "creator", current_time)

        engine.event_bus.subscribe(EventType.GIFT_SENT, record_gift)

        # Battle loop - use time_remaining as the countdown
        try:
            battle_end_time = time.time() + self.time_remaining
            last_status_time = 0

            while self.is_running:
                now = time.time()
                remaining = battle_end_time - now

                if remaining <= 0:
                    break

                # Calculate battle time for phase manager
                self.current_time = self.elapsed_at_start + int(now - self.start_time)

                # Update managers
                self.phase_manager.update(self.current_time)
                self.budget.update_battle_state(
                    int(remaining),
                    self.live_score - self.ai_score
                )

                # Check for snipe window
                if remaining <= 30 and remaining > 25:
                    print(f"\n{Colors.YELLOW}⏱️  SNIPE WINDOW: {int(remaining)}s remaining!{Colors.END}")

                # Periodic status
                if self.current_time - last_status_time >= 15:
                    last_status_time = self.current_time
                    deficit = self.live_score - self.ai_score
                    print(f"\n{'─'*50}")
                    print(f"  📊 t={self.current_time}s | Remaining: {int(remaining)}s")
                    print(f"     AI: {self.ai_score:,} | Live: {self.live_score:,} | Deficit: {deficit:,}")
                    print(f"     Budget: {self.budget.remaining_coins:,}/{self.total_budget:,}")
                    print(f"{'─'*50}")

                # Let agents act
                engine.time_manager.current_time = self.current_time
                for agent in self.team:
                    try:
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

        return self._show_results()

    def _reallocate_for_emergency(self):
        """Reallocate budget for emergency catch-up."""
        deficit = self.live_score - self.ai_score

        # If we're behind, prioritize immediate spending over saving for snipe
        if deficit > 0:
            print(f"  {Colors.YELLOW}📊 Reallocating budget for emergency response...{Colors.END}")

            # Move snipe allocation to emergency
            snipe_coins = self.budget.allocations.get(BattlePhase.SNIPE)
            if snipe_coins:
                emergency = self.budget.allocations.get(BattlePhase.EMERGENCY)
                if emergency:
                    # Combine snipe + emergency for immediate use
                    combined = snipe_coins.coins_allocated + emergency.coins_allocated
                    print(f"     Emergency fund: {combined:,} coins available for catch-up")

    def _show_results(self) -> Dict:
        """Show battle results."""
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

        # Show sync updates
        if self.sync_updates:
            print(f"\n  {Colors.CYAN}🔄 Sync Updates:{Colors.END} {len(self.sync_updates)}")

        # Budget analysis
        report = self.budget.get_efficiency_report()
        print(f"\n  💰 {Colors.YELLOW}Budget:{Colors.END}")
        print(f"     Spent: {report['total_spent']:,}/{report['total_budget']:,} coins")
        print(f"     Efficiency: {report['overall_efficiency']:.2f} pts/coin")

        return {
            'winner': winner,
            'ai_score': self.ai_score,
            'live_score': self.live_score,
            'initial_live_score': self.initial_live_score,
            'sync_updates': self.sync_updates,
            'budget_report': report
        }


async def main():
    parser = argparse.ArgumentParser(description="Synchronized Budget Battle")
    parser.add_argument('-t', '--target', required=True, help='TikTok streamer username')
    parser.add_argument('-b', '--budget', type=int, default=50000, help='Total coin budget')
    parser.add_argument('-s', '--strategy', default='balanced',
                       choices=['balanced', 'aggressive', 'conservative', 'snipe_heavy'])
    parser.add_argument('-d', '--duration', type=int, default=300, help='Full battle duration')
    parser.add_argument('--live-score', type=int, default=0,
                       help='Current opponent score (for mid-battle entry)')
    parser.add_argument('--time-left', type=int, default=None,
                       help='Seconds remaining in battle (for mid-battle entry)')

    args = parser.parse_args()

    engine = SyncedBattleEngine(
        target_streamer=args.target,
        total_budget=args.budget,
        strategy=args.strategy,
        battle_duration=args.duration,
        initial_live_score=args.live_score,
        time_remaining=args.time_left
    )

    result = await engine.run_battle()
    return result


if __name__ == "__main__":
    if not TIKTOK_LIVE_AVAILABLE:
        print("WARNING: TikTokLive not installed")

    asyncio.run(main())
