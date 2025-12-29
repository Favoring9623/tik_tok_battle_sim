#!/usr/bin/env python3
"""
Pressure-Based Tournament Runner

Best of 3 tournament using psychological warfare tactics.
Dynamic budget allocation based on opponent behavior, not fixed phases.
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field

try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import GiftEvent, ConnectEvent, DisconnectEvent
    TIKTOK_AVAILABLE = True
except ImportError:
    TIKTOK_AVAILABLE = False

from core.pressure_engine import PressureEngine, PressureTactic, OpponentState
from core.gift_catalog import get_gift_catalog


@dataclass
class BattleResult:
    """Result of a single battle."""
    battle_number: int
    ai_score: int
    opponent_score: int
    budget_used: int
    budget_remaining: int
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
    def leader(self) -> str:
        if self.ai_wins > self.opponent_wins:
            return "AI"
        elif self.opponent_wins > self.ai_wins:
            return "Opponent"
        return "Tied"


class PressureTournament:
    """
    Best of 3 tournament using pressure tactics.

    Budget allocation is dynamic based on:
    - Current tournament standing
    - Opponent behavior patterns learned from previous battles
    - Time pressure
    """

    BATTLE_DURATION = 300  # 5 minutes
    HONOR_LAP_DURATION = 178  # 2min58s

    def __init__(
        self,
        target_streamer: str,
        total_budget: int = 500000
    ):
        self.target_streamer = target_streamer
        self.total_budget = total_budget

        # Tournament state
        self.tournament = TournamentState(
            total_budget=total_budget,
            budget_remaining=total_budget
        )

        # Learned opponent patterns (persists across battles)
        self.opponent_avg_reaction_time: float = 3.0
        self.opponent_typical_state: OpponentState = OpponentState.PASSIVE
        self.opponent_endgame_aggression: float = 0.5

        # Gift catalog
        self.gifts = self._load_gifts()

    def _load_gifts(self) -> List[Dict]:
        """Load available gifts from catalog."""
        catalog = get_gift_catalog()
        return [
            {"name": g.name, "cost": g.coins, "points": g.points}
            for g in catalog.gifts
        ]

    def _calculate_battle_budget(self) -> int:
        """
        Calculate budget for next battle based on tournament state.

        NOT a fixed allocation - adapts to situation.
        """
        remaining = self.tournament.budget_remaining
        battles_left = 3 - self.tournament.battles_completed
        battles_needed_to_win = 2 - self.tournament.ai_wins

        if battles_left == 0:
            return 0

        # Base allocation
        base = remaining // battles_left

        # Adjustments based on tournament state
        if self.tournament.ai_wins == 1:
            # One win away - can be more aggressive
            if battles_left == 2:
                # Battle 2 after winning battle 1 - push to close
                return int(remaining * 0.55)
            else:
                # Battle 3 - use what we have
                return remaining
        elif self.tournament.opponent_wins == 1:
            # Must win this battle
            if battles_left == 2:
                # Can't afford to lose again - aggressive
                return int(remaining * 0.55)
            else:
                # Final battle - all in
                return remaining

        # Even or first battle - balanced approach
        return base

    def _learn_from_battle(self, pressure: PressureEngine, result: BattleResult):
        """Learn from battle for future reference."""
        state = pressure.state

        # Update reaction time estimate
        if state.opponent_reaction_time > 0:
            self.opponent_avg_reaction_time = (
                self.opponent_avg_reaction_time * 0.6 +
                state.opponent_reaction_time * 0.4
            )

        # Track typical opponent behavior
        self.opponent_typical_state = state.opponent_state

        # Track endgame aggression
        # (Did they spend heavily in final minute?)
        late_actions = [a for a in pressure.state.opponent_actions
                        if hasattr(a, 'timestamp')]
        if late_actions:
            # Simple heuristic: higher avg gift in last 60s = aggressive
            self.opponent_endgame_aggression = min(1.0,
                state.opponent_avg_gift_size / 10000)

    async def run_tournament(self):
        """Run the full Best of 3 tournament."""
        print(f"\n{'='*70}")
        print(f"🏆 PRESSURE TOURNAMENT - BEST OF 3")
        print(f"{'='*70}")
        print(f"Opponent: @{self.target_streamer}")
        print(f"Total Budget: {self.total_budget:,} coins")
        print(f"{'='*70}\n")

        while not self.tournament.is_complete:
            battle_num = self.tournament.battles_completed + 1
            battle_budget = self._calculate_battle_budget()

            print(f"\n{'='*70}")
            print(f"⚔️  BATTLE {battle_num}/3")
            print(f"{'='*70}")
            print(f"Tournament: AI {self.tournament.ai_wins} - "
                  f"{self.tournament.opponent_wins} Opponent")
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
            print(f"Budget used: {result.budget_used:,} coins")

            # Wait for honor lap if tournament continues
            if not self.tournament.is_complete:
                await self._wait_honor_lap()

        self._print_tournament_summary()

    async def _run_single_battle(
        self,
        battle_number: int,
        budget: int
    ) -> BattleResult:
        """Run a single battle with pressure tactics."""

        # Initialize pressure engine for this battle
        pressure = PressureEngine(budget)

        # Apply learned patterns
        pressure.state.opponent_reaction_time = self.opponent_avg_reaction_time

        # Battle state
        ai_score = 0
        opponent_score = 0
        battle_start = time.time()
        last_action_time = 0
        min_action_interval = 2.0
        action_log = []

        if TIKTOK_AVAILABLE:
            client = TikTokLiveClient(unique_id=self.target_streamer)

            @client.on(GiftEvent)
            async def on_gift(event):
                nonlocal opponent_score
                if event.gift.streakable and not event.streaking:
                    points = event.gift.diamond_count * event.combo_count
                else:
                    points = event.gift.diamond_count

                opponent_score += points
                pressure.record_opponent_action(points)
                print(f"👤 Opponent: {event.gift.name} (+{points:,}) "
                      f"→ {opponent_score:,}")

            try:
                await asyncio.wait_for(client.start(), timeout=10)
                print(f"✅ Connected to @{self.target_streamer}")
            except Exception as e:
                print(f"⚠️ Connection failed, running simulation: {e}")
                TIKTOK_AVAILABLE_LOCAL = False
        else:
            TIKTOK_AVAILABLE_LOCAL = False

        print(f"\n🎮 Battle {battle_number} started!")
        print(f"Budget: {budget:,} coins\n")

        # Battle loop
        time_remaining = self.BATTLE_DURATION
        while time_remaining > 0:
            now = time.time()
            elapsed = now - battle_start
            time_remaining = max(0, self.BATTLE_DURATION - int(elapsed))

            # Simulate opponent in demo mode
            if not TIKTOK_AVAILABLE:
                if elapsed % 8 < 0.5 and elapsed > 5:
                    import random
                    if random.random() < 0.3:
                        points = random.choice([500, 1000, 2000, 5000])
                        opponent_score += points
                        pressure.record_opponent_action(points)
                        print(f"👤 Opponent: simulated (+{points:,}) "
                              f"→ {opponent_score:,}")

            # Update pressure engine
            pressure.update_scores(ai_score, opponent_score, time_remaining)

            # Decide action
            if now - last_action_time >= min_action_interval:
                tactic, target_spend = pressure.decide_tactic()

                if tactic != PressureTactic.PATIENCE:
                    gift = pressure.get_gift_recommendation(self.gifts)
                    if gift:
                        # Send gift
                        points = gift["points"]
                        ai_score += points
                        pressure.record_our_action(points, gift["cost"])
                        last_action_time = now

                        # Track tactic usage
                        t_name = tactic.value
                        action_log.append(t_name)

                        emoji = {
                            PressureTactic.SHOW_STRENGTH: "💪",
                            PressureTactic.PROBE: "🔍",
                            PressureTactic.TEMPO_BURST: "⚡",
                            PressureTactic.COUNTER_PUNCH: "🥊",
                            PressureTactic.BAIT: "🎣",
                            PressureTactic.FINISH: "🏁"
                        }.get(tactic, "🎁")

                        print(f"{emoji} [{tactic.value}] {gift['name']} "
                              f"({gift['cost']:,} → {points:,} pts) "
                              f"| AI: {ai_score:,} vs {opponent_score:,}")

            # Status update every 30s
            if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                diff = ai_score - opponent_score
                print(f"\n📊 {int(elapsed)}s | AI: {ai_score:,} vs {opponent_score:,} "
                      f"(diff: {diff:+,}) | "
                      f"Budget: {pressure.state.budget_remaining:,}\n")

            await asyncio.sleep(0.5)

        if TIKTOK_AVAILABLE:
            await client.stop()

        # Learn from this battle
        tactic_counts = {}
        for t in action_log:
            tactic_counts[t] = tactic_counts.get(t, 0) + 1

        result = BattleResult(
            battle_number=battle_number,
            ai_score=ai_score,
            opponent_score=opponent_score,
            budget_used=pressure.state.budget_spent,
            budget_remaining=pressure.state.budget_remaining,
            won=ai_score > opponent_score,
            tactics_used=tactic_counts,
            opponent_final_state=pressure.state.opponent_state.value
        )

        self._learn_from_battle(pressure, result)
        return result

    async def _wait_honor_lap(self):
        """Wait for honor lap between battles."""
        print(f"\n{'='*70}")
        print(f"🎖️  HONOR LAP - {self.HONOR_LAP_DURATION}s")
        print(f"{'='*70}")
        print(f"Tournament Standing: AI {self.tournament.ai_wins} - "
              f"{self.tournament.opponent_wins} Opponent")
        print(f"Budget Remaining: {self.tournament.budget_remaining:,} coins")
        print()

        for remaining in range(self.HONOR_LAP_DURATION, 0, -1):
            if remaining % 30 == 0 or remaining <= 10:
                print(f"⏳ Next battle in {remaining}s...")
            await asyncio.sleep(1)

        print(f"\n🔔 Honor lap complete - starting next battle!\n")

    def _print_tournament_summary(self):
        """Print final tournament summary."""
        winner = "AI TEAM" if self.tournament.ai_wins >= 2 else "OPPONENT"

        print(f"\n{'='*70}")
        print(f"🏆 TOURNAMENT COMPLETE")
        print(f"{'='*70}")
        print(f"\nWINNER: {winner}")
        print(f"\nFinal Score: AI {self.tournament.ai_wins} - "
              f"{self.tournament.opponent_wins} Opponent")

        print(f"\n📊 Battle Breakdown:")
        for result in self.tournament.results:
            status = "✅ WIN" if result.won else "❌ LOSS"
            print(f"\n  Battle {result.battle_number}: {status}")
            print(f"    Score: {result.ai_score:,} vs {result.opponent_score:,}")
            print(f"    Budget: {result.budget_used:,} coins")
            print(f"    Opponent state: {result.opponent_final_state}")
            if result.tactics_used:
                top_tactics = sorted(result.tactics_used.items(),
                                     key=lambda x: -x[1])[:3]
                print(f"    Top tactics: {', '.join(f'{t}({c})' for t, c in top_tactics)}")

        total_spent = sum(r.budget_used for r in self.tournament.results)
        print(f"\n💰 Budget Summary:")
        print(f"    Total: {self.total_budget:,} coins")
        print(f"    Spent: {total_spent:,} coins ({total_spent/self.total_budget*100:.0f}%)")
        print(f"    Remaining: {self.tournament.budget_remaining:,} coins")

        print(f"\n🧠 Learned Opponent Patterns:")
        print(f"    Avg reaction time: {self.opponent_avg_reaction_time:.1f}s")
        print(f"    Typical behavior: {self.opponent_typical_state.value}")
        print(f"    Endgame aggression: {self.opponent_endgame_aggression:.0%}")

        print(f"{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Pressure-based Best of 3 Tournament"
    )
    parser.add_argument("streamer", help="Target streamer username")
    parser.add_argument("--budget", type=int, default=500000,
                        help="Total tournament budget in coins")

    args = parser.parse_args()

    tournament = PressureTournament(
        target_streamer=args.streamer,
        total_budget=args.budget
    )

    try:
        await tournament.run_tournament()
    except KeyboardInterrupt:
        print("\n\n⏹️ Tournament interrupted")
        tournament._print_tournament_summary()


if __name__ == "__main__":
    asyncio.run(main())
