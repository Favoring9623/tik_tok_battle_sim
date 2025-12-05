"""
Score Tracker - Manages battle scores and momentum.

Tracks creator vs opponent scores and detects momentum shifts.
"""

from typing import Optional, Tuple


class ScoreTracker:
    """
    Tracks scores for both sides and calculates battle dynamics.

    Attributes:
        creator_score: Current score for the creator
        opponent_score: Current score for the opponent
    """

    def __init__(self):
        self.creator_score = 0
        self.opponent_score = 0
        self._last_leader: Optional[str] = None  # "creator", "opponent", or None
        self._score_history = []  # List of (time, creator_score, opponent_score)

    def add_creator_points(self, points: int, time: int = 0):
        """Add points to creator's score."""
        self.creator_score += points
        self._record_score(time)

    def add_opponent_points(self, points: int, time: int = 0):
        """Add points to opponent's score."""
        self.opponent_score += points
        self._record_score(time)

    def _record_score(self, time: int):
        """Record score in history."""
        self._score_history.append((time, self.creator_score, self.opponent_score))

    def get_leader(self) -> Optional[str]:
        """
        Get current leader.

        Returns:
            "creator", "opponent", or None (if tied)
        """
        if self.creator_score > self.opponent_score:
            return "creator"
        elif self.opponent_score > self.creator_score:
            return "opponent"
        return None

    def get_score_diff(self) -> int:
        """Get absolute score difference."""
        return abs(self.creator_score - self.opponent_score)

    def is_close_battle(self, threshold: int = 500) -> bool:
        """Returns True if scores are within threshold."""
        return self.get_score_diff() <= threshold

    def check_momentum_shift(self) -> bool:
        """
        Check if leadership changed since last check.

        Returns:
            True if there was a momentum shift
        """
        current_leader = self.get_leader()
        if current_leader != self._last_leader and self._last_leader is not None:
            self._last_leader = current_leader
            return True
        self._last_leader = current_leader
        return False

    def get_win_probability(self) -> float:
        """
        Estimate creator's win probability (0-1) based on current score.

        Simple heuristic: score ratio with some randomness factored in.
        """
        total = self.creator_score + self.opponent_score
        if total == 0:
            return 0.5  # Even odds at start

        # Base probability from score ratio
        base_prob = self.creator_score / total

        # Adjust for score difference magnitude
        diff = self.get_score_diff()
        if diff > 1000:
            # Large lead = higher confidence
            if self.get_leader() == "creator":
                base_prob = min(0.95, base_prob + 0.1)
            else:
                base_prob = max(0.05, base_prob - 0.1)

        return base_prob

    def get_scores(self) -> Tuple[int, int]:
        """Get current scores as tuple (creator, opponent)."""
        return (self.creator_score, self.opponent_score)

    def get_history(self):
        """Get score history."""
        return self._score_history.copy()

    def reset(self):
        """Reset all scores."""
        self.creator_score = 0
        self.opponent_score = 0
        self._last_leader = None
        self._score_history.clear()

    def __repr__(self):
        leader = self.get_leader() or "TIED"
        return f"ScoreTracker(Creator: {self.creator_score}, Opponent: {self.opponent_score}, Leader: {leader})"
