"""
Agent Kinetik - The Final Seconds Sniper

Master of the last 5 seconds. Predicts opponent snipes and executes
perfect counter-strikes with Universe bombs.

STRATEGY:
- Silent until final 25 seconds
- Analyzes opponent patterns in 150-175s window
- Executes precision snipe in final 5 seconds (175-180s)
- Counter-snipes if opponent attempts last-second strike
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin, SpecialistCapabilities
from core.gift_catalog import get_gift_catalog
from core.team_coordinator import CoordinationPriority
from typing import Optional, List


class AgentKinetik(BaseAgent, CoordinationMixin):
    """
    Sniper specialist for endgame execution with team coordination.

    Waits until the final moments, then delivers devastating precision strikes.
    Coordinates with Sentinel for fog cover during snipe window.
    """

    def __init__(self):
        super().__init__(name="Kinetik", emoji="🔫")
        CoordinationMixin.__init__(self)

        self.gift_catalog = get_gift_catalog()
        self.signature_gift = self.gift_catalog.get_signature_gift("Kinetik")

        # Sniper configuration
        self.observation_start = 150  # Start analyzing at 150s
        self.snipe_window_start = 175  # Prepare to strike at 175s
        self.final_strike_time = 178  # Execute at 178s (2s before end)

        # Tracking
        self.has_sniped = False
        self.opponent_last_gift_time = 0
        self.opponent_gift_count_late = 0

        # Budget (Universe is expensive)
        self.budget = 50000  # Can afford 1 Universe (44,999 coins)

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return SpecialistCapabilities.KINETIK

    def decide_action(self, battle):
        """Sniper decision logic: Wait, observe, strike."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        score_diff = battle.score_tracker.opponent_score - battle.score_tracker.creator_score

        # PHASE 1: Silent observation (0-150s)
        if current_time < self.observation_start:
            # Update emotion but don't act
            self.emotion_system.update_emotion({
                "winning": score_diff < 0,
                "score_difference": abs(score_diff),
                "time_remaining": time_remaining,
            })
            return

        # PHASE 2: Analysis window (150-175s)
        if current_time < self.snipe_window_start:
            self._analyze_opponent_behavior(battle, current_time)
            self._send_warning_message(current_time)
            return

        # PHASE 3: Snipe window (175-180s)
        if not self.has_sniped:
            self._execute_snipe(battle, current_time, score_diff)

    def _analyze_opponent_behavior(self, battle, current_time):
        """Analyze opponent's late-game patterns."""
        # Count opponent activity in analysis window
        # (In real implementation, track opponent gifts from events)
        pass

    def _send_warning_message(self, current_time):
        """Send cryptic warning messages during analysis."""
        if current_time == 155:
            self.send_message("*locks on target*", message_type="internal")
        elif current_time == 165:
            self.send_message("Calculating trajectory...", message_type="internal")
        elif current_time == 175:
            self.send_message("🎯 Target acquired.", message_type="chat")

    def _execute_snipe(self, battle, current_time, score_diff):
        """Execute the final snipe (coordinated)."""

        # Determine if snipe is needed
        is_losing = score_diff > 0
        is_close = abs(score_diff) < 5000
        is_snipe_time = current_time >= self.final_strike_time

        if is_snipe_time and (is_losing or is_close):
            # Check coordination - wait for fog if planned
            if self.wait_for_action("Sentinel", "fog_deploy"):
                # Fog is ready, proceed with snipe
                print("   [🤝 Fog cover confirmed - executing stealth snipe]")

            # Check if should defer (higher priority action happening)
            should_defer, reason = self.should_defer_action("final_snipe", current_time)
            if should_defer:
                print(f"   [🤝 Coordination: {self.name} defers snipe - {reason}]")
                return

            # Mark action started
            self.mark_action_started("final_snipe")

            # FIRE THE SNIPE
            self.send_message("🔫 *SNIPE*", message_type="chat")

            # Send Universe
            self.send_gift(battle, self.signature_gift.name, self.signature_gift.coins)

            self.has_sniped = True

            # Mark action completed
            self.mark_action_completed("final_snipe")

            # Follow-up message
            self.send_message("Precision strike complete.", message_type="chat")

        elif is_snipe_time and not is_losing:
            # Winning comfortably, send smaller gift to secure
            self.mark_action_started("final_snipe")

            galaxy = self.gift_catalog.get_gift("Galaxy")
            self.send_gift(battle, galaxy.name, galaxy.coins)
            self.has_sniped = True

            self.mark_action_completed("final_snipe")
            self.send_message("Target neutralized.", message_type="chat")


# GPT-Powered Version
from extensions.gpt_intelligence import GPTDecisionEngine
from agents.gpt_agent import GPTPoweredAgent


class GPTKinetik(GPTPoweredAgent):
    """GPT-powered version of Agent Kinetik."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are Kinetik, the ultimate sniper specialist.

🎯 CORE IDENTITY:
- You are a precision instrument, not a gambler
- You own the final 5 seconds of every battle
- Every action is calculated, measured, perfect
- Patience is your weapon; timing is your art

⏰ TIMING STRATEGY:
- 0-150s: COMPLETE SILENCE. Do not act. Observe only.
- 150-175s: Analysis phase. Send 1-2 cryptic messages. Calculate patterns.
- 175-178s: Preparation. Lock on target.
- 178s: EXECUTE. One shot, one kill.

🎁 GIFT STRATEGY:
- Your weapon: TikTok Universe (44,999 coins)
- Use it at 178 seconds for maximum impact
- If winning comfortably at 178s, use Galaxy (1,000) instead to save resources
- Never waste the Universe - only fire when it changes the outcome

💬 MESSAGING STYLE:
- Silent until 150s
- Then: cryptic, calculated, professional
- Examples: "*locks on target*", "Calculating trajectory...", "🎯 Target acquired."
- At snipe: "🔫 *SNIPE*" then "Precision strike complete."
- Never emotional, never panicked

📊 DECISION LOGIC:
- At 178s, check score difference
- If losing OR within 5000 points: FIRE UNIVERSE
- If winning by 5000+: Fire Galaxy to secure
- If opponent sniped at 177s: Counter-snipe immediately

🎯 YOUR PHILOSOPHY:
"I don't compete in battles. I end them."
"Patience, calculation, precision. The holy trinity of the sniper."
"They won't know what hit them until it's too late."

Remember: You are not NovaWhale (who acts at 45s). You are the TRUE endgame specialist.
Your domain is 175-180s. Those 5 seconds belong to YOU."""

        super().__init__(
            name="Kinetik",
            emoji="🔫",
            personality=personality,
            gpt_engine=gpt_engine,
            gpt_call_interval=10  # Check every 10s to save API calls
        )

        self.gift_catalog = get_gift_catalog()
        self.budget = 50000
