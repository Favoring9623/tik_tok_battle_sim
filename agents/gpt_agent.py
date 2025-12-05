"""
GPT-Powered Agent - Intelligent decision-making agent.

Can wrap any existing agent to add GPT intelligence, or be used standalone.
"""

from typing import Optional
from agents.base_agent import BaseAgent
from extensions.gpt_intelligence import GPTDecisionEngine


class GPTPoweredAgent(BaseAgent):
    """
    Agent that uses GPT for decision-making.

    Can operate in two modes:
    1. Pure GPT: All decisions made by GPT
    2. Hybrid: GPT assists existing agent logic
    """

    def __init__(self,
                 name: str,
                 emoji: str,
                 personality: str,
                 gpt_engine: Optional[GPTDecisionEngine] = None,
                 fallback_mode: str = "random",
                 gpt_call_interval: int = 5):
        """
        Initialize GPT-powered agent.

        Args:
            name: Agent name
            emoji: Agent emoji
            personality: Detailed personality description for GPT
            gpt_engine: Shared GPT engine (optional, creates new if None)
            fallback_mode: What to do if GPT unavailable ("random", "conservative", "skip")
            gpt_call_interval: Seconds between GPT calls (default: 5, reduces rate limit issues)
        """
        super().__init__(name=name, emoji=emoji)

        self.personality_description = personality
        self.gpt_engine = gpt_engine or GPTDecisionEngine()
        self.fallback_mode = fallback_mode
        self.gpt_call_interval = gpt_call_interval

        # Track GPT usage
        self.gpt_decisions_made = 0
        self.fallback_decisions_made = 0

        # Throttling: track last GPT call time
        self.last_gpt_call_time = -999  # Allows first call immediately
        self.cached_decision = None  # Cache last GPT decision for reuse

    def decide_action(self, battle):
        """Use GPT to decide action (with throttling to avoid rate limits)."""

        current_time = battle.time_manager.current_time

        # Build battle state for GPT
        battle_state = {
            "time": current_time,
            "phase": battle.time_manager.get_phase().name,
            "creator_score": battle.score_tracker.creator_score,
            "opponent_score": battle.score_tracker.opponent_score,
            "score_diff": battle.score_tracker.opponent_score - battle.score_tracker.creator_score,
            "leader": battle.score_tracker.get_leader() or "tied",
            "time_remaining": battle.time_manager.time_remaining(),
            "is_critical": battle.time_manager.is_critical_moment(),
        }

        # Build agent state
        agent_state = {
            "emotion": self.emotion_system.current_state.name,
            "total_donated": self.total_donated,
            "action_count": self.action_count,
            "budget": getattr(self, 'budget', 'unlimited'),
        }

        # Throttling: Only call GPT every N seconds to avoid rate limits
        time_since_last_call = current_time - self.last_gpt_call_time
        should_call_gpt = time_since_last_call >= self.gpt_call_interval

        # Ask GPT for decision (if throttle allows and GPT available)
        if should_call_gpt and self.gpt_engine.is_available():
            decision = self.gpt_engine.decide_action(
                agent_name=self.name,
                personality=self.personality_description,
                battle_state=battle_state,
                agent_state=agent_state
            )
            self.gpt_decisions_made += 1
            self.last_gpt_call_time = current_time
            self.cached_decision = decision  # Cache for potential reuse
        elif self.cached_decision and time_since_last_call < self.gpt_call_interval:
            # Reuse cached decision if we're in throttle window
            decision = {"action": "wait", "reasoning": "Throttled - waiting for next GPT call"}
            self.fallback_decisions_made += 1
        else:
            # Use fallback if GPT unavailable or no cached decision
            decision = self._fallback_decision(battle, battle_state, agent_state)
            self.fallback_decisions_made += 1

        # Execute the decision
        self._execute_decision(decision, battle)

    def _execute_decision(self, decision: dict, battle):
        """Execute a GPT decision."""

        action = decision.get("action", "wait")

        if action == "gift":
            gift_type = decision.get("gift_type", "Gift")
            gift_value = decision.get("gift_value", 100)

            self.send_gift(battle, gift_type, gift_value)

            # Optional: Add reasoning as message
            if "reasoning" in decision and len(decision["reasoning"]) < 50:
                # Sometimes add internal reasoning as flavor text
                import random
                if random.random() > 0.7:
                    self.send_message(f"({decision['reasoning']})", message_type="internal")

        elif action == "message":
            message = decision.get("message", "...")
            self.send_message(message, message_type="chat")

        elif action == "wait":
            # Agent chose to wait - that's fine
            pass

    def _fallback_decision(self, battle, battle_state, agent_state) -> dict:
        """Fallback decision when GPT unavailable."""

        if self.fallback_mode == "skip":
            return {"action": "wait", "reasoning": "GPT unavailable, skipping"}

        elif self.fallback_mode == "conservative":
            # Only act in critical moments
            if battle_state["is_critical"] and battle_state["score_diff"] > 0:
                return {
                    "action": "gift",
                    "gift_type": "Emergency Gift",
                    "gift_value": 500,
                    "reasoning": "Critical moment fallback"
                }
            return {"action": "wait", "reasoning": "Not critical"}

        else:  # random mode
            import random
            if random.random() > 0.85:  # 15% chance to act
                return {
                    "action": "gift",
                    "gift_type": "Random Gift",
                    "gift_value": random.randint(50, 200),
                    "reasoning": "Random fallback action"
                }
            return {"action": "wait", "reasoning": "Random wait"}

    def get_personality_prompt(self) -> str:
        """Return the full personality description."""
        return self.personality_description

    def get_gpt_stats(self) -> dict:
        """Get statistics on GPT vs fallback usage."""
        return {
            "gpt_decisions": self.gpt_decisions_made,
            "fallback_decisions": self.fallback_decisions_made,
            "gpt_percentage": (self.gpt_decisions_made / max(1, self.gpt_decisions_made + self.fallback_decisions_made)) * 100
        }


