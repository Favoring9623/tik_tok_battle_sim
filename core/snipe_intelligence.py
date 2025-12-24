"""
Snipe Intelligence System for TikTok Battles

Advanced tactical analysis for final seconds:
1. Snipe Detection - Detect when opponent is saving for a snipe
2. Opponent Budget Estimation - Track and estimate remaining budget
3. Counter-Snipe Strategy - Reserve budget to counter opponent's final push
4. Anti-Snipe Defense - Tactical responses to snipe attempts

Key TikTok Battle Realities:
- Most battles are decided in the final 5-10 seconds
- Skilled players save 30-50% of budget for snipe
- Snipe timing is critical - too early reveals hand, too late may not process
- Counter-snipe requires quick reaction and reserved budget
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class SnipeThreatLevel(Enum):
    """Snipe threat assessment levels."""
    NONE = "none"           # Opponent likely out of budget
    LOW = "low"             # Small snipe possible
    MEDIUM = "medium"       # Moderate snipe expected
    HIGH = "high"           # Large snipe imminent
    CRITICAL = "critical"   # Whale snipe incoming


@dataclass
class OpponentBudgetEstimate:
    """Estimation of opponent's remaining budget."""
    estimated_remaining: int
    confidence: float  # 0-1
    total_spent_observed: int
    estimated_starting: int
    spending_rate: float  # coins per second
    is_conserving: bool  # True if spending slowed significantly
    snipe_reserve_estimate: int  # How much they might have saved for snipe


@dataclass
class SnipeThreatAnalysis:
    """Analysis of potential snipe threat."""
    threat_level: SnipeThreatLevel
    estimated_snipe_value: int
    max_possible_snipe: int
    recommended_reserve: int
    counter_strategy: str
    confidence: float


class OpponentBudgetTracker:
    """
    Track and estimate opponent's budget throughout battle.

    Uses observed spending patterns to estimate:
    - Current remaining budget
    - Snipe reserve (budget saved for final push)
    - Spending behavior (aggressive vs conservative)
    """

    def __init__(self, estimated_starting_budget: int = 200000):
        self.estimated_starting = estimated_starting_budget
        self.observed_spending: List[Tuple[int, int, str]] = []  # (time, amount, gift_name)
        self.total_observed_spent = 0

        # Spending rate tracking
        self.spending_rates: List[float] = []  # coins per second per phase
        self.last_spend_time = 0

        # Behavior analysis
        self.gifts_in_normal = 0
        self.gifts_in_boost = 0
        self.gifts_in_final = 0
        self.whale_gifts_count = 0

        # Conservation detection
        self.quiet_periods: List[Tuple[int, int]] = []  # (start, duration)
        self.current_quiet_start = None

    def record_opponent_gift(
        self,
        current_time: int,
        gift_name: str,
        gift_cost: int,
        phase: str
    ):
        """Record an observed opponent gift."""
        self.observed_spending.append((current_time, gift_cost, gift_name))
        self.total_observed_spent += gift_cost

        # Track phase distribution
        if phase == "boost":
            self.gifts_in_boost += 1
        elif phase in ["final_30s", "final_5s"]:
            self.gifts_in_final += 1
        else:
            self.gifts_in_normal += 1

        # Track whale gifts
        if gift_cost >= 10000:
            self.whale_gifts_count += 1

        # Update spending rate
        if self.last_spend_time > 0:
            time_delta = current_time - self.last_spend_time
            if time_delta > 0:
                rate = gift_cost / time_delta
                self.spending_rates.append(rate)

        # End quiet period if we were in one
        if self.current_quiet_start is not None:
            quiet_duration = current_time - self.current_quiet_start
            if quiet_duration >= 10:  # At least 10s of silence counts
                self.quiet_periods.append((self.current_quiet_start, quiet_duration))
            self.current_quiet_start = None

        self.last_spend_time = current_time

    def record_quiet_period(self, current_time: int):
        """Record that opponent hasn't spent in a while."""
        if self.current_quiet_start is None:
            self.current_quiet_start = current_time

    def get_estimate(self, current_time: int, battle_duration: int = 300) -> OpponentBudgetEstimate:
        """Get current budget estimate."""
        time_remaining = battle_duration - current_time

        # Base estimate
        estimated_remaining = max(0, self.estimated_starting - self.total_observed_spent)

        # Calculate average spending rate
        if self.spending_rates:
            avg_rate = sum(self.spending_rates) / len(self.spending_rates)
        else:
            avg_rate = self.total_observed_spent / max(current_time, 1)

        # Detect conservation behavior
        is_conserving = False
        if len(self.spending_rates) >= 5:
            recent_rates = self.spending_rates[-5:]
            early_rates = self.spending_rates[:5] if len(self.spending_rates) >= 10 else self.spending_rates

            avg_recent = sum(recent_rates) / len(recent_rates)
            avg_early = sum(early_rates) / len(early_rates)

            # If recent spending is less than 40% of early spending, they're conserving
            if avg_early > 0 and avg_recent / avg_early < 0.4:
                is_conserving = True

        # Estimate snipe reserve based on behavior
        if is_conserving:
            # Conservative player - likely has large reserve
            snipe_reserve = int(estimated_remaining * 0.6)
        elif self.quiet_periods:
            # Has quiet periods - moderate reserve
            snipe_reserve = int(estimated_remaining * 0.4)
        else:
            # Aggressive spender - smaller reserve
            snipe_reserve = int(estimated_remaining * 0.2)

        # Confidence based on observation count
        observation_count = len(self.observed_spending)
        if observation_count >= 20:
            confidence = 0.8
        elif observation_count >= 10:
            confidence = 0.6
        elif observation_count >= 5:
            confidence = 0.4
        else:
            confidence = 0.2

        return OpponentBudgetEstimate(
            estimated_remaining=estimated_remaining,
            confidence=confidence,
            total_spent_observed=self.total_observed_spent,
            estimated_starting=self.estimated_starting,
            spending_rate=avg_rate,
            is_conserving=is_conserving,
            snipe_reserve_estimate=snipe_reserve
        )

    def reset(self):
        """Reset for new battle."""
        self.observed_spending.clear()
        self.total_observed_spent = 0
        self.spending_rates.clear()
        self.last_spend_time = 0
        self.gifts_in_normal = 0
        self.gifts_in_boost = 0
        self.gifts_in_final = 0
        self.whale_gifts_count = 0
        self.quiet_periods.clear()
        self.current_quiet_start = None


