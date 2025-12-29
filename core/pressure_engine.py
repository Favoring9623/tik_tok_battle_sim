"""
Pressure Engine - Dynamic psychological warfare for TikTok battles.

Instead of fixed phase allocations, this engine:
1. Tracks opponent behavior and reaction patterns
2. Applies pressure to force opponent responses
3. Uses psychological tactics (bursts, feints, tempo changes)
4. Adapts spending based on opponent reactions, not time phases
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple
import time
import random


class OpponentState(Enum):
    """Detected opponent psychological state."""
    PASSIVE = "passive"           # Low activity, conserving
    REACTIVE = "reactive"         # Responding to our moves
    AGGRESSIVE = "aggressive"     # Actively pushing
    PANICKING = "panicking"       # Erratic high spending
    EXHAUSTED = "exhausted"       # Budget likely depleted


class PressureTactic(Enum):
    """Available psychological tactics."""
    SHOW_STRENGTH = "show_strength"     # Big gift to intimidate
    PROBE = "probe"                      # Small gift to test reaction
    TEMPO_BURST = "tempo_burst"          # Rapid small gifts
    PATIENCE = "patience"                # Wait and observe
    COUNTER_PUNCH = "counter_punch"      # Respond bigger than opponent
    BAIT = "bait"                        # Small gift to bait overreaction
    FINISH = "finish"                    # Go for the kill


@dataclass
class OpponentAction:
    """Record of an opponent gift."""
    timestamp: float
    points: int
    cumulative_score: int


@dataclass
class PressureState:
    """Current state of the pressure engine."""
    # Scores
    ai_score: int = 0
    opponent_score: int = 0

    # Budget
    budget_remaining: int = 0
    budget_spent: int = 0

    # Time
    time_remaining: int = 300
    battle_start: float = field(default_factory=time.time)

    # Opponent tracking
    opponent_actions: List[OpponentAction] = field(default_factory=list)
    opponent_state: OpponentState = OpponentState.PASSIVE
    opponent_reaction_time: float = 0.0  # How fast they respond to us
    opponent_avg_gift_size: int = 0

    # Our tracking
    our_last_action_time: float = 0.0
    our_last_action_points: int = 0
    waiting_for_reaction: bool = False

    # Boost state
    in_boost: bool = False
    boost_multiplier: float = 1.0
    boost_time_remaining: int = 0


class PressureEngine:
    """
    Dynamic pressure-based decision engine.

    Core philosophy: Force the opponent to react to US, not the other way around.
    We control the tempo and apply psychological pressure.
    """

    # Reaction window - how long to wait for opponent response
    REACTION_WINDOW = 8.0  # seconds

    # Gift size thresholds
    PROBE_SIZE = 1000       # Small test gift
    MEDIUM_SIZE = 5000      # Standard pressure
    SHOW_SIZE = 20000       # Intimidation
    FINISH_SIZE = 50000     # Closing gift

    def __init__(self, total_budget: int):
        self.total_budget = total_budget
        self.state = PressureState(budget_remaining=total_budget)
        self.tactic_history: List[Tuple[float, PressureTactic, int]] = []

    def update_scores(self, ai_score: int, opponent_score: int, time_remaining: int):
        """Update current battle state."""
        self.state.ai_score = ai_score
        self.state.opponent_score = opponent_score
        self.state.time_remaining = time_remaining

    def record_opponent_action(self, points: int):
        """Record an opponent gift and analyze behavior."""
        now = time.time()
        action = OpponentAction(
            timestamp=now,
            points=points,
            cumulative_score=self.state.opponent_score
        )
        self.state.opponent_actions.append(action)

        # Update reaction tracking
        if self.state.waiting_for_reaction:
            reaction_time = now - self.state.our_last_action_time
            if reaction_time < self.REACTION_WINDOW:
                # They reacted to our move!
                self.state.opponent_reaction_time = (
                    self.state.opponent_reaction_time * 0.7 + reaction_time * 0.3
                )
            self.state.waiting_for_reaction = False

        # Update average gift size
        if self.state.opponent_actions:
            recent = self.state.opponent_actions[-10:]  # Last 10 gifts
            self.state.opponent_avg_gift_size = sum(a.points for a in recent) // len(recent)

        # Analyze opponent state
        self._analyze_opponent_state()

    def _analyze_opponent_state(self):
        """Determine opponent's psychological state."""
        actions = self.state.opponent_actions
        if len(actions) < 2:
            self.state.opponent_state = OpponentState.PASSIVE
            return

        recent = actions[-5:] if len(actions) >= 5 else actions
        time_span = recent[-1].timestamp - recent[0].timestamp if len(recent) > 1 else 1

        # Calculate metrics
        gift_rate = len(recent) / max(time_span, 1)  # gifts per second
        avg_size = sum(a.points for a in recent) / len(recent)
        size_variance = sum((a.points - avg_size) ** 2 for a in recent) / len(recent)

        # Classify state
        if gift_rate > 0.5 and avg_size > self.MEDIUM_SIZE:
            # Fast, big gifts = panicking
            self.state.opponent_state = OpponentState.PANICKING
        elif gift_rate > 0.3:
            # Fast gifts = aggressive
            self.state.opponent_state = OpponentState.AGGRESSIVE
        elif gift_rate < 0.05 and len(actions) > 10:
            # Slowed way down after activity = exhausted
            self.state.opponent_state = OpponentState.EXHAUSTED
        elif self.state.opponent_reaction_time > 0 and self.state.opponent_reaction_time < 5:
            # Responding to our moves = reactive
            self.state.opponent_state = OpponentState.REACTIVE
        else:
            self.state.opponent_state = OpponentState.PASSIVE

    def record_our_action(self, points: int, cost: int):
        """Record our gift and start watching for reaction."""
        now = time.time()
        self.state.our_last_action_time = now
        self.state.our_last_action_points = points
        self.state.waiting_for_reaction = True
        self.state.budget_spent += cost
        self.state.budget_remaining -= cost
        self.state.ai_score += points

    def set_boost(self, active: bool, multiplier: float = 1.0, time_remaining: int = 0):
        """Update boost state."""
        self.state.in_boost = active
        self.state.boost_multiplier = multiplier
        self.state.boost_time_remaining = time_remaining

    def decide_tactic(self) -> Tuple[PressureTactic, int]:
        """
        Decide next tactic based on game state.

        Returns: (tactic, recommended_spend)
        """
        state = self.state
        score_diff = state.ai_score - state.opponent_score
        budget_pct = state.budget_remaining / self.total_budget
        time_pct = state.time_remaining / 300

        # === BOOST PRIORITY ===
        if state.in_boost:
            return self._boost_tactic()

        # === ENDGAME (last 60 seconds) ===
        if state.time_remaining <= 60:
            return self._endgame_tactic(score_diff)

        # === RESPOND TO OPPONENT STATE ===

        if state.opponent_state == OpponentState.PANICKING:
            # They're panicking - stay patient, let them waste budget
            return (PressureTactic.PATIENCE, 0)

        if state.opponent_state == OpponentState.EXHAUSTED:
            # They're out - small gifts to secure, save for snipe defense
            return (PressureTactic.PROBE, self.PROBE_SIZE)

        if state.opponent_state == OpponentState.AGGRESSIVE:
            # Match aggression but smartly
            if score_diff < 0:
                # Behind - need to counter
                return (PressureTactic.COUNTER_PUNCH, int(state.opponent_avg_gift_size * 1.2))
            else:
                # Ahead - let them burn budget
                return (PressureTactic.PATIENCE, 0)

        # === PROACTIVE PRESSURE ===

        # Early game - establish dominance
        if time_pct > 0.7:
            if score_diff < 0:
                # Behind early - show strength
                return (PressureTactic.SHOW_STRENGTH, self.SHOW_SIZE)
            else:
                # Ahead or even - probe and control tempo
                return (PressureTactic.PROBE, self.PROBE_SIZE)

        # Mid game - pressure and bait
        if time_pct > 0.3:
            if state.opponent_state == OpponentState.REACTIVE:
                # They react to us - bait them into overspending
                return (PressureTactic.BAIT, self.MEDIUM_SIZE)
            elif state.opponent_state == OpponentState.PASSIVE:
                # They're passive - tempo burst to force reaction
                return (PressureTactic.TEMPO_BURST, self.PROBE_SIZE * 3)
            else:
                # Default: measured pressure
                return (PressureTactic.PROBE, self.MEDIUM_SIZE)

        # Late game approach - prepare for finish
        return (PressureTactic.PATIENCE, 0)

    def _boost_tactic(self) -> Tuple[PressureTactic, int]:
        """Tactic during boost window."""
        state = self.state

        # Calculate optimal spend for boost
        # Goal: maximize points * multiplier while considering opponent

        if state.boost_time_remaining > 15:
            # Early boost - medium pressure
            return (PressureTactic.TEMPO_BURST, self.MEDIUM_SIZE)
        elif state.boost_time_remaining > 5:
            # Mid boost - bigger push
            spend = min(state.budget_remaining * 0.15, self.SHOW_SIZE)
            return (PressureTactic.SHOW_STRENGTH, int(spend))
        else:
            # Boost ending - final burst
            spend = min(state.budget_remaining * 0.1, self.FINISH_SIZE)
            return (PressureTactic.FINISH, int(spend))

    def _endgame_tactic(self, score_diff: int) -> Tuple[PressureTactic, int]:
        """Tactic for final 60 seconds."""
        state = self.state

        if state.time_remaining <= 15:
            # Final seconds - all or nothing
            if score_diff < 0:
                # Behind - MUST catch up
                needed = abs(score_diff) + 1000  # Buffer
                spend = min(state.budget_remaining, needed)
                return (PressureTactic.FINISH, spend)
            else:
                # Ahead - defend against snipe
                # Keep enough to counter a big gift
                return (PressureTactic.PATIENCE, 0)

        elif state.time_remaining <= 30:
            if score_diff < 0:
                # Behind with 30s - big push
                spend = min(state.budget_remaining * 0.4, self.FINISH_SIZE)
                return (PressureTactic.SHOW_STRENGTH, int(spend))
            else:
                # Ahead - maintain pressure
                return (PressureTactic.PROBE, self.PROBE_SIZE)

        else:  # 30-60 seconds
            if score_diff < -10000:
                # Way behind - need to close gap
                spend = min(state.budget_remaining * 0.3, self.SHOW_SIZE)
                return (PressureTactic.SHOW_STRENGTH, int(spend))
            elif score_diff < 0:
                # Slightly behind - measured catch-up
                return (PressureTactic.TEMPO_BURST, self.MEDIUM_SIZE)
            else:
                # Ahead - control tempo
                return (PressureTactic.PATIENCE, 0)

    def get_gift_recommendation(self, available_gifts: List[dict]) -> Optional[dict]:
        """
        Get specific gift recommendation based on current tactic.

        available_gifts: List of dicts with 'name', 'cost', 'points' keys
        Returns: Selected gift dict or None for PATIENCE tactic
        """
        tactic, target_spend = self.decide_tactic()
        self.tactic_history.append((time.time(), tactic, target_spend))

        if tactic == PressureTactic.PATIENCE:
            return None

        if not available_gifts:
            return None

        # Filter by budget
        affordable = [g for g in available_gifts if g['cost'] <= self.state.budget_remaining]
        if not affordable:
            return None

        # Select based on tactic
        if tactic == PressureTactic.PROBE:
            # Smallest affordable gift
            return min(affordable, key=lambda g: g['cost'])

        elif tactic == PressureTactic.TEMPO_BURST:
            # Small-medium gift for rapid fire
            mid_point = target_spend // 3
            closest = min(affordable, key=lambda g: abs(g['cost'] - mid_point))
            return closest

        elif tactic in (PressureTactic.SHOW_STRENGTH, PressureTactic.COUNTER_PUNCH):
            # Gift closest to target spend
            closest = min(affordable, key=lambda g: abs(g['cost'] - target_spend))
            return closest

        elif tactic == PressureTactic.BAIT:
            # Medium gift to provoke reaction
            closest = min(affordable, key=lambda g: abs(g['cost'] - self.MEDIUM_SIZE))
            return closest

        elif tactic == PressureTactic.FINISH:
            # Biggest affordable gift up to target
            under_target = [g for g in affordable if g['cost'] <= target_spend]
            if under_target:
                return max(under_target, key=lambda g: g['cost'])
            return max(affordable, key=lambda g: g['cost'])

        return None

    def get_status_summary(self) -> str:
        """Get human-readable status."""
        state = self.state
        return (
            f"AI: {state.ai_score:,} | Opp: {state.opponent_score:,} "
            f"(diff: {state.ai_score - state.opponent_score:+,})\n"
            f"Budget: {state.budget_remaining:,}/{self.total_budget:,} "
            f"({state.budget_remaining/self.total_budget*100:.0f}%)\n"
            f"Opponent: {state.opponent_state.value} "
            f"(avg gift: {state.opponent_avg_gift_size:,}, "
            f"reaction: {state.opponent_reaction_time:.1f}s)\n"
            f"Time: {state.time_remaining}s"
        )
