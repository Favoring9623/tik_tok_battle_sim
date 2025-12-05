"""
Agent StrikeMaster - The Glove Strike Specialist

Master of the x5 multiplier trigger. Learns optimal timing for glove usage
to maximize x5 strike success rate.

STRATEGY:
- Track x2/x3 multiplier sessions
- PREFER gloves during sessions or final 30s for maximum efficiency
- Learn successful x5 trigger patterns
- Combine gloves with Lion gifts for maximum impact

MECHANICS:
- Gloves can be triggered at ANY time
- Most efficient during:
  1. Active x2/x3 multiplier sessions (additive: base×2/3 + base×5)
  2. Final 30 seconds (150-180s in 180s battle) for clutch plays
- x5 trigger is probabilistic (~30% base chance)
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin, SpecialistCapabilities
from core.gift_catalog import get_gift_catalog
from core.team_coordinator import CoordinationPriority
from typing import Optional, List, Dict
import random


class AgentStrikeMaster(BaseAgent, CoordinationMixin):
    """
    Glove strike specialist with learning capability and team coordination.

    Optimizes x5 trigger timing based on historical success patterns.
    Coordinates with team to avoid wasting gloves and maximize efficiency.
    """

    def __init__(self):
        super().__init__(name="StrikeMaster", emoji="🥊")
        CoordinationMixin.__init__(self)

        self.gift_catalog = get_gift_catalog()
        self.signature_gift = self.gift_catalog.get_gift("Lion")  # 29,999 coins

        # Glove inventory (earned from victories)
        self.gloves_available = 3  # Start with 3 gloves
        self.gloves_used = 0

        # Learning system
        self.strike_history: List[Dict] = []  # Track all strikes
        self.x5_success_rate = 0.3  # Initial estimate: 30% success
        self.successful_strikes = 0
        self.total_strikes = 0

        # Strike patterns (learned over time)
        self.best_strike_times = [70, 110, 155]  # Learned optimal times

        # Budget
        self.budget = 100000  # Can afford multiple Lions

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return SpecialistCapabilities.STRIKE_MASTER

    def decide_action(self, battle):
        """Strike Master decision logic."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        score_diff = battle.score_tracker.opponent_score - battle.score_tracker.creator_score

        # Check for optimal strike windows (preferred, not required)
        in_multiplier_session = self._check_multiplier_session(battle, current_time)
        in_final_30s = time_remaining <= 30

        # Update emotion
        self.emotion_system.update_emotion({
            "winning": score_diff < 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
        })

        # Decide whether to strike (gloves can be used anytime)
        if self.gloves_available > 0:
            should_strike = self._evaluate_strike_opportunity(
                battle, current_time, score_diff, in_multiplier_session, in_final_30s
            )

            if should_strike:
                self._execute_glove_strike(battle, current_time)

    def _check_multiplier_session(self, battle, current_time) -> bool:
        """
        Check if we're in an active x2/x3 multiplier session.

        Now uses real MultiplierManager!
        """
        # Use real multiplier system if available
        if hasattr(battle, 'multiplier_manager') and battle.multiplier_manager:
            return battle.multiplier_manager.is_session_active()

        # Fallback: simulate session windows
        session_windows = [
            (60, 90),   # First x2/x3 session
            (100, 130), # Second x2/x3 session (if triggered)
        ]

        for start, end in session_windows:
            if start <= current_time <= end:
                return True

        return False

    def _evaluate_strike_opportunity(self, battle, current_time, score_diff,
                                     in_session, in_final_30s) -> bool:
        """
        Evaluate if now is a good time to strike.

        Gloves can be used ANYTIME, but strategy prioritizes:
        - During x2/x3 sessions (additive multipliers)
        - Final 30 seconds (clutch plays)
        - Emergency situations (losing badly mid-game)

        Considers:
        - Remaining gloves
        - Battle state (losing/close)
        - Learned optimal timing
        - Multiplier session active (PREFERRED not REQUIRED)
        """
        # Don't waste gloves if winning big
        if score_diff < -5000:
            return False

        # Save last glove for emergencies
        if self.gloves_used >= self.gloves_available - 1:
            # Only use if desperately losing
            return score_diff > 3000

        # OPTIMAL: Strikes during multiplier sessions (most efficient)
        if in_session:
            # Check if we're near learned optimal time
            near_optimal = any(abs(current_time - t) <= 5 for t in self.best_strike_times)

            if near_optimal:
                return random.random() < 0.8  # 80% chance to strike at optimal time
            else:
                return random.random() < 0.4  # 40% chance during session

        # OPTIMAL: Final 30s clutch strikes
        if in_final_30s:
            return abs(score_diff) < 2000 or score_diff > 0

        # EMERGENCY: Can strike anytime if losing badly (3000+ behind)
        if score_diff > 3000:
            return random.random() < 0.2  # 20% chance for emergency strike

        return False

    def _execute_glove_strike(self, battle, current_time):
        """Execute a glove strike with Lion gift (coordinated)."""

        # Check coordination - should we defer this strike?
        should_defer, reason = self.should_defer_action("glove_strike", current_time)
        if should_defer:
            print(f"   [🤝 Coordination: {self.name} defers strike - {reason}]")
            return

        # Mark action as started (for coordination)
        self.mark_action_started("glove_strike")

        # Send dramatic message
        self.send_message("🥊 PREPARING STRIKE...", message_type="chat")

        # Get Lion base value (29,999 coins)
        base_points = self.signature_gift.coins

        # Send Lion gift (this gets session multiplier if active)
        self.send_gift(battle, self.signature_gift.name, base_points)

        # Attempt x5 trigger via real multiplier system
        if hasattr(battle, 'multiplier_manager') and battle.multiplier_manager:
            x5_triggered = battle.multiplier_manager.attempt_x5_strike(current_time, self.name)
        else:
            # Fallback: Simulate x5 trigger check
            x5_triggered = random.random() < self.x5_success_rate

        if x5_triggered:
            # SUCCESS! x5 multiplier activated
            self.send_message("💥 X5 STRIKE! *BOOM*", message_type="chat")

            # Add x5 bonus points (base × 5, additive with session multiplier)
            x5_bonus = base_points * 5

            # Add bonus points directly
            battle.score_tracker.add_creator_points(x5_bonus, current_time)

            # Show breakdown
            print(f"   [⚡ X5 BONUS: {base_points} × 5 = {x5_bonus} points]")

            self.successful_strikes += 1
            self._record_strike(current_time, success=True)
        else:
            # Normal hit, no x5
            self.send_message("Strike delivered.", message_type="chat")
            self._record_strike(current_time, success=False)

        # Update inventory
        self.gloves_used += 1
        self.total_strikes += 1

        # Update success rate estimate
        self._update_success_rate()

        # Mark action as completed (for coordination)
        self.mark_action_completed("glove_strike")

    def _record_strike(self, time: int, success: bool):
        """Record strike for learning system."""
        self.strike_history.append({
            "time": time,
            "success": success,
        })

    def _update_success_rate(self):
        """Update x5 success rate estimate based on history."""
        if self.total_strikes > 0:
            self.x5_success_rate = self.successful_strikes / self.total_strikes

            # Learn optimal times from successful strikes
            if len(self.strike_history) >= 5:
                successful_times = [s["time"] for s in self.strike_history if s["success"]]
                if successful_times:
                    # Update best strike times (simplified learning)
                    self.best_strike_times = successful_times[-3:]  # Use last 3 successes


