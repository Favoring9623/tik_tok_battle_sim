"""
Multiplier System - x2/x3/x5 mechanics for TikTok battles.

Manages three types of multipliers:
1. Automatic x2/x3 sessions (random trigger at start)
2. Conditional x2/x3 sessions (threshold-based: 5 roses OR 1000 points in 15s)
3. x5 Strike (glove-triggered during sessions or final 30s)
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import random


class MultiplierType(Enum):
    """Types of multipliers available."""
    NONE = 1
    X2 = 2
    X3 = 3
    X5 = 5


@dataclass
class MultiplierSession:
    """Represents an active multiplier session."""
    multiplier: MultiplierType
    start_time: int
    duration: int
    source: str  # "auto", "threshold", "glove"

    @property
    def end_time(self) -> int:
        """When this session ends."""
        return self.start_time + self.duration

    def is_active(self, current_time: int) -> bool:
        """Check if session is currently active."""
        return self.start_time <= current_time < self.end_time

    def __repr__(self):
        return f"x{self.multiplier.value} ({self.start_time}s-{self.end_time}s, {self.source})"


class ThresholdTracker:
    """
    Tracks gift activity for threshold-based session activation.

    Monitors:
    - Rose count in sliding 15s window
    - Total points in sliding 15s window
    """

    def __init__(self):
        self.activity_log: List[Dict[str, Any]] = []
        self.window_duration = 15  # 15 second window

    def record_gift(self, time: int, gift_name: str, points: int):
        """Record a gift for threshold tracking."""
        self.activity_log.append({
            "time": time,
            "gift": gift_name,
            "points": points,
            "is_rose": gift_name.lower() == "rose"
        })

    def get_activity_in_window(self, current_time: int) -> Dict[str, Any]:
        """Get activity within the last 15 seconds."""
        window_start = max(0, current_time - self.window_duration)

        recent_activity = [
            act for act in self.activity_log
            if window_start <= act["time"] <= current_time
        ]

        rose_count = sum(1 for act in recent_activity if act["is_rose"])
        total_points = sum(act["points"] for act in recent_activity)

        return {
            "rose_count": rose_count,
            "total_points": total_points,
            "gift_count": len(recent_activity),
            "window_start": window_start,
            "window_end": current_time,
        }

    def check_threshold(self, current_time: int, rose_threshold: int = 5,
                       point_threshold: int = 1000) -> bool:
        """
        Check if activation threshold has been met.

        Returns True if:
        - 5+ roses in last 15s, OR
        - 1000+ points in last 15s
        """
        activity = self.get_activity_in_window(current_time)

        rose_threshold_met = activity["rose_count"] >= rose_threshold
        point_threshold_met = activity["total_points"] >= point_threshold

        return rose_threshold_met or point_threshold_met


class MultiplierManager:
    """
    Manages all multiplier mechanics for a battle.

    Handles:
    - Automatic x2/x3 sessions
    - Threshold-triggered bonus sessions
    - x5 glove strikes
    - Hammer counters (x5 neutralization)
    """

    def __init__(self, battle_duration: int = 60, analytics=None):
        """
        Initialize multiplier manager.

        Args:
            battle_duration: Total battle length (60s or 180s)
            analytics: Optional BattleAnalytics instance for data collection
        """
        self.battle_duration = battle_duration
        self.analytics = analytics
        self.current_multiplier = MultiplierType.NONE
        self.active_sessions: List[MultiplierSession] = []
        self.session_history: List[MultiplierSession] = []

        # Threshold tracking for bonus sessions
        self.threshold_tracker = ThresholdTracker()

        # Configuration based on battle duration
        if battle_duration >= 180:
            # 180-second battle timeline
            self.auto_session_window = (60, 90)
            self.bonus_attempt_window = (90, 100)
            self.final_30s_start = 150
        else:
            # 60-second battle timeline (scaled down)
            self.auto_session_window = (15, 35)
            self.bonus_attempt_window = (35, 45)
            self.final_30s_start = 30

        # Auto-session configuration
        self.auto_session_triggered = False
        self.auto_session_time = None
        self.auto_session_multiplier = None

        # Bonus session configuration
        self.bonus_session_available = True
        self.bonus_session_triggered = False

        # x5 strike configuration
        self.x5_success_probability = 0.3  # 30% base chance
        self.active_x5_strike = None
        self.x5_can_be_hammered = True

    def initialize_auto_session(self):
        """
        Plan the automatic x2/x3 session.

        Called at battle start. Randomly determines:
        - When session will trigger (within window)
        - Which multiplier (x2 or x3)
        - Session duration (20-30s)
        """
        # Random time within auto session window
        window_start, window_end = self.auto_session_window
        self.auto_session_time = random.randint(window_start, window_start + 5)

        # Random multiplier (x2 or x3)
        self.auto_session_multiplier = random.choice([MultiplierType.X2, MultiplierType.X3])

        print(f"\n🎲 Auto-session planned: x{self.auto_session_multiplier.value} at {self.auto_session_time}s")

    def update(self, current_time: int):
        """
        Update multiplier state each second.

        Handles:
        - Auto-session triggering
        - Session expiration
        - Current multiplier calculation
        """
        # Trigger auto-session if time has come
        if (not self.auto_session_triggered and
            self.auto_session_time and
            current_time >= self.auto_session_time):
            self._trigger_auto_session(current_time)

        # Update active sessions
        self._update_active_sessions(current_time)

        # Calculate current multiplier (highest active)
        self._calculate_current_multiplier(current_time)

    def _trigger_auto_session(self, current_time: int):
        """Trigger the automatic x2/x3 session."""
        duration = random.randint(20, 30)

        session = MultiplierSession(
            multiplier=self.auto_session_multiplier,
            start_time=current_time,
            duration=duration,
            source="auto"
        )

        self.active_sessions.append(session)
        self.auto_session_triggered = True

        print(f"\n{'='*60}")
        print(f"🔥 AUTO x{session.multiplier.value} SESSION ACTIVATED!")
        print(f"   Duration: {duration} seconds")
        print(f"   Active: {current_time}s - {session.end_time}s")
        print(f"{'='*60}\n")

    def _update_active_sessions(self, current_time: int):
        """Remove expired sessions and announce endings."""
        for session in self.active_sessions[:]:
            if not session.is_active(current_time):
                print(f"\n⏱️  x{session.multiplier.value} session ended ({session.source})\n")

                # Record in analytics
                if self.analytics:
                    self.analytics.record_multiplier_session(
                        session_type=f"x{session.multiplier.value}",
                        start_time=session.start_time,
                        end_time=session.end_time,
                        source=session.source
                    )

                self.active_sessions.remove(session)
                self.session_history.append(session)

    def _calculate_current_multiplier(self, current_time: int):
        """Calculate current multiplier (highest active session)."""
        active_multipliers = [
            session.multiplier for session in self.active_sessions
            if session.is_active(current_time)
        ]

        if active_multipliers:
            # Get highest multiplier
            self.current_multiplier = max(active_multipliers, key=lambda m: m.value)
        else:
            self.current_multiplier = MultiplierType.NONE

    def record_gift(self, current_time: int, gift_name: str, base_points: int):
        """
        Record a gift for threshold tracking.

        Used by Activator to track toward bonus session threshold.
        """
        self.threshold_tracker.record_gift(current_time, gift_name, base_points)

    def attempt_bonus_session(self, current_time: int) -> bool:
        """
        Attempt to trigger bonus x2/x3 session via threshold.

        Returns True if successfully triggered, False otherwise.
        """
        # Check if bonus is available
        if not self.bonus_session_available:
            return False

        # Check if we're in bonus attempt window
        window_start, window_end = self.bonus_attempt_window
        if not (window_start <= current_time <= window_end):
            return False

        # Check threshold
        if self.threshold_tracker.check_threshold(current_time):
            self._trigger_bonus_session(current_time)
            return True

        return False

    def _trigger_bonus_session(self, current_time: int):
        """Trigger the threshold-based bonus session."""
        # Random x2 or x3
        multiplier = random.choice([MultiplierType.X2, MultiplierType.X3])
        duration = random.randint(20, 30)

        session = MultiplierSession(
            multiplier=multiplier,
            start_time=current_time,
            duration=duration,
            source="threshold"
        )

        self.active_sessions.append(session)
        self.bonus_session_available = False
        self.bonus_session_triggered = True

        activity = self.threshold_tracker.get_activity_in_window(current_time)

        print(f"\n{'='*60}")
        print(f"💥 BONUS x{multiplier.value} SESSION TRIGGERED!")
        print(f"   Threshold met: {activity['rose_count']} roses, {activity['total_points']} points")
        print(f"   Duration: {duration} seconds")
        print(f"   Active: {current_time}s - {session.end_time}s")
        print(f"{'='*60}\n")

    def attempt_x5_strike(self, current_time: int, agent_name: str) -> bool:
        """
        Attempt to trigger x5 multiplier via glove strike.

        Can be used at ANY time, but most efficient during:
        - Active x2/x3 session (additive multipliers: base×2 + base×5 = base×7)
        - Final 30 seconds (maximize impact on close battles)

        Returns True if x5 triggered, False otherwise.
        """
        # Probabilistic x5 trigger (can be used anytime)
        if random.random() < self.x5_success_probability:
            self._trigger_x5_strike(current_time, agent_name)
            return True

        return False

    def _can_use_glove(self, current_time: int) -> bool:
        """Check if gloves can be used at this time."""
        # During active x2/x3 session
        if any(s.multiplier in [MultiplierType.X2, MultiplierType.X3]
               for s in self.active_sessions if s.is_active(current_time)):
            return True

        # During final 30 seconds
        if current_time >= self.final_30s_start:
            return True

        return False

    def _trigger_x5_strike(self, current_time: int, agent_name: str):
        """Trigger x5 multiplier strike."""
        duration = 5  # x5 lasts 5 seconds

        session = MultiplierSession(
            multiplier=MultiplierType.X5,
            start_time=current_time,
            duration=duration,
            source=f"glove_{agent_name}"
        )

        self.active_sessions.append(session)
        self.active_x5_strike = session
        self.x5_can_be_hammered = True

        print(f"\n{'='*60}")
        print(f"💥💥💥 X5 STRIKE ACTIVATED BY {agent_name}!")
        print(f"   Duration: {duration} seconds")
        print(f"   Next gifts ×5 BONUS for {duration} seconds!")
        print(f"{'='*60}\n")

    def calculate_x5_bonus(self, base_gift_points: int) -> int:
        """
        Calculate x5 strike bonus for a gift that triggered the strike.

        The triggering gift gets:
        - Normal session multiplier (if active)
        - Plus base × 5 as x5 bonus (additive)

        Args:
            base_gift_points: Base points of the triggering gift

        Returns:
            Bonus points to add (base × 5)
        """
        return base_gift_points * 5

    def deploy_hammer(self, current_time: int, agent_name: str) -> bool:
        """
        Deploy hammer to neutralize active x5 strike.

        Returns True if x5 was neutralized, False if no x5 active.
        """
        if not self.active_x5_strike:
            return False

        if not self.x5_can_be_hammered:
            return False

        # Remove the x5 session
        if self.active_x5_strike in self.active_sessions:
            self.active_sessions.remove(self.active_x5_strike)

        print(f"\n{'='*60}")
        print(f"🔨 HAMMER DEPLOYED BY {agent_name}!")
        print(f"   x5 STRIKE NEUTRALIZED!")
        print(f"{'='*60}\n")

        self.active_x5_strike = None
        self.x5_can_be_hammered = False

        return True

    def apply_multiplier(self, base_points: int, current_time: int = None) -> dict:
        """
        Apply current multiplier to gift points.

        x5 strikes are ADDITIVE with session multipliers:
        - If x3 session + x5 strike: (base × 3) + (base × 5) = base × 8
        - x5 is a separate gift event, not a multiplier stack

        Args:
            base_points: Base gift value
            current_time: Current battle time (optional, uses active_sessions if not provided)

        Returns:
            Dictionary with:
            - total_points: Final points awarded
            - session_points: Points from session multiplier
            - strike_points: Additional points from x5 strike
            - breakdown: String describing calculation
        """
        # Get active multipliers separately
        if current_time is not None:
            # Filter by current time
            active = [s for s in self.active_sessions if s.is_active(current_time)]
        else:
            # Use all active sessions
            active = self.active_sessions

        session_multipliers = [
            s.multiplier for s in active
            if s.multiplier in [MultiplierType.X2, MultiplierType.X3]
        ]

        x5_active = any(
            s.multiplier == MultiplierType.X5
            for s in active
        )

        # Apply session multiplier (x2 or x3)
        if session_multipliers:
            session_mult = max(session_multipliers, key=lambda m: m.value)
            session_points = base_points * session_mult.value
        else:
            session_mult = MultiplierType.NONE
            session_points = base_points

        # Add x5 strike points separately
        if x5_active:
            strike_points = base_points * 5
            total_points = session_points + strike_points

            if session_mult != MultiplierType.NONE:
                breakdown = f"({base_points} × {session_mult.value}) + ({base_points} × 5)"
            else:
                breakdown = f"{base_points} + ({base_points} × 5)"
        else:
            strike_points = 0
            total_points = session_points

            if session_mult != MultiplierType.NONE:
                breakdown = f"{base_points} × {session_mult.value}"
            else:
                breakdown = str(base_points)

        return {
            "total_points": total_points,
            "session_points": session_points,
            "strike_points": strike_points,
            "breakdown": breakdown,
            "session_multiplier": session_mult.value if session_mult != MultiplierType.NONE else 1,
            "has_x5": x5_active
        }

    def get_current_multiplier(self) -> MultiplierType:
        """Get currently active multiplier."""
        return self.current_multiplier

    def is_session_active(self) -> bool:
        """Check if any multiplier session is active."""
        return len(self.active_sessions) > 0

    def get_status(self) -> Dict[str, Any]:
        """Get current multiplier system status."""
        return {
            "current_multiplier": f"x{self.current_multiplier.value}",
            "active_sessions": len(self.active_sessions),
            "sessions": [str(s) for s in self.active_sessions],
            "auto_triggered": self.auto_session_triggered,
            "bonus_triggered": self.bonus_session_triggered,
            "bonus_available": self.bonus_session_available,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get multiplier statistics for end of battle."""
        total_sessions = len(self.session_history) + len(self.active_sessions)

        x2_count = sum(1 for s in self.session_history + self.active_sessions
                      if s.multiplier == MultiplierType.X2)
        x3_count = sum(1 for s in self.session_history + self.active_sessions
                      if s.multiplier == MultiplierType.X3)
        x5_count = sum(1 for s in self.session_history + self.active_sessions
                      if s.multiplier == MultiplierType.X5)

        return {
            "total_sessions": total_sessions,
            "x2_sessions": x2_count,
            "x3_sessions": x3_count,
            "x5_strikes": x5_count,
            "auto_triggered": self.auto_session_triggered,
            "bonus_triggered": self.bonus_session_triggered,
        }
