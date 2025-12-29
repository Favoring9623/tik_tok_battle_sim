#!/usr/bin/env python3
"""
Strategic Pressure Battle Runner v2

Key features:
- Boost window prioritization (x2, x3 multipliers)
- Power-up tracking (gloves, hammer, frog, time)
- Strategic 5-second snipe window (offensive/defensive)
- Meaningful probes (2000+ coins, not roses)
- Context-aware counter-attacks
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from typing import Optional, List, Dict

try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import GiftEvent, ConnectEvent, DisconnectEvent
    TIKTOK_AVAILABLE = True
except ImportError:
    TIKTOK_AVAILABLE = False

from core.pressure_engine import (
    StrategicPressureEngine, PressureTactic, BattlePhase,
    OpponentState, PowerUpType
)
from core.gift_catalog import get_gift_catalog


# Known power-up gift names
POWER_UP_GIFTS = {
    'Boxing Gloves': PowerUpType.GLOVES,
    'Gloves': PowerUpType.GLOVES,
    'Hammer': PowerUpType.HAMMER,
    'Thor Hammer': PowerUpType.HAMMER,
    'Frog': PowerUpType.FROG,
    'Lucky Frog': PowerUpType.FROG,
    'Time': PowerUpType.TIME_BONUS,
    'Extra Time': PowerUpType.TIME_BONUS,
}


class StrategicBattleEngine:
    """Battle engine with strategic pressure tactics."""

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 165000,
        battle_duration: int = 300,
        initial_opponent_score: int = 0,
        time_remaining: Optional[int] = None,
        simulate: bool = False
    ):
        self.target_streamer = target_streamer
        self.battle_duration = battle_duration
        self.time_remaining = time_remaining or battle_duration
        self.simulate = simulate

        # Initialize strategic engine
        self.engine = StrategicPressureEngine(total_budget, battle_duration)
        self.engine.state.opponent_score = initial_opponent_score
        self.engine.state.time_remaining = self.time_remaining

        # Battle state
        self.ai_score = 0
        self.opponent_score = initial_opponent_score
        self.battle_start = None
        self.is_running = False

        # Gift catalog
        self.gifts = self._load_gifts()

        # Action timing
        self.last_action_time = 0
        self.min_action_interval = 2.0

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

        print(f"\n{'='*70}")
        print(f"🎯 STRATEGIC PRESSURE BATTLE vs @{self.target_streamer}")
        print(f"{'='*70}")
        print(f"Budget: {self.engine.total_budget:,} coins")
        print(f"Snipe Reserve: {self.engine.state.snipe_reserve:,} coins (15%)")
        print(f"Time: {self.time_remaining}s")
        print(f"Initial opponent score: {self.opponent_score:,}")
        print(f"{'='*70}\n")

        if self.simulate or not TIKTOK_AVAILABLE:
            await self._run_simulated_battle()
        else:
            await self._run_live_battle()

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
            gift_name = event.gift.name
            if event.gift.streakable and not event.streaking:
                points = event.gift.diamond_count * event.combo_count
            else:
                points = event.gift.diamond_count

            # Check for power-ups
            is_power_up = gift_name in POWER_UP_GIFTS
            power_up_type = POWER_UP_GIFTS.get(gift_name)

            # Record opponent action
            self.opponent_score += points
            self.engine.record_opponent_gift(
                points, gift_name, is_power_up, power_up_type
            )
            self._log_opponent_action(gift_name, points, is_power_up)

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
        import random

        while self.is_running and self.time_remaining > 0:
            # Simulate opponent gifts
            if random.random() < 0.15:
                await self._simulate_opponent_gift()

            await self._battle_tick()
            await asyncio.sleep(0.5)

    async def _simulate_opponent_gift(self):
        """Simulate opponent gift based on phase."""
        import random

        phase = self.engine.phase
        opp_state = self.engine.state.opponent_state

        # Determine gift size based on phase
        if phase == BattlePhase.SNIPE_WINDOW:
            # 30% chance of big snipe attempt
            if random.random() < 0.3:
                points = random.choice([20000, 30000, 45000])
            else:
                points = random.choice([1000, 2000, 5000])
        elif phase == BattlePhase.ENDGAME:
            points = random.choice([2000, 5000, 10000, 15000])
        elif opp_state == OpponentState.AGGRESSIVE:
            points = random.choice([5000, 10000, 15000])
        else:
            points = random.choice([500, 1000, 2000, 5000])

        # Occasionally send power-ups
        if random.random() < 0.05:
            gift_name = random.choice(['Gloves', 'Hammer', 'Frog'])
            is_power_up = True
            power_up_type = POWER_UP_GIFTS.get(gift_name)
        else:
            gift_name = "simulated"
            is_power_up = False
            power_up_type = None

        self.opponent_score += points
        self.engine.record_opponent_gift(points, gift_name, is_power_up, power_up_type)
        self._log_opponent_action(gift_name, points, is_power_up)

    async def _battle_tick(self):
        """Single battle tick."""
        now = time.time()
        elapsed = now - self.battle_start
        self.time_remaining = max(0, self.battle_duration - int(elapsed))

        # Update engine state
        self.engine.update_time(self.time_remaining)
        self.engine.update_scores(self.ai_score, self.opponent_score)

        # Get current phase for display
        phase = self.engine.phase

        # Check action timing
        if now - self.last_action_time < self.min_action_interval:
            # Exception: snipe window requires faster response
            if phase != BattlePhase.SNIPE_WINDOW:
                return

        # Get tactical decision
        tactic, target_spend, reason = self.engine.decide_action()

        # Execute tactic
        if tactic not in (PressureTactic.PATIENCE, PressureTactic.RESERVE):
            gift = self.engine.get_gift_for_tactic(tactic, target_spend, self.gifts)
            if gift:
                await self._send_gift(gift, tactic, reason)

        # Status updates
        if int(elapsed) % 15 == 0 and int(elapsed) > 0:
            self._print_status()

        # Phase change announcements
        if self.time_remaining == 60:
            print(f"\n⚠️  ENDGAME - 60 seconds remaining!")
        elif self.time_remaining == 5:
            print(f"\n🎯 SNIPE WINDOW - Final 5 seconds!")

    async def _send_gift(self, gift: Dict, tactic: PressureTactic, reason: str):
        """Send a gift and record."""
        # Calculate points (boost multiplier if active)
        points = gift["points"]
        boost = self.engine.state.current_boost
        if boost and boost.is_active:
            points = int(points * boost.multiplier)

        # Apply gloves if we have them
        if self.engine.state.ai_has_gloves:
            points *= 2
            self.engine.use_gloves()

        # Update scores
        self.ai_score += points
        self.engine.record_our_action(gift["cost"], points)
        self.last_action_time = time.time()

        # Log
        self._log_our_action(gift, tactic, reason, points)

        # Display
        tactic_emoji = {
            PressureTactic.SHOW_STRENGTH: "💪",
            PressureTactic.COUNTER_STRIKE: "🥊",
            PressureTactic.BOOST_MAXIMIZE: "🚀",
            PressureTactic.SNIPE_OFFENSIVE: "🎯",
            PressureTactic.SNIPE_DEFENSIVE: "🛡️",
            PressureTactic.PRESSURE_TEST: "🔍",
            PressureTactic.TEMPO_CONTROL: "⚡",
            PressureTactic.BAIT: "🎣",
        }.get(tactic, "🎁")

        boost_info = ""
        if boost and boost.is_active:
            boost_info = f" [x{boost.multiplier}]"

        print(f"{tactic_emoji} [{tactic.value}] {gift['name']} "
              f"({gift['cost']:,} → {points:,} pts){boost_info}")
        print(f"   └─ {reason}")

    def _log_our_action(self, gift: Dict, tactic: PressureTactic,
                        reason: str, points: int):
        """Log our action."""
        self.action_log.append({
            "type": "ai",
            "time": time.time() - self.battle_start,
            "phase": self.engine.phase.value,
            "tactic": tactic.value,
            "gift": gift["name"],
            "cost": gift["cost"],
            "points": points,
            "reason": reason,
            "ai_score": self.ai_score,
            "opponent_score": self.opponent_score,
        })

    def _log_opponent_action(self, gift_name: str, points: int,
                              is_power_up: bool = False):
        """Log opponent action."""
        self.action_log.append({
            "type": "opponent",
            "time": time.time() - self.battle_start,
            "gift": gift_name,
            "points": points,
            "is_power_up": is_power_up,
            "ai_score": self.ai_score,
            "opponent_score": self.opponent_score
        })

        power_up_tag = " ⚡POWER-UP" if is_power_up else ""
        print(f"👤 Opponent: {gift_name} (+{points:,}){power_up_tag} "
              f"→ {self.opponent_score:,}")

    def _print_status(self):
        """Print current status."""
        status = self.engine.get_status()
        diff = status['score_diff']

        print(f"\n📊 {self.battle_duration - self.time_remaining}s | "
              f"Phase: {status['phase']}")
        print(f"   AI: {status['ai_score']:,} vs Live: {status['opponent_score']:,} "
              f"(diff: {diff:+,})")
        print(f"   Budget: {status['budget_remaining']:,} "
              f"({status['budget_pct']:.0f}%) | "
              f"Snipe reserve: {status['snipe_reserve']:,}")
        print(f"   Opponent: {status['opponent_state']}")

        if status['boost']:
            print(f"   🚀 BOOST x{status['boost']['multiplier']} "
                  f"({status['boost']['time_remaining']:.0f}s left)")

        print()

    def _print_summary(self):
        """Print battle summary."""
        diff = self.ai_score - self.opponent_score
        result = "WIN" if diff > 0 else "LOSE" if diff < 0 else "TIE"
        status = self.engine.get_status()

        print(f"\n{'='*70}")
        print(f"🏆 BATTLE COMPLETE - {result}")
        print(f"{'='*70}")
        print(f"Final Score: AI {self.ai_score:,} vs Live {self.opponent_score:,}")
        print(f"Margin: {abs(diff):,} points")
        print(f"Budget Used: {self.engine.state.budget_spent:,}/"
              f"{self.engine.total_budget:,} "
              f"({self.engine.state.budget_spent/self.engine.total_budget*100:.0f}%)")

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

        # Boost efficiency
        if self.engine.state.boost_history:
            print(f"\nBoost Performance:")
            for i, boost in enumerate(self.engine.state.boost_history, 1):
                eff = boost.points_earned / boost.coins_spent if boost.coins_spent > 0 else 0
                print(f"   Boost #{i} x{boost.multiplier}: "
                      f"{boost.coins_spent:,} coins → {boost.points_earned:,} pts "
                      f"(eff: {eff:.2f})")

        print(f"{'='*70}\n")

    # Manual controls for live battles
    def trigger_boost(self, multiplier: float, duration: int = 20):
        """Manually trigger boost detection."""
        self.engine.start_boost(multiplier, duration)
        print(f"\n🚀 BOOST ACTIVATED x{multiplier} ({duration}s)")

    def end_boost(self):
        """Manually end boost."""
        self.engine.end_boost()
        print(f"\n⏹️ Boost ended")

    def sync_score(self, opponent_score: int, time_left: Optional[int] = None):
        """Sync with live scores."""
        self.opponent_score = opponent_score
        self.engine.update_scores(self.ai_score, opponent_score)
        if time_left:
            self.time_remaining = time_left
            self.engine.update_time(time_left)
        print(f"🔄 Synced: Opponent {opponent_score:,}, Time {time_left}s")


async def main():
    parser = argparse.ArgumentParser(
        description="Strategic Pressure Battle"
    )
    parser.add_argument("streamer", help="Target streamer username")
    parser.add_argument("--budget", type=int, default=165000,
                        help="Total budget in coins")
    parser.add_argument("--duration", type=int, default=300,
                        help="Battle duration in seconds")
    parser.add_argument("--live-score", type=int, default=0,
                        help="Initial opponent score")
    parser.add_argument("--time-left", type=int, default=None,
                        help="Time remaining")
    parser.add_argument("--simulate", action="store_true",
                        help="Force simulation mode")

    args = parser.parse_args()

    engine = StrategicBattleEngine(
        target_streamer=args.streamer,
        total_budget=args.budget,
        battle_duration=args.duration,
        initial_opponent_score=args.live_score,
        time_remaining=args.time_left,
        simulate=args.simulate
    )

    try:
        await engine.run_battle()
    except KeyboardInterrupt:
        print("\n\n⏹️ Battle interrupted")
        engine._print_summary()


if __name__ == "__main__":
    asyncio.run(main())
