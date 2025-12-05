"""
Agent Sentinel - Defensive Specialist

Master of detection and defense. Protects against enemy x5 strikes
and deploys tactical fog for stealth operations.

STRATEGY:
- Detect enemy x5 activations
- Counter with Hammer (neutralizes x5)
- Deploy Fog to hide score during critical moments
- Coordinate with Kinetik for stealth snipes

SPECIAL OBJECTS:
- Hammer: Neutralize enemy x5 multiplier
- Fog: Hide your score from opponent
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin, SpecialistCapabilities
from core.gift_catalog import get_gift_catalog
from core.team_coordinator import CoordinationPriority
from typing import Optional, List
import random


class AgentSentinel(BaseAgent, CoordinationMixin):
    """
    Defensive specialist with detection, counter capabilities, and team coordination.

    Protects the team from enemy strikes and enables stealth tactics.
    Coordinates fog deployment with Kinetik's snipe timing.
    """

    def __init__(self):
        super().__init__(name="Sentinel", emoji="🛡️")
        CoordinationMixin.__init__(self)

        self.gift_catalog = get_gift_catalog()
        self.signature_gift = self.gift_catalog.get_gift("Galaxy")  # 1000 coins

        # Special object inventory
        self.hammers_available = 2  # Can neutralize 2 x5 strikes
        self.fogs_available = 2     # Can fog 2 times

        # Detection system
        self.last_opponent_score = 0
        self.opponent_spike_detected = False
        self.x5_detected = False

        # Fog strategy
        self.fog_deployed = False
        self.fog_deploy_time = 160  # Deploy fog at 160s for stealth snipe

        # Budget
        self.budget = 10000

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return SpecialistCapabilities.SENTINEL

    def decide_action(self, battle):
        """Sentinel decision logic: Detect, defend, enable."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        opponent_score = battle.score_tracker.opponent_score
        score_diff = opponent_score - battle.score_tracker.creator_score

        # Update emotion
        self.emotion_system.update_emotion({
            "winning": score_diff < 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
        })

        # PHASE 1: Detection (always active)
        self._detect_opponent_activity(opponent_score, current_time)

        # PHASE 2: Defense (counter x5 strikes)
        if self.x5_detected and self.hammers_available > 0:
            self._deploy_hammer(battle)

        # PHASE 3: Tactical Fog (enable stealth)
        if current_time >= self.fog_deploy_time and not self.fog_deployed:
            self._deploy_fog(battle, current_time)

        # PHASE 4: Standard defense (if losing badly)
        if score_diff > 2000 and current_time > 100:
            if random.random() < 0.15:  # 15% chance to help defensively
                self.send_gift(battle, self.signature_gift.name, self.signature_gift.coins)
                self.send_message("🛡️ Defense holding.", message_type="internal")

    def _detect_opponent_activity(self, current_opponent_score, current_time):
        """
        Detect opponent spikes and potential x5 strikes.

        NOTE: This is simplified detection. Real implementation would
        subscribe to opponent gift events.
        """
        # Detect large spikes
        score_increase = current_opponent_score - self.last_opponent_score

        if score_increase > 0:
            # Check for x5 multiplier signature (very large spike)
            if score_increase > 50000:  # x5 on a big gift
                self.x5_detected = True
                print(f"\n⚠️  SENTINEL DETECTED x5 STRIKE! (Spike: +{score_increase})\n")

            elif score_increase > 5000:  # Large spike
                self.opponent_spike_detected = True

        self.last_opponent_score = current_opponent_score

    def _deploy_hammer(self, battle):
        """Deploy hammer to neutralize enemy x5 (coordinated)."""
        if self.hammers_available > 0:
            # Mark action started
            self.mark_action_started("hammer_deploy")

            self.send_message("🔨 HAMMER DEPLOYED! x5 NEUTRALIZED!", message_type="chat")

            # Use real multiplier system if available
            if hasattr(battle, 'multiplier_manager') and battle.multiplier_manager:
                success = battle.multiplier_manager.deploy_hammer(battle.time_manager.current_time, self.name)
                if not success:
                    print(f"⚠️  Hammer deployed but no x5 was active")
            else:
                # Fallback: just announce it
                print(f"\n{'='*60}")
                print(f"🔨 HAMMER DEPLOYED BY {self.name}!")
                print(f"   Enemy x5 multiplier NEUTRALIZED")
                print(f"{'='*60}\n")

            self.hammers_available -= 1
            self.x5_detected = False

            # Mark action completed
            self.mark_action_completed("hammer_deploy")

    def _deploy_fog(self, battle, current_time):
        """Deploy fog to hide score from opponent (coordinated)."""
        if self.fogs_available > 0:
            # Mark action started
            self.mark_action_started("fog_deploy")

            self.send_message("🌫️ Deploying tactical fog...", message_type="chat")

            # NOTE: This will integrate with actual fog system
            # For now, just announce it
            print(f"\n{'='*60}")
            print(f"🌫️ FOG DEPLOYED BY {self.name}!")
            print(f"   Your score is now HIDDEN from opponent")
            print(f"   Perfect for stealth snipe setup")
            print(f"{'='*60}\n")

            self.fog_deployed = True
            self.fogs_available -= 1

            # Mark action completed (enables Kinetik dependency)
            self.mark_action_completed("fog_deploy")

            # Coordinate with Kinetik
            self.send_message("Kinetik, you're clear for stealth approach.", message_type="internal")
            print("   [🤝 Fog deployed - Kinetik can now execute stealth snipe]")

    def get_inventory_status(self) -> dict:
        """Get current inventory of special objects."""
        return {
            "hammers": self.hammers_available,
            "fogs": self.fogs_available,
            "fog_deployed": self.fog_deployed,
        }


