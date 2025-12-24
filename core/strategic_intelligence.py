"""
Strategic Intelligence System for TikTok Battles

Advanced decision-making for:
1. Surrender Logic - Know when to stop gifting (unrecoverable deficit)
2. Offensive/Defensive Modes - Adaptive strategy based on situation
3. Catch-up Strategy - Maximize points when trailing during boosts
4. Budget Maximization - Optimal spending for limited budgets

Key Concepts:
- Deficit Analysis: Can we mathematically recover with remaining budget?
- ROI Optimization: Spend during high-multiplier phases for maximum impact
- Opponent Modeling: Adapt based on opponent's spending patterns
- Phase Awareness: Different strategies for different battle phases
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import random

from core.budget_system import BudgetManager, BudgetTier, GIFT_CATALOG, get_gift_cost


class StrategyMode(Enum):
    """Current strategic mode."""
    AGGRESSIVE = "aggressive"      # All-out attack, maximize spending
    DEFENSIVE = "defensive"        # Protect lead, minimal spending
    BALANCED = "balanced"          # Normal spending pattern
    CATCH_UP = "catch_up"          # Behind, focus on boost phases
    SURRENDER = "surrender"        # Deficit unrecoverable, stop gifting
    CONSERVATION = "conservation"  # Save budget for key phases


@dataclass
class RecoveryAnalysis:
    """Analysis of whether a deficit can be recovered."""
    can_recover: bool
    deficit: int
    budget_remaining: int
    max_possible_points: int
    recovery_ratio: float  # max_points / deficit
    recommended_action: str
    confidence: float  # 0-1 confidence in recommendation


@dataclass
class PhaseOpportunity:
    """Opportunity during a specific phase."""
    phase_name: str
    multiplier: float
    time_until: int
    duration: int
    potential_points: int  # Max points achievable
    budget_needed: int


class StrategicIntelligence:
    """
    Advanced strategic decision-making system.

    Implements:
    - Surrender detection when deficit is mathematically unrecoverable
    - Offensive/defensive mode switching based on score and budget
    - Catch-up strategies during boost phases
    - Budget maximization for constrained resources
    """

    def __init__(
        self,
        budget_manager: BudgetManager,
        team: str = "creator",
        battle_duration: int = 300
    ):
        self.budget_manager = budget_manager
        self.team = team
        self.battle_duration = battle_duration

        # Current strategy state
        self.current_mode = StrategyMode.BALANCED
        self.previous_mode = StrategyMode.BALANCED

        # Score tracking
        self.our_score = 0
        self.opponent_score = 0
        self.peak_lead = 0
        self.max_deficit = 0

        # Phase tracking
        self.upcoming_boosts: List[PhaseOpportunity] = []
        self.current_multiplier = 1.0

        # Opponent modeling
        self.opponent_spending_history: List[Tuple[int, int]] = []  # (time, spent)
        self.opponent_avg_rate = 0
        self.opponent_is_active = True

        # Surrender threshold (configurable)
        self.surrender_confidence_threshold = 0.80  # 80% sure we can't recover
        self.minimum_recovery_ratio = 0.5  # Need at least 50% chance to not surrender

        # Strategy history for learning
        self.strategy_changes: List[Dict] = []

    def update_scores(self, our_score: int, opponent_score: int, current_time: int):
        """Update score tracking."""
        self.our_score = our_score
        self.opponent_score = opponent_score

        lead = our_score - opponent_score
        if lead > self.peak_lead:
            self.peak_lead = lead
        if lead < -self.max_deficit:
            self.max_deficit = abs(lead)

    def update_opponent_spending(self, current_time: int, opponent_total_spent: int):
        """Track opponent spending patterns."""
        self.opponent_spending_history.append((current_time, opponent_total_spent))

        # Calculate average spending rate (coins per second)
        if len(self.opponent_spending_history) >= 2:
            first_time, first_spent = self.opponent_spending_history[0]
            last_time, last_spent = self.opponent_spending_history[-1]
            time_delta = last_time - first_time
            if time_delta > 0:
                self.opponent_avg_rate = (last_spent - first_spent) / time_delta

        # Check if opponent has stopped spending (last 30 seconds)
        if len(self.opponent_spending_history) >= 6:
            recent = self.opponent_spending_history[-6:]
            recent_delta = recent[-1][1] - recent[0][1]
            self.opponent_is_active = recent_delta > 100  # Less than 100 coins = inactive

    def register_upcoming_boost(
        self,
        phase_name: str,
        multiplier: float,
        time_until: int,
        duration: int
    ):
        """Register an upcoming boost phase for planning."""
        # Calculate potential points based on budget
        budget = self._get_current_budget()
        # Assume we can spend 50% of remaining budget during boost
        spendable = budget * 0.5
        potential_points = int(spendable * multiplier)

        self.upcoming_boosts.append(PhaseOpportunity(
            phase_name=phase_name,
            multiplier=multiplier,
            time_until=time_until,
            duration=duration,
            potential_points=potential_points,
            budget_needed=int(spendable)
        ))

    def analyze_recovery(self, time_remaining: int) -> RecoveryAnalysis:
        """
        Analyze whether the current deficit can be recovered.

        This is the core surrender logic - determines if continuing to
        gift is mathematically futile.
        """
        deficit = self.opponent_score - self.our_score

        # If we're ahead or tied, no recovery needed
        if deficit <= 0:
            return RecoveryAnalysis(
                can_recover=True,
                deficit=0,
                budget_remaining=self._get_current_budget(),
                max_possible_points=0,
                recovery_ratio=float('inf'),
                recommended_action="MAINTAIN_LEAD",
                confidence=1.0
            )

        budget = self._get_current_budget()

        # Calculate maximum possible points from remaining budget
        # Consider upcoming boosts for maximum efficiency
        max_points = self._calculate_max_possible_points(budget, time_remaining)

        # Factor in expected opponent gains
        expected_opponent_gains = self._estimate_opponent_gains(time_remaining)

        # Adjusted deficit includes opponent's expected future gains
        adjusted_deficit = deficit + expected_opponent_gains

        # Calculate recovery ratio
        recovery_ratio = max_points / max(adjusted_deficit, 1)

        # Determine if recovery is possible
        can_recover = recovery_ratio >= self.minimum_recovery_ratio

        # Calculate confidence in this assessment
        confidence = self._calculate_recovery_confidence(
            recovery_ratio, time_remaining, budget
        )

        # Determine recommended action
        if recovery_ratio >= 1.5:
            action = "AGGRESSIVE_RECOVERY"
        elif recovery_ratio >= 1.0:
            action = "POSSIBLE_RECOVERY"
        elif recovery_ratio >= 0.5:
            action = "DIFFICULT_RECOVERY"
        elif recovery_ratio >= self.minimum_recovery_ratio:
            action = "HAIL_MARY"
        else:
            action = "SURRENDER"

        return RecoveryAnalysis(
            can_recover=can_recover,
            deficit=deficit,
            budget_remaining=budget,
            max_possible_points=max_points,
            recovery_ratio=recovery_ratio,
            recommended_action=action,
            confidence=confidence
        )

    def _calculate_max_possible_points(
        self,
        budget: int,
        time_remaining: int
    ) -> int:
        """Calculate maximum points achievable with remaining budget and time."""
        total_points = 0
        remaining_budget = budget

        # First, calculate points from upcoming boosts
        for boost in sorted(self.upcoming_boosts, key=lambda x: -x.multiplier):
            if boost.time_until < time_remaining:
                # Can participate in this boost
                spend_in_boost = min(remaining_budget, boost.budget_needed)
                points_from_boost = int(spend_in_boost * boost.multiplier)
                total_points += points_from_boost
                remaining_budget -= spend_in_boost

        # Remaining budget at x1 multiplier
        total_points += remaining_budget

        return total_points

    def _estimate_opponent_gains(self, time_remaining: int) -> int:
        """Estimate how many points opponent will gain in remaining time."""
        if not self.opponent_is_active:
            return 0  # Opponent has surrendered/stopped

        # Use average spending rate to project
        estimated_coins = self.opponent_avg_rate * time_remaining

        # Assume average multiplier of 1.5 (accounting for boosts)
        estimated_points = int(estimated_coins * 1.5)

        return estimated_points

    def _calculate_recovery_confidence(
        self,
        recovery_ratio: float,
        time_remaining: int,
        budget: int
    ) -> float:
        """
        Calculate confidence in recovery assessment.

        When ratio is LOW (can't recover), confidence should be HIGH that surrender is correct.
        When ratio is HIGH (can recover), confidence should be HIGH that we can win.
        """
        # For UNRECOVERABLE scenarios (ratio < 0.5):
        # Lower ratio = HIGHER confidence that we can't recover
        if recovery_ratio < 0.5:
            # Inverse relationship: very low ratio = very confident we can't recover
            if recovery_ratio < 0.1:
                base_confidence = 0.95  # Almost certainly can't recover
            elif recovery_ratio < 0.2:
                base_confidence = 0.90
            elif recovery_ratio < 0.3:
                base_confidence = 0.85
            elif recovery_ratio < 0.4:
                base_confidence = 0.80
            else:
                base_confidence = 0.70
        else:
            # For RECOVERABLE scenarios (ratio >= 0.5):
            # Higher ratio = higher confidence we can recover
            if recovery_ratio >= 2.0:
                base_confidence = 0.95
            elif recovery_ratio >= 1.5:
                base_confidence = 0.85
            elif recovery_ratio >= 1.0:
                base_confidence = 0.75
            else:
                base_confidence = 0.60

        # Adjust for time remaining (less time = more certainty)
        # With little time left, the math is more definitive
        time_factor = 1.0 - (time_remaining / self.battle_duration) * 0.1

        # Adjust for budget (very low budget = more certain of outcome)
        starting = self._get_starting_budget()
        budget_ratio = budget / max(starting, 1)
        if budget_ratio < 0.1:
            budget_factor = 1.05  # Boost confidence when almost out of budget
        else:
            budget_factor = 1.0

        return min(1.0, base_confidence * time_factor * budget_factor)

    def get_recommended_strategy(
        self,
        current_time: int,
        time_remaining: int,
        phase_info: Dict
    ) -> Dict:
        """
        Get comprehensive strategy recommendation.

        Returns:
            Dict with:
            - mode: StrategyMode
            - should_gift: bool
            - max_spend: int
            - gift_tier: str
            - reasoning: str
            - recovery_analysis: RecoveryAnalysis
        """
        # Update current multiplier
        self.current_multiplier = phase_info.get('multiplier', 1.0)

        # Analyze recovery possibility
        recovery = self.analyze_recovery(time_remaining)

        # Determine strategy mode
        new_mode = self._determine_mode(recovery, time_remaining, phase_info)

        # Track mode changes
        if new_mode != self.current_mode:
            self.strategy_changes.append({
                'time': current_time,
                'from_mode': self.current_mode.value,
                'to_mode': new_mode.value,
                'reason': recovery.recommended_action
            })
            self.previous_mode = self.current_mode
            self.current_mode = new_mode

        # Generate specific recommendation based on mode
        recommendation = self._generate_recommendation(
            new_mode, recovery, time_remaining, phase_info
        )

        recommendation['mode'] = new_mode
        recommendation['recovery_analysis'] = recovery

        return recommendation

    def _determine_mode(
        self,
        recovery: RecoveryAnalysis,
        time_remaining: int,
        phase_info: Dict
    ) -> StrategyMode:
        """Determine the appropriate strategy mode."""
        multiplier = phase_info.get('multiplier', 1.0)
        is_boost = multiplier > 1.0
        in_final_30s = time_remaining <= 30

        # Check for surrender condition
        if not recovery.can_recover and recovery.confidence >= self.surrender_confidence_threshold:
            return StrategyMode.SURRENDER

        # Leading scenarios
        if recovery.deficit <= 0:
            lead = abs(recovery.deficit)
            budget = recovery.budget_remaining

            # Big lead with low budget - go defensive
            if lead > 10000 and budget < self._get_starting_budget() * 0.3:
                return StrategyMode.DEFENSIVE

            # Comfortable lead - conservation mode
            if lead > 5000:
                return StrategyMode.CONSERVATION

            # Close battle - balanced
            return StrategyMode.BALANCED

        # Trailing scenarios
        if recovery.recovery_ratio >= 1.5:
            # Good chance to recover - be aggressive during boosts
            if is_boost or in_final_30s:
                return StrategyMode.AGGRESSIVE
            return StrategyMode.CATCH_UP

        if recovery.recovery_ratio >= 1.0:
            # Can recover but need to be strategic
            return StrategyMode.CATCH_UP

        if recovery.recovery_ratio >= 0.5:
            # Difficult but possible - focus on boosts only
            if is_boost and multiplier >= 2.0:
                return StrategyMode.AGGRESSIVE
            return StrategyMode.CONSERVATION

        # Very low chance - conserve unless perfect opportunity
        if is_boost and multiplier >= 5.0:
            return StrategyMode.AGGRESSIVE  # x5 is worth the gamble

        return StrategyMode.CONSERVATION

    def _generate_recommendation(
        self,
        mode: StrategyMode,
        recovery: RecoveryAnalysis,
        time_remaining: int,
        phase_info: Dict
    ) -> Dict:
        """Generate specific action recommendation based on mode."""
        multiplier = phase_info.get('multiplier', 1.0)
        budget = recovery.budget_remaining

        if mode == StrategyMode.SURRENDER:
            return {
                'should_gift': False,
                'max_spend': 0,
                'gift_tier': None,
                'reasoning': f"SURRENDER: Deficit of {recovery.deficit:,} unrecoverable. "
                           f"Max possible: {recovery.max_possible_points:,} "
                           f"({recovery.confidence*100:.0f}% confidence)"
            }

        if mode == StrategyMode.DEFENSIVE:
            # Minimal spending to protect lead
            return {
                'should_gift': False,
                'max_spend': min(budget * 0.05, 1000),
                'gift_tier': 'small',
                'reasoning': f"DEFENSIVE: Protecting lead of {abs(recovery.deficit):,}. "
                           f"Minimal spending only."
            }

        if mode == StrategyMode.CONSERVATION:
            # Save for boosts
            if multiplier >= 2.0:
                # In a boost - spend moderately
                max_spend = int(budget * 0.3)
                return {
                    'should_gift': True,
                    'max_spend': max_spend,
                    'gift_tier': 'large' if multiplier >= 3.0 else 'medium',
                    'reasoning': f"CONSERVATION: x{multiplier:.0f} boost active - "
                               f"spending up to {max_spend:,}"
                }
            return {
                'should_gift': False,
                'max_spend': 0,
                'gift_tier': None,
                'reasoning': f"CONSERVATION: Saving for boosts. {len(self.upcoming_boosts)} upcoming."
            }

        if mode == StrategyMode.CATCH_UP:
            # Strategic spending to close gap
            if multiplier >= 2.0:
                # Boost active - spend aggressively
                max_spend = int(budget * 0.5)
                return {
                    'should_gift': True,
                    'max_spend': max_spend,
                    'gift_tier': 'whale' if multiplier >= 3.0 else 'large',
                    'reasoning': f"CATCH-UP: x{multiplier:.0f} active. Need {recovery.deficit:,} points. "
                               f"Spending up to {max_spend:,}"
                }
            # Not in boost - limited spending
            return {
                'should_gift': time_remaining <= 60,  # Only in last minute
                'max_spend': min(budget * 0.1, 5000),
                'gift_tier': 'medium',
                'reasoning': f"CATCH-UP: Waiting for boost. Deficit: {recovery.deficit:,}"
            }

        if mode == StrategyMode.AGGRESSIVE:
            # Maximum spending for maximum points
            if multiplier >= 5.0:
                # x5 - go all in
                max_spend = budget
                return {
                    'should_gift': True,
                    'max_spend': max_spend,
                    'gift_tier': 'whale',
                    'reasoning': f"AGGRESSIVE: x5 ACTIVE! All-in with {max_spend:,} coins!"
                }
            elif multiplier >= 2.0:
                max_spend = int(budget * 0.7)
                return {
                    'should_gift': True,
                    'max_spend': max_spend,
                    'gift_tier': 'whale',
                    'reasoning': f"AGGRESSIVE: x{multiplier:.0f} boost. Heavy spending: {max_spend:,}"
                }
            else:
                max_spend = int(budget * 0.4)
                return {
                    'should_gift': True,
                    'max_spend': max_spend,
                    'gift_tier': 'large',
                    'reasoning': f"AGGRESSIVE: Final push with {max_spend:,}"
                }

        # BALANCED mode (default)
        if multiplier >= 2.0:
            max_spend = int(budget * 0.3)
            return {
                'should_gift': True,
                'max_spend': max_spend,
                'gift_tier': 'large',
                'reasoning': f"BALANCED: x{multiplier:.0f} boost. Moderate spending: {max_spend:,}"
            }
        return {
            'should_gift': random.random() < 0.3,  # 30% chance in normal phase
            'max_spend': min(budget * 0.1, 3000),
            'gift_tier': 'medium',
            'reasoning': "BALANCED: Normal phase, light spending"
        }

    def select_optimal_gift(self, max_spend: int, tier: str) -> Optional[str]:
        """Select the optimal gift within constraints."""
        tier_order = {'small': 0, 'medium': 1, 'large': 2, 'whale': 3}
        max_tier_idx = tier_order.get(tier, 3)

        best_gift = None
        best_efficiency = 0  # Points per coin

        for name, gift in GIFT_CATALOG.items():
            if gift.tier == 'powerup':
                continue
            gift_tier_idx = tier_order.get(gift.tier, 0)
            if gift.cost <= max_spend and gift_tier_idx <= max_tier_idx:
                efficiency = gift.points / gift.cost
                # Prefer larger gifts for their impact (slight bonus)
                adjusted_efficiency = efficiency * (1 + gift_tier_idx * 0.1)
                if adjusted_efficiency > best_efficiency:
                    best_efficiency = adjusted_efficiency
                    best_gift = name

        return best_gift

    def _get_current_budget(self) -> int:
        """Get current budget for our team."""
        if self.team == "creator":
            return self.budget_manager.creator_budget
        return self.budget_manager.opponent_budget

    def _get_starting_budget(self) -> int:
        """Get starting budget for our team."""
        if self.team == "creator":
            return self.budget_manager.creator_starting
        return self.budget_manager.opponent_starting

    def get_analytics(self) -> Dict:
        """Get strategic analytics for battle summary."""
        return {
            'final_mode': self.current_mode.value,
            'strategy_changes': len(self.strategy_changes),
            'changes_history': self.strategy_changes,
            'peak_lead': self.peak_lead,
            'max_deficit': self.max_deficit,
            'opponent_was_active': self.opponent_is_active,
            'opponent_avg_rate': self.opponent_avg_rate
        }


class CatchUpOptimizer:
    """
    Specialized optimizer for catch-up scenarios.

    Calculates optimal spending patterns to maximize points
    during boost phases when trailing.
    """

    @staticmethod
    def calculate_catch_up_plan(
        deficit: int,
        budget: int,
        upcoming_boosts: List[PhaseOpportunity],
        time_remaining: int
    ) -> Dict:
        """
        Calculate optimal plan to catch up.

        Returns:
            Dict with spending allocation per phase
        """
        if not upcoming_boosts:
            # No boosts - spend evenly
            return {
                'strategy': 'even_distribution',
                'allocations': [{'phase': 'normal', 'budget': budget, 'expected_points': budget}],
                'total_expected': budget,
                'can_catch_up': budget >= deficit
            }

        # Sort boosts by multiplier (highest first)
        sorted_boosts = sorted(upcoming_boosts, key=lambda x: -x.multiplier)

        allocations = []
        remaining_budget = budget
        total_expected = 0

        for boost in sorted_boosts:
            # Calculate optimal spend for this boost
            # Higher multiplier = allocate more budget
            multiplier_weight = boost.multiplier / sum(b.multiplier for b in sorted_boosts)
            allocation = int(remaining_budget * min(multiplier_weight * 1.5, 0.7))

            if allocation > 0:
                expected = int(allocation * boost.multiplier)
                allocations.append({
                    'phase': boost.phase_name,
                    'multiplier': boost.multiplier,
                    'budget': allocation,
                    'expected_points': expected
                })
                remaining_budget -= allocation
                total_expected += expected

        # Any remaining budget goes to normal phase
        if remaining_budget > 0:
            allocations.append({
                'phase': 'normal',
                'multiplier': 1.0,
                'budget': remaining_budget,
                'expected_points': remaining_budget
            })
            total_expected += remaining_budget

        return {
            'strategy': 'boost_focused',
            'allocations': allocations,
            'total_expected': total_expected,
            'can_catch_up': total_expected >= deficit,
            'deficit': deficit,
            'surplus': total_expected - deficit
        }


class BudgetMaximizer:
    """
    Optimizer for limited budgets.

    Helps players with low budgets maximize their impact
    by focusing spending on optimal moments.
    """

    @staticmethod
    def get_optimal_spending_windows(
        budget: int,
        battle_duration: int,
        boost_schedule: List[Dict]
    ) -> List[Dict]:
        """
        Identify optimal spending windows for limited budget.

        Returns list of windows with recommended spending.
        """
        windows = []

        # Always save some for final 30 seconds
        final_reserve = min(budget * 0.3, 30000)
        available = budget - final_reserve

        # Allocate to boosts by expected value
        for boost in boost_schedule:
            multiplier = boost.get('multiplier', 1.0)
            duration = boost.get('duration', 20)
            start_time = boost.get('start_time', 0)

            # Higher multiplier = more allocation
            if multiplier >= 5.0:
                allocation = available * 0.5
            elif multiplier >= 3.0:
                allocation = available * 0.3
            elif multiplier >= 2.0:
                allocation = available * 0.2
            else:
                allocation = 0

            if allocation > 0:
                windows.append({
                    'start_time': start_time,
                    'end_time': start_time + duration,
                    'multiplier': multiplier,
                    'recommended_spend': int(allocation),
                    'expected_points': int(allocation * multiplier),
                    'priority': 'HIGH' if multiplier >= 3.0 else 'MEDIUM'
                })
                available -= allocation

        # Final 30 seconds window
        windows.append({
            'start_time': battle_duration - 30,
            'end_time': battle_duration,
            'multiplier': 1.0,  # Base, may have glove x5
            'recommended_spend': int(final_reserve),
            'expected_points': int(final_reserve),  # Minimum, could be x5
            'priority': 'CRITICAL'
        })

        return sorted(windows, key=lambda x: x['start_time'])

    @staticmethod
    def should_spend_now(
        budget: int,
        current_time: int,
        time_remaining: int,
        current_multiplier: float,
        upcoming_boosts: List[Dict]
    ) -> Tuple[bool, str]:
        """
        Determine if now is a good time to spend for limited budget.

        Returns (should_spend, reason)
        """
        # Always spend in final 5 seconds
        if time_remaining <= 5:
            return True, "FINAL_SECONDS"

        # Check if we're in a high-value boost
        if current_multiplier >= 5.0:
            return True, "X5_ACTIVE"
        if current_multiplier >= 3.0:
            return True, "HIGH_MULTIPLIER"

        # Check upcoming boosts - should we wait?
        for boost in upcoming_boosts:
            time_until = boost.get('start_time', 0) - current_time
            if 0 < time_until <= 30 and boost.get('multiplier', 1.0) >= 2.0:
                return False, f"WAIT_FOR_BOOST_IN_{time_until}s"

        # Low budget + low multiplier = wait
        if current_multiplier < 2.0:
            return False, "CONSERVE_FOR_BOOST"

        return True, "MODERATE_OPPORTUNITY"


class MultiplierStatus(Enum):
    """État du multiplicateur détecté."""
    NORMAL = "normal"          # x1
    DOUBLE = "double"          # x2
    TRIPLE = "triple"          # x3
    DETECTING = "detecting"    # En cours de détection


@dataclass
class MultiplierEvent:
    """Événement de multiplicateur détecté."""
    started_at: float  # timestamp
    ended_at: Optional[float]
    multiplier: float
    duration_seconds: Optional[int]
    gifts_during: int
    points_gained: int


@dataclass
class TikTokAlgorithmPattern:
    """
    Pattern de l'algorithme TikTok pour les missions bonus.

    Basé sur observations:
    - Les missions bonus (x2, x3) arrivent à intervalles semi-réguliers
    - Typiquement: ~60s, ~90s, ~120s, ~180s, ~240s après début de battle
    - Durée typique: 15-30 secondes
    """
    # Timing typique des events (secondes après début battle)
    TYPICAL_EVENT_TIMES: List[int] = None
    # Tolérance pour la prédiction (±15s)
    TIME_TOLERANCE: int = 15
    # Durée typique d'un event
    EVENT_DURATION_MIN: int = 15
    EVENT_DURATION_MAX: int = 30
    # Probabilité de base qu'un event soit x2 vs x3
    X2_PROBABILITY: float = 0.7
    X3_PROBABILITY: float = 0.3

    def __post_init__(self):
        if self.TYPICAL_EVENT_TIMES is None:
            self.TYPICAL_EVENT_TIMES = [60, 90, 120, 150, 180, 210, 240, 270]


class BattleDetectionIntelligence:
    """
    Intelligence pour rejoindre une battle TikTok à n'importe quel moment.

    Fonctionnalités:
    - Détection de battle en cours
    - Estimation du temps restant
    - Détection des multiplicateurs (x2, x3)
    - Prédiction des événements bonus basée sur l'algorithme TikTok
    - Estimation des events passés

    Proposition de valeur: Rejoindre à chaud et dominer.
    """

    # Points moyens par seconde dans une battle typique
    TYPICAL_POINTS_PER_SECOND = 100

    def __init__(self, battle_duration: int = 300):
        self.battle_duration = battle_duration
        self.joined_at = None
        self.battle_detected_at = None

        # Observations de gifts
        self.gift_history: List[Dict] = []
        self.baseline_ratios: Dict[str, float] = {}

        # État actuel
        self.battle_active = False
        self.estimated_elapsed = 0
        self.estimated_remaining = battle_duration

        # Scores
        self.live_score = 0
        self.opponent_score = 0

        # Multiplicateurs
        self.current_multiplier = 1.0
        self.multiplier_status = MultiplierStatus.NORMAL
        self.multiplier_active_since = None
        self.multiplier_history: List[MultiplierEvent] = []
        self._last_multiplier_end = None

        # Prédictions
        self.next_multiplier_probability = 0.0
        self.estimated_next_multiplier_in = None
        self.predicted_multiplier_type = 2.0

        # Events passés estimés
        self.detected_past_events = 0

        # Pattern TikTok
        self._algorithm_pattern = TikTokAlgorithmPattern()

        # Callbacks
        self._on_multiplier_detected = []
        self._on_battle_detected = []

    def observe_gift(
        self,
        gift_name: str,
        observed_points: int,
        expected_points: int,
        username: str,
        team: str = "live",
        timestamp: float = None
    ) -> float:
        """
        Observer un gift et analyser le multiplicateur.

        Returns:
            Multiplicateur détecté (1.0, 2.0, 3.0, 5.0)
        """
        import time
        if timestamp is None:
            timestamp = time.time()

        if self.joined_at is None:
            self.joined_at = timestamp

        # Calculer ratio
        if expected_points > 0:
            observed_ratio = observed_points / expected_points
        else:
            observed_ratio = 1.0

        # Détecter multiplicateur
        multiplier = self._detect_multiplier(gift_name, observed_ratio, timestamp)

        # Enregistrer observation
        self.gift_history.append({
            'timestamp': timestamp,
            'gift_name': gift_name,
            'expected_points': expected_points,
            'observed_points': observed_points,
            'multiplier': multiplier,
            'username': username,
            'team': team
        })

        # Mettre à jour scores
        if team == "live":
            self.live_score += observed_points
        else:
            self.opponent_score += observed_points

        # Détecter battle si pas encore fait
        if not self.battle_active:
            self._detect_battle()

        # Mettre à jour estimations
        self._update_timing_estimates()
        self._predict_next_multiplier()

        return multiplier

    def _detect_multiplier(self, gift_name: str, ratio: float, timestamp: float) -> float:
        """Détecter le multiplicateur basé sur le ratio observé."""
        old_multiplier = self.current_multiplier

        # Baseline (x1)
        if 0.9 <= ratio <= 1.1:
            if old_multiplier > 1.0:
                self._end_multiplier(timestamp)
            return 1.0

        # x2
        if 1.8 <= ratio <= 2.2:
            if old_multiplier == 1.0:
                self._start_multiplier(2.0, timestamp)
            return 2.0

        # x3
        if 2.7 <= ratio <= 3.3:
            if old_multiplier == 1.0:
                self._start_multiplier(3.0, timestamp)
            return 3.0

        # x5 (Boosting Glove)
        if 4.5 <= ratio <= 5.5:
            if old_multiplier == 1.0:
                self._start_multiplier(5.0, timestamp)
            return 5.0

        # Ratio anormal
        if ratio > 1.5:
            self.multiplier_status = MultiplierStatus.DETECTING
            return ratio

        return 1.0

    def _start_multiplier(self, multiplier: float, timestamp: float):
        """Démarrer un nouveau multiplicateur."""
        self.current_multiplier = multiplier
        self.multiplier_active_since = timestamp
        self.multiplier_status = (
            MultiplierStatus.DOUBLE if multiplier == 2.0
            else MultiplierStatus.TRIPLE if multiplier == 3.0
            else MultiplierStatus.DETECTING
        )

        # Callbacks
        for cb in self._on_multiplier_detected:
            try:
                cb(multiplier, "started")
            except:
                pass

    def _end_multiplier(self, timestamp: float):
        """Terminer le multiplicateur actuel."""
        if self.multiplier_active_since:
            duration = int(timestamp - self.multiplier_active_since)
            gifts_during = sum(
                1 for g in self.gift_history
                if g['timestamp'] >= self.multiplier_active_since
            )
            points_during = sum(
                g['observed_points'] for g in self.gift_history
                if g['timestamp'] >= self.multiplier_active_since
            )

            event = MultiplierEvent(
                started_at=self.multiplier_active_since,
                ended_at=timestamp,
                multiplier=self.current_multiplier,
                duration_seconds=duration,
                gifts_during=gifts_during,
                points_gained=points_during
            )
            self.multiplier_history.append(event)
            self._last_multiplier_end = timestamp

        self.current_multiplier = 1.0
        self.multiplier_status = MultiplierStatus.NORMAL
        self.multiplier_active_since = None

        # Callbacks
        for cb in self._on_multiplier_detected:
            try:
                cb(1.0, "ended")
            except:
                pass

    def _detect_battle(self):
        """Détecter si une battle est en cours."""
        if len(self.gift_history) >= 3:
            self.battle_active = True
            self.battle_detected_at = self.gift_history[-1]['timestamp']

            # Callbacks
            for cb in self._on_battle_detected:
                try:
                    cb(self)
                except:
                    pass

    def _update_timing_estimates(self):
        """Mettre à jour les estimations de timing."""
        total_score = self.live_score + self.opponent_score

        if total_score > 0:
            # Estimer temps écoulé basé sur score total
            self.estimated_elapsed = min(
                total_score // self.TYPICAL_POINTS_PER_SECOND,
                self.battle_duration
            )
            self.estimated_remaining = max(0, self.battle_duration - self.estimated_elapsed)

            # Estimer events passés
            pattern = self._algorithm_pattern
            self.detected_past_events = sum(
                1 for t in pattern.TYPICAL_EVENT_TIMES
                if t + pattern.TIME_TOLERANCE < self.estimated_elapsed
            )

    def _predict_next_multiplier(self):
        """Prédire le prochain événement multiplicateur."""
        if not self.estimated_elapsed:
            return

        pattern = self._algorithm_pattern

        # Trouver le prochain event typique
        next_event_time = None
        for event_time in pattern.TYPICAL_EVENT_TIMES:
            if event_time > self.estimated_elapsed:
                next_event_time = event_time
                break

        if next_event_time:
            time_until = next_event_time - self.estimated_elapsed
            self.estimated_next_multiplier_in = time_until

            # Probabilité basée sur proximité
            if time_until <= 10:
                self.next_multiplier_probability = 0.7
            elif time_until <= 20:
                self.next_multiplier_probability = 0.5
            elif time_until <= 30:
                self.next_multiplier_probability = 0.4
            else:
                self.next_multiplier_probability = 0.2

            self.predicted_multiplier_type = 2.0 if random.random() < pattern.X2_PROBABILITY else 3.0
        else:
            self.next_multiplier_probability = 0.1
            self.estimated_next_multiplier_in = None

    def get_multiplier_analysis(self) -> Dict:
        """Obtenir l'analyse complète des multiplicateurs."""
        return {
            'current': {
                'multiplier': self.current_multiplier,
                'status': self.multiplier_status.value,
                'active_since': self.multiplier_active_since
            },
            'history': [
                {
                    'multiplier': e.multiplier,
                    'duration': e.duration_seconds,
                    'points_gained': e.points_gained
                }
                for e in self.multiplier_history
            ],
            'prediction': {
                'next_in_seconds': self.estimated_next_multiplier_in,
                'probability': self.next_multiplier_probability,
                'predicted_type': self.predicted_multiplier_type
            },
            'past_events_estimated': self.detected_past_events
        }

    def get_timing_analysis(self) -> Dict:
        """Obtenir l'analyse du timing."""
        return {
            'battle_active': self.battle_active,
            'estimated_elapsed': self.estimated_elapsed,
            'estimated_remaining': self.estimated_remaining,
            'in_final_push': self.estimated_remaining <= 30,
            'joined_at': self.joined_at,
            'battle_detected_at': self.battle_detected_at
        }

    def get_recommendation(self) -> Dict:
        """Obtenir une recommandation stratégique."""
        # Multiplicateur actif → ALL IN
        if self.current_multiplier > 1.0:
            return {
                'mode': 'ALL_IN',
                'reasoning': f'Mission bonus x{self.current_multiplier} active!',
                'gift_tier': 'whale',
                'urgency': 1.0,
                'wait_for_multiplier': False
            }

        # Multiplicateur prédit imminent
        if self.next_multiplier_probability > 0.5 and self.estimated_next_multiplier_in and self.estimated_next_multiplier_in <= 15:
            return {
                'mode': 'SAVE',
                'reasoning': f'Mission bonus prédite dans ~{self.estimated_next_multiplier_in}s',
                'gift_tier': 'micro',
                'urgency': 0.3,
                'wait_for_multiplier': True
            }

        # Final push
        if self.estimated_remaining <= 30:
            return {
                'mode': 'WHALE',
                'reasoning': 'Final push - dernières 30 secondes!',
                'gift_tier': 'whale',
                'urgency': 0.95,
                'wait_for_multiplier': False
            }

        # Défaut
        return {
            'mode': 'BALANCED',
            'reasoning': 'Situation normale',
            'gift_tier': 'medium',
            'urgency': 0.5,
            'wait_for_multiplier': self.next_multiplier_probability > 0.4
        }

    def on_multiplier_detected(self, callback):
        """Enregistrer callback pour détection de multiplicateur."""
        self._on_multiplier_detected.append(callback)

    def on_battle_detected(self, callback):
        """Enregistrer callback pour détection de battle."""
        self._on_battle_detected.append(callback)

    def reset(self):
        """Reset pour nouvelle session."""
        self.joined_at = None
        self.battle_detected_at = None
        self.gift_history.clear()
        self.baseline_ratios.clear()
        self.battle_active = False
        self.estimated_elapsed = 0
        self.estimated_remaining = self.battle_duration
        self.live_score = 0
        self.opponent_score = 0
        self.current_multiplier = 1.0
        self.multiplier_status = MultiplierStatus.NORMAL
        self.multiplier_active_since = None
        self.multiplier_history.clear()
        self._last_multiplier_end = None
        self.next_multiplier_probability = 0.0
        self.estimated_next_multiplier_in = None
        self.detected_past_events = 0


if __name__ == "__main__":
    print("Strategic Intelligence Demo")
    print("=" * 60)

    # Create budget manager
    budget = BudgetManager(creator_budget=100000, opponent_budget=150000)

    # Create strategic intelligence
    intel = StrategicIntelligence(budget, team="creator", battle_duration=300)

    # Simulate a losing scenario
    intel.update_scores(5000, 25000, current_time=150)

    # Register upcoming boost
    intel.register_upcoming_boost("Boost #2", 3.0, time_until=30, duration=30)

    # Analyze recovery
    analysis = intel.analyze_recovery(time_remaining=150)
    print(f"\n📊 Recovery Analysis:")
    print(f"   Deficit: {analysis.deficit:,}")
    print(f"   Budget: {analysis.budget_remaining:,}")
    print(f"   Max Points: {analysis.max_possible_points:,}")
    print(f"   Recovery Ratio: {analysis.recovery_ratio:.2f}")
    print(f"   Can Recover: {analysis.can_recover}")
    print(f"   Recommendation: {analysis.recommended_action}")

    # Get strategy recommendation
    recommendation = intel.get_recommended_strategy(
        current_time=150,
        time_remaining=150,
        phase_info={'multiplier': 1.0, 'name': 'Normal'}
    )
    print(f"\n🎯 Strategy Recommendation:")
    print(f"   Mode: {recommendation['mode'].value}")
    print(f"   Should Gift: {recommendation['should_gift']}")
    print(f"   Max Spend: {recommendation['max_spend']:,}")
    print(f"   Gift Tier: {recommendation['gift_tier']}")
    print(f"   Reasoning: {recommendation['reasoning']}")
