"""
Tournament Manager for Best of 3 TikTok Battles
================================================

Manages budget allocation across a multi-battle tournament.
Features:
- Best of 3 format with strategic budget distribution
- Honor lap detection (2min58s between battles)
- Boost score tracking and learning
- Dynamic budget reallocation based on tournament state
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TournamentState(Enum):
    """Tournament state machine."""
    NOT_STARTED = "not_started"
    BATTLE_IN_PROGRESS = "battle_in_progress"
    HONOR_LAP = "honor_lap"           # 2min58s between battles
    WAITING_NEXT_BATTLE = "waiting"
    COMPLETED = "completed"


class BattleResult(Enum):
    """Result of a single battle."""
    WIN = "win"
    LOSS = "loss"
    TIE = "tie"


@dataclass
class BoostStats:
    """Statistics for a boost window."""
    boost_number: int  # 1 or 2
    multiplier: float
    coins_spent: int = 0
    points_earned: int = 0
    effective_points: int = 0  # points * multiplier
    duration_seconds: int = 0
    threshold_reached: bool = False

    @property
    def efficiency(self) -> float:
        """Points per coin during boost."""
        if self.coins_spent == 0:
            return 0.0
        return self.effective_points / self.coins_spent

    @property
    def roi(self) -> float:
        """Return on investment (effective vs base points)."""
        if self.points_earned == 0:
            return 0.0
        return self.effective_points / self.points_earned


@dataclass
class BattleStats:
    """Complete statistics for a single battle."""
    battle_number: int
    result: Optional[BattleResult] = None
    ai_score: int = 0
    opponent_score: int = 0
    coins_spent: int = 0
    duration_seconds: int = 300

    # Boost tracking
    boost1_stats: Optional[BoostStats] = None
    boost2_stats: Optional[BoostStats] = None

    # Phase breakdown
    phase_spending: Dict[str, int] = field(default_factory=dict)
    phase_points: Dict[str, int] = field(default_factory=dict)

    @property
    def margin(self) -> int:
        """Score margin (positive = win)."""
        return self.ai_score - self.opponent_score

    @property
    def efficiency(self) -> float:
        """Overall points per coin."""
        if self.coins_spent == 0:
            return 0.0
        return self.ai_score / self.coins_spent

    def get_boost_total(self) -> Tuple[int, int]:
        """Get total (coins, effective_points) from boosts."""
        coins = 0
        points = 0
        if self.boost1_stats:
            coins += self.boost1_stats.coins_spent
            points += self.boost1_stats.effective_points
        if self.boost2_stats:
            coins += self.boost2_stats.coins_spent
            points += self.boost2_stats.effective_points
        return coins, points


@dataclass
class TournamentStats:
    """Complete tournament statistics."""
    total_budget: int
    battles: List[BattleStats] = field(default_factory=list)

    @property
    def wins(self) -> int:
        return sum(1 for b in self.battles if b.result == BattleResult.WIN)

    @property
    def losses(self) -> int:
        return sum(1 for b in self.battles if b.result == BattleResult.LOSS)

    @property
    def coins_spent(self) -> int:
        return sum(b.coins_spent for b in self.battles)

    @property
    def coins_remaining(self) -> int:
        return self.total_budget - self.coins_spent

    @property
    def tournament_result(self) -> Optional[str]:
        if self.wins >= 2:
            return "WIN"
        elif self.losses >= 2:
            return "LOSS"
        return None

    def get_boost_learning(self) -> Dict:
        """Aggregate boost performance across battles."""
        boost1_data = []
        boost2_data = []

        for battle in self.battles:
            if battle.boost1_stats:
                boost1_data.append(battle.boost1_stats)
            if battle.boost2_stats:
                boost2_data.append(battle.boost2_stats)

        return {
            'boost1': {
                'count': len(boost1_data),
                'avg_multiplier': sum(b.multiplier for b in boost1_data) / len(boost1_data) if boost1_data else 0,
                'avg_efficiency': sum(b.efficiency for b in boost1_data) / len(boost1_data) if boost1_data else 0,
                'total_effective_points': sum(b.effective_points for b in boost1_data),
            },
            'boost2': {
                'count': len(boost2_data),
                'avg_multiplier': sum(b.multiplier for b in boost2_data) / len(boost2_data) if boost2_data else 0,
                'avg_efficiency': sum(b.efficiency for b in boost2_data) / len(boost2_data) if boost2_data else 0,
                'total_effective_points': sum(b.effective_points for b in boost2_data),
                'threshold_success_rate': sum(1 for b in boost2_data if b.threshold_reached) / len(boost2_data) if boost2_data else 0,
            }
        }


class TournamentManager:
    """
    Manages a Best of 3 tournament with strategic budget allocation.

    Features:
    - Budget distribution across 3 potential battles
    - Honor lap (2min58s) detection between battles
    - Boost score tracking for learning
    - Dynamic reallocation based on tournament state
    """

    # Honor lap duration (2 minutes 58 seconds)
    HONOR_LAP_DURATION = 178  # seconds
    HONOR_LAP_TOLERANCE = 10  # seconds tolerance

    # Battle duration
    BATTLE_DURATION = 300  # 5 minutes

    # Budget allocation strategies
    ALLOCATION_STRATEGIES = {
        # Even distribution
        'balanced': [0.34, 0.33, 0.33],

        # Front-loaded (win early)
        'aggressive': [0.45, 0.35, 0.20],

        # Back-loaded (save for later)
        'conservative': [0.25, 0.35, 0.40],

        # Adaptive based on results
        'adaptive': [0.33, 0.33, 0.34],  # Adjusted dynamically
    }

    def __init__(
        self,
        total_budget: int = 500000,
        strategy: str = "adaptive",
        battle_duration: int = 300
    ):
        self.total_budget = total_budget
        self.strategy = strategy
        self.battle_duration = battle_duration

        # Tournament state
        self.state = TournamentState.NOT_STARTED
        self.current_battle = 0  # 0 = not started, 1-3 = battle number
        self.stats = TournamentStats(total_budget=total_budget)

        # Budget tracking
        self.budget_per_battle = self._calculate_initial_allocation()
        self.spent_this_battle = 0

        # Timing
        self.tournament_start_time: Optional[float] = None
        self.battle_start_time: Optional[float] = None
        self.battle_end_time: Optional[float] = None
        self.honor_lap_start_time: Optional[float] = None

        # Current battle tracking
        self.current_battle_stats: Optional[BattleStats] = None
        self.current_boost_stats: Optional[BoostStats] = None

        # Learning
        self.boost_history: List[BoostStats] = []

        logger.info(f"[TournamentManager] Initialized: {total_budget:,} coins, {strategy} strategy")
        logger.info(f"[TournamentManager] Initial allocation: {[f'{b:,}' for b in self.budget_per_battle]}")

    def _calculate_initial_allocation(self) -> List[int]:
        """Calculate initial budget allocation per battle."""
        percentages = self.ALLOCATION_STRATEGIES.get(self.strategy, [0.34, 0.33, 0.33])
        return [int(self.total_budget * p) for p in percentages]

    def start_tournament(self):
        """Start the tournament."""
        self.state = TournamentState.NOT_STARTED
        self.tournament_start_time = time.time()
        self.current_battle = 0
        self.stats = TournamentStats(total_budget=self.total_budget)

        print(f"\n{'='*60}")
        print(f"{'TOURNAMENT START - BEST OF 3':^60}")
        print(f"{'='*60}")
        print(f"  Total Budget: {self.total_budget:,} coins")
        print(f"  Strategy: {self.strategy}")
        print(f"  Allocation: Battle 1: {self.budget_per_battle[0]:,} | "
              f"Battle 2: {self.budget_per_battle[1]:,} | "
              f"Battle 3: {self.budget_per_battle[2]:,}")
        print(f"{'='*60}\n")

    def start_battle(self) -> int:
        """
        Start a new battle in the tournament.
        Returns the budget allocated for this battle.
        """
        self.current_battle += 1
        self.state = TournamentState.BATTLE_IN_PROGRESS
        self.battle_start_time = time.time()
        self.spent_this_battle = 0

        # Get budget for this battle
        battle_budget = self.get_battle_budget()

        # Initialize battle stats
        self.current_battle_stats = BattleStats(
            battle_number=self.current_battle,
            duration_seconds=self.battle_duration
        )

        print(f"\n{'─'*60}")
        print(f"  BATTLE {self.current_battle}/3 STARTING")
        print(f"  Budget: {battle_budget:,} coins")
        print(f"  Tournament Score: {self.stats.wins}-{self.stats.losses}")
        print(f"{'─'*60}\n")

        return battle_budget

    def get_battle_budget(self) -> int:
        """Get the budget for the current battle."""
        if self.current_battle < 1 or self.current_battle > 3:
            return 0

        # Base allocation
        base_budget = self.budget_per_battle[self.current_battle - 1]

        # Adaptive reallocation based on tournament state
        if self.strategy == "adaptive":
            base_budget = self._adapt_budget(base_budget)

        return base_budget

    def _adapt_budget(self, base_budget: int) -> int:
        """Dynamically adapt budget based on tournament state."""
        remaining = self.stats.coins_remaining

        if self.current_battle == 2:
            # Battle 2: If we won battle 1, can be more conservative
            # If we lost, need to be more aggressive
            if self.stats.wins == 1:
                # Leading 1-0, save some for potential battle 3
                return min(base_budget, int(remaining * 0.40))
            elif self.stats.losses == 1:
                # Down 0-1, must win this one
                return min(int(remaining * 0.60), remaining)

        elif self.current_battle == 3:
            # Battle 3: Use everything remaining
            return remaining

        return base_budget

    def get_remaining_budget(self) -> int:
        """Get remaining budget for current battle."""
        battle_budget = self.get_battle_budget()
        return max(0, battle_budget - self.spent_this_battle)

    def record_spend(self, coins: int, points: int, phase: str, in_boost: bool = False, multiplier: float = 1.0):
        """Record spending during the current battle."""
        self.spent_this_battle += coins

        if self.current_battle_stats:
            self.current_battle_stats.coins_spent += coins
            self.current_battle_stats.ai_score += points

            # Phase tracking
            if phase not in self.current_battle_stats.phase_spending:
                self.current_battle_stats.phase_spending[phase] = 0
                self.current_battle_stats.phase_points[phase] = 0
            self.current_battle_stats.phase_spending[phase] += coins
            self.current_battle_stats.phase_points[phase] += points

        # Boost tracking
        if in_boost and self.current_boost_stats:
            self.current_boost_stats.coins_spent += coins
            self.current_boost_stats.points_earned += points
            self.current_boost_stats.effective_points += int(points * multiplier)

    def start_boost(self, boost_number: int, multiplier: float, duration: int = 20):
        """Start tracking a boost window."""
        self.current_boost_stats = BoostStats(
            boost_number=boost_number,
            multiplier=multiplier,
            duration_seconds=duration
        )

        print(f"\n📊 [Tournament] Tracking Boost #{boost_number} (x{multiplier})")

    def end_boost(self, threshold_reached: bool = False):
        """End tracking the current boost window."""
        if self.current_boost_stats:
            self.current_boost_stats.threshold_reached = threshold_reached

            # Store in battle stats
            if self.current_battle_stats:
                if self.current_boost_stats.boost_number == 1:
                    self.current_battle_stats.boost1_stats = self.current_boost_stats
                else:
                    self.current_battle_stats.boost2_stats = self.current_boost_stats

            # Add to history for learning
            self.boost_history.append(self.current_boost_stats)

            print(f"📊 [Tournament] Boost #{self.current_boost_stats.boost_number} ended:")
            print(f"   Coins: {self.current_boost_stats.coins_spent:,}")
            print(f"   Points: {self.current_boost_stats.points_earned:,} (effective: {self.current_boost_stats.effective_points:,})")
            print(f"   Efficiency: {self.current_boost_stats.efficiency:.2f} pts/coin")

            self.current_boost_stats = None

    def end_battle(self, ai_score: int, opponent_score: int) -> BattleResult:
        """
        End the current battle and record results.
        Returns the battle result.
        """
        self.battle_end_time = time.time()

        # Determine result
        if ai_score > opponent_score:
            result = BattleResult.WIN
        elif opponent_score > ai_score:
            result = BattleResult.LOSS
        else:
            result = BattleResult.TIE

        # Update battle stats
        if self.current_battle_stats:
            self.current_battle_stats.result = result
            self.current_battle_stats.ai_score = ai_score
            self.current_battle_stats.opponent_score = opponent_score
            self.stats.battles.append(self.current_battle_stats)

        # Check if tournament is over
        if self.stats.wins >= 2:
            self.state = TournamentState.COMPLETED
            print(f"\n🏆 TOURNAMENT WON! ({self.stats.wins}-{self.stats.losses})")
        elif self.stats.losses >= 2:
            self.state = TournamentState.COMPLETED
            print(f"\n💔 TOURNAMENT LOST ({self.stats.wins}-{self.stats.losses})")
        else:
            # More battles to come - enter honor lap
            self.state = TournamentState.HONOR_LAP
            self.honor_lap_start_time = time.time()
            print(f"\n⏱️  HONOR LAP - {self.HONOR_LAP_DURATION}s until next battle")

        self._print_battle_summary(result, ai_score, opponent_score)

        return result

    def _print_battle_summary(self, result: BattleResult, ai_score: int, opponent_score: int):
        """Print battle summary with boost analysis."""
        print(f"\n{'─'*60}")
        print(f"  BATTLE {self.current_battle} COMPLETE: {result.value.upper()}")
        print(f"{'─'*60}")
        print(f"  Score: AI {ai_score:,} vs Opponent {opponent_score:,}")
        print(f"  Margin: {ai_score - opponent_score:+,}")
        print(f"  Coins Spent: {self.spent_this_battle:,}")

        if self.current_battle_stats:
            # Boost breakdown
            boost_coins, boost_points = self.current_battle_stats.get_boost_total()
            if boost_coins > 0:
                print(f"\n  📊 Boost Performance:")
                if self.current_battle_stats.boost1_stats:
                    b1 = self.current_battle_stats.boost1_stats
                    print(f"     Boost #1 (x{b1.multiplier}): {b1.coins_spent:,} coins → {b1.effective_points:,} pts ({b1.efficiency:.2f} eff)")
                if self.current_battle_stats.boost2_stats:
                    b2 = self.current_battle_stats.boost2_stats
                    qualified = "✅" if b2.threshold_reached else "❌"
                    print(f"     Boost #2 (x{b2.multiplier}): {b2.coins_spent:,} coins → {b2.effective_points:,} pts ({b2.efficiency:.2f} eff) {qualified}")

        print(f"\n  Tournament: {self.stats.wins}-{self.stats.losses}")
        print(f"  Budget Remaining: {self.stats.coins_remaining:,}/{self.total_budget:,}")
        print(f"{'─'*60}\n")

    def check_honor_lap_complete(self) -> bool:
        """
        Check if the honor lap period is complete.
        Returns True if ready for next battle.
        """
        if self.state != TournamentState.HONOR_LAP:
            return False

        if self.honor_lap_start_time is None:
            return False

        elapsed = time.time() - self.honor_lap_start_time

        # Check if honor lap duration has passed
        if elapsed >= self.HONOR_LAP_DURATION - self.HONOR_LAP_TOLERANCE:
            print(f"\n⏱️  Honor lap complete ({elapsed:.0f}s elapsed)")
            self.state = TournamentState.WAITING_NEXT_BATTLE
            return True

        return False

    def detect_honor_lap_from_gifts(self, gift_rate: float, last_boost_time: float) -> bool:
        """
        Detect honor lap based on gift patterns.

        During honor lap:
        - Gift rate typically drops significantly
        - No boost announcements
        - Duration is approximately 2min58s

        Args:
            gift_rate: Current gifts per minute
            last_boost_time: Time since last boost ended

        Returns:
            True if likely in honor lap
        """
        # Low gift rate suggests honor lap
        if gift_rate < 5:  # Less than 5 gifts per minute
            # Check if it's been roughly the right duration since battle end
            if self.battle_end_time:
                elapsed = time.time() - self.battle_end_time
                if 30 < elapsed < self.HONOR_LAP_DURATION + 30:
                    return True

        return False

    def detect_new_battle_start(self, boost_announced: bool, gift_spike: bool) -> bool:
        """
        Detect when a new battle is starting.

        Signs of new battle:
        - Boost #1 announcement
        - Sudden spike in gift activity
        - ~3 minutes after previous battle ended

        Returns:
            True if new battle is starting
        """
        if self.state == TournamentState.COMPLETED:
            return False

        # Clear sign: Boost #1 announcement
        if boost_announced:
            return True

        # Gift spike after honor lap period
        if gift_spike and self.battle_end_time:
            elapsed = time.time() - self.battle_end_time
            if elapsed >= self.HONOR_LAP_DURATION - self.HONOR_LAP_TOLERANCE:
                return True

        return False

    def is_tournament_complete(self) -> bool:
        """Check if tournament is complete."""
        return self.state == TournamentState.COMPLETED

    def get_tournament_summary(self) -> Dict:
        """Get complete tournament summary with boost learning data."""
        return {
            'result': self.stats.tournament_result,
            'wins': self.stats.wins,
            'losses': self.stats.losses,
            'total_budget': self.total_budget,
            'coins_spent': self.stats.coins_spent,
            'coins_remaining': self.stats.coins_remaining,
            'battles': [
                {
                    'number': b.battle_number,
                    'result': b.result.value if b.result else None,
                    'ai_score': b.ai_score,
                    'opponent_score': b.opponent_score,
                    'margin': b.margin,
                    'coins_spent': b.coins_spent,
                    'efficiency': b.efficiency,
                }
                for b in self.stats.battles
            ],
            'boost_learning': self.stats.get_boost_learning(),
        }

    def get_optimal_boost_allocation(self) -> Dict[int, float]:
        """
        Based on historical boost performance, recommend optimal allocation.
        Returns recommended percentage of battle budget per boost.
        """
        learning = self.stats.get_boost_learning()

        # Default allocation
        default = {1: 0.35, 2: 0.45}  # 35% for boost 1, 45% for boost 2

        if not self.boost_history:
            return default

        # Calculate weighted allocation based on efficiency
        boost1_eff = learning['boost1']['avg_efficiency']
        boost2_eff = learning['boost2']['avg_efficiency']

        if boost1_eff + boost2_eff == 0:
            return default

        # Weight by efficiency
        total_eff = boost1_eff + boost2_eff

        return {
            1: max(0.25, min(0.50, boost1_eff / total_eff * 0.80)),
            2: max(0.30, min(0.55, boost2_eff / total_eff * 0.80)),
        }


# Convenience function
def create_tournament_manager(
    total_budget: int = 500000,
    strategy: str = "adaptive"
) -> TournamentManager:
    """Create a tournament manager with the given settings."""
    return TournamentManager(
        total_budget=total_budget,
        strategy=strategy
    )


if __name__ == "__main__":
    # Demo
    tm = create_tournament_manager(500000, "adaptive")
    tm.start_tournament()

    # Simulate Battle 1
    budget1 = tm.start_battle()
    print(f"Battle 1 budget: {budget1:,}")

    tm.start_boost(1, 3.0)
    tm.record_spend(30000, 30000, "boost_1", in_boost=True, multiplier=3.0)
    tm.end_boost()

    tm.start_boost(2, 2.0)
    tm.record_spend(20000, 20000, "boost_2", in_boost=True, multiplier=2.0)
    tm.end_boost(threshold_reached=True)

    result1 = tm.end_battle(ai_score=150000, opponent_score=50000)

    # Check honor lap
    print(f"\nIn honor lap: {tm.state == TournamentState.HONOR_LAP}")

    # Summary
    print("\nTournament Summary:")
    print(tm.get_tournament_summary())
