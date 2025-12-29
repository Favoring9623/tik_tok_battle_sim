#!/usr/bin/env python3
"""
Pressure-Based Battle Runner

Instead of fixed phase allocations, this uses psychological warfare:
- Track opponent behavior and reactions
- Apply pressure to force opponent responses
- Adapt strategy based on opponent state
- Control tempo to exhaust opponent budget
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from typing import Optional, List, Dict

# TikTok Live integration (optional for demo mode)
try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import GiftEvent, ConnectEvent, DisconnectEvent
    TIKTOK_AVAILABLE = True
except ImportError:
    TIKTOK_AVAILABLE = False
    print("⚠️  TikTokLive not available - running in simulation mode")

from core.pressure_engine import PressureEngine, PressureTactic, OpponentState
from core.gift_catalog import get_gift_catalog


class PressureBattleEngine:
    """Battle engine using psychological pressure tactics."""

    BATTLE_DURATION = 300  # 5 minutes

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 165000,
        battle_duration: int = 300,
        initial_opponent_score: int = 0,
        time_remaining: Optional[int] = None
    ):
        self.target_streamer = target_streamer
        self.battle_duration = battle_duration
        self.time_remaining = time_remaining or battle_duration

        # Initialize pressure engine
        self.pressure = PressureEngine(total_budget)
        self.pressure.state.opponent_score = initial_opponent_score
        self.pressure.state.time_remaining = self.time_remaining

        # Battle state
        self.ai_score = 0
        self.opponent_score = initial_opponent_score
        self.battle_start = None
        self.is_running = False

        # Gift catalog
        self.gifts = self._load_gifts()

        # Action cooldown
        self.last_action_time = 0
        self.min_action_interval = 2.0  # Minimum seconds between gifts

        # Logging
        self.action_log: List[Dict] = []

    def _load_gifts(self) -> List[Dict]:
        """Load available gifts from catalog."""
        catalog = get_gift_catalog()
        return [
            {"name": g.name, "cost": g.coins, "points": g.points}
            for g in catalog.gifts
        ]

    async def run_battle(self):
        """Main battle loop."""
        self.battle_start = time.time()
        self.is_running = True

        print(f"\n{'='*60}")
        print(f"🎯 PRESSURE BATTLE vs @{self.target_streamer}")
        print(f"{'='*60}")
        print(f"Budget: {self.pressure.total_budget:,} coins")
        print(f"Time: {self.time_remaining}s")
        print(f"Initial opponent score: {self.opponent_score:,}")
        print(f"{'='*60}\n")

        if TIKTOK_AVAILABLE:
            await self._run_live_battle()
        else:
            await self._run_simulated_battle()

        self._print_summary()

    async def _run_live_battle(self):
        """Run battle with live TikTok connection."""
        client = TikTokLiveClient(unique_id=self.target_streamer)
        connected = False

        @client.on(ConnectEvent)
        async def on_connect(event):
            nonlocal connected
            connected = True
            print(f"✅ Connected to @{self.target_streamer}")

        @client.on(GiftEvent)
        async def on_gift(event):
            if event.gift.streakable and not event.streaking:
                points = event.gift.diamond_count * event.combo_count
            else:
                points = event.gift.diamond_count

            # Record opponent action
            self.opponent_score += points
            self.pressure.record_opponent_action(points)
            self._log_opponent_action(event.gift.name, points)

        # Try to connect
        try:
            asyncio.create_task(client.start())
            await asyncio.sleep(3)

            if not connected:
                print("⚠️ Could not connect - running simulation")
                await self._run_simulated_battle()
                return
        except Exception as e:
            print(f"⚠️ Connection failed: {e} - running simulation")
            await self._run_simulated_battle()
            return

        # Battle loop
        while self.is_running and self.time_remaining > 0:
            await self._battle_tick()
            await asyncio.sleep(0.5)

        try:
            await client.disconnect()
        except Exception:
            pass

    async def _run_simulated_battle(self):
        """Run simulated battle for testing."""
        print("📺 Running in SIMULATION mode\n")

        while self.is_running and self.time_remaining > 0:
            # Simulate opponent gifts randomly
            if asyncio.get_event_loop().time() % 5 < 0.5:
                await self._simulate_opponent_gift()

            await self._battle_tick()
            await asyncio.sleep(0.5)

    async def _simulate_opponent_gift(self):
        """Simulate opponent gift based on current state."""
        import random

        # Probability based on game state
        prob = 0.1

        # Increase if opponent should be reacting
        if self.pressure.state.waiting_for_reaction:
            prob = 0.4

        # Increase late game
        if self.time_remaining < 60:
            prob = 0.3

        if random.random() < prob:
            # Choose gift size based on opponent state
            if self.pressure.state.opponent_state == OpponentState.AGGRESSIVE:
                points = random.choice([5000, 10000, 20000])
            elif self.pressure.state.opponent_state == OpponentState.PANICKING:
                points = random.choice([10000, 20000, 50000])
            else:
                points = random.choice([100, 500, 1000, 2000])

            self.opponent_score += points
            self.pressure.record_opponent_action(points)
            self._log_opponent_action("simulated", points)

    async def _battle_tick(self):
        """Single battle tick - decide and execute action."""
        now = time.time()
        elapsed = now - self.battle_start
        self.time_remaining = max(0, self.battle_duration - int(elapsed))

        # Update pressure engine state
        self.pressure.update_scores(self.ai_score, self.opponent_score, self.time_remaining)

        # Check if we should act
        if now - self.last_action_time < self.min_action_interval:
            return

        # Get recommendation from pressure engine
        tactic, target_spend = self.pressure.decide_tactic()

        # Execute tactic
        if tactic != PressureTactic.PATIENCE:
            gift = self.pressure.get_gift_recommendation(self.gifts)
            if gift:
                await self._send_gift(gift, tactic)

        # Print status periodically
        if int(elapsed) % 10 == 0:
            self._print_status(tactic)

    async def _send_gift(self, gift: Dict, tactic: PressureTactic):
        """Send a gift and record the action."""
        # Calculate points (with potential boost multiplier)
        points = gift["points"]
        if self.pressure.state.in_boost:
            points = int(points * self.pressure.state.boost_multiplier)

        # Update scores
        self.ai_score += points
        self.pressure.record_our_action(points, gift["cost"])
        self.last_action_time = time.time()

        # Log
        self._log_our_action(gift, tactic, points)

        # Print action
        tactic_emoji = {
            PressureTactic.SHOW_STRENGTH: "💪",
            PressureTactic.PROBE: "🔍",
            PressureTactic.TEMPO_BURST: "⚡",
            PressureTactic.COUNTER_PUNCH: "🥊",
            PressureTactic.BAIT: "🎣",
            PressureTactic.FINISH: "🏁"
        }.get(tactic, "🎁")

        print(f"{tactic_emoji} [{tactic.value}] Sent {gift['name']} "
              f"({gift['cost']:,} coins → {points:,} pts)")

    def _log_our_action(self, gift: Dict, tactic: PressureTactic, points: int):
        """Log our action for analysis."""
        self.action_log.append({
            "type": "ai",
            "time": time.time() - self.battle_start,
            "tactic": tactic.value,
            "gift": gift["name"],
            "cost": gift["cost"],
            "points": points,
            "ai_score": self.ai_score,
            "opponent_score": self.opponent_score,
            "opponent_state": self.pressure.state.opponent_state.value
        })

    def _log_opponent_action(self, gift_name: str, points: int):
        """Log opponent action."""
        self.action_log.append({
            "type": "opponent",
            "time": time.time() - self.battle_start,
            "gift": gift_name,
            "points": points,
            "ai_score": self.ai_score,
            "opponent_score": self.opponent_score
        })
        print(f"👤 Opponent: {gift_name} (+{points:,} pts) "
              f"→ Total: {self.opponent_score:,}")

    def _print_status(self, current_tactic: PressureTactic):
        """Print current battle status."""
        state = self.pressure.state
        diff = self.ai_score - self.opponent_score

        print(f"\n📊 Status @ {self.battle_duration - self.time_remaining}s")
        print(f"   AI: {self.ai_score:,} | Live: {self.opponent_score:,} "
              f"(diff: {diff:+,})")
        print(f"   Budget: {state.budget_remaining:,}/{self.pressure.total_budget:,} "
              f"({state.budget_remaining/self.pressure.total_budget*100:.0f}%)")
        print(f"   Opponent: {state.opponent_state.value}")
        print(f"   Tactic: {current_tactic.value}")
        print()

    def _print_summary(self):
        """Print battle summary."""
        state = self.pressure.state
        diff = self.ai_score - self.opponent_score
        result = "WIN" if diff > 0 else "LOSE" if diff < 0 else "TIE"

        print(f"\n{'='*60}")
        print(f"🏆 BATTLE COMPLETE - {result}")
        print(f"{'='*60}")
        print(f"Final Score: AI {self.ai_score:,} vs Live {self.opponent_score:,}")
        print(f"Margin: {abs(diff):,} points")
        print(f"Budget Used: {state.budget_spent:,}/{self.pressure.total_budget:,} "
              f"({state.budget_spent/self.pressure.total_budget*100:.0f}%)")

        # Tactic breakdown
        tactic_counts = {}
        for entry in self.action_log:
            if entry["type"] == "ai":
                t = entry["tactic"]
                tactic_counts[t] = tactic_counts.get(t, 0) + 1

        if tactic_counts:
            print(f"\nTactic Usage:")
            for tactic, count in sorted(tactic_counts.items(), key=lambda x: -x[1]):
                print(f"   {tactic}: {count}")

        print(f"{'='*60}\n")

    def sync_live_score(self, score: int, time_left: Optional[int] = None):
        """Sync with actual live score mid-battle."""
        self.opponent_score = score
        self.pressure.state.opponent_score = score
        if time_left:
            self.time_remaining = time_left
            self.pressure.state.time_remaining = time_left

    def set_boost(self, active: bool, multiplier: float = 1.0, duration: int = 0):
        """Set boost state."""
        self.pressure.set_boost(active, multiplier, duration)
        if active:
            print(f"\n🚀 BOOST ACTIVE x{multiplier} ({duration}s)")


async def main():
    parser = argparse.ArgumentParser(description="Pressure-based TikTok Battle")
    parser.add_argument("streamer", help="Target streamer username")
    parser.add_argument("--budget", type=int, default=165000,
                        help="Total budget in coins")
    parser.add_argument("--duration", type=int, default=300,
                        help="Battle duration in seconds")
    parser.add_argument("--live-score", type=int, default=0,
                        help="Initial opponent score (for mid-battle join)")
    parser.add_argument("--time-left", type=int, default=None,
                        help="Time remaining (for mid-battle join)")

    args = parser.parse_args()

    engine = PressureBattleEngine(
        target_streamer=args.streamer,
        total_budget=args.budget,
        battle_duration=args.duration,
        initial_opponent_score=args.live_score,
        time_remaining=args.time_left
    )

    try:
        await engine.run_battle()
    except KeyboardInterrupt:
        print("\n\n⏹️ Battle interrupted")
        engine._print_summary()


if __name__ == "__main__":
    asyncio.run(main())