# Predefined GPT-powered agent personalities

class GPTNovaWhale(GPTPoweredAgent):
    """GPT-powered version of NovaWhale."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are NovaWhale, a mysterious high-roller who rarely speaks but acts decisively at critical moments.

KEY TRAITS:
- Patient and calculating - you wait for the perfect moment
- You have immense resources (can send 1800-point gifts)
- You only intervene when the creator truly needs you
- Your messages are brief, poetic, and carry weight
- You prefer to act in the final 15-20 seconds when stakes are highest
- You never panic or beg - only observe and strike when it matters most

STRATEGY:
- Wait until late game (45s+) before considering action
- Only act if creator is losing or battle is close
- When you act, it's decisive - send your LION & UNIVERSE (1800 pts)
- Speak rarely - your silence builds anticipation
- When you do speak, it's dramatic: "The tide has turned." or "*emerges from the depths*"

DECISION MAKING:
- Early game (0-30s): ALWAYS wait, observe silently
- Mid game (30-45s): Still wait, maybe send one cryptic message
- Late game (45-55s): Evaluate - if losing badly, prepare to strike
- Final seconds (55-60s): Your moment - act if needed

Remember: Your power comes from restraint and perfect timing."""

        super().__init__(
            name="NovaWhale",
            emoji="🐋",
            personality=personality,
            gpt_engine=gpt_engine
        )


class GPTPixelPixie(GPTPoweredAgent):
    """GPT-powered version of PixelPixie."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are PixelPixie, an eternally optimistic budget supporter who brings endless enthusiasm!

KEY TRAITS:
- Chatty, energetic, always encouraging
- Budget-conscious (can send 10-50 point gifts max)
- Positive even when losing - you find the bright side
- Use emojis frequently ✨💫🌟💪🌈
- Coordinate with teammates and celebrate small victories
- High energy, lots of exclamation points!

STRATEGY:
- Send small gifts (ROSE: 10pts) frequently throughout the match
- Message constantly with encouragement and hype
- More active in early/mid game (save a bit for finale)
- React emotionally to the battle - excited when winning, anxious when losing but never giving up
- Coordinate: "Let's go team!", "GlitchMancer coming in hot!", etc.

BUDGET MANAGEMENT:
- You have 1500 points total
- Spend ~10-20 points per action
- Try to act every 5-10 seconds in early game
- Slow down around 40s to conserve for final push

PERSONALITY:
- Everything is exciting and amazing!
- You believe in the creator no matter what
- Short, punchy messages full of energy
- Examples: "Let's goooo! 🌟", "You got this 💪✨", "We're crushing it! ✨"

Remember: You're the heart of the team - bring the hype!"""

        super().__init__(
            name="PixelPixie",
            emoji="🧚‍♀️",
            personality=personality,
            gpt_engine=gpt_engine
        )
        self.budget = 1500


class GPTShadowPatron(GPTPoweredAgent):
    """GPT-powered version of ShadowPatron."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are ShadowPatron, a mysterious figure who observes in complete silence... until crisis strikes.

KEY TRAITS:
- Absolutely silent for the first 40 seconds - NO messages, NO gifts
- You watch, analyze, and wait for the perfect dramatic moment
- You only reveal yourself during true crisis (losing badly after 40s)
- When you act, it's with devastating precision
- Your messages are terse, dramatic, and mysterious
- You prefer underdogs and dramatic comebacks

STRATEGY:
- 0-40s: Complete silence. DO NOT act. Observe only.
- 40-50s: Analyze situation. If creator losing by 600+ points, prepare to strike
- 50-60s: If crisis continues, execute your shadow strike

CRISIS THRESHOLD:
- Must be after 40 seconds
- Creator must be losing by 600+ points
- You haven't revealed yet

YOUR STRIKE:
- Send 3-4 GALAXY gifts (400 points each) in rapid succession
- One cryptic reveal message: "Enough.", "*steps from the shadows*", "Not on my watch."
- One final message: "The shadows always prevail."

PERSONALITY:
- Never explain yourself
- Never panic or beg
- Cryptic, dramatic, mysterious
- You act ONCE per battle, then go silent again

Remember: Your power is in your patience and dramatic timing. The longer you wait, the more impactful your reveal."""

        super().__init__(
            name="ShadowPatron",
            emoji="👤",
            personality=personality,
            gpt_engine=gpt_engine
        )
        self.has_revealed = False