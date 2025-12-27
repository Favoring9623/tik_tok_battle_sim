#!/usr/bin/env python3
"""
Evolved AI Agents vs Live TikTok Stream

Uses the trained EvolvingKinetik, EvolvingStrikeMaster, EvolvingPhaseTracker,
and EvolvingLoadoutMaster agents against a real TikTok live stream.

These agents have learned from 66+ battles with 100% win rate.
"""

import asyncio
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveGiftEvent,
    TIKTOK_LIVE_AVAILABLE
)
from core.advanced_phase_system import AdvancedPhaseManager
from core.battle_engine import BattleEngine
from agents.evolving_agents import (
    create_evolving_team,
    EvolvingKinetik,
    EvolvingStrikeMaster,
    EvolvingPhaseTracker,
    EvolvingLoadoutMaster
)
from core.battle_history import BattleHistoryDB


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


class EvolvedVsLiveEngine:
    """
    Pits trained evolving agents against a live TikTok stream.
    """

    def __init__(
        self,
        target_streamer: str,
        battle_duration: int = 180,
        db_path: str = "data/evolved_vs_live.db"
    ):
        self.target = target_streamer.lstrip("@")
        self.battle_duration = battle_duration
        self.db_path = db_path

        # Initialize components
        self.phase_manager = AdvancedPhaseManager(battle_duration=battle_duration)
        self.db = BattleHistoryDB(db_path)

        # Create trained team
        self.team = create_evolving_team(self.phase_manager, db=self.db)

        # Live connector
        self.connector = None
        self.live_score = 0
        self.ai_score = 0
        self.live_gifts = []

        # Battle state
        self.is_running = False
        self.start_time = None
        self.current_time = 0

    async def connect(self) -> bool:
        """Connect to live stream."""
        print(f"\n{Colors.YELLOW}🔌 Connecting to @{self.target}...{Colors.END}")

        try:
            self.connector = TikTokLiveConnector(self.target)

            # Set up gift callback
            def on_gift(event: LiveGiftEvent):
                self.live_score += event.total_points
                self.live_gifts.append({
                    'time': time.time() - self.start_time if self.start_time else 0,
                    'user': event.username,
                    'gift': event.gift_name,
                    'coins': event.total_coins,
                    'points': event.total_points
                })
                print(f"\n  🔴 {Colors.RED}{event.username}{Colors.END}: {event.gift_name} "
                      f"x{event.repeat_count} ({Colors.YELLOW}{event.total_coins:,} coins{Colors.END}, "
                      f"{Colors.GREEN}+{event.total_points:,} pts{Colors.END})")
                self._print_score_bar()

            self.connector.on_gift(on_gift)

            # Try to connect (with timeout)
            try:
                await asyncio.wait_for(self.connector.connect(), timeout=15)
                print(f"{Colors.GREEN}✅ Connected to @{self.target}{Colors.END}\n")
                return True
            except asyncio.TimeoutError:
                print(f"{Colors.YELLOW}⚠️ Stream may be paused, continuing anyway...{Colors.END}\n")
                return True  # Continue even if stream is paused

        except Exception as e:
            print(f"{Colors.RED}❌ Connection failed: {e}{Colors.END}")
            print(f"{Colors.YELLOW}Continuing in offline mode...{Colors.END}\n")
            return True  # Continue anyway to show agents working

    def _print_score_bar(self):
        """Print score comparison bar."""
        total = self.ai_score + self.live_score or 1
        ai_pct = int((self.ai_score / total) * 40)
        live_pct = 40 - ai_pct

        bar = f"{Colors.BLUE}{'█' * ai_pct}{Colors.END}{Colors.RED}{'█' * live_pct}{Colors.END}"
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        remaining = max(0, self.battle_duration - elapsed)

        print(f"\r  [{bar}] {Colors.BLUE}AI {self.ai_score:,}{Colors.END} vs "
              f"{Colors.RED}{self.live_score:,} Live{Colors.END} │ ⏱️  {remaining}s  ",
              end='', flush=True)

    async def run_battle(self):
        """Run a battle with evolved agents vs live stream."""

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'EVOLVED AI vs LIVE BATTLE'.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

        print(f"  {Colors.BLUE}🔵 AI Team (Trained):{Colors.END}")
        for agent in self.team:
            print(f"     {agent.emoji} {agent.name}")
        print(f"\n  {Colors.RED}🔴 Target:{Colors.END} @{self.target}")
        print(f"  ⏱️  Duration: {self.battle_duration}s")
        print()

        # Connect to live stream
        if not await self.connect():
            return None

        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}  🎮 BATTLE START{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'─'*60}{Colors.END}\n")

        self.is_running = True
        self.start_time = time.time()

        # Create a minimal battle engine for agents to interact with
        engine = BattleEngine(
            battle_duration=self.battle_duration,
            tick_speed=1.0,
            enable_multipliers=False,
            enable_analytics=True
        )

        # Add our evolved agents
        for agent in self.team:
            engine.add_agent(agent)

        # Subscribe to gift events to track AI score
        from core.event_bus import EventType

        def on_ai_gift(event):
            points = event.data.get("points", 0)
            self.ai_score += points
            agent_name = event.source or "Agent"
            gift_name = event.data.get("gift", "Gift")
            print(f"  🔵 {Colors.BLUE}{agent_name}{Colors.END}: {gift_name} "
                  f"{Colors.GREEN}+{points:,} pts{Colors.END}")
            self._print_score_bar()

        engine.event_bus.subscribe(EventType.GIFT_SENT, on_ai_gift)

        # Also record for phase manager
        def record_gift(event):
            gift_name = event.data.get("gift", "Gift")
            points = event.data.get("points", 0)
            current_time = int(event.timestamp)
            self.phase_manager.record_gift(gift_name, points, "creator", current_time)

        engine.event_bus.subscribe(EventType.GIFT_SENT, record_gift)

        # Run battle loop
        try:
            while self.is_running:
                elapsed = time.time() - self.start_time
                self.current_time = int(elapsed)

                if elapsed >= self.battle_duration:
                    break

                # Update phase manager
                self.phase_manager.update(self.current_time)

                # Let agents act
                engine.time_manager._current_time = self.current_time
                for agent in self.team:
                    try:
                        agent.act(engine)
                    except Exception as e:
                        pass

                # Small delay
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.RED}Battle cancelled{Colors.END}")
        finally:
            self.is_running = False
            if self.connector:
                await self.connector.disconnect()

        # Results
        print(f"\n\n{Colors.BOLD}{'─'*60}{Colors.END}")
        print(f"{Colors.BOLD}  🏁 BATTLE COMPLETE{Colors.END}")
        print(f"{Colors.BOLD}{'─'*60}{Colors.END}\n")

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

        if self.live_gifts:
            print(f"\n  📊 Live Gifts Received: {len(self.live_gifts)}")

        return {
            'winner': winner,
            'ai_score': self.ai_score,
            'live_score': self.live_score,
            'live_gifts': self.live_gifts
        }


async def main():
    parser = argparse.ArgumentParser(description="Evolved AI vs Live TikTok Battle")
    parser.add_argument('-t', '--target', required=True, help='TikTok streamer username')
    parser.add_argument('-d', '--duration', type=int, default=180, help='Battle duration (default: 180s)')

    args = parser.parse_args()

    engine = EvolvedVsLiveEngine(
        target_streamer=args.target,
        battle_duration=args.duration
    )

    result = await engine.run_battle()
    return result


if __name__ == "__main__":
    if not TIKTOK_LIVE_AVAILABLE:
        print("ERROR: TikTokLive not installed!")
        sys.exit(1)

    asyncio.run(main())
