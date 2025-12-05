"""
Emotion System - Models agent emotional states.

Emotions affect:
- Gift timing and frequency
- Message tone and content
- Decision-making strategy
- Interactions with other agents
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
import random


class EmotionalState(Enum):
    """Primary emotional states an agent can have."""

    CALM = auto()          # Neutral, calculated
    EXCITED = auto()       # Energized, frequent actions
    FRUSTRATED = auto()    # Losing badly, desperate
    VENGEFUL = auto()      # Betrayed, aggressive
    CONFIDENT = auto()     # Winning comfortably
    ANXIOUS = auto()       # Close battle, nervous
    TRIUMPHANT = auto()    # Major victory achieved
    CHAOTIC = auto()       # Unpredictable, manic energy


@dataclass
class EmotionModifiers:
    """How emotions affect agent behavior."""

    gift_frequency_multiplier: float = 1.0  # Higher = gift more often
    gift_size_multiplier: float = 1.0       # Higher = bigger gifts
    message_verbosity: float = 1.0          # Higher = more talkative
    risk_tolerance: float = 0.5             # 0-1: conservative to aggressive
    cooperation_level: float = 0.5          # How likely to coordinate with others


class EmotionSystem:
    """
    Manages an agent's emotional state and transitions.

    Emotions change based on battle events:
    - Winning → Confident
    - Losing → Frustrated
    - Close score → Anxious
    - Betrayal detected → Vengeful
    - Victory → Triumphant
    """

    # Emotion-to-modifiers mapping
    EMOTION_PROFILES = {
        EmotionalState.CALM: EmotionModifiers(
            gift_frequency_multiplier=1.0,
            gift_size_multiplier=1.0,
            message_verbosity=0.5,
            risk_tolerance=0.5,
            cooperation_level=0.7
        ),
        EmotionalState.EXCITED: EmotionModifiers(
            gift_frequency_multiplier=1.5,
            gift_size_multiplier=1.2,
            message_verbosity=1.5,
            risk_tolerance=0.6,
            cooperation_level=0.8
        ),
        EmotionalState.FRUSTRATED: EmotionModifiers(
            gift_frequency_multiplier=1.3,
            gift_size_multiplier=0.8,
            message_verbosity=0.7,
            risk_tolerance=0.8,  # More desperate risks
            cooperation_level=0.3
        ),
        EmotionalState.VENGEFUL: EmotionModifiers(
            gift_frequency_multiplier=2.0,
            gift_size_multiplier=1.5,
            message_verbosity=1.2,
            risk_tolerance=0.9,
            cooperation_level=0.1  # Solo mission
        ),
        EmotionalState.CONFIDENT: EmotionModifiers(
            gift_frequency_multiplier=0.7,
            gift_size_multiplier=1.0,
            message_verbosity=0.8,
            risk_tolerance=0.3,  # Playing it safe
            cooperation_level=0.6
        ),
        EmotionalState.ANXIOUS: EmotionModifiers(
            gift_frequency_multiplier=1.4,
            gift_size_multiplier=0.9,
            message_verbosity=0.6,
            risk_tolerance=0.7,
            cooperation_level=0.9  # Needs help!
        ),
        EmotionalState.TRIUMPHANT: EmotionModifiers(
            gift_frequency_multiplier=0.5,
            gift_size_multiplier=1.5,
            message_verbosity=2.0,  # Victory speech!
            risk_tolerance=0.2,
            cooperation_level=0.5
        ),
        EmotionalState.CHAOTIC: EmotionModifiers(
            gift_frequency_multiplier=random.uniform(0.5, 2.5),
            gift_size_multiplier=random.uniform(0.5, 2.0),
            message_verbosity=random.uniform(0.5, 2.0),
            risk_tolerance=random.uniform(0.3, 1.0),
            cooperation_level=random.uniform(0.0, 1.0)
        ),
    }

    def __init__(self, initial_state: EmotionalState = EmotionalState.CALM):
        self.current_state = initial_state
        self.state_history = [(0, initial_state)]  # (time, state)
        self._emotional_momentum = 0  # Tracks how long in current state

    def update_emotion(self, battle_context: dict) -> Optional[EmotionalState]:
        """
        Update emotional state based on battle context.

        Args:
            battle_context: Dict with keys:
                - creator_score: int
                - opponent_score: int
                - time_remaining: int
                - recent_events: list of event types

        Returns:
            New emotion if changed, None otherwise
        """
        creator_score = battle_context.get("creator_score", 0)
        opponent_score = battle_context.get("opponent_score", 0)
        time_remaining = battle_context.get("time_remaining", 60)
        recent_events = battle_context.get("recent_events", [])

        # Calculate score situation
        total = creator_score + opponent_score
        if total == 0:
            score_ratio = 0.5
        else:
            score_ratio = creator_score / total

        score_diff = abs(creator_score - opponent_score)
        is_close = score_diff < 500

        # Determine new emotion based on situation
        new_emotion = self._calculate_emotion(
            score_ratio,
            is_close,
            time_remaining,
            recent_events
        )

        if new_emotion != self.current_state:
            old_state = self.current_state
            self.current_state = new_emotion
            self._emotional_momentum = 0
            return new_emotion
        else:
            self._emotional_momentum += 1
            return None

    def _calculate_emotion(self, score_ratio: float, is_close: bool,
                           time_remaining: int, recent_events: list) -> EmotionalState:
        """Determine emotion based on battle state."""

        # Final moments + close = ANXIOUS
        if time_remaining < 10 and is_close:
            return EmotionalState.ANXIOUS

        # Winning by a lot = CONFIDENT
        if score_ratio > 0.7:
            return EmotionalState.CONFIDENT

        # Losing badly = FRUSTRATED
        if score_ratio < 0.3:
            return EmotionalState.FRUSTRATED

        # Close battle in middle = EXCITED
        if is_close and time_remaining > 20:
            return EmotionalState.EXCITED

        # Default
        return EmotionalState.CALM

    def get_modifiers(self) -> EmotionModifiers:
        """Get current behavior modifiers based on emotion."""
        return self.EMOTION_PROFILES[self.current_state]

    def force_emotion(self, emotion: EmotionalState, time: int = 0):
        """Manually set emotion (for special events)."""
        self.current_state = emotion
        self.state_history.append((time, emotion))
        self._emotional_momentum = 0

    def get_emotion_display(self) -> str:
        """Get emoji representation of current emotion."""
        emoji_map = {
            EmotionalState.CALM: "😌",
            EmotionalState.EXCITED: "🔥",
            EmotionalState.FRUSTRATED: "😤",
            EmotionalState.VENGEFUL: "😈",
            EmotionalState.CONFIDENT: "😎",
            EmotionalState.ANXIOUS: "😰",
            EmotionalState.TRIUMPHANT: "🏆",
            EmotionalState.CHAOTIC: "🌀",
        }
        return emoji_map.get(self.current_state, "❓")

    def __repr__(self):
        return f"EmotionSystem({self.current_state.name} {self.get_emotion_display()})"
