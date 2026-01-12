"""
Pressure Engine v3 - Economic Efficiency Edition

Key strategic elements:
1. WIN with MINIMUM spending - coins have real monetary value
2. Secure victory threshold - stop spending when victory is assured
3. Conditional snipe - only use reserve if opponent threatens
4. ROI optimization - track coins saved as key metric
5. Boost/power-up awareness when needed
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
    Strategic pressure engine with ECONOMIC EFFICIENCY focus.

    Key principles:
    1. WIN with MINIMUM coins - every coin has real value
    2. Stop spending when victory is SECURE
    3. Snipe reserve is CONDITIONAL - only if opponent threatens
    4. Track ROI and coins saved
    5. Boost/power-up awareness when actively needed
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

    # === ECONOMIC EFFICIENCY THRESHOLDS ===
    SECURE_LEAD_MULTIPLIER = 10    # Victory secure if lead > 10x opponent score
    MIN_SECURE_MARGIN = 5000       # Minimum absolute margin to consider secure
    SNIPE_THREAT_THRESHOLD = 0.8   # Only snipe if opponent within 80% of our score

    # === BOOST-CENTRIC STRATEGY ===
    # Key insight: Coins spent during boost are worth 2-3x more
    # Strategy: CONSERVE outside boost, SPEND AGGRESSIVELY during boost
    BOOST_SPEND_PCT = 0.50         # Spend up to 50% of remaining budget during boost
    NON_BOOST_SPEND_PCT = 0.05     # Only 5% outside boost (observation mode)
    PROBE_INTERVAL_SECONDS = 15    # Probe every 15s outside boost

    # === COUNTER-SNIPE STRATEGY ===
    # Key insight: Opponents snipe at END of boost and END of battle
    # Strategy: Reserve coins for counter-sniping, react don't initiate
    BOOST_END_RESERVE_PCT = 0.30   # Keep 30% of boost budget for last 5s of boost
    BOOST_SNIPE_WINDOW = 5         # Last 5 seconds of boost = danger zone
    COUNTER_SNIPE_MULTIPLIER = 1.2 # Counter with 120% of opponent's snipe

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

    @property
    def is_victory_secure(self) -> bool:
        """
        Check if victory is economically secure.

        Victory is secure when:
        1. We're ahead by at least MIN_SECURE_MARGIN, AND
        2. Our lead is > SECURE_LEAD_MULTIPLIER times opponent score
        OR
        3. Opponent is EXHAUSTED and we're ahead

        When secure, we STOP spending to maximize ROI.
        """
        diff = self.score_diff
        opp_score = self.state.opponent_score
        opp_state = self.state.opponent_state

        # Must be ahead
        if diff <= 0:
            return False

        # If opponent is exhausted and we're ahead, victory is secure
        if opp_state == OpponentState.EXHAUSTED and diff > 0:
            return True

        # Must have minimum margin
        if diff < self.MIN_SECURE_MARGIN:
            return False

        # Lead must be > 10x opponent score (or opponent has 0)
        if opp_score > 0 and diff < opp_score * self.SECURE_LEAD_MULTIPLIER:
            return False

        return True

    @property
    def is_snipe_needed(self) -> bool:
        """
        Check if snipe defense is actually needed.

        Only snipe if opponent is a real threat (within SNIPE_THREAT_THRESHOLD).
        """
        ai_score = self.state.ai_score
        opp_score = self.state.opponent_score

        # If we're behind, always need snipe
        if ai_score <= opp_score:
            return True

        # If opponent is within threat threshold, need snipe
        if ai_score > 0 and opp_score / ai_score >= self.SNIPE_THREAT_THRESHOLD:
            return True

        # If margin is small, need snipe
        if ai_score - opp_score < self.MIN_SECURE_MARGIN:
            return True

        return False

    @property
    def coins_saved(self) -> int:
        """Calculate coins saved vs full budget usage."""
        return self.state.budget_remaining

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
        Decide next action based on BOOST-CENTRIC strategy.

        Key principle: Coins are 2-3x more valuable during boost.
        - BOOST ACTIVE → Spend aggressively
        - NO BOOST → Conserve, observe, minimal probes

        Returns: (tactic, recommended_spend, reason)
        """
        phase = self.phase
        boost = self.state.current_boost

        # === SNIPE WINDOW (Last 5 seconds) ===
        if phase == BattlePhase.SNIPE_WINDOW:
            return self._snipe_decision()

        # === ECONOMIC EFFICIENCY: Stop if victory is secure ===
        if self.is_victory_secure:
            diff = self.score_diff
            saved = self.coins_saved
            return (PressureTactic.RESERVE, 0,
                    f"Victory SECURE (+{diff:,} lead) - saving {saved:,} coins")

        # === BOOST PRIORITY - THIS IS WHERE WE SPEND ===
        if boost and boost.is_active:
            return self._boost_decision()

        # === NO BOOST - CONSERVATION MODE ===
        # Only respond to critical situations or probe occasionally

        # Critical: We're way behind and need to act
        if self.score_diff < -20000:
            return self._emergency_decision()

        # Counter only if opponent sent a VERY big gift (20k+)
        if self._should_counter_critical():
            return self._counter_decision()

        # Otherwise: Patience - wait for boost
        return self._conservation_decision()

    def _snipe_decision(self) -> Tuple[PressureTactic, int, str]:
        """
        Critical final 5 seconds decision - ECONOMIC EFFICIENCY.

        Only spend if snipe is actually needed!
        """
        diff = self.score_diff
        budget = self.state.budget_remaining

        if diff < 0:
            # BEHIND - Must snipe to win
            needed = abs(diff) + 1000  # Buffer
            spend = min(budget, needed, self.SNIPE_GIFT)
            return (PressureTactic.SNIPE_OFFENSIVE, spend,
                    f"Behind by {abs(diff):,} - offensive snipe")

        # === ECONOMIC: Check if snipe is actually needed ===
        if not self.is_snipe_needed:
            saved = self.coins_saved
            return (PressureTactic.RESERVE, 0,
                    f"Lead SECURE (+{diff:,}) - NO SNIPE needed, saving {saved:,} coins")

        elif diff < 5000:
            # CLOSE - Defensive snipe but minimal spend
            # Only spend enough to maintain small buffer
            spend = min(budget, 5000)  # Minimal defensive spend
            return (PressureTactic.SNIPE_DEFENSIVE, spend,
                    f"Close lead ({diff:,}) - minimal defense")

        else:
            # Moderate lead but opponent threatening
            # Spend proportionally to threat, not max
            opp_score = self.state.opponent_score
            threat_ratio = opp_score / max(self.state.ai_score, 1)
            spend = min(budget, int(diff * threat_ratio) + 2000)
            return (PressureTactic.SNIPE_DEFENSIVE, spend,
                    f"Lead ({diff:,}) with threat ({threat_ratio:.0%}) - proportional defense")

    def _boost_decision(self) -> Tuple[PressureTactic, int, str]:
        """
        SMART boost window spending with COUNTER-SNIPE awareness.

        Strategy:
        - Early/mid boost: Build lead with moderate spending
        - Last 5s of boost: WAIT for opponent snipe, then counter
        - React to opponent moves, don't just spend blindly
        """
        boost = self.state.current_boost
        time_left = boost.time_remaining
        mult = boost.multiplier
        available = self.available_budget
        diff = self.score_diff

        # === BOOST SNIPE WINDOW (last 5 seconds) ===
        if time_left <= self.BOOST_SNIPE_WINDOW:
            return self._boost_snipe_decision(mult, available, diff)

        # === EARLY/MID BOOST ===
        # Build lead but keep reserve for counter-snipe at end
        reserve_for_snipe = int(available * self.BOOST_END_RESERVE_PCT)
        spendable = available - reserve_for_snipe

        if time_left > 15:
            # Early boost - moderate start
            spend = min(spendable * 0.20, self.MEDIUM_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"🚀 BOOST x{mult} ({time_left:.0f}s) - building lead (reserve: {reserve_for_snipe:,})")

        elif time_left > 8:
            # Mid boost - push harder
            spend = min(spendable * 0.30, self.BIG_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"🚀 BOOST x{mult} ({time_left:.0f}s) - pushing (reserve: {reserve_for_snipe:,})")

        else:
            # Late boost (before snipe window) - prepare for counter
            spend = min(spendable * 0.25, self.MEDIUM_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"🚀 BOOST x{mult} ({time_left:.0f}s) - preparing counter-snipe")

    def _boost_snipe_decision(self, mult: float, available: int, diff: int) -> Tuple[PressureTactic, int, str]:
        """
        Handle last 5 seconds of boost - COUNTER-SNIPE mode.

        Strategy: Wait for opponent to snipe, then counter.
        If opponent doesn't snipe and we're ahead, save coins.
        """
        # Check if opponent just sniped (big gift in last 3 seconds)
        opponent_sniped = self._detect_recent_snipe(seconds=3)

        if opponent_sniped:
            # COUNTER-SNIPE: Respond with multiplied amount
            snipe_amount = opponent_sniped
            counter = int(snipe_amount * self.COUNTER_SNIPE_MULTIPLIER)
            spend = min(available, counter)
            return (PressureTactic.COUNTER_STRIKE, spend,
                    f"⚡ COUNTER-SNIPE x{mult}! Opponent sent {snipe_amount:,}, countering with {spend:,}")

        elif diff < 0:
            # We're behind - need to push
            spend = min(available * 0.50, self.WHALE_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"🚀 BOOST ending, behind by {abs(diff):,} - pushing!")

        elif diff < 5000:
            # Close lead - small defensive spend
            spend = min(available * 0.20, self.MEDIUM_GIFT)
            return (PressureTactic.BOOST_MAXIMIZE, int(spend),
                    f"🚀 BOOST ending, close lead (+{diff:,}) - light defense")

        else:
            # Good lead - WAIT for opponent snipe, save coins
            return (PressureTactic.PATIENCE, 0,
                    f"⏳ BOOST ending, ahead +{diff:,} - WAITING for opponent snipe")

    def _detect_recent_snipe(self, seconds: int = 3) -> int:
        """Detect if opponent sent a big gift recently (potential snipe)."""
        if not self.state.opponent_actions:
            return 0

        now = time.time()
        recent_big_gifts = [
            a.points for a in self.state.opponent_actions
            if now - a.timestamp < seconds and a.points >= self.BIG_GIFT_THRESHOLD
        ]

        return sum(recent_big_gifts) if recent_big_gifts else 0

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

    def _should_counter_critical(self) -> bool:
        """Check if we should counter a CRITICAL opponent gift (20k+)."""
        if not self.state.opponent_actions:
            return False

        last_action = self.state.opponent_actions[-1]
        time_since = time.time() - last_action.timestamp

        # Only counter VERY big gifts (20k+) outside of boost
        return (last_action.points >= 20000 and
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

    def _emergency_decision(self) -> Tuple[PressureTactic, int, str]:
        """Emergency: We're way behind (20k+) and need to act even without boost."""
        diff = self.score_diff
        available = self.available_budget

        # Spend minimally to close the gap - save rest for boost
        spend = min(available * 0.15, self.MEDIUM_GIFT)
        return (PressureTactic.SHOW_STRENGTH, int(spend),
                f"EMERGENCY: Behind {abs(diff):,} - minimal recovery (waiting for boost)")

    def _conservation_decision(self) -> Tuple[PressureTactic, int, str]:
        """
        Conservation mode: No boost active, save coins.

        Only send occasional small probes to observe opponent.
        """
        diff = self.score_diff
        saved = self.coins_saved
        time_since_last = time.time() - self.state.last_action_time

        # If we're ahead, just wait
        if diff > 0:
            return (PressureTactic.RESERVE, 0,
                    f"Leading +{diff:,} - CONSERVING for boost (saved {saved:,})")

        # If we're slightly behind, occasional probe every 15s
        if time_since_last > self.PROBE_INTERVAL_SECONDS and diff > -10000:
            return (PressureTactic.PRESSURE_TEST, self.MIN_PROBE,
                    f"Behind {abs(diff):,} - light probe (conserving for boost)")

        # Otherwise, patience - wait for boost
        return (PressureTactic.PATIENCE, 0,
                f"No boost - WAITING (saved {saved:,} coins for boost)")

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
            'ai_has_gloves': self.state.ai_has_gloves,
            # Economic metrics
            'coins_saved': self.coins_saved,
            'coins_saved_pct': self.coins_saved / self.total_budget * 100,
            'victory_secure': self.is_victory_secure,
            'snipe_needed': self.is_snipe_needed,
        }
