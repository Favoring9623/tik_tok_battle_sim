"""
Advanced Phase System for TikTok Battles

Implements:
- 300s battle duration (5 minutes)
- Random Boost #1 in 10s-30s window (not compulsory)
- Random Boost #2 in 120s-160s window with threshold (not compulsory)
- Stacking multipliers (boost * glove)
- Glove x5 in boosts OR last 30 seconds (with fog combo)
- Hammer, Fog, and Time Bonus power-ups
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class PhaseType(Enum):
    """Types of battle phases."""
    NORMAL = "normal"          # x1 multiplier
    BOOST_X2 = "boost_x2"     # x2 multiplier
    BOOST_X3 = "boost_x3"     # x3 multiplier
    GLOVE_X5 = "glove_x5"     # x5 multiplier (glove triggered)


class PowerUpType(Enum):
    """Available power-ups."""
    GLOVE = "glove"           # Can trigger x5
    HAMMER = "hammer"         # Neutralize opponent x5
    FOG = "fog"              # Hide score
    TIME_BONUS = "time_bonus" # Add +25s


@dataclass
class PhaseDefinition:
    """Defines a battle phase."""
    name: str
    start_time: int
    end_time: int
    multiplier: float
    phase_type: PhaseType
    auto_trigger: bool = True
    condition_met: bool = False


@dataclass
class PowerUp:
    """Represents a power-up item."""
    type: PowerUpType
    owner: str  # "creator" or "opponent"
    used: bool = False
    activated_at: Optional[int] = None


@dataclass
class PhaseCondition:
    """Conditions for triggering Boost #2 phase."""
    time_window: int = 40  # 40 seconds window (120s-160s)

    @staticmethod
    def generate_random_threshold() -> int:
        """
        Generate random point threshold for Boost #2.
        Range: 2 to 80,000+ coins with weighted distribution.
        """
        roll = random.random()

        if roll < 0.15:  # 15% - Very easy (2-50)
            return random.randint(2, 50)
        elif roll < 0.35:  # 20% - Easy (50-500)
            return random.randint(50, 500)
        elif roll < 0.60:  # 25% - Medium (500-5,000)
            return random.randint(500, 5000)
        elif roll < 0.80:  # 20% - Hard (5,000-20,000)
            return random.randint(5000, 20000)
        elif roll < 0.95:  # 15% - Very hard (20,000-50,000)
            return random.randint(20000, 50000)
        else:  # 5% - Extreme (50,000-100,000)
            return random.randint(50000, 100000)