class SnipeIntelligence:
    """
    Advanced snipe detection and counter-snipe strategy.

    Analyzes opponent behavior to:
    - Predict snipe timing and size
    - Recommend counter-snipe reserves
    - Suggest tactical responses
    """

    def __init__(
        self,
        our_budget: int,
        opponent_estimated_budget: int,
        battle_duration: int = 300
    ):
        self.our_budget = our_budget
        self.our_starting_budget = our_budget
        self.battle_duration = battle_duration

        # Opponent tracking
        self.opponent_tracker = OpponentBudgetTracker(opponent_estimated_budget)

        # Score tracking
        self.our_score = 0
        self.opponent_score = 0
        self.score_history: List[Tuple[int, int, int]] = []  # (time, our, theirs)

        # Snipe reserve management
        self.snipe_reserve = 0
        self.counter_snipe_reserve = 0
        self.reserve_locked = False

        # Battle state
        self.in_final_30s = False
        self.in_final_5s = False
        self.snipe_executed = False

    def update_scores(self, our_score: int, opponent_score: int, current_time: int):
        """Update score tracking."""
        self.our_score = our_score
        self.opponent_score = opponent_score
        self.score_history.append((current_time, our_score, opponent_score))

        # Update phase flags
        time_remaining = self.battle_duration - current_time
        self.in_final_30s = time_remaining <= 30
        self.in_final_5s = time_remaining <= 5

    def update_our_budget(self, new_budget: int):
        """Update our current budget."""
        self.our_budget = new_budget

    def record_opponent_action(
        self,
        current_time: int,
        gift_name: str,
        gift_cost: int,
        phase: str
    ):
        """Record opponent's gift for tracking."""
        self.opponent_tracker.record_opponent_gift(current_time, gift_name, gift_cost, phase)

    def analyze_snipe_threat(self, time_remaining: int) -> SnipeThreatAnalysis:
        """
        Analyze the current snipe threat from opponent.

        Returns detailed threat analysis with recommended response.
        """
        # Get opponent budget estimate
        current_time = self.battle_duration - time_remaining
        estimate = self.opponent_tracker.get_estimate(current_time, self.battle_duration)

        # Calculate current score gap
        score_gap = self.our_score - self.opponent_score  # Positive = we're ahead

        # Estimate maximum possible snipe
        max_snipe = estimate.snipe_reserve_estimate

        # With x5 glove, snipe can be 5x more effective
        max_snipe_with_x5 = max_snipe * 5

        # Determine threat level
        if max_snipe_with_x5 > score_gap + 50000:
            threat_level = SnipeThreatLevel.CRITICAL
            estimated_snipe = max_snipe_with_x5
        elif max_snipe_with_x5 > score_gap:
            threat_level = SnipeThreatLevel.HIGH
            estimated_snipe = max_snipe_with_x5
        elif max_snipe > score_gap * 0.5:
            threat_level = SnipeThreatLevel.MEDIUM
            estimated_snipe = max_snipe
        elif max_snipe > 10000:
            threat_level = SnipeThreatLevel.LOW
            estimated_snipe = max_snipe
        else:
            threat_level = SnipeThreatLevel.NONE
            estimated_snipe = max_snipe

        # Calculate recommended reserve to counter
        if threat_level == SnipeThreatLevel.CRITICAL:
            # Need maximum counter-snipe capability
            recommended_reserve = min(self.our_budget * 0.5, estimated_snipe * 0.6)
        elif threat_level == SnipeThreatLevel.HIGH:
            recommended_reserve = min(self.our_budget * 0.4, estimated_snipe * 0.5)
        elif threat_level == SnipeThreatLevel.MEDIUM:
            recommended_reserve = min(self.our_budget * 0.3, estimated_snipe * 0.4)
        elif threat_level == SnipeThreatLevel.LOW:
            recommended_reserve = min(self.our_budget * 0.2, 30000)
        else:
            recommended_reserve = min(self.our_budget * 0.1, 10000)

        # Determine counter-strategy
        counter_strategy = self._get_counter_strategy(
            threat_level, score_gap, estimate.is_conserving, time_remaining
        )

        return SnipeThreatAnalysis(
            threat_level=threat_level,
            estimated_snipe_value=int(estimated_snipe),
            max_possible_snipe=int(max_snipe_with_x5),
            recommended_reserve=int(recommended_reserve),
            counter_strategy=counter_strategy,
            confidence=estimate.confidence
        )

    def _get_counter_strategy(
        self,
        threat_level: SnipeThreatLevel,
        score_gap: int,
        opponent_conserving: bool,
        time_remaining: int
    ) -> str:
        """Determine the best counter-strategy."""

        if time_remaining <= 5:
            # Final 5 seconds - execute immediately
            if threat_level in [SnipeThreatLevel.CRITICAL, SnipeThreatLevel.HIGH]:
                return "COUNTER_SNIPE_NOW"
            elif score_gap < 0:
                return "SNIPE_TO_WIN"
            else:
                return "DEFEND_LEAD"

        if time_remaining <= 30:
            # Final 30 seconds
            if opponent_conserving:
                return "PREPARE_COUNTER_SNIPE"
            elif threat_level == SnipeThreatLevel.CRITICAL:
                return "PRE_EMPTIVE_STRIKE"
            else:
                return "BUILD_LEAD"

        # Normal phases
        if threat_level == SnipeThreatLevel.CRITICAL and opponent_conserving:
            return "FORCE_EARLY_SPEND"
        elif threat_level == SnipeThreatLevel.HIGH:
            return "RESERVE_FOR_COUNTER"
        else:
            return "NORMAL_PLAY"

    def get_snipe_recommendation(
        self,
        time_remaining: int,
        current_multiplier: float = 1.0,
        glove_available: bool = False
    ) -> Dict:
        """
        Get specific recommendation for snipe/counter-snipe action.

        Returns:
            Dict with timing, amount, gift selection, and reasoning
        """
        threat = self.analyze_snipe_threat(time_remaining)
        score_gap = self.our_score - self.opponent_score

        # Base recommendation
        recommendation = {
            'should_snipe': False,
            'should_reserve': False,
            'reserve_amount': 0,
            'snipe_timing': None,
            'snipe_amount': 0,
            'use_glove': False,
            'reasoning': '',
            'threat_level': threat.threat_level.value
        }

        # Final 5 seconds logic
        if time_remaining <= 5:
            if score_gap < 0:
                # We're behind - MUST snipe
                recommendation['should_snipe'] = True
                recommendation['snipe_amount'] = self.our_budget
                recommendation['snipe_timing'] = 'NOW'
                recommendation['use_glove'] = glove_available
                recommendation['reasoning'] = f"BEHIND by {abs(score_gap):,} - ALL IN SNIPE"
            elif threat.threat_level in [SnipeThreatLevel.CRITICAL, SnipeThreatLevel.HIGH]:
                # Ahead but threat is high - counter-snipe
                recommendation['should_snipe'] = True
                recommendation['snipe_amount'] = min(self.our_budget, threat.recommended_reserve)
                recommendation['snipe_timing'] = 'NOW'
                recommendation['use_glove'] = glove_available and threat.threat_level == SnipeThreatLevel.CRITICAL
                recommendation['reasoning'] = f"COUNTER-SNIPE: Threat level {threat.threat_level.value}"
            else:
                # Safe lead
                recommendation['should_snipe'] = False
                recommendation['reasoning'] = f"Lead of {score_gap:,} is safe"

        # Final 30 seconds - prepare
        elif time_remaining <= 30:
            if threat.threat_level in [SnipeThreatLevel.CRITICAL, SnipeThreatLevel.HIGH]:
                recommendation['should_reserve'] = True
                recommendation['reserve_amount'] = threat.recommended_reserve
                recommendation['snipe_timing'] = f"at {time_remaining - 3}s remaining"
                recommendation['reasoning'] = f"Reserve {threat.recommended_reserve:,} for counter-snipe"
            elif score_gap < -30000:
                # Far behind - need aggressive play
                recommendation['should_snipe'] = current_multiplier >= 2.0
                recommendation['snipe_amount'] = int(self.our_budget * 0.5)
                recommendation['reasoning'] = "Far behind - aggressive boost play needed"

        # Before final 30s
        else:
            if threat.threat_level == SnipeThreatLevel.CRITICAL:
                recommendation['should_reserve'] = True
                recommendation['reserve_amount'] = threat.recommended_reserve
                recommendation['reasoning'] = "Opponent conserving heavily - prepare for snipe"

        return recommendation

    def calculate_optimal_snipe_timing(self, time_remaining: int) -> int:
        """
        Calculate optimal snipe timing.

        TikTok battle realities:
        - Gifts take ~0.5-1s to process
        - Too early (>3s) lets opponent react
        - Too late (<1s) might not process
        - Ideal: 2-3 seconds remaining
        """
        if time_remaining <= 3:
            return 0  # Execute now
        elif time_remaining <= 5:
            return time_remaining - 2  # Wait until 2s remaining
        else:
            return time_remaining - 3  # Wait until 3s remaining

    def get_anti_snipe_reserve(self) -> int:
        """Get recommended budget to reserve for anti-snipe defense."""
        threat = self.analyze_snipe_threat(30)  # Analyze with 30s remaining
        return threat.recommended_reserve

    def should_use_glove_for_snipe(
        self,
        gloves_remaining: int,
        score_gap: int,
        time_remaining: int
    ) -> bool:
        """Determine if glove should be used for snipe."""
        if gloves_remaining <= 0:
            return False

        if time_remaining > 10:
            return False  # Too early for snipe glove

        # Use glove if:
        # 1. We're behind and need the x5
        if score_gap < 0:
            return True

        # 2. Threat is critical and we need counter-power
        threat = self.analyze_snipe_threat(time_remaining)
        if threat.threat_level == SnipeThreatLevel.CRITICAL:
            return True

        # 3. Score is close and glove could secure victory
        if abs(score_gap) < 50000:
            return True

        return False

    def reset(self):
        """Reset for new battle."""
        self.our_budget = self.our_starting_budget
        self.our_score = 0
        self.opponent_score = 0
        self.score_history.clear()
        self.snipe_reserve = 0
        self.counter_snipe_reserve = 0
        self.reserve_locked = False
        self.in_final_30s = False
        self.in_final_5s = False
        self.snipe_executed = False
        self.opponent_tracker.reset()


