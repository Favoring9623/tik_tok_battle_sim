"""
Budget Manager for TikTok Battle Simulator
===========================================

Manages coin budget allocation and spending optimization for battles.

Key features:
- Budget allocation across battle phases (opening, mid-battle, boost, snipe)
- Gift cost optimization (best points-per-coin ratio)
- Spending tracking and alerts
- Dynamic reallocation based on battle state
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BattlePhase(Enum):
    """Battle phases for budget allocation."""
    OPENING = "opening"           # First 30 seconds
    MID_BATTLE = "mid_battle"     # 30s - 240s (before final minute)
    BOOST_1 = "boost_1"           # First boost window (~60s mark)
    BOOST_2 = "boost_2"           # Second boost window (~180s mark)
    SNIPE = "snipe"               # Final 30 seconds
    EMERGENCY = "emergency"       # When behind, need to catch up


@dataclass
class BudgetAllocation:
    """Budget allocation for a specific phase."""
    phase: BattlePhase
    coins_allocated: int
    coins_spent: int = 0
    priority: int = 1  # Higher = more important

    @property
    def coins_remaining(self) -> int:
        return max(0, self.coins_allocated - self.coins_spent)

    @property
    def utilization(self) -> float:
        if self.coins_allocated == 0:
            return 0.0
        return self.coins_spent / self.coins_allocated


@dataclass
class GiftEfficiency:
    """Gift efficiency metrics."""
    name: str
    coins: int
    points: int
    efficiency: float  # points per coin
    tier: str


class BudgetManager:
    """
    Manages battle budget allocation and spending optimization.

    Usage:
        budget = BudgetManager(total_coins=5000)
        budget.allocate_for_battle()

        # During battle
        gift = budget.get_optimal_gift(phase=BattlePhase.OPENING)
        budget.record_spend(gift.coins, BattlePhase.OPENING)
    """

    # Default allocation percentages by phase
    DEFAULT_ALLOCATION = {
        BattlePhase.OPENING: 0.10,      # 10% for opening (make presence known)
        BattlePhase.MID_BATTLE: 0.20,   # 20% for mid-battle maintenance
        BattlePhase.BOOST_1: 0.15,      # 15% for first boost
        BattlePhase.BOOST_2: 0.20,      # 20% for second boost
        BattlePhase.SNIPE: 0.30,        # 30% for final snipe (most critical)
        BattlePhase.EMERGENCY: 0.05,    # 5% reserve for emergencies
    }

    # Phase priorities (higher = more important to fund)
    PHASE_PRIORITY = {
        BattlePhase.SNIPE: 5,           # Most critical
        BattlePhase.BOOST_2: 4,
        BattlePhase.BOOST_1: 3,
        BattlePhase.OPENING: 2,
        BattlePhase.MID_BATTLE: 1,
        BattlePhase.EMERGENCY: 0,
    }

    def __init__(
        self,
        total_coins: int,
        allocation_strategy: str = "balanced",
        gift_catalog: Optional[Dict] = None
    ):
        """
        Initialize budget manager.

        Args:
            total_coins: Total coin budget for the battle
            allocation_strategy: "balanced", "aggressive", "conservative", "snipe_heavy"
            gift_catalog: Optional gift catalog for efficiency calculations
        """
        self.total_coins = total_coins
        self.remaining_coins = total_coins
        self.strategy = allocation_strategy

        # Phase allocations
        self.allocations: Dict[BattlePhase, BudgetAllocation] = {}

        # Spending history
        self.spending_history: List[Dict] = []
        self.total_spent = 0
        self.total_points_earned = 0

        # Gift efficiency cache
        self._gift_efficiency: List[GiftEfficiency] = []
        self._load_gift_efficiency(gift_catalog)

        # Battle state
        self.current_phase = BattlePhase.OPENING
        self.deficit = 0
        self.time_remaining = 300

        logger.info(f"[BudgetManager] Initialized with {total_coins:,} coins, strategy={allocation_strategy}")

    def _load_gift_efficiency(self, catalog: Optional[Dict] = None):
        """Load and calculate gift efficiency ratings."""
        # Default gift data if no catalog provided
        gifts = [
            # Budget tier (1-99 coins) - best efficiency
            ("Rose", 1, 1, "budget"),
            ("TikTok", 1, 1, "budget"),
            ("Heart", 1, 1, "budget"),
            ("Finger Heart", 5, 5, "budget"),
            ("Friendship Necklace", 10, 10, "budget"),
            ("Doughnut", 30, 30, "budget"),
            ("Paper Crane", 99, 99, "budget"),

            # Mid tier (100-999 coins)
            ("Confetti", 100, 100, "mid"),
            ("Hand Heart", 150, 150, "mid"),
            ("Shooting Star", 300, 300, "mid"),
            ("Sports Car", 500, 500, "mid"),
            ("Swan", 699, 699, "mid"),
            ("Diamond Ring", 999, 999, "mid"),

            # Premium tier (1000-9999 coins)
            ("Galaxy", 1000, 1000, "premium"),
            ("Fireworks", 1088, 1088, "premium"),
            ("Star of Red Carpet", 1999, 1999, "premium"),
            ("Whale Diving", 2150, 2150, "premium"),
            ("Private Jet", 3000, 3000, "premium"),
            ("Yacht", 5000, 5000, "premium"),
            ("Castle", 8000, 8000, "premium"),

            # Ultra premium (10000+ coins)
            ("Dragon Flame", 10000, 10000, "ultra"),
            ("Adam's Dream", 15000, 15000, "ultra"),
            ("Lion", 29999, 29999, "ultra"),
            ("TikTok Universe", 44999, 44999, "ultra"),
        ]

        self._gift_efficiency = []
        for name, coins, points, tier in gifts:
            efficiency = points / coins if coins > 0 else 0
            self._gift_efficiency.append(GiftEfficiency(
                name=name,
                coins=coins,
                points=points,
                efficiency=efficiency,
                tier=tier
            ))

        # Sort by efficiency (descending)
        self._gift_efficiency.sort(key=lambda g: g.efficiency, reverse=True)

    def allocate_for_battle(self, custom_allocation: Optional[Dict[BattlePhase, float]] = None):
        """
        Allocate budget across battle phases.

        Args:
            custom_allocation: Optional custom allocation percentages
        """
        allocation_pcts = custom_allocation or self._get_strategy_allocation()

        # Ensure percentages sum to 1.0
        total_pct = sum(allocation_pcts.values())
        if total_pct > 0:
            allocation_pcts = {k: v / total_pct for k, v in allocation_pcts.items()}

        self.allocations = {}
        for phase, pct in allocation_pcts.items():
            coins = int(self.total_coins * pct)
            self.allocations[phase] = BudgetAllocation(
                phase=phase,
                coins_allocated=coins,
                priority=self.PHASE_PRIORITY.get(phase, 1)
            )

        logger.info(f"[BudgetManager] Allocated budget: {self._format_allocations()}")

    def _get_strategy_allocation(self) -> Dict[BattlePhase, float]:
        """Get allocation percentages based on strategy."""
        if self.strategy == "aggressive":
            # Front-load spending to build early lead
            return {
                BattlePhase.OPENING: 0.25,
                BattlePhase.MID_BATTLE: 0.25,
                BattlePhase.BOOST_1: 0.15,
                BattlePhase.BOOST_2: 0.15,
                BattlePhase.SNIPE: 0.15,
                BattlePhase.EMERGENCY: 0.05,
            }
        elif self.strategy == "conservative":
            # Minimize mid-battle, save for critical moments
            return {
                BattlePhase.OPENING: 0.05,
                BattlePhase.MID_BATTLE: 0.10,
                BattlePhase.BOOST_1: 0.20,
                BattlePhase.BOOST_2: 0.25,
                BattlePhase.SNIPE: 0.35,
                BattlePhase.EMERGENCY: 0.05,
            }
        elif self.strategy == "snipe_heavy":
            # Maximum snipe allocation
            return {
                BattlePhase.OPENING: 0.05,
                BattlePhase.MID_BATTLE: 0.05,
                BattlePhase.BOOST_1: 0.10,
                BattlePhase.BOOST_2: 0.20,
                BattlePhase.SNIPE: 0.55,
                BattlePhase.EMERGENCY: 0.05,
            }
        else:  # balanced
            return self.DEFAULT_ALLOCATION.copy()

    def _format_allocations(self) -> str:
        """Format allocations for logging."""
        parts = []
        for phase, alloc in self.allocations.items():
            parts.append(f"{phase.value}={alloc.coins_allocated:,}")
        return ", ".join(parts)

    def get_phase_budget(self, phase: BattlePhase) -> int:
        """Get remaining budget for a specific phase."""
        if phase not in self.allocations:
            return 0
        return self.allocations[phase].coins_remaining

    def can_afford(self, coins: int, phase: Optional[BattlePhase] = None) -> bool:
        """Check if we can afford a gift."""
        if phase:
            return self.get_phase_budget(phase) >= coins
        return self.remaining_coins >= coins

    def record_spend(
        self,
        coins: int,
        points: int,
        phase: BattlePhase,
        gift_name: str = "",
        multiplier: float = 1.0
    ):
        """
        Record a spending transaction.

        Args:
            coins: Coins spent
            points: Battle points earned
            phase: Battle phase
            gift_name: Name of gift sent
            multiplier: Active multiplier (for tracking effective points)
        """
        effective_points = int(points * multiplier)

        # Update phase allocation
        if phase in self.allocations:
            self.allocations[phase].coins_spent += coins

        # Update totals
        self.total_spent += coins
        self.remaining_coins -= coins
        self.total_points_earned += effective_points

        # Record in history
        self.spending_history.append({
            'coins': coins,
            'points': points,
            'effective_points': effective_points,
            'phase': phase.value,
            'gift': gift_name,
            'multiplier': multiplier,
            'remaining': self.remaining_coins
        })

        logger.debug(f"[BudgetManager] Spent {coins} coins on {gift_name}, "
                    f"earned {effective_points} pts (x{multiplier}), "
                    f"remaining: {self.remaining_coins:,}")

    def get_optimal_gift(
        self,
        phase: BattlePhase,
        min_impact: int = 0,
        prefer_efficiency: bool = True
    ) -> Optional[GiftEfficiency]:
        """
        Get the optimal gift for current budget and phase.

        Args:
            phase: Current battle phase
            min_impact: Minimum points impact required
            prefer_efficiency: If True, prefer high efficiency; if False, prefer max impact

        Returns:
            Optimal gift or None if budget exhausted
        """
        budget = self.get_phase_budget(phase)

        if budget <= 0:
            # Try to borrow from lower priority phases
            budget = self._borrow_from_reserves(phase)
            if budget <= 0:
                return None

        # Filter affordable gifts
        affordable = [g for g in self._gift_efficiency if g.coins <= budget and g.points >= min_impact]

        if not affordable:
            return None

        if prefer_efficiency:
            # Return most efficient gift
            return affordable[0]  # Already sorted by efficiency
        else:
            # Return highest impact gift
            return max(affordable, key=lambda g: g.points)

    def get_gift_for_target_points(
        self,
        target_points: int,
        phase: BattlePhase,
        allow_overspend: bool = False
    ) -> Optional[GiftEfficiency]:
        """
        Get a gift that achieves target points most efficiently.

        Args:
            target_points: Points needed
            phase: Current phase
            allow_overspend: Allow spending more than phase budget

        Returns:
            Best gift for the target
        """
        budget = self.get_phase_budget(phase)
        if allow_overspend:
            budget = self.remaining_coins

        # Find gifts that meet or exceed target
        candidates = [
            g for g in self._gift_efficiency
            if g.coins <= budget and g.points >= target_points
        ]

        if candidates:
            # Return cheapest that meets target
            return min(candidates, key=lambda g: g.coins)

        # If no single gift meets target, return the biggest we can afford
        affordable = [g for g in self._gift_efficiency if g.coins <= budget]
        if affordable:
            return max(affordable, key=lambda g: g.points)

        return None

    def _borrow_from_reserves(self, requesting_phase: BattlePhase) -> int:
        """
        Borrow budget from lower-priority phases.

        Returns:
            Coins available to borrow
        """
        requesting_priority = self.PHASE_PRIORITY.get(requesting_phase, 0)
        borrowed = 0

        # Sort phases by priority (ascending) to borrow from lowest first
        sorted_phases = sorted(
            self.allocations.items(),
            key=lambda x: x[1].priority
        )

        for phase, alloc in sorted_phases:
            if phase == requesting_phase:
                continue
            if alloc.priority < requesting_priority and alloc.coins_remaining > 0:
                # Take up to 50% of remaining from lower priority phases
                take = alloc.coins_remaining // 2
                if take > 0:
                    borrowed += take
                    alloc.coins_spent += take  # Mark as "borrowed"
                    logger.debug(f"[BudgetManager] Borrowed {take} from {phase.value}")

        return borrowed

    def reallocate_unused(self):
        """
        Reallocate unused budget from completed phases to remaining phases.
        Called when transitioning between phases.
        """
        # Find phases with unused budget
        unused_total = 0
        completed_phases = []

        for phase, alloc in self.allocations.items():
            if self._is_phase_completed(phase):
                unused = alloc.coins_remaining
                if unused > 0:
                    unused_total += unused
                    completed_phases.append(phase)

        if unused_total <= 0:
            return

        # Redistribute to future phases by priority
        future_phases = [
            (p, a) for p, a in self.allocations.items()
            if not self._is_phase_completed(p)
        ]
        future_phases.sort(key=lambda x: x[1].priority, reverse=True)

        # Give more to higher priority phases
        total_priority = sum(a.priority for _, a in future_phases)
        if total_priority > 0:
            for phase, alloc in future_phases:
                share = int(unused_total * alloc.priority / total_priority)
                alloc.coins_allocated += share
                logger.debug(f"[BudgetManager] Reallocated {share} to {phase.value}")

        # Mark completed phases as fully spent
        for phase in completed_phases:
            self.allocations[phase].coins_spent = self.allocations[phase].coins_allocated

    def _is_phase_completed(self, phase: BattlePhase) -> bool:
        """Check if a phase is completed based on battle time."""
        if phase == BattlePhase.OPENING:
            return self.time_remaining < 270  # After first 30s
        elif phase == BattlePhase.BOOST_1:
            return self.time_remaining < 200  # After ~100s
        elif phase == BattlePhase.MID_BATTLE:
            return self.time_remaining < 60   # After 240s
        elif phase == BattlePhase.BOOST_2:
            return self.time_remaining < 90   # After ~210s
        return False

    def update_battle_state(self, time_remaining: int, deficit: int):
        """
        Update battle state for dynamic reallocation.

        Args:
            time_remaining: Seconds remaining in battle
            deficit: Points behind opponent (negative if ahead)
        """
        old_phase = self.current_phase
        self.time_remaining = time_remaining
        self.deficit = deficit

        # Determine current phase
        if time_remaining <= 30:
            self.current_phase = BattlePhase.SNIPE
        elif time_remaining <= 60:
            self.current_phase = BattlePhase.BOOST_2
        elif time_remaining <= 180:
            self.current_phase = BattlePhase.MID_BATTLE
        elif time_remaining <= 240:
            self.current_phase = BattlePhase.BOOST_1
        else:
            self.current_phase = BattlePhase.OPENING

        # Trigger reallocation on phase change
        if old_phase != self.current_phase:
            self.reallocate_unused()
            logger.info(f"[BudgetManager] Phase changed: {old_phase.value} -> {self.current_phase.value}")

        # If in significant deficit, consider emergency spending
        if deficit > 500 and self.current_phase not in [BattlePhase.SNIPE, BattlePhase.BOOST_2]:
            self._consider_emergency_spending(deficit)

    def _consider_emergency_spending(self, deficit: int):
        """Consider tapping emergency reserves if behind."""
        emergency = self.allocations.get(BattlePhase.EMERGENCY)
        if emergency and emergency.coins_remaining > 0:
            # Allow emergency funds to be used for current phase
            current_alloc = self.allocations.get(self.current_phase)
            if current_alloc:
                transfer = min(emergency.coins_remaining, deficit)
                current_alloc.coins_allocated += transfer
                emergency.coins_spent += transfer
                logger.info(f"[BudgetManager] Emergency transfer: {transfer} coins to {self.current_phase.value}")

    def get_recommended_action(self) -> Dict:
        """
        Get recommended spending action based on current state.

        Returns:
            Dict with recommendation details
        """
        phase = self.current_phase
        budget = self.get_phase_budget(phase)

        # Calculate spend intensity based on deficit
        if self.deficit > 1000:
            intensity = "aggressive"
            gift = self.get_optimal_gift(phase, min_impact=100, prefer_efficiency=False)
        elif self.deficit > 0:
            intensity = "moderate"
            gift = self.get_optimal_gift(phase, prefer_efficiency=True)
        else:
            intensity = "conservative"
            # We're ahead, be efficient
            gift = self.get_optimal_gift(phase, prefer_efficiency=True)

        return {
            'phase': phase.value,
            'intensity': intensity,
            'budget_remaining': budget,
            'total_remaining': self.remaining_coins,
            'recommended_gift': gift.name if gift else None,
            'gift_coins': gift.coins if gift else 0,
            'deficit': self.deficit
        }

    def get_efficiency_report(self) -> Dict:
        """Get spending efficiency report."""
        if self.total_spent == 0:
            return {'efficiency': 0, 'spent': 0, 'points': 0}

        efficiency = self.total_points_earned / self.total_spent if self.total_spent > 0 else 0

        # Calculate by phase
        phase_stats = {}
        for phase, alloc in self.allocations.items():
            phase_spends = [s for s in self.spending_history if s['phase'] == phase.value]
            phase_points = sum(s['effective_points'] for s in phase_spends)
            phase_spent = sum(s['coins'] for s in phase_spends)
            phase_stats[phase.value] = {
                'spent': phase_spent,
                'points': phase_points,
                'efficiency': phase_points / phase_spent if phase_spent > 0 else 0,
                'utilization': alloc.utilization
            }

        return {
            'total_budget': self.total_coins,
            'total_spent': self.total_spent,
            'remaining': self.remaining_coins,
            'total_points': self.total_points_earned,
            'overall_efficiency': efficiency,
            'by_phase': phase_stats,
            'transactions': len(self.spending_history)
        }

    def get_status(self) -> Dict:
        """Get current budget status."""
        return {
            'total': self.total_coins,
            'spent': self.total_spent,
            'remaining': self.remaining_coins,
            'utilization': self.total_spent / self.total_coins if self.total_coins > 0 else 0,
            'phase': self.current_phase.value,
            'phase_budget': self.get_phase_budget(self.current_phase),
            'points_earned': self.total_points_earned,
            'efficiency': self.total_points_earned / self.total_spent if self.total_spent > 0 else 0
        }


def create_budget_manager(
    total_coins: int,
    strategy: str = "balanced"
) -> BudgetManager:
    """
    Factory to create a configured BudgetManager.

    Args:
        total_coins: Total coin budget
        strategy: "balanced", "aggressive", "conservative", "snipe_heavy"

    Returns:
        Configured BudgetManager
    """
    manager = BudgetManager(total_coins, allocation_strategy=strategy)
    manager.allocate_for_battle()
    return manager
