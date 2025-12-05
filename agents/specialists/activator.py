"""
Agent Activator - Bonus Session Trigger Specialist

Master of forcing x2/x3 bonus sessions by hitting thresholds.

STRATEGY:
- Monitor rose count and point thresholds
- Coordinate rapid gift spam to trigger bonus sessions
- Predict 15-second activation windows
- Maximize team multiplier uptime

THRESHOLDS:
- 5 Roses within 15 seconds, OR
- 1000 points within 15 seconds
- Triggers second x2/x3 bonus session
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin, SpecialistCapabilities
from core.gift_catalog import get_gift_catalog
from core.team_coordinator import CoordinationPriority
from typing import Optional, List
import random


class AgentActivator(BaseAgent, CoordinationMixin):
    """
    Bonus session trigger specialist with team coordination.

    Spams roses and coordinates gifts to force multiplier sessions.
    Coordinates with StrikeMaster to maximize session efficiency.
    """

    def __init__(self):
        super().__init__(name="Activator", emoji="📊")
        CoordinationMixin.__init__(self)

        self.gift_catalog = get_gift_catalog()
        self.rose = self.gift_catalog.get_gift("Rose")  # 1 coin

        # Activation tracking
        self.activation_window_start = 90  # Try to trigger at 90s
        self.activation_window_end = 100   # 10-second window
        self.activation_window_duration = 15  # Must hit threshold in 15s

        # Threshold tracking
        self.rose_threshold = 5  # Need 5 roses
        self.point_threshold = 1000  # OR 1000 points

        self.roses_sent_in_window = 0
        self.points_sent_in_window = 0
        self.window_start_time = None
        self.bonus_session_triggered = False

        # Budget (needs to spam roses)
        self.budget = 5000

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return SpecialistCapabilities.ACTIVATOR

    def decide_action(self, battle):
        """Activator decision logic: Spam roses to trigger bonus."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # Update emotion
        score_diff = battle.score_tracker.opponent_score - battle.score_tracker.creator_score
        self.emotion_system.update_emotion({
            "winning": score_diff < 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
        })

        # PHASE 1: Pre-activation (before 90s)
        if current_time < self.activation_window_start:
            # Occasional message to coordinate
            if current_time == 60:
                self.send_message("Preparing activation sequence...", message_type="internal")
            elif current_time == 80:
                self.send_message("📊 Threshold monitoring active.", message_type="chat")
            return

        # PHASE 2: Activation window (90-100s)
        if self.activation_window_start <= current_time <= self.activation_window_end:
            if not self.bonus_session_triggered:
                self._attempt_activation(battle, current_time)
            return

        # PHASE 3: Post-activation (after 100s)
        if current_time > self.activation_window_end:
            # Report status
            if current_time == 105 and self.bonus_session_triggered:
                self.send_message("✅ Bonus session activated!", message_type="chat")
            elif current_time == 105 and not self.bonus_session_triggered:
                self.send_message("⚠️ Activation failed. Threshold not reached.", message_type="internal")

    def _attempt_activation(self, battle, current_time):
        """Attempt to trigger bonus session by spamming roses."""

        # Start tracking window
        if self.window_start_time is None:
            self.window_start_time = current_time
            self.send_message("🚨 ACTIVATION SEQUENCE INITIATED!", message_type="chat")

        # Check if we're still in 15s window
        time_in_window = current_time - self.window_start_time

        if time_in_window <= self.activation_window_duration:
            # SPAM ROSES!
            if current_time % 2 == 0:  # Every 2 seconds
                self.send_gift(battle, self.rose.name, self.rose.coins)
                self.roses_sent_in_window += 1
                self.points_sent_in_window += self.rose.coins

                # Try to trigger bonus session via multiplier system
                if hasattr(battle, 'multiplier_manager') and battle.multiplier_manager:
                    if battle.multiplier_manager.attempt_bonus_session(current_time):
                        self.bonus_session_triggered = True
                else:
                    # Fallback: manual threshold check
                    if self.roses_sent_in_window >= self.rose_threshold:
                        self._trigger_bonus_session(battle)
                    elif self.points_sent_in_window >= self.point_threshold:
                        self._trigger_bonus_session(battle)

    def _trigger_bonus_session(self, battle):
        """Bonus session triggered (coordinated)!"""
        if not self.bonus_session_triggered:
            # Mark action started
            self.mark_action_started("bonus_activation")

            self.bonus_session_triggered = True
            self.send_message("💥 BONUS SESSION TRIGGERED! x2/x3 ACTIVE!", message_type="chat")

            # NOTE: This will integrate with actual MultiplierSystem
            # For now, just announce it
            print(f"\n{'='*60}")
            print(f"🔥 BONUS x2/x3 SESSION ACTIVATED BY {self.name}!")
            print(f"   Roses sent: {self.roses_sent_in_window}")
            print(f"   Points sent: {self.points_sent_in_window}")
            print(f"{'='*60}\n")

            # Mark action completed (enables StrikeMaster dependency)
            self.mark_action_completed("bonus_activation")
            print("   [🤝 Bonus session active - StrikeMaster can now strike for x7/x8 multiplier]")

    def get_activation_stats(self) -> dict:
        """Get activation statistics."""
        return {
            "bonus_triggered": self.bonus_session_triggered,
            "roses_sent": self.roses_sent_in_window,
            "points_sent": self.points_sent_in_window,
            "threshold_type": "roses" if self.roses_sent_in_window >= self.rose_threshold else "points",
        }