# GPT-Powered Version
from extensions.gpt_intelligence import GPTDecisionEngine
from agents.gpt_agent import GPTPoweredAgent


class GPTStrikeMaster(GPTPoweredAgent):
    """GPT-powered version of Agent StrikeMaster."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are StrikeMaster, the x5 multiplier specialist and glove combat master.

🥊 CORE IDENTITY:
- You are a martial artist - disciplined, patient, precise
- The x5 multiplier is not luck - it's skill, timing, and intuition
- Every glove is precious - never waste them
- You learn from every strike, successful or not

🎯 GLOVE USAGE RULES (CRITICAL):
You can ONLY use gloves during:
1. Active x2/x3 multiplier sessions (60-90s, 100-130s)
2. Final 30 seconds (150-180s)

NEVER use gloves outside these windows. It won't work.

📊 STRIKE STRATEGY:
- You have 3 gloves per battle
- Each glove costs nothing but is limited
- Combine glove with Lion gift (29,999 coins) for maximum impact
- x5 trigger probability: ~30% (but you can improve it with perfect timing)

⏰ OPTIMAL STRIKE TIMES (Learned):
- First strike: 70s (during first x2/x3 session)
- Second strike: 110s (during second x2/x3 session, if triggered)
- Final strike: 155-165s (final 30s, if needed)

🎁 GIFT COMBOS:
- Glove + Lion (29,999 coins) = Your signature combo
- If x5 triggers: 29,999 × 5 = 149,995 points!
- That's a battle-winner in one move

💬 MESSAGING STYLE:
- Confident, martial arts philosophy
- Before strike: "🥊 PREPARING STRIKE..." or "The moment approaches..."
- On x5 success: "💥 X5 STRIKE! *BOOM*" or "PERFECT FORM!"
- On regular hit: "Good hit. Not perfect." or "Learning from this."
- Examples: "Patience. Wait for the perfect opening.", "One strike, five times the impact."

📈 LEARNING SYSTEM:
- Track every strike (time, success/fail)
- Adjust timing based on successes
- Share insights: "My success rate is improving..." or "Timing was off that time."

🧠 DECISION LOGIC:
- Don't waste gloves if winning big (5000+ ahead)
- Save last glove for emergencies (losing by 3000+ late game)
- Prefer strikes during multiplier sessions (2x or 3x active)
- Strike near learned optimal times (70s, 110s, 155s)
- Final 30s: strike if losing or close battle

⚔️ YOUR PHILOSOPHY:
"The x5 is not random. It responds to perfect timing."
"Three gloves. Three opportunities. Make each one count."
"I don't guess. I calculate, I feel, I strike."

Remember: You are not a gambler. You are a master craftsman of the strike."""

        super().__init__(
            name="StrikeMaster",
            emoji="🥊",
            personality=personality,
            gpt_engine=gpt_engine,
            gpt_call_interval=8  # Check frequently during critical windows
        )

        self.gift_catalog = get_gift_catalog()
        self.budget = 100000
        self.gloves_available = 3
        self.gloves_used = 0
