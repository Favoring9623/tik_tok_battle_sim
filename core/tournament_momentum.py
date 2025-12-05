"""
Tournament Series Momentum Tracker

Tracks psychological momentum, pressure, and storylines across tournament battles.

Features:
- Win streak detection
- Comeback tracking
- Pressure indicators
- Momentum shifts
- Clutch performance tracking
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MomentumState(Enum):
    """Current momentum state."""
    STRONG_CREATOR = "strong_creator"      # Creator has strong momentum
    MODERATE_CREATOR = "moderate_creator"  # Creator has slight edge
    NEUTRAL = "neutral"                     # Balanced
    MODERATE_OPPONENT = "moderate_opponent" # Opponent has slight edge
    STRONG_OPPONENT = "strong_opponent"    # Opponent has strong momentum


class PressureLevel(Enum):
    """Pressure level for each team."""
    NONE = 0          # No pressure
    LOW = 1           # Light pressure
    MODERATE = 2      # Moderate pressure
    HIGH = 3          # High pressure
    ELIMINATION = 4   # Must-win situation


@dataclass
class MomentumEvent:
    """Significant momentum event in the series."""
    battle_num: int
    event_type: str  # "win_streak", "comeback", "clutch", "domination", "close_call"
    team: str        # "creator" or "opponent"
    description: str
    impact: float    # -1.0 to 1.0 (negative = opponent momentum, positive = creator)


@dataclass
class BattleStats:
    """Statistics for a single battle."""
    battle_num: int
    winner: str
    creator_score: int
    opponent_score: int
    margin: int
    margin_percent: float  # % difference from average


class MomentumTracker:
    """
    Tracks momentum and storylines across a tournament series.

    Detects:
    - Win streaks
    - Comebacks (being down 0-2, winning 3-2)
    - Close battles vs blowouts
    - Clutch performances
    - Pressure situations
    """

    def __init__(self, battles_to_win: int = 2):
        """
        Initialize momentum tracker.

        Args:
            battles_to_win: Wins needed to win series (2 for BO3, 3 for BO5)
        """
        self.battles_to_win = battles_to_win
        self.battles: List[BattleStats] = []
        self.events: List[MomentumEvent] = []

        # Current state
        self.creator_wins = 0
        self.opponent_wins = 0
        self.current_momentum = MomentumState.NEUTRAL
        self.creator_pressure = PressureLevel.NONE
        self.opponent_pressure = PressureLevel.NONE

        # Streaks
        self.creator_win_streak = 0
        self.opponent_win_streak = 0
        self.longest_creator_streak = 0
        self.longest_opponent_streak = 0

        # Comeback tracking
        self.comeback_opportunity = None  # "creator" or "opponent" if possible

    def record_battle(self, battle_num: int, winner: str,
                     creator_score: int, opponent_score: int):
        """
        Record a battle result and update momentum.

        Args:
            battle_num: Battle number
            winner: "creator" or "opponent"
            creator_score: Creator final score
            opponent_score: Opponent final score
        """
        margin = abs(creator_score - opponent_score)
        avg_score = (creator_score + opponent_score) / 2
        margin_percent = (margin / avg_score * 100) if avg_score > 0 else 0

        # Store battle stats
        battle = BattleStats(
            battle_num=battle_num,
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score,
            margin=margin,
            margin_percent=margin_percent
        )
        self.battles.append(battle)

        # Update wins
        if winner == "creator":
            self.creator_wins += 1
            self.creator_win_streak += 1
            self.opponent_win_streak = 0
            self.longest_creator_streak = max(self.longest_creator_streak, self.creator_win_streak)
        else:
            self.opponent_wins += 1
            self.opponent_win_streak += 1
            self.creator_win_streak = 0
            self.longest_opponent_streak = max(self.longest_opponent_streak, self.opponent_win_streak)

        # Detect events
        self._detect_momentum_events(battle)

        # Update pressure levels
        self._update_pressure()

        # Update momentum state
        self._update_momentum()

        # Check for comeback opportunities
        self._check_comeback_opportunity()

    def _detect_momentum_events(self, battle: BattleStats):
        """Detect and record significant momentum events."""

        # Win streak
        if self.creator_win_streak >= 2:
            self.events.append(MomentumEvent(
                battle_num=battle.battle_num,
                event_type="win_streak",
                team="creator",
                description=f"Creator on {self.creator_win_streak}-battle win streak!",
                impact=0.3 * self.creator_win_streak
            ))
        elif self.opponent_win_streak >= 2:
            self.events.append(MomentumEvent(
                battle_num=battle.battle_num,
                event_type="win_streak",
                team="opponent",
                description=f"Opponent on {self.opponent_win_streak}-battle win streak!",
                impact=-0.3 * self.opponent_win_streak
            ))

        # Domination (>30% margin)
        if battle.margin_percent > 30:
            self.events.append(MomentumEvent(
                battle_num=battle.battle_num,
                event_type="domination",
                team=battle.winner,
                description=f"{battle.winner.title()} dominated with {battle.margin_percent:.1f}% margin!",
                impact=0.5 if battle.winner == "creator" else -0.5
            ))

        # Close call (<10% margin)
        elif battle.margin_percent < 10:
            self.events.append(MomentumEvent(
                battle_num=battle.battle_num,
                event_type="close_call",
                team=battle.winner,
                description=f"Nail-biter! {battle.winner.title()} won by only {battle.margin:,} points",
                impact=0.2 if battle.winner == "creator" else -0.2
            ))

        # Clutch win (won while facing elimination)
        if battle.winner == "creator" and self.creator_pressure == PressureLevel.ELIMINATION:
            self.events.append(MomentumEvent(
                battle_num=battle.battle_num,
                event_type="clutch",
                team="creator",
                description="Creator survives elimination with clutch performance!",
                impact=0.7
            ))
        elif battle.winner == "opponent" and self.opponent_pressure == PressureLevel.ELIMINATION:
            self.events.append(MomentumEvent(
                battle_num=battle.battle_num,
                event_type="clutch",
                team="opponent",
                description="Opponent survives elimination with clutch performance!",
                impact=-0.7
            ))

    def _update_pressure(self):
        """Update pressure levels based on series score."""
        # Calculate how close each team is to elimination
        creator_elimination_distance = self.battles_to_win - self.opponent_wins
        opponent_elimination_distance = self.battles_to_win - self.creator_wins

        # Creator pressure
        if creator_elimination_distance == 1:
            self.creator_pressure = PressureLevel.ELIMINATION
        elif creator_elimination_distance == 2:
            self.creator_pressure = PressureLevel.HIGH
        elif self.opponent_wins > self.creator_wins:
            self.creator_pressure = PressureLevel.MODERATE
        elif self.opponent_wins == self.creator_wins:
            self.creator_pressure = PressureLevel.LOW
        else:
            self.creator_pressure = PressureLevel.NONE

        # Opponent pressure
        if opponent_elimination_distance == 1:
            self.opponent_pressure = PressureLevel.ELIMINATION
        elif opponent_elimination_distance == 2:
            self.opponent_pressure = PressureLevel.HIGH
        elif self.creator_wins > self.opponent_wins:
            self.opponent_pressure = PressureLevel.MODERATE
        elif self.creator_wins == self.opponent_wins:
            self.opponent_pressure = PressureLevel.LOW
        else:
            self.opponent_pressure = PressureLevel.NONE

    def _update_momentum(self):
        """Update overall momentum state."""
        # Calculate momentum score from recent battles (more weight on recent)
        momentum_score = 0.0

        for i, battle in enumerate(reversed(self.battles[-3:])):  # Last 3 battles
            weight = (i + 1) / 3  # More recent = higher weight
            if battle.winner == "creator":
                momentum_score += weight
            else:
                momentum_score -= weight

        # Add streak bonus
        if self.creator_win_streak >= 2:
            momentum_score += 0.5
        elif self.opponent_win_streak >= 2:
            momentum_score -= 0.5

        # Determine state
        if momentum_score > 0.7:
            self.current_momentum = MomentumState.STRONG_CREATOR
        elif momentum_score > 0.2:
            self.current_momentum = MomentumState.MODERATE_CREATOR
        elif momentum_score > -0.2:
            self.current_momentum = MomentumState.NEUTRAL
        elif momentum_score > -0.7:
            self.current_momentum = MomentumState.MODERATE_OPPONENT
        else:
            self.current_momentum = MomentumState.STRONG_OPPONENT

    def _check_comeback_opportunity(self):
        """Check if a comeback scenario is possible."""
        # 0-2 comeback in BO5
        if self.battles_to_win == 3:
            if self.creator_wins == 0 and self.opponent_wins == 2:
                self.comeback_opportunity = "creator"
            elif self.opponent_wins == 0 and self.creator_wins == 2:
                self.comeback_opportunity = "opponent"
            # 1-2 comeback
            elif self.creator_wins == 1 and self.opponent_wins == 2:
                if self.comeback_opportunity != "creator":
                    self.comeback_opportunity = "creator"
            elif self.opponent_wins == 1 and self.creator_wins == 2:
                if self.comeback_opportunity != "opponent":
                    self.comeback_opportunity = "opponent"

    def print_momentum_report(self):
        """Print detailed momentum report."""
        print("\n" + "=" * 70)
        print("📊 SERIES MOMENTUM REPORT")
        print("=" * 70)

        # Current state
        print(f"\nMomentum: {self._format_momentum_state()}")
        print(f"Pressure: Creator {self._format_pressure(self.creator_pressure)} | "
              f"Opponent {self._format_pressure(self.opponent_pressure)}")

        # Streaks
        if self.creator_win_streak > 0:
            print(f"\n🔥 Creator is on a {self.creator_win_streak}-battle win streak!")
        elif self.opponent_win_streak > 0:
            print(f"\n🔥 Opponent is on a {self.opponent_win_streak}-battle win streak!")

        # Comeback storyline
        if self.comeback_opportunity:
            team = self.comeback_opportunity.title()
            print(f"\n⚡ COMEBACK ALERT: {team} fighting to stay alive!")

        # Recent events
        if self.events:
            print(f"\n📰 Key Moments:")
            for event in self.events[-3:]:  # Last 3 events
                print(f"   Battle {event.battle_num}: {event.description}")

        print("=" * 70 + "\n")

    def _format_momentum_state(self) -> str:
        """Format momentum state with emoji."""
        state_map = {
            MomentumState.STRONG_CREATOR: "🔵🔵🔵 STRONG CREATOR",
            MomentumState.MODERATE_CREATOR: "🔵🔵 Favoring Creator",
            MomentumState.NEUTRAL: "⚪ Balanced",
            MomentumState.MODERATE_OPPONENT: "🔴🔴 Favoring Opponent",
            MomentumState.STRONG_OPPONENT: "🔴🔴🔴 STRONG OPPONENT"
        }
        return state_map.get(self.current_momentum, "⚪ Unknown")

    def _format_pressure(self, pressure: PressureLevel) -> str:
        """Format pressure level with emoji."""
        pressure_map = {
            PressureLevel.NONE: "😌 None",
            PressureLevel.LOW: "🙂 Low",
            PressureLevel.MODERATE: "😐 Moderate",
            PressureLevel.HIGH: "😰 High",
            PressureLevel.ELIMINATION: "💀 ELIMINATION"
        }
        return pressure_map.get(pressure, "Unknown")

    def get_momentum_state(self) -> Dict[str, Any]:
        """
        Get complete momentum state as dictionary.

        Returns:
            Dictionary with all momentum data
        """
        return {
            "momentum": self.current_momentum.value,
            "creator_pressure": self.creator_pressure.value,
            "opponent_pressure": self.opponent_pressure.value,
            "creator_win_streak": self.creator_win_streak,
            "opponent_win_streak": self.opponent_win_streak,
            "comeback_opportunity": self.comeback_opportunity,
            "recent_events": [
                {
                    "battle_num": e.battle_num,
                    "type": e.event_type,
                    "team": e.team,
                    "description": e.description,
                    "impact": e.impact
                }
                for e in self.events[-5:]  # Last 5 events
            ]
        }
