"""
Agent DefenseMaster - The Counter-Strategy Specialist

Master of defensive plays and opponent neutralization. Uses power-ups
strategically to counter opponent moves and protect team advantages.

STRATEGY:
- Track opponent patterns aggressively
- Use Hammer to neutralize opponent x5 gloves
- Deploy Fog to hide critical team moves
- Counter opponent whales with defensive positioning
- Budget-aware defensive spending

MECHANICS:
- Prioritizes Hammer when opponent has active x5
- Uses Fog before team's big plays for surprise
- Adapts strategy based on detected opponent patterns
- Coordinates with team for defensive coverage
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin
from agents.learning_system import QLearningAgent, State, ActionType, LearningAgent
from core.gift_catalog import get_gift_catalog
from typing import Optional, List, Dict
import random


class DefenseMaster(BaseAgent, CoordinationMixin):
    """
    Counter-strategy specialist focused on defensive plays and opponent neutralization.

    Uses power-ups (Hammer, Fog) strategically and adapts to opponent patterns.
    """

    def __init__(self, phase_manager=None, db=None):
        super().__init__(name="DefenseMaster", emoji="🛡️")
        CoordinationMixin.__init__(self)

        self.phase_manager = phase_manager
        self.gift_catalog = get_gift_catalog()

        # Power-up inventory
        self.hammers_available = 2
        self.hammers_used = 0
        self.fogs_available = 2
        self.fogs_used = 0

        # Counter-strategy tracking
        self.opponent_x5_detected = False
        self.opponent_whale_incoming = False
        self.last_opponent_gift_time = 0
        self.opponent_gift_count = 0
        self.opponent_total_donated = 0

        # Learning system
        self.learning_agent = LearningAgent(
            name="DefenseMaster",
            agent_type="defense_master"
        )
        self.q_learner = QLearningAgent(
            agent_type="defense_master",
            learning_rate=0.12,
            epsilon=0.25  # Less exploration, more exploitation
        )

        # Load from DB if available
        if db:
            self.learning_agent.load_from_db(db)
            self.q_learner.load_from_db(db)

        # Strategy parameters (learned over time)
        self.hammer_threshold = 0.85  # High probability to use hammer when x5 detected
        self.fog_before_whale_chance = 0.7  # Fog before team whale
        self.counter_aggression = 0.6  # How aggressively to counter

        # Proactive defense settings
        self.proactive_gift_rate = 0.25  # 25% chance to send defensive gift each tick
        self.whale_alert_threshold = 5000  # Alert at 5k+ gifts (lowered from 10k)

        # Budget
        self.budget = 100000  # Increased budget for more active defense

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return ["HAMMER", "FOG", "COUNTER_STRATEGY", "PATTERN_DETECTION"]

    def decide_action(self, battle):
        """DefenseMaster decision logic - prioritize counters and defense."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        score_diff = battle.score_tracker.creator_score - battle.score_tracker.opponent_score

        # Build state for Q-learning
        state = self._build_state(battle, current_time, time_remaining, score_diff)

        # Update emotion based on defensive situation
        self.emotion_system.update_emotion({
            "winning": score_diff > 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
            "threat_level": self._assess_threat_level(battle)
        })

        # PRIORITY 1: Counter opponent x5 with Hammer
        if self._should_use_hammer(battle, current_time):
            self._execute_hammer(battle, current_time)
            return

        # PRIORITY 2: Deploy Fog before team's big play
        if self._should_use_fog(battle, current_time, time_remaining):
            self._execute_fog(battle, current_time)
            return

        # PRIORITY 3: Counter opponent pattern with gifts
        if self._should_counter_with_gift(battle, current_time, score_diff):
            self._execute_counter_gift(battle, current_time, score_diff)
            return

        # PRIORITY 4: Defensive gift to maintain pressure
        if self._should_send_defensive_gift(time_remaining, score_diff):
            self._send_defensive_gift(battle, current_time)

    def _build_state(self, battle, current_time, time_remaining, score_diff) -> State:
        """Build state representation for learning."""
        in_boost = False
        if self.phase_manager:
            in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active

        return State(
            time_remaining=time_remaining,
            score_diff=score_diff,
            multiplier=self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0,
            in_boost=in_boost,
            boost2_triggered=self.phase_manager.boost2_triggered if self.phase_manager else False,
            phase="boost" if in_boost else "normal",
            gloves_available=self.hammers_available,  # Use hammers as "defensive gloves"
            power_ups_available=self._get_available_powerups()
        )

    def _get_available_powerups(self) -> List[str]:
        """Get list of available power-ups."""
        powerups = []
        if self.hammers_available > self.hammers_used:
            powerups.append("HAMMER")
        if self.fogs_available > self.fogs_used:
            powerups.append("FOG")
        return powerups

    def _assess_threat_level(self, battle) -> float:
        """Assess current threat level from opponent (0-1)."""
        threat = 0.0

        # Check if opponent has x5 active
        if self.phase_manager and self.phase_manager.active_glove_x5:
            if self.phase_manager.active_glove_owner == "opponent":
                threat += 0.5

        # Check opponent spending rate
        if self.opponent_gift_count > 0:
            avg_gift = self.opponent_total_donated / self.opponent_gift_count
            if avg_gift > 10000:  # Whale-level gifts
                threat += 0.3

        # Check score situation
        score_diff = battle.score_tracker.creator_score - battle.score_tracker.opponent_score
        if score_diff < 0:
            threat += min(0.2, abs(score_diff) / 100000)

        return min(1.0, threat)

    def _should_use_hammer(self, battle, current_time) -> bool:
        """Determine if we should use Hammer to neutralize opponent x5."""
        if self.hammers_used >= self.hammers_available:
            return False

        # Check if opponent has active x5
        if not self.phase_manager:
            return False

        if self.phase_manager.active_glove_x5 and self.phase_manager.active_glove_owner == "opponent":
            # Probability-based decision (learned threshold)
            return random.random() < self.hammer_threshold

        return False

    def _execute_hammer(self, battle, current_time):
        """Execute Hammer power-up to neutralize opponent x5."""
        from core.advanced_phase_system import PowerUpType

        if self.phase_manager.use_power_up(PowerUpType.HAMMER, "creator", current_time):
            self.hammers_used += 1
            self.send_message("HAMMER DOWN! Your x5 is GONE!", message_type="taunt")
            print(f"   [{self.emoji} DefenseMaster: HAMMER neutralizes opponent x5!]")

            # Learn from successful hammer use
            self.q_learner.update_q_value_direct(
                state_key=("hammer_use", current_time // 30),
                action=ActionType.USE_HAMMER,
                reward=50.0  # Reward for successful counter
            )

    def _should_use_fog(self, battle, current_time, time_remaining) -> bool:
        """Determine if we should deploy Fog."""
        if self.fogs_used >= self.fogs_available:
            return False

        # Use fog in final 30s for hidden plays
        if time_remaining <= 30 and random.random() < self.fog_before_whale_chance:
            return True

        # Use fog before team's coordinated strike (if coordinator signals)
        if hasattr(self, 'coordinator') and self.coordinator:
            pending = self.coordinator.get_pending_actions()
            if any(a.get('type') == 'whale_gift' for a in pending):
                return True

        return False

    def _execute_fog(self, battle, current_time):
        """Deploy Fog to hide team's moves."""
        from core.advanced_phase_system import PowerUpType

        if self.phase_manager and self.phase_manager.use_power_up(PowerUpType.FOG, "creator", current_time):
            self.fogs_used += 1
            self.send_message("*deploys smoke screen*", message_type="action")
            print(f"   [{self.emoji} DefenseMaster: FOG deployed - scores hidden!]")

    def _should_counter_with_gift(self, battle, current_time, score_diff) -> bool:
        """Determine if we should counter opponent with a gift."""
        # Counter if opponent is on a gifting streak
        if self.opponent_gift_count >= 3:
            time_since_last = current_time - self.last_opponent_gift_time
            if time_since_last < 10:  # Opponent is active
                return random.random() < self.counter_aggression

        # Counter if losing and need to respond
        if score_diff < -5000:
            return random.random() < 0.3

        return False

    def _execute_counter_gift(self, battle, current_time, score_diff):
        """Send a counter-gift based on opponent's activity."""
        # Adjust counter based on detected pattern
        counter = self.get_counter_adjustments()

        if counter.get('counter_whale', False) and self.can_afford("Galaxy"):
            # Counter with medium gift
            gift = self.gift_catalog.get_gift("Galaxy")
            self.send_gift(battle, gift.name, gift.coins)
            self.send_message("Countering your move!", message_type="taunt")
        elif self.can_afford("Doughnut"):
            gift = self.gift_catalog.get_gift("Doughnut")
            self.send_gift(battle, gift.name, gift.coins)

    def _should_send_defensive_gift(self, time_remaining, score_diff) -> bool:
        """Determine if we should send a defensive gift."""
        # Proactive defensive presence
        if random.random() < self.proactive_gift_rate:
            return True

        # More active in final phase
        if time_remaining <= 60 and random.random() < 0.35:
            return True

        # Counter when losing
        if score_diff < -3000 and random.random() < 0.3:
            return True

        return False

    def _send_defensive_gift(self, battle, current_time):
        """Send a defensive gift to maintain pressure."""
        # Scale gift based on situation
        if self.opponent_whale_incoming:
            # Counter whale with medium gift
            counter_gifts = ["Galaxy", "Confetti", "Shooting Star"]
            for gift_name in counter_gifts:
                if self.can_afford(gift_name):
                    gift = self.gift_catalog.get_gift(gift_name)
                    self.send_gift(battle, gift.name, gift.coins)
                    self.send_message("Countering!", message_type="chat")
                    self.opponent_whale_incoming = False  # Reset flag
                    return

        # Standard defensive gifts
        gifts = [
            ("Doughnut", 30),
            ("Heart", 5),
            ("Rose", 1)
        ]

        for gift_name, coins in gifts:
            if self.can_afford(gift_name):
                self.send_gift(battle, gift_name, coins)
                if random.random() < 0.2:
                    self.send_message("🛡️ Holding the line!", message_type="chat")
                break

    def on_opponent_gift(self, amount: int, current_time: int, phase: str, time_remaining: int):
        """Override to track opponent gifts for counter-strategy."""
        super().on_opponent_gift(amount, current_time, phase, time_remaining)

        self.opponent_gift_count += 1
        self.opponent_total_donated += amount
        self.last_opponent_gift_time = current_time

        # Detect whale incoming (lowered threshold for more reactivity)
        if amount >= self.whale_alert_threshold:
            self.opponent_whale_incoming = True
            print(f"   [{self.emoji} DefenseMaster: THREAT DETECTED - {amount:,} coins incoming!]")
            self.send_message(f"I see you! Countering...", message_type="taunt")

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.hammers_used = 0
        self.fogs_used = 0
        self.opponent_x5_detected = False
        self.opponent_whale_incoming = False
        self.last_opponent_gift_time = 0
        self.opponent_gift_count = 0
        self.opponent_total_donated = 0
        self.reset_pattern_tracking()

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Learn from battle outcome."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=self.total_donated,
            battle_stats=battle_stats
        )

        # Adjust parameters based on outcome
        if won:
            # Reinforce successful strategies
            if self.hammers_used > 0:
                self.hammer_threshold = min(0.9, self.hammer_threshold + 0.05)
        else:
            # Become more aggressive with counters
            self.counter_aggression = min(0.8, self.counter_aggression + 0.05)

        return reward

    def save_learning(self, db):
        """Save learning state to database."""
        self.learning_agent.save_to_db(db)
        self.q_learner.save_to_db(db)


# Add helper method to QLearningAgent for direct updates
def update_q_value_direct(self, state_key, action, reward):
    """Direct Q-value update without full state."""
    if state_key not in self.q_table:
        self.q_table[state_key] = {a: 0.0 for a in ActionType}
    current = self.q_table[state_key].get(action, 0.0)
    self.q_table[state_key][action] = current + self.learning_rate * (reward - current)

# Monkey-patch the method
QLearningAgent.update_q_value_direct = update_q_value_direct
