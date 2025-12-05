"""
Time Manager - Handles battle timing and phases.

Manages battle timelines (60s or 180s) and identifies critical moments.
"""

from typing import Optional
from enum import Enum, auto


class BattlePhase(Enum):
    """Different phases of a battle."""
    EARLY = auto()   # 0-20s: Opening, building momentum
    MID = auto()     # 20-40s: Main engagement
    LATE = auto()    # 40-55s: Closing push
    FINAL = auto()   # 55-60s: Last stand


class TimeManager:
    """
    Manages battle time and identifies strategic moments.

    Attributes:
        current_time: Current battle time in seconds (0-60)
        battle_duration: Total battle length in seconds (can be extended)
        base_duration: Original battle duration (before extensions)
    """

    def __init__(self, battle_duration: int = 60):
        self.base_duration = battle_duration
        self.battle_duration = battle_duration
        self.current_time = 0
        self.start_real_time: Optional[float] = None
        self.extensions_used = 0

    def tick(self) -> int:
        """Advance time by one second. Returns current time."""
        if self.current_time < self.battle_duration:
            self.current_time += 1
        return self.current_time

    def reset(self):
        """Reset to beginning."""
        self.current_time = 0
        self.start_real_time = None
        self.battle_duration = self.base_duration
        self.extensions_used = 0

    def extend_duration(self, additional_seconds: int) -> int:
        """
        Extend battle duration by additional seconds.

        Args:
            additional_seconds: Time to add (typically 20s)

        Returns:
            New total battle duration
        """
        self.battle_duration += additional_seconds
        self.extensions_used += 1
        return self.battle_duration

    def get_phase(self) -> BattlePhase:
        """
        Get current battle phase based on time.

        Scales dynamically based on battle duration:
        - 60s:  EARLY(0-20), MID(20-40), LATE(40-55), FINAL(55-60)
        - 180s: EARLY(0-60), MID(60-150), LATE(150-175), FINAL(175-180)
        """
        progress = self.current_time / self.battle_duration

        if progress <= 0.33:  # First third
            return BattlePhase.EARLY
        elif progress <= 0.83:  # Middle ~50%
            return BattlePhase.MID
        elif progress <= 0.97:  # Late game approach
            return BattlePhase.LATE
        else:  # Final moments
            return BattlePhase.FINAL

    def is_critical_moment(self) -> bool:
        """
        Returns True during critical final moments.

        Scales based on duration:
        - 60s: Last 10 seconds (50-60s)
        - 180s: Last 30 seconds (150-180s)
        """
        critical_window = 10 if self.battle_duration <= 60 else 30
        return self.time_remaining() <= critical_window

    def is_battle_over(self) -> bool:
        """Returns True if battle time has elapsed."""
        return self.current_time >= self.battle_duration

    def time_remaining(self) -> int:
        """Get seconds remaining in battle."""
        return max(0, self.battle_duration - self.current_time)

    def progress_percent(self) -> float:
        """Get battle progress as percentage (0-100)."""
        return (self.current_time / self.battle_duration) * 100

    def __repr__(self):
        return f"TimeManager(t={self.current_time}/{self.battle_duration}, phase={self.get_phase().name})"
