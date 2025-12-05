"""
Agent ChaoticTrickster - The Psychological Warfare Specialist

Master of mind games and unpredictable tactics. Uses bluffs, decoys,
and chaotic patterns to confuse opponents and create opportunities.

STRATEGY:
- Bluff with rapid small gifts (fake aggression)
- Send decoy medium gifts before whale pushes
- Strategic pauses to create uncertainty
- Fog bursts to obscure true intentions
- Unpredictable timing patterns

MECHANICS:
- Psychological warfare actions have cooldowns
- Bluffs are cheap but effective for confusion
- Decoys set up real attacks
- Learns which tactics work against different opponents
- Can trigger opponent mistakes
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin
from agents.learning_system import QLearningAgent, State, ActionType, LearningAgent
from core.gift_catalog import get_gift_catalog
from typing import Optional, List, Dict
import random


class ChaoticTrickster(BaseAgent, CoordinationMixin):
    """
    Psychological warfare specialist using bluffs, decoys, and chaos.

    Unpredictable tactics designed to confuse and manipulate opponents.
    """

    def __init__(self, phase_manager=None, db=None):
        super().__init__(name="ChaoticTrickster", emoji="🎭")
        CoordinationMixin.__init__(self)

        self.phase_manager = phase_manager
        self.gift_catalog = get_gift_catalog()

        # Psychological warfare state
        self.bluff_active = False
        self.bluff_end_time = 0
        self.decoy_deployed = False
        self.pause_active = False
        self.pause_end_time = 0
        self.fog_burst_active = False

        # Cooldowns (in seconds) - REDUCED for more chaos
        self.cooldowns = {
            "bluff": 0,
            "decoy": 0,
            "pause": 0,
            "fog_burst": 0
        }
        self.cooldown_durations = {
            "bluff": 20,      # Reduced from 30
            "decoy": 30,      # Reduced from 45
            "pause": 12,      # Reduced from 20
            "fog_burst": 40   # Reduced from 60
        }

        # Learning system
        self.learning_agent = LearningAgent(
            name="ChaoticTrickster",
            agent_type="chaotic_trickster"
        )
        self.q_learner = QLearningAgent(
            agent_type="chaotic_trickster",
            learning_rate=0.1,
            epsilon=0.4  # High exploration - chaos is key!
        )

        # Load from DB if available
        if db:
            self.learning_agent.load_from_db(db)
            self.q_learner.load_from_db(db)

        # Tactic effectiveness (learned)
        self.tactic_success = {
            "bluff": {"uses": 0, "successes": 0},
            "decoy": {"uses": 0, "successes": 0},
            "pause": {"uses": 0, "successes": 0},
            "fog_burst": {"uses": 0, "successes": 0}
        }

        # Chaos parameters - BOOSTED
        self.chaos_level = 0.65  # Higher chaos for more unpredictability
        self.aggression_mask = 0.4  # More fake aggression
        self.taunt_chance = 0.08  # 8% taunt chance (up from 3%)

        # Budget
        self.budget = 75000  # Increased budget for more tricks

        # Taunt messages
        self.taunt_messages = [
            "Is this all you've got?",
            "*yawns dramatically*",
            "Predicting your every move...",
            "Too easy.",
            "You're playing checkers, I'm playing chess.",
            "Watch closely... or don't.",
            "Now you see me...",
            "Was that supposed to hurt?"
        ]

        self.bluff_messages = [
            "HERE IT COMES!!!",
            "WHALE INCOMING!!!",
            "GET READY!!!",
            "THIS IS IT!!!",
            "*intensifies*"
        ]

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return ["PSYCHOLOGICAL_WARFARE", "BLUFF", "DECOY", "CHAOS"]

    def decide_action(self, battle):
        """ChaoticTrickster decision logic - sow confusion."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        score_diff = battle.score_tracker.creator_score - battle.score_tracker.opponent_score

        # Update cooldowns
        self._update_cooldowns(current_time)

        # Update emotion - tricksters thrive on chaos
        self.emotion_system.update_emotion({
            "winning": score_diff > 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
            "chaos": self.chaos_level
        })

        # Check if any active tactics should end
        self._check_active_tactics(current_time)

        # Random taunt (more frequent)
        if random.random() < self.taunt_chance:
            self.send_message(random.choice(self.taunt_messages), message_type="taunt")

        # DECIDE TACTIC based on situation
        action = self._choose_chaotic_action(battle, current_time, time_remaining, score_diff)

        if action == "bluff":
            self._execute_bluff(battle, current_time)
        elif action == "decoy":
            self._execute_decoy(battle, current_time)
        elif action == "pause":
            self._execute_strategic_pause(current_time)
        elif action == "fog_burst":
            self._execute_fog_burst(battle, current_time)
        elif action == "chaos_gift":
            self._send_chaos_gift(battle, current_time)
        elif action == "real_attack":
            self._execute_real_attack(battle, current_time)

    def _update_cooldowns(self, current_time: int):
        """Update all cooldown timers."""
        for tactic in self.cooldowns:
            if self.cooldowns[tactic] > 0 and self.cooldowns[tactic] <= current_time:
                self.cooldowns[tactic] = 0

    def _check_active_tactics(self, current_time: int):
        """Check and end active tactics."""
        if self.bluff_active and current_time >= self.bluff_end_time:
            self.bluff_active = False
            # Bluff ends with a whimper
            self.send_message("...just kidding.", message_type="chat")

        if self.pause_active and current_time >= self.pause_end_time:
            self.pause_active = False

    def _can_use_tactic(self, tactic: str, current_time: int) -> bool:
        """Check if a tactic is off cooldown."""
        return self.cooldowns[tactic] == 0 or self.cooldowns[tactic] <= current_time

    def _start_cooldown(self, tactic: str, current_time: int):
        """Start cooldown for a tactic."""
        self.cooldowns[tactic] = current_time + self.cooldown_durations[tactic]

    def _choose_chaotic_action(self, battle, current_time: int,
                                time_remaining: int, score_diff: int) -> str:
        """Choose a chaotic action based on situation."""

        # During pause, do nothing
        if self.pause_active:
            return "none"

        # During bluff, send rapid small gifts
        if self.bluff_active:
            return "chaos_gift"

        # Analyze situation
        losing_badly = score_diff < -20000
        winning_big = score_diff > 20000
        close_game = abs(score_diff) < 5000
        final_phase = time_remaining <= 60

        # Build action weights - INCREASED activity
        weights = {
            "bluff": 0.18,
            "decoy": 0.14,
            "pause": 0.08,
            "fog_burst": 0.10,
            "chaos_gift": 0.30,
            "real_attack": 0.15,
            "none": 0.05  # Reduced idle time
        }

        # Adjust based on situation
        if losing_badly:
            weights["bluff"] = 0.05
            weights["real_attack"] = 0.4
            weights["decoy"] = 0.2
        elif winning_big:
            weights["pause"] = 0.2  # Let them sweat
            weights["chaos_gift"] = 0.3
        elif close_game:
            weights["bluff"] = 0.25  # Mind games
            weights["fog_burst"] = 0.15
        elif final_phase:
            weights["real_attack"] = 0.35
            weights["decoy"] = 0.15

        # Add chaos factor
        if random.random() < self.chaos_level:
            # Truly chaotic - random weights
            weights = {k: random.random() for k in weights}

        # Check cooldowns
        for tactic in ["bluff", "decoy", "pause", "fog_burst"]:
            if not self._can_use_tactic(tactic, current_time):
                weights[tactic] = 0

        # Normalize and select
        total = sum(weights.values())
        if total == 0:
            return "none"

        roll = random.random() * total
        cumulative = 0
        for action, weight in weights.items():
            cumulative += weight
            if roll <= cumulative:
                return action

        return "none"

    def _execute_bluff(self, battle, current_time: int):
        """Execute a bluff - rapid small gifts with dramatic announcements."""
        self.bluff_active = True
        self.bluff_end_time = current_time + 5  # Bluff lasts 5 seconds

        # Dramatic announcement
        self.send_message(random.choice(self.bluff_messages), message_type="shout")
        print(f"   [{self.emoji} ChaoticTrickster: BLUFF INITIATED!]")

        # Start cooldown
        self._start_cooldown("bluff", current_time)
        self.tactic_success["bluff"]["uses"] += 1

        # Send a few rapid small gifts
        for _ in range(random.randint(2, 4)):
            if self.can_afford("Rose"):
                self.send_gift(battle, "Rose", 1)

    def _execute_decoy(self, battle, current_time: int):
        """Execute a decoy - medium gift that signals whale incoming."""
        self.decoy_deployed = True

        # Send a decoy medium gift
        decoy_gifts = ["Galaxy", "Perfume", "Confetti"]
        for gift_name in decoy_gifts:
            if self.can_afford(gift_name):
                gift = self.gift_catalog.get_gift(gift_name)
                self.send_gift(battle, gift.name, gift.coins)
                break

        # Fake announcement
        self.send_message("Warming up...", message_type="chat")
        print(f"   [{self.emoji} ChaoticTrickster: DECOY DEPLOYED!]")

        # Start cooldown
        self._start_cooldown("decoy", current_time)
        self.tactic_success["decoy"]["uses"] += 1

    def _execute_strategic_pause(self, current_time: int):
        """Execute a strategic pause - go silent to create uncertainty."""
        self.pause_active = True
        self.pause_end_time = current_time + random.randint(8, 15)

        # Silent exit
        self.send_message("...", message_type="whisper")
        print(f"   [{self.emoji} ChaoticTrickster: STRATEGIC PAUSE - going dark]")

        # Start cooldown
        self._start_cooldown("pause", current_time)
        self.tactic_success["pause"]["uses"] += 1

    def _execute_fog_burst(self, battle, current_time: int):
        """Execute a fog burst - rapid gifts to obscure intent."""
        from core.advanced_phase_system import PowerUpType

        print(f"   [{self.emoji} ChaoticTrickster: FOG BURST!]")

        # Use fog if available
        if self.phase_manager:
            self.phase_manager.use_power_up(PowerUpType.FOG, "creator", current_time)

        # Rapid gift burst
        burst_count = random.randint(5, 10)
        for _ in range(burst_count):
            if self.can_afford("Rose"):
                self.send_gift(battle, "Rose", 1)

        self.send_message("*vanishes in a puff of roses*", message_type="action")

        # Start cooldown
        self._start_cooldown("fog_burst", current_time)
        self.tactic_success["fog_burst"]["uses"] += 1

    def _send_chaos_gift(self, battle, current_time: int):
        """Send a chaotic gift - random selection."""
        # Chaotic gift selection
        if random.random() < 0.7:
            # Small chaos gift
            gifts = ["Rose", "Heart", "Doughnut"]
        else:
            # Medium chaos gift
            gifts = ["Confetti", "Butterfly"]

        for gift_name in gifts:
            if self.can_afford(gift_name):
                gift = self.gift_catalog.get_gift(gift_name)
                self.send_gift(battle, gift.name, gift.coins)

                # Random chaotic message
                if random.random() < 0.3:
                    chaos_msgs = ["*giggles*", "Catch!", "Or maybe not?", "Yes? No?"]
                    self.send_message(random.choice(chaos_msgs), message_type="chat")
                break

    def _execute_real_attack(self, battle, current_time: int):
        """Execute a real attack - actual significant gift."""
        # Choose real gift based on budget
        attack_gifts = [
            ("Galaxy", 1000),
            ("Sports Car", 500),
            ("Shooting Star", 300)
        ]

        for gift_name, _ in attack_gifts:
            if self.can_afford(gift_name):
                gift = self.gift_catalog.get_gift(gift_name)
                self.send_gift(battle, gift.name, gift.coins)

                # Sometimes be serious
                if random.random() < 0.4:
                    self.send_message("This one's real.", message_type="chat")
                break

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.bluff_active = False
        self.bluff_end_time = 0
        self.decoy_deployed = False
        self.pause_active = False
        self.pause_end_time = 0
        self.fog_burst_active = False
        self.cooldowns = {k: 0 for k in self.cooldowns}
        self.reset_pattern_tracking()

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Learn from battle outcome - adjust chaos parameters."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=self.total_donated,
            battle_stats=battle_stats
        )

        # Track tactic success
        for tactic in self.tactic_success:
            if self.tactic_success[tactic]["uses"] > 0:
                if won:
                    self.tactic_success[tactic]["successes"] += 1

        # Adjust chaos level
        if won:
            # Winning with chaos? More chaos!
            self.chaos_level = min(0.8, self.chaos_level + 0.05)
        else:
            # Losing? Maybe be more predictable
            self.chaos_level = max(0.2, self.chaos_level - 0.05)

        return reward

    def save_learning(self, db):
        """Save learning state to database."""
        self.learning_agent.save_to_db(db)
        self.q_learner.save_to_db(db)

    def get_chaos_report(self) -> Dict:
        """Get report on chaos tactics used."""
        return {
            "chaos_level": self.chaos_level,
            "tactics_used": {
                k: v["uses"] for k, v in self.tactic_success.items()
            },
            "success_rates": {
                k: (v["successes"] / max(1, v["uses"]))
                for k, v in self.tactic_success.items()
            }
        }