class AdvancedPhaseManager:
    """
    Manages advanced battle phases with random triggering.

    Features:
    - 300s duration (5 minutes)
    - Random Boost #1 (10s-30s window, not compulsory)
    - Random Boost #2 (120s-160s window, with threshold, not compulsory)
    - Stacking multipliers (boost * glove = e.g. x3 * x5 = x15)
    - Glove x5 during boosts OR last 30 seconds
    - Fog can hide glove activation in final seconds
    """

    def __init__(self, battle_duration: int = 300, enigma_mode: bool = True):
        self.battle_duration = battle_duration
        self.enigma_mode = enigma_mode  # Hide Boost #2 details for suspense!
        self.current_phase: Optional[PhaseDefinition] = None
        self.phases_history: List[PhaseDefinition] = []

        # Boost #1 tracking (random in 10s-30s window)
        self.boost1_window_start = 10
        self.boost1_window_end = 30
        self.boost1_triggered = False
        self.boost1_trigger_time = None  # Random time when it will trigger (or None if not triggering)
        self.boost1_active = False
        self.boost1_multiplier = 1.0
        self.boost1_end_time = None

        # Decide randomly if Boost #1 will happen (70% chance)
        if random.random() < 0.70:
            self.boost1_trigger_time = random.randint(self.boost1_window_start, self.boost1_window_end)
            self.boost1_multiplier = random.choice([2.0, 3.0])
            print(f"\n🎲 Boost #1 scheduled at {self.boost1_trigger_time}s (x{int(self.boost1_multiplier)})")
        else:
            print(f"\n🎲 Boost #1 will NOT trigger this battle")

        # Boost #2 tracking (random in 120s-160s window, with threshold)
        self.boost2_window_start = 120
        self.boost2_window_end = 160
        self.boost2_triggered = False
        self.boost2_trigger_time = None
        self.boost2_active = False
        self.boost2_multiplier = 1.0
        self.boost2_end_time = None
        self.boost2_threshold = None  # Only set if boost #2 is triggered
        self.boost2_threshold_window_active = False
        self.boost2_threshold_window_start = None
        self.boost2_early_warning_shown = False  # 10s before threshold window
        self.boost2_creator_points = 0
        self.boost2_opponent_points = 0
        self.boost2_creator_qualified = False
        self.boost2_opponent_qualified = False

        # Decide randomly if Boost #2 will happen (60% chance)
        if random.random() < 0.60:
            self.boost2_trigger_time = random.randint(self.boost2_window_start, self.boost2_window_end)
            self.boost2_multiplier = random.choice([2.0, 3.0])
            self.boost2_threshold = PhaseCondition.generate_random_threshold()
            if self.enigma_mode:
                # ENIGMA MODE: Hide details, create mystery!
                print(f"🔮 Boost #2: ??? (Enigma Mode - details hidden)")
            else:
                print(f"🎲 Boost #2 scheduled at {self.boost2_trigger_time}s (x{int(self.boost2_multiplier)})")
                print(f"   Threshold: {self.boost2_threshold:,} coins (30s window before trigger)")
        else:
            if self.enigma_mode:
                print(f"🔮 Boost #2: ??? (Enigma Mode - will it happen?)")
            else:
                print(f"🎲 Boost #2 will NOT trigger this battle")

        # Glove tracking
        self.gloves_sent = []  # List of (time, team, activated, multiplier) tuples
        self.active_glove_x5 = None  # Currently active x5 phase
        self.active_glove_owner = None  # Who owns the active glove: "creator" or "opponent"
        self.glove_end_time = None
        self.last_glove_bonuses = []  # Bonuses applied to last glove (name, value)
        self.last_glove_base_chance = 0  # Base chance of last glove
        self.last_glove_final_chance = 0  # Final activation chance

        # Detailed glove stats by condition
        self.glove_stats = {
            'boost': {'sent': 0, 'activated': 0},      # During boost windows
            'final_30s': {'sent': 0, 'activated': 0},  # Last 30 seconds
            'normal': {'sent': 0, 'activated': 0},     # Normal phase
            'with_bonuses': {'sent': 0, 'activated': 0}  # Had any bonus modifiers
        }

        # Power-ups inventory
        self.power_ups: List[PowerUp] = []

        # Time bonus
        self.time_bonuses_used = 0
        self.max_time_bonuses = 1

        # Fog tracking
        self.fog_active = False
        self.fog_end_time = 0

        # Score tracking (for glove bonus calculations)
        self.creator_score = 0
        self.opponent_score = 0

        # === CLUTCH MOMENTS TRACKING ===
        self.score_history = []  # Track score over time for comeback detection
        self.max_deficit = 0     # Worst deficit we've been in
        self.comeback_active = False  # True if we recovered from 20%+ deficit
        self.clutch_moments_triggered = []  # List of clutch moments this battle
        self.last_clutch_announcement = None  # Prevent spam

        # Start with normal phase
        self.current_phase = PhaseDefinition(
            name="Battle Phase",
            start_time=0,
            end_time=self.battle_duration,
            multiplier=1.0,
            phase_type=PhaseType.NORMAL,
            auto_trigger=True
        )

        print(f"⏱️  Battle duration: {self.battle_duration}s (5 minutes)")

    def update(self, current_time: int):
        """Update phase system based on current time."""

        # Check for Boost #1 activation (10s-30s window)
        if (self.boost1_trigger_time is not None and
            not self.boost1_triggered and
            current_time >= self.boost1_trigger_time):
            self._activate_boost1(current_time)

        # Check for Boost #1 end (lasts 20 seconds)
        if self.boost1_active and self.boost1_end_time and current_time >= self.boost1_end_time:
            self._deactivate_boost1(current_time)

        # Check for Boost #2 EARLY WARNING (40s before trigger = 10s before threshold window)
        # Maximum suspense - announce it's coming!
        if (self.boost2_trigger_time is not None and
            not self.boost2_early_warning_shown and
            not self.boost2_triggered and
            current_time >= self.boost2_trigger_time - 40):
            self._show_boost2_early_warning(current_time)

        # Check for Boost #2 threshold window (30s before trigger time)
        if (self.boost2_trigger_time is not None and
            not self.boost2_threshold_window_active and
            not self.boost2_triggered and
            current_time >= self.boost2_trigger_time - 30):
            self._start_boost2_threshold_window(current_time)

        # Check for Boost #2 activation
        if (self.boost2_trigger_time is not None and
            not self.boost2_triggered and
            current_time >= self.boost2_trigger_time):
            self._check_and_activate_boost2(current_time)

        # Check for Boost #2 end (lasts 30 seconds)
        if self.boost2_active and self.boost2_end_time and current_time >= self.boost2_end_time:
            self._deactivate_boost2(current_time)

        # Check if active glove x5 should end (30 seconds duration)
        if self.active_glove_x5 and self.glove_end_time and current_time >= self.glove_end_time:
            print(f"\n⏱️  x5 Glove boost ended (after 30s) - was {self.active_glove_owner}'s")
            self.active_glove_x5 = None
            self.active_glove_owner = None
            self.glove_end_time = None

        # Check if fog should end
        if self.fog_active and current_time >= self.fog_end_time:
            self.fog_active = False
            print(f"\n🌫️ Fog cleared - scores visible again")

    def _activate_boost1(self, current_time: int):
        """Activate Boost #1."""
        self.boost1_triggered = True
        self.boost1_active = True
        self.boost1_end_time = current_time + 20  # Lasts 20 seconds

        phase_type = PhaseType.BOOST_X2 if self.boost1_multiplier == 2.0 else PhaseType.BOOST_X3
        self.current_phase = PhaseDefinition(
            name=f"Boost #1 - x{int(self.boost1_multiplier)}",
            start_time=current_time,
            end_time=self.boost1_end_time,
            multiplier=self.boost1_multiplier,
            phase_type=phase_type,
            auto_trigger=False
        )

        print(f"\n{'='*60}")
        print(f"🔥 BOOST #1 ACTIVATED! (x{int(self.boost1_multiplier)})")
        print(f"   Duration: {current_time}s - {self.boost1_end_time}s (20 seconds)")
        print(f"{'='*60}\n")

    def _deactivate_boost1(self, current_time: int):
        """Deactivate Boost #1."""
        self.boost1_active = False
        self.current_phase = PhaseDefinition(
            name="Battle Phase",
            start_time=current_time,
            end_time=self.battle_duration,
            multiplier=1.0,
            phase_type=PhaseType.NORMAL,
            auto_trigger=True
        )
        print(f"\n⏱️  Boost #1 ended - back to normal (x1)")

    def _show_boost2_early_warning(self, current_time: int):
        """Show early warning 10 seconds before threshold window opens."""
        self.boost2_early_warning_shown = True
        time_to_threshold = self.boost2_trigger_time - 30 - current_time
        time_to_boost = self.boost2_trigger_time - current_time

        if self.enigma_mode:
            # ENIGMA MODE: Mysterious cryptic warning!
            print(f"\n{'🔮'*30}")
            print(f"✨ Something is stirring in the void... ✨")
            print(f"   🌀 An energy disturbance detected...")
            print(f"   ⏳ The threshold window approaches...")
            print(f"   💫 Prepare yourselves... in ~{time_to_threshold}s")
            print(f"{'🔮'*30}\n")
        else:
            print(f"\n{'⚡'*30}")
            print(f"🚨 BOOST #2 INCOMING! 🚨")
            print(f"   ⏱️  Threshold window opens in {time_to_threshold}s")
            print(f"   🔥 Boost #2 (x{int(self.boost2_multiplier)}) triggers at {self.boost2_trigger_time}s ({time_to_boost}s)")
            print(f"   🎯 Threshold: {self.boost2_threshold:,} coins")
            print(f"   💡 Send roses NOW to signal for qualification!")
            print(f"{'⚡'*30}\n")

    def _start_boost2_threshold_window(self, current_time: int):
        """Start the 30-second threshold window before Boost #2."""
        self.boost2_threshold_window_active = True
        self.boost2_threshold_window_start = current_time
        self.boost2_creator_points = 0
        self.boost2_opponent_points = 0

        if self.enigma_mode:
            # ENIGMA MODE: Dramatic reveal of the threshold!
            print(f"\n{'🔮'*30}")
            print(f"⚡⚡⚡ THE ENIGMA REVEALS ITSELF! ⚡⚡⚡")
            print(f"")
            print(f"   🎯 BOOST #2 THRESHOLD: {self.boost2_threshold:,} COINS")
            print(f"   ⏱️  You have 30 SECONDS to qualify!")
            print(f"   🔥 Multiplier: x{int(self.boost2_multiplier)}")
            print(f"")
            print(f"   💀 Will you make it in time?!")
            print(f"{'🔮'*30}\n")
        else:
            print(f"\n🎯 Boost #2 Threshold Window OPEN! (30 seconds)")
            print(f"   Target: {self.boost2_threshold:,} coins for both teams")
            print(f"   Boost triggers at {self.boost2_trigger_time}s")

    def _check_and_activate_boost2(self, current_time: int):
        """Check threshold and activate Boost #2."""
        self.boost2_triggered = True
        self.boost2_threshold_window_active = False

        # Check who qualified
        self.boost2_creator_qualified = self.boost2_creator_points >= self.boost2_threshold
        self.boost2_opponent_qualified = self.boost2_opponent_points >= self.boost2_threshold

        if self.boost2_creator_qualified or self.boost2_opponent_qualified:
            self.boost2_active = True
            self.boost2_end_time = current_time + 30  # Lasts 30 seconds

            if self.boost2_creator_qualified and self.boost2_opponent_qualified:
                boost_label = "BOTH"
                print(f"\n🎯🎯 BOTH teams qualified for Boost #2!")
            elif self.boost2_creator_qualified:
                boost_label = "CREATOR"
                print(f"\n🎯 CREATOR qualified for Boost #2!")
                print(f"   ❌ Opponent failed: {self.boost2_opponent_points:,}/{self.boost2_threshold:,}")
            else:
                boost_label = "OPPONENT"
                print(f"\n🎯 OPPONENT qualified for Boost #2!")
                print(f"   ❌ Creator failed: {self.boost2_creator_points:,}/{self.boost2_threshold:,}")

            phase_type = PhaseType.BOOST_X2 if self.boost2_multiplier == 2.0 else PhaseType.BOOST_X3
            self.current_phase = PhaseDefinition(
                name=f"Boost #2 - x{int(self.boost2_multiplier)} ({boost_label})",
                start_time=current_time,
                end_time=self.boost2_end_time,
                multiplier=self.boost2_multiplier,
                phase_type=phase_type,
                auto_trigger=False
            )

            print(f"\n{'='*60}")
            print(f"🔥 BOOST #2 ACTIVATED! (x{int(self.boost2_multiplier)})")
            print(f"   Duration: {current_time}s - {self.boost2_end_time}s (30 seconds)")
            print(f"{'='*60}\n")
        else:
            print(f"\n❌ Boost #2 NOT activated - no one reached threshold")
            print(f"   Creator: {self.boost2_creator_points:,}/{self.boost2_threshold:,}")
            print(f"   Opponent: {self.boost2_opponent_points:,}/{self.boost2_threshold:,}")

    def _deactivate_boost2(self, current_time: int):
        """Deactivate Boost #2."""
        self.boost2_active = False
        self.current_phase = PhaseDefinition(
            name="Final Phase",
            start_time=current_time,
            end_time=self.battle_duration,
            multiplier=1.0,
            phase_type=PhaseType.NORMAL,
            auto_trigger=True
        )
        print(f"\n⏱️  Boost #2 ended - back to normal (x1)")

    def record_gift(self, gift_type: str, points: int, team: str, current_time: int) -> float:
        """
        Record a gift and handle special mechanics.
        Returns the effective multiplier to apply (boost * glove stacking).
        """
        # Track for Boost #2 qualification during threshold window
        if self.boost2_threshold_window_active:
            if team == "creator" and not self.boost2_creator_qualified:
                self.boost2_creator_points += points
                if self.boost2_creator_points >= self.boost2_threshold:
                    self.boost2_creator_qualified = True
                    print(f"\n🎯✅ CREATOR reached Boost #2 threshold!")
                    print(f"   {self.boost2_creator_points:,}/{self.boost2_threshold:,} coins")

            elif team == "opponent" and not self.boost2_opponent_qualified:
                self.boost2_opponent_points += points
                if self.boost2_opponent_points >= self.boost2_threshold:
                    self.boost2_opponent_qualified = True
                    print(f"\n🎯✅ OPPONENT reached Boost #2 threshold!")
                    print(f"   {self.boost2_opponent_points:,}/{self.boost2_threshold:,} coins")

        # Update score tracking for glove bonus calculations
        if team == "creator":
            self.creator_score += points
        else:
            self.opponent_score += points

        # Handle Glove mechanics
        if "GLOVE" in gift_type.upper() or "🥊" in gift_type:
            return self._handle_glove(team, current_time, points)

        # Calculate stacked multiplier (boost * glove)
        return self._get_stacked_multiplier()

    def update_scores(self, creator_score: int, opponent_score: int):
        """Update score tracking for glove bonus calculations."""
        self.creator_score = creator_score
        self.opponent_score = opponent_score

    def _get_stacked_multiplier(self) -> float:
        """
        Get the current stacked multiplier (boost + glove, additive).

        Example: 10,000 coins during x3 boost + x5 glove:
        - 10,000 × 3 = 30,000 (from boost)
        - 10,000 × 5 = 50,000 (from glove)
        - Total = 80,000 (effectively x8)
        """
        total_multiplier = 1.0

        # Add boost multiplier if active
        if self.boost1_active:
            total_multiplier = self.boost1_multiplier
        elif self.boost2_active:
            total_multiplier = self.boost2_multiplier

        # Add glove multiplier (additive: x3 + x5 = x8, not x3 * x5 = x15)
        if self.active_glove_x5:
            # Additive: base + (glove - 1) because base already includes x1
            # x3 boost + x5 glove = x3 + x5 = x8
            boost_value = total_multiplier
            glove_value = 5.0
            return boost_value + glove_value

        return total_multiplier

    def _handle_glove(self, team: str, current_time: int, points: int) -> float:
        """
        Handle glove gift mechanics.

        Glove can trigger x5 if:
        1. Sent during active boost (x2 or x3), OR
        2. Sent in last 30 seconds

        Multipliers are ADDITIVE: boost + glove
        Example: x3 boost + x5 glove = x8 (not x15)
        10,000 coins → 30,000 + 50,000 = 80,000
        """
        can_trigger_x5 = False

        # Condition 1: During active boost
        if self.boost1_active or self.boost2_active:
            can_trigger_x5 = True

        # Condition 2: Last 30 seconds
        if current_time >= self.battle_duration - 30:
            can_trigger_x5 = True

        # Random activation (40% chance if conditions met)
        x5_activated = False
        if can_trigger_x5:
            x5_activated = random.random() < 0.40

        # Calculate the stacked multiplier (additive)
        base_multiplier = 1.0
        if self.boost1_active:
            base_multiplier = self.boost1_multiplier
        elif self.boost2_active:
            base_multiplier = self.boost2_multiplier

        # Additive: x3 + x5 = x8
        final_multiplier = base_multiplier + 5.0 if x5_activated else base_multiplier

        self.gloves_sent.append((current_time, team, x5_activated, final_multiplier))

        if x5_activated:
            # Activate x5 for 30 seconds
            self.active_glove_x5 = True
            self.active_glove_owner = team  # Track who owns this glove!
            self.glove_end_time = current_time + 30

            # Check if fog is hiding the activation
            fog_hidden = self.fog_active and current_time >= self.battle_duration - 30

            print(f"\n{'🥊'*30}")
            print(f"💥 GLOVE x5 ACTIVATED by {team.upper()}! (30s)")
            print(f"   Additive: x{int(base_multiplier)} boost + x5 glove = x{int(final_multiplier)}")
            if fog_hidden:
                print(f"   🌫️ FOG ACTIVE - Opponent cannot see this boost!")
            print(f"{'🥊'*30}\n")

            return final_multiplier
        else:
            print(f"   🥊 {team.capitalize()} sent Glove (no x5 trigger)")
            return base_multiplier

    def use_power_up(self, power_up_type: PowerUpType, team: str, current_time: int) -> bool:
        """Use a power-up. Returns True if successfully used."""
        available = [p for p in self.power_ups
                    if p.type == power_up_type and p.owner == team and not p.used]

        if not available:
            return False

        power_up = available[0]
        power_up.used = True
        power_up.activated_at = current_time

        if power_up_type == PowerUpType.GLOVE:
            # Glove power-up: PROBABILISTIC x5 activation with BONUS MODIFIERS
            # Agent must learn which conditions stack for best activation chance
            import random

            in_boost = self.boost1_active or self.boost2_active
            in_final_30s = current_time >= self.battle_duration - 30
            in_final_5s = current_time >= self.battle_duration - 5

            # === BASE PROBABILITY ===
            # Boost windows and final 30s are mutually exclusive (never overlap)
            if in_boost:
                base_chance = 0.40  # During boost: 40% base
            elif in_final_30s:
                base_chance = 0.35  # Last 30s: 35% base
            else:
                base_chance = 0.08  # Normal phase: 8% base (very risky)

            # === BONUS MODIFIERS (agent must learn these!) ===
            bonuses = []

            # BONUS 1: Last 5 seconds of battle - critical clutch moment
            if in_final_5s:
                bonuses.append(("clutch_5s", 0.25))

            # BONUS 2: Score distance - closer battles favor the underdog
            score_diff = abs(self.creator_score - self.opponent_score) if hasattr(self, 'creator_score') else 0
            if score_diff < 3000:
                bonuses.append(("nail_biter", 0.20))  # Very close: +20%
            elif score_diff < 8000:
                bonuses.append(("competitive", 0.10))  # Competitive: +10%

            # BONUS 3: Behind in score (underdog bonus)
            if hasattr(self, 'creator_score') and self.creator_score < self.opponent_score:
                deficit = self.opponent_score - self.creator_score
                if deficit > 10000:
                    bonuses.append(("underdog_large", 0.15))  # Big deficit: +15%
                elif deficit > 5000:
                    bonuses.append(("underdog_medium", 0.10))  # Medium deficit: +10%

            # BONUS 4: Contributed to Boost #2 threshold (rewarding team play)
            if self.boost2_creator_qualified and self.boost2_creator_points > 0:
                contribution_ratio = self.boost2_creator_points / max(1, self.boost2_threshold)
                if contribution_ratio >= 1.0:
                    bonuses.append(("boost2_hero", 0.15))  # Met threshold: +15%
                elif contribution_ratio >= 0.5:
                    bonuses.append(("boost2_contributor", 0.08))  # Halfway: +8%

            # BONUS 5: Fog is active (hidden advantage)
            if self.fog_active:
                bonuses.append(("fog_cover", 0.12))  # Fog active: +12%

            # === CLUTCH MOMENT BONUSES (Maximum Drama!) ===

            # BONUS 6: Comeback Momentum - Recovered from 20%+ deficit
            if self._check_comeback_momentum():
                bonuses.append(("comeback_momentum", 0.15))
                self._announce_clutch_moment("comeback_momentum")

            # BONUS 7: Final Stand - Last 10s, within 5% of opponent
            if self._check_final_stand(current_time):
                bonuses.append(("final_stand", 0.20))
                self._announce_clutch_moment("final_stand")

            # BONUS 8: Threshold Heroics - Within 500 coins of boost threshold
            if self._check_threshold_heroics():
                bonuses.append(("threshold_heroics", 0.25))
                self._announce_clutch_moment("threshold_heroics")

            # BONUS 9: Desperation Surge - Losing by 30%+ in final minute
            if self._check_desperation_surge(current_time):
                bonuses.append(("desperation_surge", 0.10))
                self._announce_clutch_moment("desperation_surge")

            # === CALCULATE FINAL PROBABILITY ===
            activation_chance = base_chance
            for name, bonus in bonuses:
                activation_chance += bonus

            # Cap at 85% - never guaranteed!
            activation_chance = min(0.85, activation_chance)

            # Store for UI display
            self.last_glove_bonuses = bonuses.copy()
            self.last_glove_base_chance = base_chance
            self.last_glove_final_chance = activation_chance

            # Roll the dice!
            x5_activated = random.random() < activation_chance

            # Track stats by condition
            if in_boost:
                self.glove_stats['boost']['sent'] += 1
                if x5_activated:
                    self.glove_stats['boost']['activated'] += 1
            elif in_final_30s:
                self.glove_stats['final_30s']['sent'] += 1
                if x5_activated:
                    self.glove_stats['final_30s']['activated'] += 1
            else:
                self.glove_stats['normal']['sent'] += 1
                if x5_activated:
                    self.glove_stats['normal']['activated'] += 1

            # Track if any bonuses were applied
            if bonuses:
                self.glove_stats['with_bonuses']['sent'] += 1
                if x5_activated:
                    self.glove_stats['with_bonuses']['activated'] += 1

            base_multiplier = 1.0
            if self.boost1_active:
                base_multiplier = self.boost1_multiplier
            elif self.boost2_active:
                base_multiplier = self.boost2_multiplier

            # Build bonus string for output
            bonus_str = ", ".join([f"{name}+{int(b*100)}%" for name, b in bonuses]) if bonuses else "none"

            if x5_activated:
                self.active_glove_x5 = True
                self.active_glove_owner = team  # Track who owns this glove!
                self.glove_end_time = current_time + 30
                final_mult = base_multiplier + 5.0

                print(f"\n{'🥊'*30}")
                print(f"💥 GLOVE x5 ACTIVATED by {team.upper()}! (30s)")
                print(f"   Additive: x{int(base_multiplier)} boost + x5 glove = x{int(final_mult)}")
                print(f"   Base: {int(base_chance*100)}% | Bonuses: {bonus_str}")
                print(f"   Final chance: {int(activation_chance * 100)}%")
                print(f"{'🥊'*30}\n")
            else:
                print(f"\n🥊 Glove deployed but x5 did NOT activate!")
                print(f"   Base: {int(base_chance*100)}% | Bonuses: {bonus_str}")
                print(f"   Final chance: {int(activation_chance * 100)}% - unlucky roll")

            # Glove is always consumed (used), regardless of activation
            return True

        elif power_up_type == PowerUpType.HAMMER:
            # Hammer only works against OPPONENT's glove, not your own!
            opponent_team = "opponent" if team == "creator" else "creator"
            if self.active_glove_x5 and self.active_glove_owner == opponent_team:
                print(f"\n🔨 HAMMER ACTIVATED! {opponent_team.upper()}'s x5 NEUTRALIZED!")
                self.active_glove_x5 = None
                self.active_glove_owner = None
                self.glove_end_time = None
                return True
            elif self.active_glove_x5 and self.active_glove_owner == team:
                print(f"\n🔨 Hammer REFUSED - can't neutralize your OWN glove!")
                power_up.used = False  # Refund
                return False
            else:
                print(f"\n🔨 Hammer has no target - no opponent glove active")
                power_up.used = False  # Refund
                return False

        elif power_up_type == PowerUpType.FOG:
            self.fog_active = True
            self.fog_end_time = current_time + 15
            print(f"\n🌫️ FOG ACTIVATED! Scores HIDDEN for 15s!")
            return True

        elif power_up_type == PowerUpType.TIME_BONUS:
            # Best used in last 5 seconds - adds 25s to current elapsed time
            if self.time_bonuses_used < self.max_time_bonuses:
                self.battle_duration += 25
                self.time_bonuses_used += 1
                time_left = self.battle_duration - current_time
                print(f"\n⏱️ TIME BONUS ACTIVATED! +25 seconds!")
                print(f"   New duration: {self.battle_duration}s ({time_left}s remaining)")
                return True

        return False

    def add_power_up(self, power_up_type: PowerUpType, owner: str):
        """Add a power-up to team inventory."""
        self.power_ups.append(PowerUp(type=power_up_type, owner=owner))

    def get_current_multiplier(self) -> float:
        """Get the current effective stacked multiplier."""
        return self._get_stacked_multiplier()

    def get_phase_info(self) -> Dict:
        """Get current phase information."""
        if not self.current_phase:
            return {}

        return {
            'name': self.current_phase.name,
            'multiplier': self._get_stacked_multiplier(),
            'base_multiplier': self.current_phase.multiplier,
            'type': self.current_phase.phase_type.value,
            'start': self.current_phase.start_time,
            'end': self.current_phase.end_time,
            'glove_x5_active': self.active_glove_x5 is not None,
            'boost1_active': self.boost1_active,
            'boost2_active': self.boost2_active
        }

    def get_analytics(self) -> Dict:
        """Get phase analytics."""
        return {
            'total_phases': len(self.phases_history) + (1 if self.current_phase else 0),
            'boost1_triggered': self.boost1_triggered,
            'boost1_multiplier': self.boost1_multiplier if self.boost1_triggered else None,
            'boost2_triggered': self.boost2_triggered,
            'boost2_multiplier': self.boost2_multiplier if self.boost2_triggered else None,
            'boost2_threshold': self.boost2_threshold,
            'boost2_creator_qualified': self.boost2_creator_qualified,
            'boost2_opponent_qualified': self.boost2_opponent_qualified,
            'boost2_creator_points': self.boost2_creator_points,
            'boost2_opponent_points': self.boost2_opponent_points,
            'gloves_sent': len(self.gloves_sent),
            'gloves_activated': sum(1 for _, _, activated, _ in self.gloves_sent if activated),
            'glove_stats': self.glove_stats,
            'time_bonuses_used': self.time_bonuses_used,
            'final_duration': self.battle_duration,
            'power_ups_used': sum(1 for p in self.power_ups if p.used)
        }

    def get_glove_stats_by_condition(self) -> Dict:
        """Get detailed glove stats for UI display."""
        stats = {}
        for condition, data in self.glove_stats.items():
            sent = data['sent']
            activated = data['activated']
            rate = (activated / sent * 100) if sent > 0 else 0
            stats[condition] = {
                'sent': sent,
                'activated': activated,
                'rate': round(rate, 1)
            }
        return stats

    def get_boost1_status(self) -> Dict:
        """Get Boost #1 status."""
        return {
            'will_trigger': self.boost1_trigger_time is not None,
            'trigger_time': self.boost1_trigger_time,
            'triggered': self.boost1_triggered,
            'active': self.boost1_active,
            'multiplier': self.boost1_multiplier,
            'end_time': self.boost1_end_time
        }

    def get_boost2_status(self) -> Dict:
        """Get Boost #2 status."""
        progress_creator = 0
        progress_opponent = 0
        if self.boost2_threshold and self.boost2_threshold > 0:
            progress_creator = min(100, (self.boost2_creator_points / self.boost2_threshold) * 100)
            progress_opponent = min(100, (self.boost2_opponent_points / self.boost2_threshold) * 100)

        return {
            'will_trigger': self.boost2_trigger_time is not None,
            'trigger_time': self.boost2_trigger_time,
            'threshold': self.boost2_threshold,
            'early_warning_shown': self.boost2_early_warning_shown,
            'threshold_window_active': self.boost2_threshold_window_active,
            'triggered': self.boost2_triggered,
            'active': self.boost2_active,
            'multiplier': self.boost2_multiplier,
            'end_time': self.boost2_end_time,
            'creator_points': self.boost2_creator_points,
            'opponent_points': self.boost2_opponent_points,
            'creator_progress': progress_creator,
            'opponent_progress': progress_opponent,
            'creator_qualified': self.boost2_creator_qualified,
            'opponent_qualified': self.boost2_opponent_qualified
        }

    def is_in_final_30s(self, current_time: int) -> bool:
        """Check if we're in the last 30 seconds (glove + fog combo zone)."""
        return current_time >= self.battle_duration - 30

    def get_active_glove_status(self, current_time: int) -> Dict:
        """Get status of active glove including bonuses and countdown."""
        if not self.active_glove_x5:
            return {
                'active': False,
                'owner': None,
                'time_remaining': 0,
                'bonuses': [],
                'base_chance': 0,
                'final_chance': 0
            }

        time_remaining = max(0, self.glove_end_time - current_time) if self.glove_end_time else 0

        # Convert bonus tuples to readable format
        bonus_labels = {
            'clutch_5s': 'Last 5s clutch',
            'nail_biter': 'Nail-biter (<3k)',
            'competitive': 'Competitive (<8k)',
            'underdog_large': 'Underdog (>10k)',
            'underdog_medium': 'Underdog (>5k)',
            'boost2_hero': 'Boost#2 hero',
            'boost2_contributor': 'Boost#2 contrib',
            'fog_cover': 'Fog cover',
            # New clutch moment bonuses
            'comeback_momentum': '🔥 COMEBACK!',
            'final_stand': '⚔️ FINAL STAND!',
            'threshold_heroics': '💎 THRESHOLD HERO!',
            'desperation_surge': '😤 DESPERATION!'
        }

        bonuses_display = [
            {
                'name': bonus_labels.get(name, name),
                'value': int(value * 100)
            }
            for name, value in self.last_glove_bonuses
        ]

        return {
            'active': True,
            'owner': self.active_glove_owner,
            'time_remaining': time_remaining,
            'bonuses': bonuses_display,
            'base_chance': int(self.last_glove_base_chance * 100),
            'final_chance': int(self.last_glove_final_chance * 100)
        }

    # === CLUTCH MOMENT DETECTION METHODS ===

    def update_score_tracking(self, creator_score: int, opponent_score: int):
        """Update score history for comeback detection."""
        self.creator_score = creator_score
        self.opponent_score = opponent_score

        # Track score history
        self.score_history.append((creator_score, opponent_score))
        if len(self.score_history) > 100:
            self.score_history = self.score_history[-100:]

        # Track max deficit
        if creator_score < opponent_score:
            deficit_pct = (opponent_score - creator_score) / max(1, opponent_score)
            if deficit_pct > self.max_deficit:
                self.max_deficit = deficit_pct

    def _check_comeback_momentum(self) -> bool:
        """Check if we've made a comeback from 15%+ deficit (BALANCE v1.1: was 20%)."""
        if self.max_deficit < 0.15:  # Never had 15%+ deficit (was 0.2)
            return False

        # Currently close or ahead?
        if self.opponent_score <= 0:
            return False
        current_diff_pct = (self.creator_score - self.opponent_score) / max(1, self.opponent_score)

        # Recovered to within 10% or ahead
        if current_diff_pct > -0.10 and self.max_deficit >= 0.15:  # was 0.2
            if not self.comeback_active:
                self.comeback_active = True
                return True
            return self.comeback_active

        return False

    def _check_final_stand(self, current_time: int) -> bool:
        """Check if we're in final stand mode - last 15s, within 8% (BALANCE v1.1)."""
        time_remaining = self.battle_duration - current_time
        if time_remaining > 15:  # was 10s
            return False

        # Within 8%? (was 5%)
        total_score = max(1, self.creator_score + self.opponent_score)
        score_diff_pct = abs(self.creator_score - self.opponent_score) / total_score

        return score_diff_pct < 0.08  # was 0.05

    def _check_threshold_heroics(self) -> bool:
        """Check if we're within 750 coins of boost threshold (BALANCE v1.1: was 500)."""
        if not self.boost2_threshold_window_active:
            return False

        if self.boost2_creator_qualified:
            return False  # Already qualified

        remaining = self.boost2_threshold - self.boost2_creator_points
        return 0 < remaining <= 750  # was 500

    def _check_desperation_surge(self, current_time: int) -> bool:
        """Check if we're losing badly (25%+) in final minute (BALANCE v1.1: was 30%)."""
        time_remaining = self.battle_duration - current_time
        if time_remaining > 60:
            return False

        if self.opponent_score <= 0:
            return False

        deficit_pct = (self.opponent_score - self.creator_score) / self.opponent_score
        return deficit_pct >= 0.25  # was 0.30

    def _announce_clutch_moment(self, moment_type: str):
        """Announce clutch moment with maximum drama!"""
        # Prevent spam - only announce once per moment type
        if moment_type in self.clutch_moments_triggered:
            return

        self.clutch_moments_triggered.append(moment_type)

        announcements = {
            'comeback_momentum': '''
╔══════════════════════════════════════════════════════════════╗
║  🔥🔥🔥  C O M E B A C K   M O M E N T U M  🔥🔥🔥           ║
║                                                              ║
║     From the ashes... A PHOENIX RISES!                       ║
║     +15% Glove Probability ACTIVATED                         ║
╚══════════════════════════════════════════════════════════════╝''',

            'final_stand': '''
╔══════════════════════════════════════════════════════════════╗
║  ⚔️⚔️⚔️  F I N A L   S T A N D  ⚔️⚔️⚔️                       ║
║                                                              ║
║     THIS IS IT! Everything on the line!                      ║
║     +20% Glove Probability ACTIVATED                         ║
╚══════════════════════════════════════════════════════════════╝''',

            'threshold_heroics': '''
╔══════════════════════════════════════════════════════════════╗
║  💎💎💎  T H R E S H O L D   H E R O I C S  💎💎💎           ║
║                                                              ║
║     SO CLOSE! Every coin counts now!                         ║
║     +25% Glove Probability ACTIVATED                         ║
╚══════════════════════════════════════════════════════════════╝''',

            'desperation_surge': '''
╔══════════════════════════════════════════════════════════════╗
║  😤😤😤  D E S P E R A T I O N   S U R G E  😤😤😤           ║
║                                                              ║
║     NOTHING TO LOSE! Going all in!                           ║
║     +10% Glove Probability ACTIVATED                         ║
╚══════════════════════════════════════════════════════════════╝'''
        }

        if moment_type in announcements:
            print(announcements[moment_type])

    def get_clutch_status(self) -> Dict:
        """Get current clutch moment status."""
        return {
            'comeback_active': self.comeback_active,
            'max_deficit': self.max_deficit,
            'moments_triggered': self.clutch_moments_triggered.copy(),
            'score_history_len': len(self.score_history)
        }


