"""
ShadowPatron - The Silent Observer 👤

Personality:
- Completely silent until crisis point
- Observes patterns before acting
- Contrarian strategy - bets on underdogs
- Mysterious, no messages until the reveal
- Medium-high budget

Strategy:
- Silent for first 40 seconds (tuned from 50)
- Only acts if losing badly (>600 point deficit, tuned from 1000)
- Delivers 3-4 medium gifts in sequence
- Single dramatic message upon reveal
- VENGEFUL emotion when activated
"""

import random
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState


class ShadowPatron(BaseAgent):
    """The mysterious patron who watches in silence... until the moment strikes."""

    def __init__(self):
        super().__init__(name="ShadowPatron", emoji="👤")
        self.has_revealed = False
        self.silence_period = 40  # Silent until 40s (tuned from 50)

    def decide_action(self, battle):
        """Stay completely silent, then strike during crisis."""

        current_time = battle.time_manager.current_time
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score
        score_diff = opponent_score - creator_score  # Positive if losing

        # Maintain absolute silence
        if current_time < self.silence_period:
            return

        # Crisis detection: Losing by 600+ points after silence period (tuned from 1000)
        is_crisis = score_diff >= 600 and not self.has_revealed

        if is_crisis:
            self._execute_shadow_strike(battle, current_time)

    def _execute_shadow_strike(self, battle, current_time):
        """The dramatic reveal and counter-attack."""

        # Force VENGEFUL emotion
        self.emotion_system.force_emotion(EmotionalState.VENGEFUL, current_time)

        # The reveal message
        reveal_messages = [
            "Enough.",
            "*steps from the shadows*",
            "You thought you'd won.",
            "Not on my watch.",
            "I've seen enough."
        ]
        self.send_message(random.choice(reveal_messages), message_type="chat")

        # Deliver sequence of 3-4 gifts
        gift_count = random.randint(3, 4)
        for i in range(gift_count):
            self.send_gift(battle, "GALAXY", 400)

        # Final statement
        self.send_message("The shadows always prevail.", message_type="chat")

        self.has_revealed = True

    def get_personality_prompt(self) -> str:
        return """You are ShadowPatron, a mysterious figure who observes in complete silence.
        You speak only when absolutely necessary - during true crisis moments.
        Your messages are terse, dramatic, and carry an air of mystery.
        You prefer underdogs and dramatic comebacks.
        You never explain yourself, only act."""
