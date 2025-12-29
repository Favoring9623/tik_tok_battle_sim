#!/usr/bin/env python3
"""
Strategic Tournament Runner - Best of 3

Uses StrategicPressureEngine with:
- Boost window prioritization
- Power-up tracking
- Strategic 5-second snipe window
- Snipe reserve (15% per battle)
- Honor lap detection (2min58s)
"""

import argparse
import asyncio
import time
from typing import Optional, List, Dict
from dataclasses import dataclass, field

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


# Power-up detection
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


@dataclass
class BattleResult:
    """Result of a single battle."""
    battle_number: int
    ai_score: int
    opponent_score: int
    budget_used: int
    budget_allocated: int
    won: bool
    tactics_used: Dict[str, int] = field(default_factory=dict)
    opponent_final_state: str = "unknown"


@dataclass
class TournamentState:
    """State of the Best of 3 tournament."""
    battles_completed: int = 0
    ai_wins: int = 0
    opponent_wins: int = 0
    total_budget: int = 0
    budget_remaining: int = 0
    results: List[BattleResult] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return self.ai_wins >= 2 or self.opponent_wins >= 2

    @property
    def status_str(self) -> str:
        return f"AI {self.ai_wins} - {self.opponent_wins} Opponent"


class StrategicTournament:
    """
    Best of 3 tournament with strategic pressure tactics.

    Budget allocation adapts based on tournament state:
    - If ahead: can be more conservative
    - If behind: must be more aggressive
    - Must-win battles get more budget
    """

    BATTLE_DURATION = 300  # 5 minutes
    HONOR_LAP_DURATION = 178  # 2min58s

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 500000,
        simulate: bool = False
    ):
        self.target_streamer = target_streamer
        self.total_budget = total_budget
        self.simulate = simulate

        self.tournament = TournamentState(
            total_budget=total_budget,
            budget_remaining=total_budget
        )

        # Learned patterns across battles
        self.opponent_avg_gift_size: int = 0
        self.opponent_typical_state: OpponentState = OpponentState.PASSIVE

        # Gift catalog
        self.gifts = self._load_gifts()

    def _load_gifts(self) -> List[Dict]:
        """Load available gifts."""
        catalog = get_gift_catalog()
        return [
            {"name": g.name, "cost": g.coins, "points": g.points}
            for g in catalog.gifts
        ]

    def _calculate_battle_budget(self) -> int:
        """
        Calculate budget for next battle based on tournament state.

        Strategy:
        - Battle 1: ~35% (establish position)
        - Battle 2: ~35% or more if must-win
        - Battle 3: All remaining
        """
        remaining = self.tournament.budget_remaining
        battles_left = 3 - self.tournament.battles_completed

        if battles_left == 0:
            return 0

        if battles_left == 1:
            # Final battle - use everything
            return remaining

        # Calculate base allocation
        if self.tournament.battles_completed == 0:
            # First battle: 35%
            return int(remaining * 0.35)

        elif self.tournament.battles_completed == 1:
            # Second battle
            if self.tournament.ai_wins == 1:
                # Won first - can close it out, use 40%
                return int(remaining * 0.40)
            elif self.tournament.opponent_wins == 1:
                # Lost first - MUST win, use 50%
                return int(remaining * 0.50)
            else:
                # Tie (shouldn't happen in Bo3)
                return int(remaining * 0.45)

        return remaining // battles_left

    async def run_tournament(self):
        """Run the full Best of 3 tournament."""
        print(f"\n{'='*70}")
        print(f"🏆 STRATEGIC TOURNAMENT - BEST OF 3")
        print(f"{'='*70}")
        print(f"Opponent: @{self.target_streamer}")
        print(f"Total Budget: {self.total_budget:,} coins")
        print(f"Battle Duration: {self.BATTLE_DURATION}s")
        print(f"Honor Lap: {self.HONOR_LAP_DURATION}s (2min58s)")
        print(f"{'='*70}\n")

        while not self.tournament.is_complete:
            battle_num = self.tournament.battles_completed + 1
            battle_budget = self._calculate_battle_budget()

            # Must-win indicator
            must_win = (self.tournament.opponent_wins == 1 and
                        self.tournament.ai_wins == 0)

            print(f"\n{'='*70}")
            print(f"⚔️  BATTLE {battle_num}/3" + (" ⚠️ MUST WIN!" if must_win else ""))
            print(f"{'='*70}")
            print(f"Tournament: {self.tournament.status_str}")
            print(f"Battle Budget: {battle_budget:,} coins")
            print(f"Reserve: {self.tournament.budget_remaining - battle_budget:,} coins")
            print(f"{'='*70}\n")

            result = await self._run_single_battle(battle_num, battle_budget)
            self.tournament.results.append(result)
            self.tournament.battles_completed += 1
            self.tournament.budget_remaining -= result.budget_used

            if result.won:
                self.tournament.ai_wins += 1
                print(f"\n🎉 Battle {battle_num}: AI WINS!")
            else:
                self.tournament.opponent_wins += 1
                print(f"\n😔 Battle {battle_num}: Opponent wins")

            print(f"Score: {result.ai_score:,} vs {result.opponent_score:,}")
            print(f"Budget used: {result.budget_used:,} / {result.budget_allocated:,}")

            # Honor lap if tournament continues
            if not self.tournament.is_complete:
                await self._wait_honor_lap()

        self._print_tournament_summary()

    async def _run_single_battle(
        self,
        battle_number: int,
        budget: int
    ) -> BattleResult:
        """Run a single battle with strategic pressure."""

        # Initialize engine for this battle
        engine = StrategicPressureEngine(budget, self.BATTLE_DURATION)

        # Battle state
        ai_score = 0
        opponent_score = 0
        battle_start = time.time()
        last_action_time = 0
        min_action_interval = 2.0
        tactic_counts: Dict[str, int] = {}

        if not self.simulate and TIKTOK_AVAILABLE:
            client = TikTokLiveClient(unique_id=self.target_streamer)
            connected = False

            @client.on(ConnectEvent)
            async def on_connect(event):
                nonlocal connected
                connected = True
                print(f"✅ Connected to @{self.target_streamer}")

            @client.on(GiftEvent)
            async def on_gift(event):
                nonlocal opponent_score
                gift_name = event.gift.name
                if event.gift.streakable and not event.streaking:
                    points = event.gift.diamond_count * event.combo_count
                else:
                    points = event.gift.diamond_count

                is_power_up = gift_name in POWER_UP_GIFTS
                power_up_type = POWER_UP_GIFTS.get(gift_name)

                opponent_score += points
                engine.record_opponent_gift(points, gift_name, is_power_up, power_up_type)

                power_tag = " ⚡" if is_power_up else ""
                print(f"👤 {gift_name} (+{points:,}){power_tag} → {opponent_score:,}")

            try:
                asyncio.create_task(client.start())
                await asyncio.sleep(3)
                if not connected:
                    print("⚠️ Could not connect - simulation mode")
            except Exception as e:
                print(f"⚠️ Connection error: {e}")

        print(f"🎮 Battle {battle_number} started!\n")

        # Battle loop
        time_remaining = self.BATTLE_DURATION
        while time_remaining > 0:
            now = time.time()
            elapsed = now - battle_start
            time_remaining = max(0, self.BATTLE_DURATION - int(elapsed))

            # Simulate opponent in demo mode
            if self.simulate or not TIKTOK_AVAILABLE:
                import random
                if random.random() < 0.12:
                    phase = engine.phase
                    if phase == BattlePhase.SNIPE_WINDOW:
                        points = random.choice([5000, 10000, 20000]) if random.random() < 0.3 else random.choice([1000, 2000])
                    elif phase == BattlePhase.ENDGAME:
                        points = random.choice([2000, 5000, 10000])
                    else:
                        points = random.choice([500, 1000, 2000, 5000])

                    opponent_score += points
                    engine.record_opponent_gift(points, "simulated")
                    print(f"👤 simulated (+{points:,}) → {opponent_score:,}")

            # Update engine
            engine.update_time(time_remaining)
            engine.update_scores(ai_score, opponent_score)

            phase = engine.phase

            # Check action timing (faster in snipe window)
            if now - last_action_time < min_action_interval:
                if phase != BattlePhase.SNIPE_WINDOW:
                    await asyncio.sleep(0.5)
                    continue

            # Get decision
            tactic, target_spend, reason = engine.decide_action()

            # Execute
            if tactic not in (PressureTactic.PATIENCE, PressureTactic.RESERVE):
                gift = engine.get_gift_for_tactic(tactic, target_spend, self.gifts)
                if gift:
                    points = gift["points"]
                    boost = engine.state.current_boost
                    if boost and boost.is_active:
                        points = int(points * boost.multiplier)

                    ai_score += points
                    engine.record_our_action(gift["cost"], points)
                    last_action_time = now

                    tactic_counts[tactic.value] = tactic_counts.get(tactic.value, 0) + 1

                    emoji = {
                        PressureTactic.SHOW_STRENGTH: "💪",
                        PressureTactic.COUNTER_STRIKE: "🥊",
                        PressureTactic.BOOST_MAXIMIZE: "🚀",
                        PressureTactic.SNIPE_OFFENSIVE: "🎯",
                        PressureTactic.SNIPE_DEFENSIVE: "🛡️",
                        PressureTactic.PRESSURE_TEST: "🔍",
                        PressureTactic.TEMPO_CONTROL: "⚡",
                    }.get(tactic, "🎁")

                    print(f"{emoji} [{tactic.value}] {gift['name']} "
                          f"({gift['cost']:,} → {points:,} pts)")
                    print(f"   └─ {reason}")

            # Status updates
            if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                diff = ai_score - opponent_score
                print(f"\n📊 {int(elapsed)}s | {phase.value}")
                print(f"   AI: {ai_score:,} vs Live: {opponent_score:,} (diff: {diff:+,})")
                print(f"   Budget: {engine.state.budget_remaining:,} "
                      f"({engine.state.budget_remaining/budget*100:.0f}%)\n")

            # Phase announcements
            if time_remaining == 60:
                print(f"\n⚠️  ENDGAME - 60 seconds!")
            elif time_remaining == 5:
                print(f"\n🎯 SNIPE WINDOW!")

            await asyncio.sleep(0.5)

        # Battle complete
        return BattleResult(
            battle_number=battle_number,
            ai_score=ai_score,
            opponent_score=opponent_score,
            budget_used=engine.state.budget_spent,
            budget_allocated=budget,
            won=ai_score > opponent_score,
            tactics_used=tactic_counts,
            opponent_final_state=engine.state.opponent_state.value
        )

    async def _wait_honor_lap(self):
        """Wait for honor lap between battles."""
        print(f"\n{'='*70}")
        print(f"🎖️  HONOR LAP - {self.HONOR_LAP_DURATION}s (2min58s)")
        print(f"{'='*70}")
        print(f"Tournament: {self.tournament.status_str}")
        print(f"Budget Remaining: {self.tournament.budget_remaining:,} coins")
        print()

        for remaining in range(self.HONOR_LAP_DURATION, 0, -1):
            if remaining % 30 == 0 or remaining <= 10:
                print(f"⏳ Next battle in {remaining}s...")
            await asyncio.sleep(1)

        print(f"\n🔔 Honor lap complete!\n")

    def _print_tournament_summary(self):
        """Print final tournament summary."""
        winner = "AI TEAM 🏆" if self.tournament.ai_wins >= 2 else "OPPONENT"

        print(f"\n{'='*70}")
        print(f"🏆 TOURNAMENT COMPLETE")
        print(f"{'='*70}")
        print(f"\nWINNER: {winner}")
        print(f"Final Score: {self.tournament.status_str}")

        print(f"\n📊 Battle Breakdown:")
        for result in self.tournament.results:
            status = "✅ WIN" if result.won else "❌ LOSS"
            margin = result.ai_score - result.opponent_score
            print(f"\n  Battle {result.battle_number}: {status}")
            print(f"    Score: {result.ai_score:,} vs {result.opponent_score:,} "
                  f"({margin:+,})")
            print(f"    Budget: {result.budget_used:,} / {result.budget_allocated:,} "
                  f"({result.budget_used/result.budget_allocated*100:.0f}%)")
            if result.tactics_used:
                top = sorted(result.tactics_used.items(), key=lambda x: -x[1])[:3]
                print(f"    Tactics: {', '.join(f'{t}({c})' for t, c in top)}")

        total_spent = sum(r.budget_used for r in self.tournament.results)
        print(f"\n💰 Budget Summary:")
        print(f"    Total: {self.total_budget:,}")
        print(f"    Spent: {total_spent:,} ({total_spent/self.total_budget*100:.0f}%)")
        print(f"    Remaining: {self.tournament.budget_remaining:,}")

        print(f"{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Strategic Best of 3 Tournament"
    )
    parser.add_argument("streamer", help="Target streamer username")
    parser.add_argument("--budget", type=int, default=500000,
                        help="Total tournament budget")
    parser.add_argument("--simulate", action="store_true",
                        help="Force simulation mode")

    args = parser.parse_args()

    tournament = StrategicTournament(
        target_streamer=args.streamer,
        total_budget=args.budget,
        simulate=args.simulate
    )

    try:
        await tournament.run_tournament()
    except KeyboardInterrupt:
        print("\n\n⏹️ Tournament interrupted")
        tournament._print_tournament_summary()


if __name__ == "__main__":
    asyncio.run(main())