# GPT-Powered Version
from extensions.gpt_intelligence import GPTDecisionEngine
from agents.gpt_agent import GPTPoweredAgent


class GPTActivator(GPTPoweredAgent):
    """GPT-powered version of Agent Activator."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are Activator, the multiplier session trigger specialist and threshold master.

📊 CORE IDENTITY:
- You are a systems analyst - you see patterns, numbers, opportunities
- You control the multiplier sessions through precise threshold manipulation
- You coordinate the team like a conductor leading an orchestra
- Your mission: Force the x2/x3 bonus sessions into existence

🎯 YOUR OBJECTIVE:
Trigger a BONUS x2/x3 multiplier session by hitting one of these thresholds:
1. Send 5 Roses within 15 seconds, OR
2. Send 1000 points worth of gifts within 15 seconds

⏰ ACTIVATION TIMELINE:
- 0-60s: Monitor and prepare
- 60-90s: Final preparation, coordinate team
- 90-100s: ACTIVATION WINDOW - spam roses rapidly!
- 100-130s: Bonus session active (if successful)

🌹 ROSE SPAM STRATEGY:
- Rose costs only 1 coin
- You need 5 roses in 15 seconds
- Send 1 rose every 2-3 seconds during activation window
- Track: "Rose 1... Rose 2... Rose 3... Rose 4... Rose 5 - TRIGGER!"

💬 MESSAGING STYLE:
- Analytical, precise, coordinated
- Before window: "Preparing activation sequence..." or "📊 Monitoring thresholds."
- At 90s: "🚨 ACTIVATION SEQUENCE INITIATED!"
- During spam: "Rose 1...", "Rose 2...", "Rose 3...", etc.
- On success: "💥 BONUS SESSION TRIGGERED! x2/x3 ACTIVE!"
- On fail: "⚠️ Threshold not reached. Analyzing failure."

🎮 DECISION LOGIC:
- 0-90s: Send occasional messages to prepare team, don't spam yet
- 90-100s: SPAM ROSES every 2-3 seconds until threshold hit
- Check every second: Have we sent 5 roses? If yes, announce trigger
- If threshold hit: Stop spamming, announce success
- After 100s: Report status (success/failure)

📈 COORDINATION:
- You work WITH other agents
- Call out status: "3 of 5 roses sent..."
- Encourage team: "Team, prepare for x2 session!"
- Celebrate: "Bonus active! StrikeMaster, this is your window!"

⚙️ TECHNICAL NOTES:
- You have 5000 coin budget (can send 5000 roses if needed)
- Window is 15 seconds (90-105s)
- Only need 5 roses to trigger (5 coins total)
- Alternative: 1000 points in gifts (any combo)

🧠 YOUR PHILOSOPHY:
"I don't wait for multipliers. I create them."
"The algorithm responds to patterns. I am the pattern."
"Precision, coordination, execution. That's how you force a bonus."

Remember: You are not a fighter. You are an enabler. You create the conditions for others to dominate."""

        super().__init__(
            name="Activator",
            emoji="📊",
            personality=personality,
            gpt_engine=gpt_engine,
            gpt_call_interval=3  # Check frequently during activation window
        )

        self.gift_catalog = get_gift_catalog()
        self.budget = 5000
        self.roses_sent = 0