class SnipeCoordinator:
    """
    Coordinates snipe timing across multiple agents.

    In team battles, snipe should be coordinated:
    - One agent uses glove (x5 activator)
    - Others send whale gifts during x5
    - Timing is synchronized for maximum impact
    """

    def __init__(self, team_size: int = 7):
        self.team_size = team_size
        self.glove_assignee: Optional[str] = None
        self.snipe_order: List[str] = []
        self.snipe_timing: int = 3  # seconds before end
        self.execution_started = False

    def assign_snipe_roles(self, agents: List, gloves_available: Dict[str, int]):
        """Assign snipe roles to team members."""
        # Find agent with gloves for x5
        for agent in agents:
            name = agent.name if hasattr(agent, 'name') else str(agent)
            if gloves_available.get(name, 0) > 0:
                self.glove_assignee = name
                break

        # Order other agents by gift-sending capability
        self.snipe_order = [
            a.name if hasattr(a, 'name') else str(a)
            for a in agents
            if (a.name if hasattr(a, 'name') else str(a)) != self.glove_assignee
        ]

    def get_snipe_instruction(self, agent_name: str, time_remaining: int) -> Dict:
        """Get snipe instruction for specific agent."""
        if time_remaining > self.snipe_timing + 2:
            return {'action': 'WAIT', 'reason': 'Too early for snipe'}

        if agent_name == self.glove_assignee:
            if time_remaining <= self.snipe_timing + 1:
                return {
                    'action': 'DEPLOY_GLOVE',
                    'reason': 'Activate x5 for team snipe'
                }
            return {'action': 'PREPARE_GLOVE', 'reason': 'Prepare to activate x5'}

        # Other agents wait for x5 then send whales
        if self.execution_started or time_remaining <= self.snipe_timing:
            return {
                'action': 'SEND_WHALE',
                'reason': 'x5 active - send maximum gift'
            }

        return {'action': 'WAIT', 'reason': 'Waiting for x5 activation'}

    def mark_execution_started(self):
        """Mark that snipe execution has begun."""
        self.execution_started = True

    def reset(self):
        """Reset for new battle."""
        self.glove_assignee = None
        self.snipe_order.clear()
        self.execution_started = False


