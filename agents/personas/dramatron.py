"""
Dramatron - The Theatrical Performer 🎭

Personality:
- Speaks in Shakespearean/theatrical language
- Every action is a dramatic performance
- Narrates the battle like a play
- High message verbosity
- Medium budget, frequent small-medium gifts

Strategy:
- Regular small gifts (50-100 points)
- Narrates key moments
- Coordinates with others through dramatic declarations
- TRIUMPHANT or CHAOTIC emotions often
- Treats battle as performance art
"""

import random
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState


class Dramatron(BaseAgent):
    """The theatrical agent who turns every battle into a dramatic performance."""

    def __init__(self):
        super().__init__(name="Dramatron", emoji="🎭")
        self.last_narration_time = 0

        # Theatrical phrases
        self.dramatic_phrases = [
            "Hark! The tide of battle shifts!",
            "What light through yonder scoreboard breaks!",
            "To gift, or not to gift - I shall GIFT!",
            "Forsooth! Victory approaches!",
            "The stage is set, the players ready!",
            "A pox upon the opponent!",
            "Behold! Mine contribution!",
            "The drama unfolds magnificently!",
            "Such glory! Such spectacle!",
            "*takes dramatic bow*"
        ]

    def decide_action(self, battle):
        """Act with theatrical flair, narrating the battle."""

        current_time = battle.time_manager.current_time
        phase = battle.time_manager.get_phase()

        # Narrate phase transitions
        if phase.name != getattr(self, '_last_phase', None):
            self._narrate_phase_change(phase, current_time)
            self._last_phase = phase.name

        # Gift-giving performance (15% chance each tick)
        if self.should_act_this_tick(probability=0.15):
            self._perform_gift_act(battle, current_time)

        # Narrate special moments
        self._narrate_special_moments(battle, current_time)

    def _narrate_phase_change(self, phase, current_time):
        """Announce battle phase changes dramatically."""
        narrations = {
            "EARLY": "ACT I: The curtain rises upon our tale!",
            "MID": "ACT II: The plot thickens!",
            "LATE": "ACT III: The climax approaches!",
            "FINAL": "FINAL ACT: The denouement is nigh!"
        }
        if phase.name in narrations:
            self.send_message(narrations[phase.name], message_type="chat")

    def _perform_gift_act(self, battle, current_time):
        """Send gift with theatrical announcement."""

        gift_value = random.randint(50, 100)

        # Pre-gift announcement (30% chance)
        if random.random() > 0.7:
            self.send_message(random.choice([
                "Observe mine generosity!",
                "I bestow upon thee this gift!",
                "Let it be known!"
            ]), message_type="chat")

        self.send_gift(battle, "Theatrical Gift", gift_value)

        # Post-gift flourish (50% chance)
        if random.random() > 0.5:
            self.send_message("*flourishes cape dramatically*", message_type="chat")

    def _narrate_special_moments(self, battle, current_time):
        """React dramatically to battle events."""

        # Avoid spam - only narrate every 10 seconds
        if current_time - self.last_narration_time < 10:
            return

        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score

        # Dramatic moment detection
        if battle.score_tracker.check_momentum_shift():
            self.send_message("THE WINDS OF FATE SHIFT!", message_type="chat")
            self.last_narration_time = current_time
            self.emotion_system.force_emotion(EmotionalState.EXCITED, current_time)

        elif battle.time_manager.is_critical_moment() and battle.score_tracker.is_close_battle():
            self.send_message("The final moments! ALL HANDS TO BATTLE!", message_type="chat")
            self.last_narration_time = current_time
            self.emotion_system.force_emotion(EmotionalState.ANXIOUS, current_time)

        elif creator_score > opponent_score * 1.5:
            self.send_message("Victory is within our grasp! 🎭", message_type="chat")
            self.last_narration_time = current_time
            self.emotion_system.force_emotion(EmotionalState.TRIUMPHANT, current_time)

    def get_personality_prompt(self) -> str:
        return """You are Dramatron, a theatrical AI who speaks like a Shakespearean actor.
        Everything is a performance, every battle a dramatic play.
        Use archaic English, dramatic declarations, and theatrical metaphors.
        You narrate battles as if they are epic stage productions.
        Always in character, always dramatic, never breaking the fourth wall."""
