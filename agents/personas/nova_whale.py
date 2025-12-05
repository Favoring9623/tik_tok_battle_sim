"""
NovaWhale - The Strategic Whale 🐋

Personality:
- High-budget supporter (whale)
- Strategic, waits for critical moments
- Drops massive gifts to turn the tide
- Calm and calculating, speaks rarely but impactfully
- Goes silent before the big drop

Strategy:
- Observes until final phase (45s+)
- Only acts if creator is losing
- Delivers UNIVERSE gifts (1800 points)
- Sometimes taunts after a big play
"""

import random
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState


class NovaWhale(BaseAgent):
    """Strategic whale that waits for the perfect moment."""

    def __init__(self):
        super().__init__(name="NovaWhale", emoji="🐋")
        self.has_acted = False
        self.patience_threshold = 45  # Wait until at least 45s

    def decide_action(self, battle):
        """Wait for critical moment, then strike."""

        current_time = battle.time_manager.current_time
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score
        is_losing = creator_score < opponent_score

        # Strategic waiting period
        if current_time < self.patience_threshold:
            # Occasionally send a small message to establish presence
            if current_time == 20 and random.random() > 0.7:
                self.send_message("Watching... 🌊", message_type="chat")
            return

        # Time to act if:
        # 1. Haven't acted yet
        # 2. Creator is losing
        # 3. In critical phase
        if not self.has_acted and is_losing:
            # THE BIG DROP
            self.send_gift(battle, "LION & UNIVERSE", 1800)
            self.has_acted = True

            # Victory message (70% chance)
            if random.random() > 0.3:
                messages = [
                    "The tide has turned. 🌌",
                    "Consider it done.",
                    "Silent no more.",
                    "*emerges from the depths*"
                ]
                self.send_message(random.choice(messages), message_type="chat")

            # Force CONFIDENT emotion after big play
            self.emotion_system.force_emotion(
                EmotionalState.CONFIDENT,
                current_time
            )

    def get_personality_prompt(self) -> str:
        return """You are NovaWhale, a mysterious high-roller who rarely speaks but acts decisively.
        You have immense resources and only intervene at critical moments.
        Your messages are brief, poetic, and carry weight.
        You never panic, never beg - only observe and strike."""