# Helper function for phase-aware gift sending
def apply_phase_multiplier(base_points: int, manager: AdvancedPhaseManager,
                          gift_type: str, team: str, current_time: int) -> int:
    """
    Apply phase multiplier to gift points.
    This handles all special mechanics (gloves, boosts, stacking).
    """
    multiplier = manager.record_gift(gift_type, base_points, team, current_time)
    return int(base_points * multiplier)


if __name__ == '__main__':
    # Demo
    print("Advanced Phase System Demo (300s battle)")
    print("="*70)

    manager = AdvancedPhaseManager(battle_duration=300)

    # Simulate battle
    print("\n📍 t=0s: Battle starts")
    manager.update(0)

    print("\n📍 Simulating through boost windows...")

    # Simulate through boost #1 window
    for t in range(0, 50, 5):
        manager.update(t)
        if manager.boost1_active:
            print(f"   t={t}s: Boost #1 active (x{int(manager.boost1_multiplier)})")

    # Jump to boost #2 threshold window
    print("\n📍 t=100s: Approaching Boost #2 window...")
    for t in range(100, 200, 10):
        manager.update(t)

        # Simulate gifts during threshold window
        if manager.boost2_threshold_window_active:
            manager.record_gift("Rose", 1000, "creator", t)
            manager.record_gift("Rose", 800, "opponent", t)

        if manager.boost2_active:
            print(f"   t={t}s: Boost #2 active (x{int(manager.boost2_multiplier)})")

    # Test glove in last 30 seconds
    print("\n📍 t=275s: Last 30 seconds - testing glove + fog combo")
    manager.update(275)
    manager.use_power_up(PowerUpType.FOG, "creator", 275)
    mult = manager.record_gift("GLOVE", 100, "creator", 276)
    print(f"   Glove multiplier: x{int(mult)}")

    print("\n📊 Analytics:")
    analytics = manager.get_analytics()
    for key, value in analytics.items():
        print(f"   {key}: {value}")
