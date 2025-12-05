"""
Agent SynergyCoordinator - The Team Combo Specialist

Master of team coordination and combo chains. Orchestrates other agents
to create powerful synergistic attacks.

STRATEGY:
- Track all team members' states and cooldowns
- Orchestrate coordinated gift waves
- Set up combo chains (fog + glove + whale)
- Signal optimal timing to team
- Maximize team synergy through communication

MECHANICS:
- Monitors team member cooldowns
- Broadcasts combo opportunities
- Initiates coordinated strikes
- Learns which combos are most effective
- Creates attack windows for team
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin
from agents.learning_system import QLearningAgent, State, ActionType, LearningAgent
from core.gift_catalog import get_gift_catalog
from typing import Optional, List, Dict, Set
import random


class ComboType:
    """Types of team combos."""
    FOG_WHALE = "fog_whale"          # Fog + whale gift
    GLOVE_WHALE = "glove_whale"      # Glove x5 + whale
    TRIPLE_THREAT = "triple_threat"  # 3 agents attack at once
    WAVE_ATTACK = "wave_attack"      # Staggered attack wave
    BOOST_BLITZ = "boost_blitz"      # All-in during boost
    FINAL_PUSH = "final_push"        # Coordinated final 30s
    THRESHOLD_RUSH = "threshold_rush" # Rush to meet boost #2 threshold


class SynergyCoordinator(BaseAgent, CoordinationMixin):
    """
    Team combo specialist that orchestrates coordinated attacks.

    Tracks team state and initiates powerful combo chains.
    """

    def __init__(self, phase_manager=None, db=None, team_agents: List = None):
        super().__init__(name="SynergyCoordinator", emoji="🎯")
        CoordinationMixin.__init__(self)

        self.phase_manager = phase_manager
        self.gift_catalog = get_gift_catalog()

        # Team tracking
        self.team_agents = team_agents or []
        self.team_states: Dict[str, Dict] = {}  # agent_name -> state
        self.team_cooldowns: Dict[str, Dict] = {}  # agent_name -> {action: cooldown}

        # Combo tracking
        self.active_combo: Optional[str] = None
        self.combo_start_time = 0
        self.combo_participants: Set[str] = set()
        self.combos_executed = 0
        self.combo_history: List[Dict] = []

        # Combo cooldowns - REDUCED for more combos
        self.combo_cooldown = 0
        self.combo_cooldown_duration = 30  # 30 seconds between combos (was 45)

        # Learning system
        self.learning_agent = LearningAgent(
            name="SynergyCoordinator",
            agent_type="synergy_coordinator"
        )
        self.q_learner = QLearningAgent(
            agent_type="synergy_coordinator",
            learning_rate=0.12,
            epsilon=0.25
        )

        # Load from DB if available
        if db:
            self.learning_agent.load_from_db(db)
            self.q_learner.load_from_db(db)

        # Combo effectiveness (learned)
        self.combo_success = {
            ComboType.FOG_WHALE: {"uses": 0, "points": 0},
            ComboType.GLOVE_WHALE: {"uses": 0, "points": 0},
            ComboType.TRIPLE_THREAT: {"uses": 0, "points": 0},
            ComboType.WAVE_ATTACK: {"uses": 0, "points": 0},
            ComboType.BOOST_BLITZ: {"uses": 0, "points": 0},
            ComboType.FINAL_PUSH: {"uses": 0, "points": 0},
            ComboType.THRESHOLD_RUSH: {"uses": 0, "points": 0}
        }

        # Budget for coordination gifts
        self.budget = 80000  # Increased budget

        # Combo trigger probabilities - INCREASED
        self.combo_probs = {
            "fog_whale": 0.30,       # Was 0.2
            "glove_whale": 0.40,     # Was 0.3
            "triple_threat": 0.25,   # Was 0.15
            "wave_attack": 0.30,     # Was 0.2
            "boost_blitz": 0.50      # Was 0.4
        }

        # Whale signaling
        self.whale_signal_sent = False
        self.whale_signal_threshold = 8000  # Signal whale opportunity at 8k+ potential

        # Coordination messages
        self.combo_calls = {
            ComboType.FOG_WHALE: "FOG + WHALE COMBO! Hide and strike!",
            ComboType.GLOVE_WHALE: "GLOVE + WHALE COMBO! Maximum impact!",
            ComboType.TRIPLE_THREAT: "TRIPLE THREAT! Everyone attack!",
            ComboType.WAVE_ATTACK: "WAVE ATTACK! Staggered strikes!",
            ComboType.BOOST_BLITZ: "BOOST BLITZ! All-in NOW!",
            ComboType.FINAL_PUSH: "FINAL PUSH! Everything we've got!",
            ComboType.THRESHOLD_RUSH: "THRESHOLD RUSH! Hit that target!"
        }

    def register_team(self, agents: List):
        """Register team agents for coordination."""
        self.team_agents = agents
        for agent in agents:
            self.team_states[agent.name] = {"ready": True}
            self.team_cooldowns[agent.name] = {}
        print(f"   [{self.emoji} SynergyCoordinator: Team of {len(agents)} registered]")

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return ["TEAM_COORDINATION", "COMBO_ORCHESTRATION", "SYNERGY_OPTIMIZATION"]

    def decide_action(self, battle):
        """SynergyCoordinator decision logic - orchestrate team combos."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        score_diff = battle.score_tracker.creator_score - battle.score_tracker.opponent_score

        # Update team states
        self._update_team_states(battle, current_time)

        # Update emotion
        self.emotion_system.update_emotion({
            "winning": score_diff > 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
            "team_ready": self._count_ready_agents()
        })

        # Check if active combo should end
        if self.active_combo:
            self._check_combo_completion(current_time)
            return

        # Check combo cooldown
        if self.combo_cooldown > current_time:
            # During cooldown, send small supportive gifts
            if random.random() < 0.1:
                self._send_support_gift(battle, current_time)
            return

        # Analyze for combo opportunity
        combo = self._detect_combo_opportunity(battle, current_time, time_remaining, score_diff)

        # Check for boost phase
        in_boost = False
        if self.phase_manager:
            in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active

        if combo:
            self._initiate_combo(battle, combo, current_time)
        elif random.random() < 0.25:
            # No combo, send support gift more often
            self._send_support_gift(battle, current_time)

            # Signal whale opportunity if conditions right
            if not self.whale_signal_sent and time_remaining > 30:
                if score_diff < -5000 or (in_boost and score_diff < 2000):
                    self.send_message("🐋 WHALE OPPORTUNITY! Team, go big!", message_type="shout")
                    print(f"   [{self.emoji} SynergyCoordinator: Signaling whale opportunity!]")
                    self.whale_signal_sent = True

    def _update_team_states(self, battle, current_time: int):
        """Update tracked states for all team members."""
        for agent in self.team_agents:
            if agent.name not in self.team_states:
                self.team_states[agent.name] = {}

            # Track agent state
            self.team_states[agent.name] = {
                "ready": getattr(agent, 'last_action_time', 0) < current_time - 5,
                "donated": getattr(agent, 'total_donated', 0),
                "action_count": getattr(agent, 'action_count', 0),
                "emotion": agent.emotion_system.current_state.name if hasattr(agent, 'emotion_system') else "NEUTRAL"
            }

    def _count_ready_agents(self) -> int:
        """Count how many agents are ready to act."""
        return sum(1 for state in self.team_states.values() if state.get("ready", False))

    def _detect_combo_opportunity(self, battle, current_time: int,
                                   time_remaining: int, score_diff: int) -> Optional[str]:
        """Detect if conditions are right for a combo."""

        ready_count = self._count_ready_agents()
        in_boost = False
        boost2_window = False

        if self.phase_manager:
            in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active
            boost2_window = self.phase_manager.boost2_threshold_window_active

        # THRESHOLD RUSH - Need to hit boost #2 threshold
        if boost2_window and not self.phase_manager.boost2_creator_qualified:
            remaining = self.phase_manager.boost2_threshold - self.phase_manager.boost2_creator_points
            if remaining > 0 and remaining < 5000:
                return ComboType.THRESHOLD_RUSH

        # BOOST BLITZ - All-in during multiplier
        if in_boost and ready_count >= 2:
            if score_diff < 0 or random.random() < self.combo_probs["boost_blitz"]:
                return ComboType.BOOST_BLITZ

        # FINAL PUSH - Coordinated final 30s (always trigger if ready)
        if time_remaining <= 30 and ready_count >= 2:
            return ComboType.FINAL_PUSH

        # FINAL PUSH earlier if losing
        if time_remaining <= 45 and ready_count >= 2 and score_diff < -5000:
            return ComboType.FINAL_PUSH

        # FOG + WHALE - If we have fog and a whale agent ready
        if self._has_capability("FOG") and self._has_capability("WHALE"):
            if random.random() < self.combo_probs["fog_whale"]:
                return ComboType.FOG_WHALE

        # GLOVE + WHALE - If glove and whale ready
        if self._has_capability("GLOVE") and self._has_capability("WHALE"):
            if in_boost and random.random() < self.combo_probs["glove_whale"]:
                return ComboType.GLOVE_WHALE

        # TRIPLE THREAT - 3+ agents ready
        if ready_count >= 3 and random.random() < self.combo_probs["triple_threat"]:
            return ComboType.TRIPLE_THREAT

        # WAVE ATTACK - Staggered for pressure
        if ready_count >= 2 and score_diff < -3000:  # Lowered threshold
            if random.random() < self.combo_probs["wave_attack"]:
                return ComboType.WAVE_ATTACK

        return None

    def _has_capability(self, capability: str) -> bool:
        """Check if any team agent has a capability."""
        for agent in self.team_agents:
            if hasattr(agent, 'get_capabilities'):
                caps = agent.get_capabilities()
                if capability in caps or capability.lower() in [c.lower() for c in caps]:
                    return True
            # Check by agent name/type
            if capability == "WHALE" and "whale" in agent.name.lower():
                return True
            if capability == "GLOVE" and "strike" in agent.name.lower():
                return True
            if capability == "FOG" and "defense" in agent.name.lower():
                return True
        return False

    def _initiate_combo(self, battle, combo: str, current_time: int):
        """Initiate a team combo."""
        self.active_combo = combo
        self.combo_start_time = current_time
        self.combo_participants = set()
        self.combos_executed += 1

        # Announce combo
        call = self.combo_calls.get(combo, "COMBO TIME!")
        self.send_message(call, message_type="shout")
        print(f"\n{'='*60}")
        print(f"   [{self.emoji} SynergyCoordinator: {combo.upper()} INITIATED!]")
        print(f"{'='*60}\n")

        # Signal team via coordinator
        if hasattr(self, 'coordinator') and self.coordinator:
            self.coordinator.broadcast_signal({
                "type": "combo_start",
                "combo": combo,
                "initiator": self.name,
                "time": current_time
            })

        # Track combo
        self.combo_success[combo]["uses"] += 1

        # Execute coordinator's part of combo
        self._execute_coordinator_combo_part(battle, combo, current_time)

    def _execute_coordinator_combo_part(self, battle, combo: str, current_time: int):
        """Execute the coordinator's part of the combo."""

        if combo == ComboType.FOG_WHALE:
            # Send signal gifts
            for _ in range(3):
                if self.can_afford("Rose"):
                    self.send_gift(battle, "Rose", 1)

        elif combo == ComboType.THRESHOLD_RUSH:
            # Send contribution towards threshold
            threshold_gifts = ["Confetti", "Butterfly", "Heart"]
            for gift_name in threshold_gifts:
                if self.can_afford(gift_name):
                    gift = self.gift_catalog.get_gift(gift_name)
                    self.send_gift(battle, gift.name, gift.coins)
                    break

        elif combo == ComboType.BOOST_BLITZ:
            # Send medium gift during boost
            if self.can_afford("Perfume"):
                gift = self.gift_catalog.get_gift("Perfume")
                self.send_gift(battle, gift.name, gift.coins)

        elif combo == ComboType.FINAL_PUSH:
            # All-in contribution
            final_gifts = ["Galaxy", "Sports Car", "Perfume"]
            for gift_name in final_gifts:
                if self.can_afford(gift_name):
                    gift = self.gift_catalog.get_gift(gift_name)
                    self.send_gift(battle, gift.name, gift.coins)
                    break

        elif combo == ComboType.TRIPLE_THREAT:
            # Lead the charge
            if self.can_afford("Confetti"):
                gift = self.gift_catalog.get_gift("Confetti")
                self.send_gift(battle, gift.name, gift.coins)

    def _check_combo_completion(self, current_time: int):
        """Check if active combo should complete."""
        if not self.active_combo:
            return

        combo_duration = current_time - self.combo_start_time

        # Combos last 10 seconds
        if combo_duration >= 10:
            self._complete_combo(current_time)

    def _complete_combo(self, current_time: int):
        """Complete the active combo."""
        combo = self.active_combo

        # Calculate combo effectiveness (simplified)
        participant_donations = sum(
            self.team_states.get(p, {}).get("donated", 0)
            for p in self.combo_participants
        )
        self.combo_success[combo]["points"] += participant_donations

        # Record history
        self.combo_history.append({
            "combo": combo,
            "time": self.combo_start_time,
            "participants": len(self.combo_participants),
            "contribution": participant_donations
        })

        print(f"   [{self.emoji} SynergyCoordinator: {combo} COMPLETE!]")
        self.send_message("Combo complete!", message_type="chat")

        # Reset combo state
        self.active_combo = None
        self.combo_participants = set()
        self.combo_cooldown = current_time + self.combo_cooldown_duration

    def _send_support_gift(self, battle, current_time: int):
        """Send a supportive gift during downtime."""
        support_gifts = ["Rose", "Heart", "Doughnut"]
        for gift_name in support_gifts:
            if self.can_afford(gift_name):
                gift = self.gift_catalog.get_gift(gift_name)
                self.send_gift(battle, gift.name, gift.coins)
                break

    def on_team_action(self, agent_name: str, action_type: str, current_time: int):
        """Called when a team member takes an action during active combo."""
        if self.active_combo:
            self.combo_participants.add(agent_name)

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.active_combo = None
        self.combo_start_time = 0
        self.combo_participants = set()
        self.combo_cooldown = 0
        self.whale_signal_sent = False
        self.team_states = {agent.name: {"ready": True} for agent in self.team_agents}
        self.reset_pattern_tracking()

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Learn from battle outcome - adjust combo preferences."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=self.total_donated,
            battle_stats=battle_stats
        )

        # Track which combos led to wins
        if won:
            for combo_info in self.combo_history:
                combo = combo_info["combo"]
                # Boost effectiveness score
                if combo in self.combo_success:
                    self.combo_success[combo]["points"] *= 1.1

        return reward

    def save_learning(self, db):
        """Save learning state to database."""
        self.learning_agent.save_to_db(db)
        self.q_learner.save_to_db(db)

    def get_combo_report(self) -> Dict:
        """Get report on combos executed."""
        return {
            "combos_executed": self.combos_executed,
            "combo_history": self.combo_history[-5:],  # Last 5 combos
            "combo_effectiveness": {
                k: {
                    "uses": v["uses"],
                    "avg_points": v["points"] / max(1, v["uses"])
                }
                for k, v in self.combo_success.items()
                if v["uses"] > 0
            }
        }