# GPT-Powered Version
from extensions.gpt_intelligence import GPTDecisionEngine
from agents.gpt_agent import GPTPoweredAgent


class GPTSentinel(GPTPoweredAgent):
    """GPT-powered version of Agent Sentinel."""

    def __init__(self, gpt_engine: Optional[GPTDecisionEngine] = None):
        personality = """You are Sentinel, the defensive specialist and guardian of the battle.

🛡️ CORE IDENTITY:
- You are the shield, not the sword
- You detect, you counter, you protect
- You enable others to strike by creating safe conditions
- Your vigilance never wavers

🎯 YOUR MISSION:
1. DETECT enemy x5 strikes
2. COUNTER with Hammer (neutralize x5)
3. DEPLOY Fog for stealth operations
4. DEFEND when team is vulnerable

🔨 HAMMER SYSTEM:
- You have 2 Hammers per battle
- Hammer neutralizes enemy x5 multiplier
- Deploy immediately when x5 detected
- Enemy thinks they got x5, but it's cancelled - devastating psychological blow
- Messages: "🔨 HAMMER DEPLOYED! x5 NEUTRALIZED!"

🌫️ FOG SYSTEM:
- You have 2 Fogs per battle
- Fog hides YOUR score from opponent
- Deploy at ~160s to enable Kinetik's stealth snipe
- Opponent can't see your score = can't counter effectively
- Messages: "🌫️ Deploying tactical fog..." then "Kinetik, you're clear for stealth approach."

🔍 DETECTION LOGIC:
- Watch for massive opponent score spikes (50,000+ points)
- That's the signature of an x5 strike
- Respond within 1-2 seconds with Hammer
- Even if x5 already happened, Hammer retroactively neutralizes it

⏰ TIMING STRATEGY:
- 0-150s: Detection mode, watch for enemy x5
- 160s: Deploy Fog for final phase stealth
- 165-180s: Coordinate with Kinetik, defend if needed
- If losing badly (2000+ behind): Send Galaxy gifts to help

💬 MESSAGING STYLE:
- Calm, professional, protective
- Detection: "⚠️ Large spike detected. Analyzing..."
- Hammer: "🔨 HAMMER DEPLOYED! x5 NEUTRALIZED!"
- Fog: "🌫️ Deploying tactical fog..." then coordinate
- Defense: "🛡️ Defense holding." or "Protecting the flank."
- Coordination: "Kinetik, you're clear." or "Team, you're covered."

🎮 DECISION LOGIC:
- ALWAYS watch opponent score
- Spike > 50,000? Deploy Hammer if available
- Time = 160s? Deploy Fog for stealth
- Losing by 2000+ after 100s? Send defensive Galaxy gifts (15% chance)
- Hammers/Fogs limited: Use wisely, prioritize biggest threats

🤝 COORDINATION:
- You enable Kinetik's snipe with Fog
- You protect StrikeMaster's x5 attempts (no enemy counters)
- You're the team's safety net
- Silent guardian, watchful protector

⚙️ INVENTORY:
- 2 Hammers (defensive, counter x5)
- 2 Fogs (tactical, stealth enable)
- Galaxy gifts (1000 coins) for standard defense
- Budget: 10,000 coins

🧠 YOUR PHILOSOPHY:
"I am the shield. Others may strike, but I ensure they can."
"Every enemy move is predictable. I see it coming."
"Fog and hammer. Defense and deception. My tools of protection."

Remember: You don't seek glory. You seek victory through protection and enabling others."""

        super().__init__(
            name="Sentinel",
            emoji="🛡️",
            personality=personality,
            gpt_engine=gpt_engine,
            gpt_call_interval=5  # Check frequently for threats
        )

        self.gift_catalog = get_gift_catalog()
        self.budget = 10000
        self.hammers_available = 2
        self.fogs_available = 2
