"""
Time Extension System - +20s Battle Duration Bonuses

Allows extending battle duration when behind in score.

MECHANICS:
- Earned as rewards from previous battle victories
- Can be used mid-battle to extend duration by +20 seconds
- Strategic resource for comeback attempts
- Limited inventory (earned from wins)

STRATEGY:
- Use when losing (behind in score)
- Deploy in final moments to create comeback window
- Coordinate with team for maximum impact
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import time


@dataclass
class TimeExtension:
    """A time extension bonus."""
    duration: int = 20  # Seconds to add
    used: bool = False
    use_time: Optional[int] = None
    triggered_by: Optional[str] = None


class TimeExtensionManager:
    """
    Manages time extension bonuses for battles.

    Features:
    - Track available extensions
    - Evaluate when to use extensions
    - Apply extensions to battle duration
    - Coordinate with team strategy
    """

    def __init__(self, initial_extensions: int = 1):
        """
        Initialize time extension manager.

        Args:
            initial_extensions: Number of +20s bonuses available
        """
        self.available_extensions: List[TimeExtension] = [
            TimeExtension() for _ in range(initial_extensions)
        ]
        self.used_extensions: List[TimeExtension] = []
        self.total_time_added = 0

        # Strategy thresholds
        self.activation_threshold = 1000  # Points behind to trigger
        self.min_time_remaining = 15      # Don't use if < 15s left

    def can_use_extension(self) -> bool:
        """Check if extensions are available."""
        return len(self.available_extensions) > 0

    def should_use_extension(self, score_diff: int, time_remaining: int,
                            current_time: int, battle_duration: int) -> bool:
        """
        Evaluate if now is a good time to use a time extension.

        Strategy:
        - Use when losing (score_diff > threshold)
        - Use in final moments (but not too late)
        - Don't use if winning
        - Don't use too early (waste potential)

        Args:
            score_diff: opponent_score - creator_score (positive = losing)
            time_remaining: Seconds left in battle
            current_time: Current battle time
            battle_duration: Total battle duration

        Returns:
            True if extension should be used
        """
        if not self.can_use_extension():
            return False

        # Don't use if winning
        if score_diff <= 0:
            return False

        # Don't use too late (need time to execute comeback)
        if time_remaining < self.min_time_remaining:
            return False

        # Calculate battle progress
        progress = current_time / battle_duration

        # SCENARIO 1: Desperately losing in final 30s
        if time_remaining <= 30 and score_diff >= self.activation_threshold:
            return True

        # SCENARIO 2: Significantly behind in final third (need more time)
        if progress >= 0.67 and score_diff >= self.activation_threshold * 2:
            return True

        # SCENARIO 3: Massively behind mid-game (emergency extension)
        if progress >= 0.50 and score_diff >= self.activation_threshold * 3:
            return True

        return False

    def use_extension(self, current_time: int, agent_name: str) -> Optional[int]:
        """
        Use a time extension bonus.

        Args:
            current_time: Current battle time
            agent_name: Agent triggering the extension

        Returns:
            Duration added (20s) or None if no extensions available
        """
        if not self.can_use_extension():
            return None

        # Pop one extension
        extension = self.available_extensions.pop(0)
        extension.used = True
        extension.use_time = current_time
        extension.triggered_by = agent_name

        # Track usage
        self.used_extensions.append(extension)
        self.total_time_added += extension.duration

        # Announce
        print(f"\n{'='*60}")
        print(f"⏱️  TIME EXTENSION ACTIVATED BY {agent_name}!")
        print(f"   +{extension.duration} seconds added to battle")
        print(f"   Used at t={current_time}s")
        print(f"   Extensions remaining: {len(self.available_extensions)}")
        print(f"{'='*60}\n")

        return extension.duration

    def get_status(self) -> Dict[str, Any]:
        """Get current time extension status."""
        return {
            "available": len(self.available_extensions),
            "used": len(self.used_extensions),
            "total_time_added": self.total_time_added,
            "can_extend": self.can_use_extension()
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for end of battle."""
        return {
            "extensions_available": len(self.available_extensions),
            "extensions_used": len(self.used_extensions),
            "total_time_added": self.total_time_added,
            "use_times": [ext.use_time for ext in self.used_extensions if ext.use_time],
            "triggered_by": [ext.triggered_by for ext in self.used_extensions if ext.triggered_by]
        }

    def add_extension_reward(self, count: int = 1):
        """
        Add time extension bonuses (earned from previous victory).

        Args:
            count: Number of extensions to add
        """
        for _ in range(count):
            self.available_extensions.append(TimeExtension())

        print(f"🏆 Earned {count} time extension bonus(es)!")
        print(f"   Total available: {len(self.available_extensions)}")


# Strategy Coordinator Integration
class TimeExtensionStrategy:
    """Strategic decision-making for time extensions."""

    @staticmethod
    def evaluate_extension_value(score_diff: int, time_remaining: int,
                                 team_firepower: int) -> float:
        """
        Evaluate the value of using a time extension now.

        Returns value score (0-1, higher = better time to use)
        """
        if score_diff <= 0:
            return 0.0  # Winning, no value

        # Base value on how far behind we are
        deficit_value = min(score_diff / 5000, 1.0)  # Normalize to 0-1

        # Time urgency (higher value in final moments)
        time_urgency = 1.0 - (time_remaining / 180)

        # Team capability (can we make use of extra time?)
        capability_factor = min(team_firepower / 50000, 1.0)

        # Combined score
        value = (deficit_value * 0.5 +
                time_urgency * 0.3 +
                capability_factor * 0.2)

        return value

    @staticmethod
    def suggest_extension_timing(battle_duration: int, extensions_available: int) -> List[int]:
        """
        Suggest optimal times to use extensions.

        Args:
            battle_duration: Base battle duration
            extensions_available: Number of extensions available

        Returns:
            List of suggested times to consider extensions
        """
        suggestions = []

        if extensions_available >= 1:
            # Primary suggestion: Final 25-30s
            suggestions.append(battle_duration - 25)

        if extensions_available >= 2:
            # Secondary: 2/3 mark if desperately losing
            suggestions.append(int(battle_duration * 0.67))

        if extensions_available >= 3:
            # Tertiary: Mid-battle emergency
            suggestions.append(int(battle_duration * 0.50))

        return suggestions