if __name__ == "__main__":
    print("Snipe Intelligence Demo")
    print("=" * 60)

    # Create snipe intelligence
    intel = SnipeIntelligence(
        our_budget=100000,
        opponent_estimated_budget=150000,
        battle_duration=300
    )

    # Simulate opponent gifts during battle
    print("\n📊 Recording opponent activity...")
    intel.record_opponent_action(30, "Dragon Flame", 10000, "boost")
    intel.record_opponent_action(60, "Lion", 29999, "boost")
    intel.record_opponent_action(100, "Rosa Nebula", 299, "normal")
    # Opponent goes quiet (conserving)

    # Update scores
    intel.update_scores(our_score=80000, opponent_score=60000, current_time=250)

    # Analyze threat at different times
    for time_remaining in [30, 10, 5]:
        print(f"\n⏱️ Time remaining: {time_remaining}s")
        threat = intel.analyze_snipe_threat(time_remaining)
        print(f"   Threat Level: {threat.threat_level.value}")
        print(f"   Estimated Snipe: {threat.estimated_snipe_value:,}")
        print(f"   Max Possible: {threat.max_possible_snipe:,}")
        print(f"   Recommended Reserve: {threat.recommended_reserve:,}")
        print(f"   Strategy: {threat.counter_strategy}")

        rec = intel.get_snipe_recommendation(time_remaining, glove_available=True)
        print(f"   Should Snipe: {rec['should_snipe']}")
        print(f"   Reasoning: {rec['reasoning']}")
