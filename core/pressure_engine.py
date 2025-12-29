"""
Pressure Engine v2 - Strategic psychological warfare for TikTok battles.

Key strategic elements:
1. Boost periods (x2, x3) - maximize multiplied points
2. Power-ups (gloves, hammer, frog, time) - tactical advantages
3. Final 5-second snipe window - defensive or offensive
4. Meaningful probes (2000+ coins) - not roses
5. Context-aware counter-attacks
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple
import time


class OpponentState(Enum):
    """Detected opponent psychological state."""
    PASSIVE = "passive"           # Low activity, conserving
    REACTIVE = "reactive"         # Responding to our moves
    AGGRESSIVE = "aggressive"     # Actively pushing
    PANICKING = "panicking"       # Erratic high spending
    EXHAUSTED = "exhausted"       # Budget likely depleted


class BattlePhase(Enum):
    """Current battle phase."""
    OPENING = "opening"           # First 60s - establish position
    MID_BATTLE = "mid_battle"     # 60-180s - main engagement
    LATE_GAME = "late_game"       # 180-240s - prepare for finish
    ENDGAME = "endgame"           # 240-295s - final push
    SNIPE_WINDOW = "snipe_window" # Last 5s - critical moment


class PowerUpType(Enum):
    """TikTok battle power-ups."""
    GLOVES = "gloves"             # 2x next gift value
    HAMMER = "hammer"             # Damage to opponent
    FROG = "frog"                 # Random bonus
    TIME_BONUS = "time_bonus"     # Extra seconds


class PressureTactic(Enum):
    """Available tactical moves."""
    # Offensive
    SHOW_STRENGTH = "show_strength"     # Big gift to intimidate (15k+)
    COUNTER_STRIKE = "counter_strike"   # Respond strategically to opponent
    BOOST_MAXIMIZE = "boost_maximize"   # All-in during boost
    SNIPE_OFFENSIVE = "snipe_offensive" # Final 5s attack to win

    # Defensive
    SNIPE_DEFENSIVE = "snipe_defensive" # Final 5s defense
    PATIENCE = "patience"               # Wait and observe
    RESERVE = "reserve"                 # Save budget for later

    # Probing / Pressure
    PRESSURE_TEST = "pressure_test"     # Meaningful probe (2k+ coins)
    TEMPO_CONTROL = "tempo_control"     # Control the rhythm
    BAIT = "bait"                       # Provoke overreaction


@dataclass
class OpponentAction:
    """Record of an opponent gift."""
    timestamp: float
    points: int
    gift_name: str = ""
    is_power_up: bool = False
    power_up_type: Optional[PowerUpType] = None


@dataclass
class BoostWindow:
    """Active boost window."""
    multiplier: float
    start_time: float
    duration: int = 20
    coins_spent: int = 0
    points_earned: int = 0

    @property
    def time_remaining(self) -> float:
        return max(0, self.duration - (time.time() - self.start_time))

    @property
    def is_active(self) -> bool:
        return self.time_remaining > 0


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
    battle_duration: int = 300

    # Opponent tracking
    opponent_actions: List[OpponentAction] = field(default_factory=list)
    opponent_state: OpponentState = OpponentState.PASSIVE
    opponent_last_big_gift_time: float = 0.0
    opponent_estimated_budget_used: int = 0

    # Power-up state
    ai_has_gloves: bool = False
    opponent_has_gloves: bool = False

    # Boost tracking
    current_boost: Optional[BoostWindow] = None
    boost_history: List[BoostWindow] = field(default_factory=list)

    # Our action tracking
    last_action_time: float = 0.0
    last_action_cost: int = 0

    # Snipe tracking
    snipe_reserve: int = 0  # Reserved for final 5s


class StrategicPressureEngine:
    """
    Strategic pressure engine with boost/power-up awareness.

    Key principles:
    1. Boost windows are PRIORITY - maximize multiplied points
    2. Power-ups change the game - track and respond
    3. Final 5 seconds are CRITICAL - always have snipe reserve
    4. Probes must be meaningful - 2000+ coins minimum
    5. Counter-attacks are contextual - timing matters
    """

    # Gift thresholds (meaningful amounts)
    MIN_PROBE = 2000           # Minimum to provoke reaction
    MEDIUM_GIFT = 5000         # Standard pressure
    BIG_GIFT = 15000           # Show strength
    WHALE_GIFT = 30000         # Intimidation
    SNIPE_GIFT = 45000         # Final snipe

    # Big gift detection threshold
    BIG_GIFT_THRESHOLD = 10000

    # Snipe reserve percentage
    SNIPE_RESERVE_PCT = 0.15   # Reserve 15% for final 5s

    def __init__(self, total_budget: int, battle_duration: int = 300):
        self.total_budget = total_budget
        self.battle_duration = battle_duration
        self.state = PressureState(
            budget_remaining=total_budget,
            battle_duration=battle_duration,
            snipe_reserve=int(total_budget * self.SNIPE_RESERVE_PCT)
        )

    @property
    def phase(self) -> BattlePhase:
        """Determine current battle phase."""
        remaining = self.state.time_remaining
        if remaining <= 5:
            return BattlePhase.SNIPE_WINDOW
        elif remaining <= 60:
            return BattlePhase.ENDGAME
        elif remaining <= 120:
            return BattlePhase.LATE_GAME
        elif remaining <= 240:
            return BattlePhase.MID_BATTLE
        else:
            return BattlePhase.OPENING

    @property
    def score_diff(self) -> int:
        """Current score differential (positive = AI ahead)."""
        return self.state.ai_score - self.state.opponent_score

    @property
    def available_budget(self) -> int:
        """Budget available for non-snipe actions."""
        if self.phase == BattlePhase.SNIPE_WINDOW:
            return self.state.budget_remaining
        return max(0, self.state.budget_remaining - self.state.snipe_reserve)

    def update_time(self, time_remaining: int):
        """Update time remaining."""
        self.state.time_remaining = time_remaining

    def update_scores(self, ai_score: int, opponent_score: int):
        """Update scores."""
        self.state.ai_score = ai_score
        self.state.opponent_score = opponent_score

    def record_opponent_gift(self, points: int, gift_name: str = "",
                              is_power_up: bool = False,
                              power_up_type: Optional[PowerUpType] = None):
        """Record opponent gift and analyze."""
        now = time.time()

        action = OpponentAction(
            timestamp=now,
            points=points,
            gift_name=gift_name,
            is_power_up=is_power_up,
            power_up_type=power_up_type
        )
        self.state.opponent_actions.append(action)

        # Track big gifts
        if points >= self.BIG_GIFT_THRESHOLD:
            self.state.opponent_last_big_gift_time = now

        # Track opponent budget usage (estimate)
        self.state.opponent_estimated_budget_used += points

        # Track power-ups
        if is_power_up and power_up_type == PowerUpType.GLOVES:
            self.state.opponent_has_gloves = True

        self._analyze_opponent()

    def _analyze_opponent(self):
        """Analyze opponent behavior."""
        actions = self.state.opponent_actions
        if len(actions) < 3:
            self.state.opponent_state = OpponentState.PASSIVE
            return

        recent = actions[-10:]
        now = time.time()

        # Calculate metrics
        time_span = now - recent[0].timestamp if recent else 1
        gift_rate = len(recent) / max(time_span, 1)
        avg_points = sum(a.points for a in recent) / len(recent)
        big_gifts = sum(1 for a in recent if a.points >= self.BIG_GIFT_THRESHOLD)

        # Classify
        if big_gifts >= 3 and gift_rate > 0.2:
            self.state.opponent_state = OpponentState.PANICKING
        elif gift_rate > 0.3 or avg_points > self.MEDIUM_GIFT:
            self.state.opponent_state = OpponentState.AGGRESSIVE
        elif gift_rate < 0.05 and self.state.opponent_estimated_budget_used > 50000:
            self.state.opponent_state = OpponentState.EXHAUSTED
        elif gift_rate > 0.1:
            self.state.opponent_state = OpponentState.REACTIVE
        else:
            self.state.opponent_state = OpponentState.PASSIVE

    def start_boost(self, multiplier: float, duration: int = 20):
        """Start a boost window."""
        self.state.current_boost = BoostWindow(
            multiplier=multiplier,
            start_time=time.time(),
            duration=duration
        )

    def end_boost(self):
        """End current boost and record stats."""
        if self.state.current_boost:
            self.state.boost_history.append(self.state.current_boost)
            self.state.current_boost = None

    def set_power_up(self, power_up: PowerUpType, is_ai: bool = True):
        """Record power-up acquisition."""
        if power_up == PowerUpType.GLOVES:
            if is_ai:
                self.state.ai_has_gloves = True
            else:
                self.state.opponent_has_gloves = True

    def use_gloves(self):
        """Mark AI gloves as used."""
        self.state.ai_has_gloves = False

    def record_our_action(self, cost: int, points: int):
        """Record our gift."""
        self.state.last_action_time = time.time()
        self.state.last_action_cost = cost
        self.state.budget_spent += cost
        self.state.budget_remaining -= cost
        self.state.ai_score += points

        # Track boost spending
        if self.state.current_boost and self.state.current_boost.is_active:
            self.state.current_boost.coins_spent += cost
            self.state.current_boost.points_earned += points

    def decide_action(self) -> Tuple[PressureTactic, int, str]:
        """
        Decide next action based on strategic context.

        Returns: (tactic, recommended_spend, reason)
        """
        phase = self.phase
        boost = self.state.current_boost

        # === SNIPE WINDOW (Last 5 seconds) ===
        if phase == BattlePhase.SNIPE_WINDOW:
            return self._snipe_decision()

        # === BOOST PRIORITY ===
        if boost and boost.is_active:
            return self._boost_decision()

        # === RESPOND TO OPPONENT BIG GIFT ===
        if self._should_counter():
            return self._counter_decision()

        # === PHASE-BASED TACTICS ===
        if phase == BattlePhase.OPENING:
            return self._opening_decision()
        elif phase == BattlePhase.MID_BATTLE:
            return self._mid_battle_decision()
        elif phase == BattlePhase.LATE_GAME:
            return self._late_game_decision()
        elif phase == BattlePhase.ENDGAME:
            return self._endgame_decision()

        return (PressureTactic.PATIENCE, 0, "Default patience")

    def _snipe_decision(self) -> Tuple[PressureTactic, int, str]:
        """Critical final 5 seconds decision."""
        diff = self.score_diff
        budget = self.state.budget_remaining

        if diff < 0:
            # BEHIND - Must snipe to win
            needed = abs(diff) + 1000  # Buffer
            spend = min(budget, needed, self.SNIPE_GIFT)
            return (PressureTactic.SNIPE_OFFENSIVE, spend,
                    f"Behind by {abs(diff):,} - offensive snipe")

        elif diff < 5000:
            # CLOSE - Defensive snipe ready
            # Wait and watch, respond if opponent attacks
            return (PressureTactic.SNIPE_DEFENSIVE, min(budget, self.SNIPE_GIFT),
                    f"Close lead ({diff:,}) - defensive snipe ready")

        else:
            # COMFORTABLE LEAD - Still defend
            return (PressureTactic.SNIPE_DEFENSIVE, min(budget, diff + 5000),
                    f"Comfortable lead ({diff:,}) - snipe defense ready")

    def _boost_decision(self) -> Tuple[PressureTactic, int, str]:
        """Maximize boost window value."""
        boost = self.state.current_boost
        time_left = boost.time_remaining
        mult = boost.multiplier
        available = self.available_budget

        # Calculate optimal spend based on remaining boost time
        if time_left > 15:
            # Early boost - ramp up
            spend = min(available * 0.2, self.MEDIUM_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"Boost x{mult} ({time_left:.0f}s left) - ramping up")

        elif time_left > 8:
            # Mid boost - push harder
            spend = min(available * 0.3, self.BIG_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"Boost x{mult} ({time_left:.0f}s left) - pushing")

        elif time_left > 3:
            # Late boost - maximize
            spend = min(available * 0.4, self.WHALE_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"Boost x{mult} ({time_left:.0f}s left) - maximizing")

        else:
            # Boost ending - final push
            spend = min(available * 0.25, self.BIG_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"Boost x{mult} ending - final push")

    def _should_counter(self) -> bool:
        """Check if we should counter opponent's recent big gift."""
        if not self.state.opponent_actions:
            return False

        last_action = self.state.opponent_actions[-1]
        time_since = time.time() - last_action.timestamp

        # Counter if opponent sent big gift in last 5 seconds
        return (last_action.points >= self.BIG_GIFT_THRESHOLD and
                time_since < 5 and
                self.score_diff < 0)

    def _counter_decision(self) -> Tuple[PressureTactic, int, str]:
        """Strategic counter to opponent's big gift."""
        last_gift = self.state.opponent_actions[-1].points
        diff = self.score_diff
        available = self.available_budget

        # Counter with enough to take lead plus buffer
        needed = abs(diff) + 2000
        spend = min(available, needed, self.WHALE_GIFT)

        # If we have gloves, this is doubled - spend less
        if self.state.ai_has_gloves:
            spend = spend // 2

        return (PressureTactic.COUNTER_STRIKE, int(spend),
                f"Counter opponent's {last_gift:,} gift - need {needed:,} to lead")

    def _opening_decision(self) -> Tuple[PressureTactic, int, str]:
        """Opening phase (first 60s) - establish position."""
        diff = self.score_diff
        available = self.available_budget
        opp_state = self.state.opponent_state

        if diff < -5000:
            # Behind significantly - show strength
            spend = min(available * 0.15, self.BIG_GIFT)
            return (PressureTactic.SHOW_STRENGTH, int(spend),
                    f"Behind {abs(diff):,} in opening - establishing position")

        elif opp_state == OpponentState.PASSIVE:
            # Opponent passive - probe to gauge
            return (PressureTactic.PRESSURE_TEST, self.MIN_PROBE,
                    "Probing passive opponent")

        elif opp_state == OpponentState.AGGRESSIVE:
            # Opponent aggressive early - let them spend
            return (PressureTactic.PATIENCE, 0,
                    "Opponent aggressive - conserving")

        else:
            # Control tempo
            return (PressureTactic.TEMPO_CONTROL, self.MIN_PROBE,
                    "Opening tempo control")

    def _mid_battle_decision(self) -> Tuple[PressureTactic, int, str]:
        """Mid battle (60-180s) - main engagement."""
        diff = self.score_diff
        available = self.available_budget
        opp_state = self.state.opponent_state

        if opp_state == OpponentState.PANICKING:
            # Opponent panicking - let them exhaust
            return (PressureTactic.PATIENCE, 0,
                    "Opponent panicking - letting them exhaust")

        elif opp_state == OpponentState.EXHAUSTED:
            # Opponent exhausted - light pressure to maintain
            return (PressureTactic.TEMPO_CONTROL, self.MIN_PROBE,
                    "Opponent exhausted - maintaining lead")

        elif diff < -10000:
            # Way behind - need to push
            spend = min(available * 0.2, self.BIG_GIFT)
            return (PressureTactic.SHOW_STRENGTH, int(spend),
                    f"Behind {abs(diff):,} mid-battle - pushing")

        elif diff > 10000:
            # Comfortable lead - control
            return (PressureTactic.PATIENCE, 0,
                    f"Leading by {diff:,} - controlling")

        else:
            # Close battle - pressure test
            return (PressureTactic.PRESSURE_TEST, self.MEDIUM_GIFT,
                    "Close battle - pressure testing")

    def _late_game_decision(self) -> Tuple[PressureTactic, int, str]:
        """Late game (180-240s) - prepare for finish."""
        diff = self.score_diff
        available = self.available_budget

        if diff < -15000:
            # Need to close gap before endgame
            spend = min(available * 0.25, self.BIG_GIFT)
            return (PressureTactic.SHOW_STRENGTH, int(spend),
                    f"Behind {abs(diff):,} late game - closing gap")

        elif diff < 0:
            # Slightly behind - measured push
            spend = min(available * 0.15, self.MEDIUM_GIFT)
            return (PressureTactic.TEMPO_CONTROL, int(spend),
                    "Slightly behind - measured push")

        else:
            # Ahead - reserve for endgame
            return (PressureTactic.RESERVE, 0,
                    f"Leading {diff:,} - reserving for endgame")

    def _endgame_decision(self) -> Tuple[PressureTactic, int, str]:
        """Endgame (last 60s, before snipe window)."""
        diff = self.score_diff
        available = self.available_budget
        time_left = self.state.time_remaining

        if diff < -20000:
            # Way behind - all-in push
            spend = min(available * 0.5, self.WHALE_GIFT)
            return (PressureTactic.SHOW_STRENGTH, int(spend),
                    f"Way behind ({diff:,}) in endgame - all-in")

        elif diff < 0:
            # Behind - strategic push based on time
            if time_left > 30:
                spend = min(available * 0.3, self.BIG_GIFT)
                return (PressureTactic.SHOW_STRENGTH, int(spend),
                        f"Behind {abs(diff):,} with {time_left}s - pushing")
            else:
                # Save more for snipe
                spend = min(available * 0.2, self.MEDIUM_GIFT)
                return (PressureTactic.TEMPO_CONTROL, int(spend),
                        f"Behind {abs(diff):,} - saving for snipe")

        elif diff < 10000:
            # Close lead - stay alert
            return (PressureTactic.PATIENCE, 0,
                    f"Close lead ({diff:,}) - snipe defense ready")

        else:
            # Comfortable lead - light maintenance
            return (PressureTactic.PATIENCE, 0,
                    f"Comfortable lead ({diff:,}) - maintaining")

    def get_gift_for_tactic(self, tactic: PressureTactic, target_spend: int,
                            available_gifts: List[dict]) -> Optional[dict]:
        """
        Select appropriate gift for tactic.

        available_gifts: List of dicts with 'name', 'cost', 'points'
        """
        if tactic in (PressureTactic.PATIENCE, PressureTactic.RESERVE):
            return None

        if not available_gifts:
            return None

        # Determine available budget based on phase
        if self.phase == BattlePhase.SNIPE_WINDOW:
            # Snipe window: use ALL remaining budget
            budget = self.state.budget_remaining
        else:
            # Before snipe: respect snipe reserve
            budget = self.available_budget
            if budget < self.MIN_PROBE:
                # Not enough budget outside reserve - wait for snipe
                return None

        # Filter by budget
        affordable = [g for g in available_gifts if g['cost'] <= budget]
        if not affordable:
            return None

        # CRITICAL: Never send gifts smaller than MIN_PROBE (except in snipe window)
        if self.phase != BattlePhase.SNIPE_WINDOW:
            meaningful = [g for g in affordable if g['cost'] >= self.MIN_PROBE]
            if not meaningful:
                # Can't afford meaningful gift - save for snipe
                return None
            affordable = meaningful

        # For snipe tactics, maximize spend
        if tactic in (PressureTactic.SNIPE_OFFENSIVE, PressureTactic.SNIPE_DEFENSIVE):
            target_spend = min(target_spend, budget)
            # In snipe window, get biggest possible
            return max(affordable, key=lambda g: g['cost'])

        # Select closest to target
        if target_spend > 0:
            under_target = [g for g in affordable if g['cost'] <= target_spend]
            if under_target:
                return max(under_target, key=lambda g: g['cost'])
            # If nothing under target, get smallest meaningful affordable
            return min(affordable, key=lambda g: g['cost'])

        # Default: smallest meaningful gift
        return min(affordable, key=lambda g: g['cost'])

    def get_status(self) -> Dict:
        """Get current status for display."""
        boost_info = None
        if self.state.current_boost and self.state.current_boost.is_active:
            boost_info = {
                'multiplier': self.state.current_boost.multiplier,
                'time_remaining': self.state.current_boost.time_remaining
            }

        return {
            'phase': self.phase.value,
            'ai_score': self.state.ai_score,
            'opponent_score': self.state.opponent_score,
            'score_diff': self.score_diff,
            'budget_remaining': self.state.budget_remaining,
            'budget_pct': self.state.budget_remaining / self.total_budget * 100,
            'snipe_reserve': self.state.snipe_reserve,
            'time_remaining': self.state.time_remaining,
            'opponent_state': self.state.opponent_state.value,
            'boost': boost_info,
            'ai_has_gloves': self.state.ai_has_gloves
        }
