"""
Evolving Strategic Agents

Self-improving agents that learn and adapt from battles:
- Dynamic parameter adjustment based on outcomes
- Q-learning for action selection
- Cross-battle memory
- Performance evolution tracking
"""

import sys
import os
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from agents.learning_system import (
    QLearningAgent, State, ActionType, Experience,
    LearningAgent, StrategyOptimizer
)
from core.battle_history import BattleHistoryDB, AgentBattleRecord, GiftTimingRecord, generate_battle_id
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType

# Import persona agents for mixed teams
from agents.personas.pixel_pixie import PixelPixie
from agents.personas.glitch_mancer import GlitchMancer
from agents.personas.boost_responder import BoostResponder
from agents.personas.evolving_glitch_mancer import EvolvingGlitchMancer


class EvolvingKinetik(BaseAgent):
    """
    🔫 Evolving Final Sniper

    Learns optimal timing and gift selection:
    - Adjusts snipe window based on success
    - Learns best gift for different deficit sizes
    - Tracks timing effectiveness
    """

    def __init__(self, db: Optional[BattleHistoryDB] = None):
        super().__init__(name="EvolvingKinetik", emoji="🔫")
        self.agent_type = "sniper"
        self.db = db

        # Learnable parameters (using real TikTok coin values)
        self.params = {
            'snipe_window': 5,  # Seconds before end to act
            'min_deficit_for_universe': 30000,  # Use Universe if deficit > 30k
            'min_deficit_for_lion': 15000,      # Use Lion if deficit > 15k
            'min_deficit_for_phoenix': 5000     # Use Phoenix if deficit > 5k
        }

        # Learning state
        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)
        self.q_learner = QLearningAgent(self.agent_type)

        # Battle state
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.has_acted = False
        self.action_taken = None
        self.action_time = None

        # Load learned params and state if available
        self._load_learned_params()
        self._load_learning_state()

    def _load_learned_params(self):
        """Load parameters from database if available."""
        if self.db:
            latest = self.db.get_latest_strategy_params(self.agent_type)
            if latest:
                self.params.update(latest['params'])
                print(f"🔫 Loaded learned params v{latest['meta']['version']} "
                      f"(win rate: {latest['meta']['win_rate']*100:.1f}%)")

    def _load_learning_state(self):
        """Load learning state from database."""
        if self.db:
            self.learning_agent.load_from_db(self.db)
            self.q_learner.load_from_db(self.db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.has_acted = False
        self.action_taken = None
        self.action_time = None

    def decide_action(self, battle):
        """Learning-enhanced decision making."""
        if self.has_acted:
            return

        time_remaining = battle.time_manager.time_remaining()
        current_time = battle.time_manager.current_time

        # Only act within snipe window
        if time_remaining > self.params['snipe_window']:
            return

        # Get current state
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score
        deficit = opponent_score - creator_score

        # Build state for Q-learning
        state = State(
            time_remaining=time_remaining,
            score_diff=creator_score - opponent_score,
            multiplier=self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0,
            in_boost=self.phase_manager.boost1_active or self.phase_manager.boost2_active if self.phase_manager else False,
            boost2_triggered=self.phase_manager.boost2_triggered if self.phase_manager else False,
            phase="FINAL",
            gloves_available=0,
            power_ups_available=[]
        )

        # Q-learning suggests action (exploration vs exploitation)
        suggested_action = self.q_learner.choose_action(state, [
            ActionType.SEND_WHALE_GIFT,
            ActionType.SEND_LARGE_GIFT,
            ActionType.SEND_MEDIUM_GIFT,
            ActionType.WAIT
        ])

        # Map Q-action to actual gift (real TikTok coin values)
        if deficit <= 0:
            # We're winning, maybe wait
            if suggested_action == ActionType.WAIT:
                return
            gift_name, points = "Lion", 29999
        elif deficit > self.params['min_deficit_for_universe']:
            gift_name, points = "TikTok Universe", 44999
        elif deficit > self.params['min_deficit_for_lion']:
            gift_name, points = "Lion", 29999
        elif deficit > self.params['min_deficit_for_phoenix']:
            gift_name, points = "Dragon Flame", 10000
        else:
            gift_name, points = "Lion", 29999

        # Execute action
        print(f"\n🔫 EvolvingKinetik activating! Deficit: {deficit:,} points")
        print(f"   Params: snipe_window={self.params['snipe_window']}s")
        print(f"   🚀 Deploying {gift_name}!")

        self.send_gift(battle, gift_name, points)
        self.has_acted = True
        self.action_taken = gift_name
        self.action_time = current_time

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        # Adjust parameters based on outcome
        if won and self.action_taken:
            # Successful timing, reinforce
            pass
        elif not won and self.action_taken:
            # Failed despite acting, maybe act earlier
            self.params['snipe_window'] = min(10, self.params['snipe_window'] + 0.5)

        # Save learning state to database
        if self.db:
            self.learning_agent.save_to_db(self.db)
            self.q_learner.save_to_db(self.db)

        return reward

    def get_evolution_status(self) -> Dict:
        """Get learning/evolution status."""
        return {
            'name': self.name,
            'params': self.params,
            'battles': self.learning_agent.total_battles,
            'win_rate': self.learning_agent.get_win_rate(),
            'recent_performance': self.learning_agent.get_recent_performance(10)
        }


class EvolvingStrikeMaster(BaseAgent):
    """
    🥊 Evolving Glove Expert

    Learns optimal glove timing through experience:
    - Tracks success rate by phase/timing
    - Adapts strategy based on patterns
    - Uses Q-learning for timing decisions
    """

    def __init__(self, db: Optional[BattleHistoryDB] = None):
        super().__init__(name="EvolvingStrikeMaster", emoji="🥊")
        self.agent_type = "glove_expert"
        self.db = db

        # Learnable parameters
        self.params = {
            'prefer_boost_phase': 0.7,  # Probability to prefer boost
            'prefer_last_30s': 0.3,     # Probability to prefer last 30s
            'min_gloves_per_battle': 2,
            'max_gloves_per_battle': 4,
            'cooldown': 15              # Seconds between gloves
        }

        # Learning state
        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)
        self.q_learner = QLearningAgent(self.agent_type, epsilon=0.4)

        # Battle state
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.gloves_sent = 0
        self.gloves_activated = 0
        self.last_glove_time = -100
        self.glove_history: List[Dict] = []

        self._load_learned_params()
        self._load_learning_state()

    def _load_learned_params(self):
        """Load parameters from database if available."""
        if self.db:
            latest = self.db.get_latest_strategy_params(self.agent_type)
            if latest:
                for key in ['prefer_boost_phase', 'prefer_last_30s']:
                    if key in latest['params']:
                        self.params[key] = latest['params'][key]

    def _load_learning_state(self):
        """Load learning state from database."""
        if self.db:
            self.learning_agent.load_from_db(self.db)
            self.q_learner.load_from_db(self.db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.gloves_sent = 0
        self.gloves_activated = 0
        self.last_glove_time = -100
        self.glove_history = []

    def decide_action(self, battle):
        """Learning-enhanced glove timing."""
        if self.gloves_sent >= self.params['max_gloves_per_battle']:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # Respect cooldown
        if current_time - self.last_glove_time < self.params['cooldown']:
            return

        # Build state
        multiplier = self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0
        in_boost = multiplier > 1.0
        in_last_30s = time_remaining <= 30

        state = State(
            time_remaining=time_remaining,
            score_diff=battle.score_tracker.creator_score - battle.score_tracker.opponent_score,
            multiplier=multiplier,
            in_boost=in_boost,
            boost2_triggered=self.phase_manager.boost2_triggered if self.phase_manager else False,
            phase="BOOST" if in_boost else ("FINAL" if in_last_30s else "NORMAL"),
            gloves_available=self.params['max_gloves_per_battle'] - self.gloves_sent,
            power_ups_available=[]
        )

        # Q-learning decision
        action = self.q_learner.choose_action(state, [ActionType.SEND_GLOVE, ActionType.WAIT])

        if action == ActionType.WAIT:
            return

        # Check conditions with learned preferences
        should_send = False
        send_reason = ""

        if in_boost and random.random() < self.params['prefer_boost_phase']:
            should_send = True
            send_reason = "boost phase (learned preference)"
        elif in_last_30s and random.random() < self.params['prefer_last_30s']:
            should_send = True
            send_reason = "last 30s (learned preference)"
        elif self.gloves_sent < self.params['min_gloves_per_battle'] and time_remaining < 60:
            should_send = True
            send_reason = "minimum glove requirement"

        if should_send:
            print(f"\n🥊 EvolvingStrikeMaster sending GLOVE!")
            print(f"   Reason: {send_reason}")
            print(f"   Gloves sent: {self.gloves_sent + 1}/{self.params['max_gloves_per_battle']}")
            print(f"   Success rate: {self.gloves_activated}/{self.gloves_sent} "
                  f"({self.gloves_activated/max(self.gloves_sent, 1)*100:.0f}%)")

            self.send_gift(battle, "GLOVE", 100)
            self.gloves_sent += 1
            self.last_glove_time = current_time

            # Record for learning
            self.glove_history.append({
                'time': current_time,
                'in_boost': in_boost,
                'in_last_30s': in_last_30s,
                'multiplier': multiplier
            })

    def record_glove_activation(self, activated: bool):
        """Record glove activation result."""
        if self.glove_history:
            self.glove_history[-1]['activated'] = activated
            if activated:
                self.gloves_activated += 1

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        # Analyze glove history and adapt
        if self.glove_history:
            boost_gloves = [g for g in self.glove_history if g.get('in_boost', False)]
            last30_gloves = [g for g in self.glove_history if g.get('in_last_30s', False)]

            boost_success = sum(1 for g in boost_gloves if g.get('activated', False)) / max(len(boost_gloves), 1)
            last30_success = sum(1 for g in last30_gloves if g.get('activated', False)) / max(len(last30_gloves), 1)

            # Adaptive learning
            if len(boost_gloves) >= 2:
                self.params['prefer_boost_phase'] = 0.3 + boost_success * 0.6
            if len(last30_gloves) >= 2:
                self.params['prefer_last_30s'] = 0.3 + last30_success * 0.6

            print(f"\n📊 StrikeMaster Learning Update:")
            print(f"   Boost success: {boost_success*100:.0f}% -> prefer: {self.params['prefer_boost_phase']:.2f}")
            print(f"   Last30 success: {last30_success*100:.0f}% -> prefer: {self.params['prefer_last_30s']:.2f}")

        # Save learning state to database
        if self.db:
            self.learning_agent.save_to_db(self.db)
            self.q_learner.save_to_db(self.db)

        return reward

    def get_evolution_status(self) -> Dict:
        """Get learning/evolution status."""
        return {
            'name': self.name,
            'params': self.params,
            'battles': self.learning_agent.total_battles,
            'win_rate': self.learning_agent.get_win_rate(),
            'glove_stats': {
                'total_sent': self.gloves_sent,
                'total_activated': self.gloves_activated
            }
        }


class EvolvingPhaseTracker(BaseAgent):
    """
    ⏱️ Evolving Phase Tracker

    Helps qualify for Boost #2 threshold during the 30s window before trigger.
    New timing: Boost #2 triggers between 120-160s
    Threshold window opens 30s before trigger time.

    Enhanced with RACE MODE:
    - Detects when opponent is close to qualifying
    - Sends bigger gifts when behind in the race
    - Urgent mode triggers whale gifts for last-second qualification
    """

    def __init__(self, db: Optional[BattleHistoryDB] = None):
        super().__init__(name="EvolvingPhaseTracker", emoji="⏱️")
        self.agent_type = "phase_tracker"
        self.db = db

        # Learnable parameters
        self.params = {
            'aggression_in_window': 0.6,  # Probability to send during threshold window
            'gift_size_multiplier': 1.0,  # Scale gift sizes
            'race_mode_threshold': 0.7,   # Trigger race mode when opponent at 70%+
            'urgent_mode_threshold': 0.9, # Trigger urgent mode when opponent at 90%+
        }

        # Learning state
        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)

        # Battle state
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.gifts_sent = 0
        self.last_action_time = -5
        self.race_mode_active = False
        self.urgent_mode_active = False
        self.total_donated = 0

        # SUSPENSE: Wait 15-20 seconds before starting qualification
        # This creates tension - only 10-15 seconds left to qualify!
        self.qualification_delay = random.randint(15, 20)
        self.suspense_announced = False

        self._load_learned_params()
        self._load_learning_state()

    def _load_learned_params(self):
        """Load parameters from database if available."""
        if self.db:
            latest = self.db.get_latest_strategy_params(self.agent_type)
            if latest:
                for key in self.params:
                    if key in latest['params']:
                        self.params[key] = latest['params'][key]

    def _load_learning_state(self):
        """Load learning state from database."""
        if self.db:
            self.learning_agent.load_from_db(self.db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.gifts_sent = 0
        self.last_action_time = -5
        self.race_mode_active = False
        self.urgent_mode_active = False
        self.total_donated = 0
        # Randomize qualification delay for suspense (15-20 seconds)
        self.qualification_delay = random.randint(15, 20)
        self.suspense_announced = False

    def decide_action(self, battle):
        """Send gifts during Boost #2 threshold window with race mode awareness."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time

        # Check if Boost #2 will trigger
        if not self.phase_manager.boost2_trigger_time:
            return  # No Boost #2 this battle

        # Already qualified? Stop racing but maybe sabotage opponent?
        if self.phase_manager.boost2_creator_qualified:
            self.race_mode_active = False
            self.urgent_mode_active = False
            return

        # Check if threshold window is active
        if not self.phase_manager.boost2_threshold_window_active:
            return  # Window not open yet

        # === SUSPENSE: Wait 15-20 seconds before starting qualification! ===
        window_start = self.phase_manager.boost2_threshold_window_start
        time_in_window = current_time - window_start if window_start else 0
        time_to_trigger = self.phase_manager.boost2_trigger_time - current_time

        # Announce the wait once (5 seconds into window)
        if not self.suspense_announced and time_in_window >= 5:
            self.suspense_announced = True
            print(f"\n⏱️🔮 PhaseTracker: The enigma challenges us...")
            print(f"   ⏳ Analyzing the threshold... {time_to_trigger}s to solve it")

        # Wait for qualification delay (building suspense!)
        if time_in_window < self.qualification_delay:
            return  # Not time yet... suspense building!

        # === NOW IT'S GO TIME! Only 10-15 seconds left! ===

        # Get race status
        threshold = self.phase_manager.boost2_threshold
        creator_points = self.phase_manager.boost2_creator_points
        opponent_points = self.phase_manager.boost2_opponent_points
        creator_progress = creator_points / max(threshold, 1)
        opponent_progress = opponent_points / max(threshold, 1)
        remaining = threshold - creator_points

        if remaining <= 0:
            return  # Already qualified

        # RACE MODE DETECTION
        old_race_mode = self.race_mode_active
        old_urgent_mode = self.urgent_mode_active

        # Enter race mode when opponent is getting close
        if opponent_progress >= self.params['race_mode_threshold']:
            self.race_mode_active = True
        if opponent_progress >= self.params['urgent_mode_threshold']:
            self.urgent_mode_active = True

        # Also enter urgent mode in last 10s of window (but after delay has passed)
        if time_to_trigger <= 10 and creator_progress < 1.0:
            self.urgent_mode_active = True

        # Announce mode changes
        if self.race_mode_active and not old_race_mode:
            print(f"\n⏱️🏁 PhaseTracker: RACE TO CRACK THE ENIGMA! Only {time_to_trigger}s left!")
            print(f"   Opponent at {opponent_progress*100:.0f}% - stepping up gifts!")
        if self.urgent_mode_active and not old_urgent_mode:
            print(f"\n⏱️🚨 PhaseTracker: URGENT MODE! ({time_to_trigger:.0f}s left)")
            print(f"   Switching to WHALE GIFTS!")

        # Dynamic cooldown based on mode
        if self.urgent_mode_active:
            cooldown = 1  # Super fast in urgent mode
        elif self.race_mode_active:
            cooldown = 2  # Fast in race mode
        else:
            cooldown = 3  # Normal cooldown

        if current_time - self.last_action_time < cooldown:
            return

        # Choose gift based on mode and remaining points
        # REALISTIC: Gift size matches what we actually need to qualify!
        if self.urgent_mode_active and remaining >= 10000:
            # URGENT and need a lot: Send whale gifts
            if remaining >= 30000:
                gift_name, points = "TikTok Universe", 44999
            elif remaining >= 10000:
                gift_name, points = "Lion", 29999
            else:
                gift_name, points = "Dragon Flame", 10000
        elif self.race_mode_active and remaining >= 1000:
            # RACE MODE with significant remaining: Send big gifts
            if remaining >= 20000:
                gift_name, points = "Lion", 29999
            elif remaining >= 5000:
                gift_name, points = "Dragon Flame", 10000
            elif remaining >= 1000:
                gift_name, points = "Rosa Nebula", 299
            else:
                gift_name, points = "Cap", 99
        else:
            # Normal mode OR small remaining: Calculated gifts matching need
            # REALISTIC matching - don't send Dragon Flame for 4 coin threshold!
            if remaining >= 10000:
                gift_name, points = "Dragon Flame", 10000
            elif remaining >= 1000:
                gift_name, points = "Rosa Nebula", 299
            elif remaining >= 200:
                gift_name, points = "Cap", 99
            elif remaining >= 50:
                gift_name, points = "Doughnut", 30
            elif remaining >= 10:
                gift_name, points = "Heart", 5
            else:
                # Tiny threshold (< 10): use Rose or Heart
                gift_name, points = "Heart", 5

        # Determine send probability based on mode
        if self.urgent_mode_active:
            send_chance = 0.95  # Almost always send in urgent
        elif self.race_mode_active:
            send_chance = 0.85  # High chance in race mode
        else:
            send_chance = self.params['aggression_in_window']

        # Send gift
        if random.random() < send_chance:
            points = int(points * self.params['gift_size_multiplier'])

            mode_str = "🚨URGENT" if self.urgent_mode_active else ("🏁RACING" if self.race_mode_active else "")
            print(f"\n⏱️ PhaseTracker {mode_str}: Qualifying for Boost #2!")
            print(f"   Progress: {creator_points:,}/{threshold:,} ({creator_progress*100:.0f}%)")
            print(f"   Opponent: {opponent_points:,}/{threshold:,} ({opponent_progress*100:.0f}%)")
            print(f"   Sending {gift_name} ({points:,} coins) - need {remaining:,} more")

            self.send_gift(battle, gift_name, points)
            self.total_donated += points
            self.gifts_sent += 1
            self.last_action_time = current_time

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle with race mode analysis."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        # Adapt based on boost2 outcome
        qualified = battle_stats.get('boost2_creator_qualified', False)
        opponent_qualified = battle_stats.get('boost2_opponent_qualified', False)

        if won and qualified:
            # We qualified and won - good strategy
            self.params['aggression_in_window'] = min(0.9, self.params['aggression_in_window'] + 0.05)
        elif not qualified and self.phase_manager and self.phase_manager.boost2_trigger_time:
            # Boost #2 was available but we didn't qualify - be more aggressive
            self.params['aggression_in_window'] = min(0.95, self.params['aggression_in_window'] + 0.1)
            self.params['gift_size_multiplier'] = min(2.0, self.params['gift_size_multiplier'] + 0.2)
            # Lower race mode thresholds to react earlier
            self.params['race_mode_threshold'] = max(0.5, self.params['race_mode_threshold'] - 0.1)
            self.params['urgent_mode_threshold'] = max(0.7, self.params['urgent_mode_threshold'] - 0.1)

        # Learn from race outcomes
        if opponent_qualified and not qualified:
            # Lost the race - be more aggressive next time
            print(f"⏱️📉 PhaseTracker Learning: Lost race to opponent - increasing aggression")
            self.params['race_mode_threshold'] = max(0.4, self.params['race_mode_threshold'] - 0.15)
        elif qualified and not opponent_qualified:
            # Won the race - strategy is working
            print(f"⏱️📈 PhaseTracker Learning: Won race! Strategy working well")

        # Save learning state to database
        if self.db:
            self.learning_agent.save_to_db(self.db)

        return reward


class EvolvingLoadoutMaster(BaseAgent):
    """
    🧰 Evolving Loadout Master

    Learns optimal power-up deployment:
    - GLOVE: Use during boosts for guaranteed x5 (30s duration)
    - HAMMER: Counter opponent x5
    - FOG: Hide scores when ahead
    - TIME BONUS: Use in last 5 seconds to extend battle
    """

    def __init__(self, db: Optional[BattleHistoryDB] = None):
        super().__init__(name="EvolvingLoadoutMaster", emoji="🧰")
        self.agent_type = "loadout_master"
        self.db = db

        # Learnable parameters
        self.params = {
            'hammer_when_x5': True,
            'fog_lead_threshold': 5000,    # Use fog when leading by 5k+ coins
            'fog_time_threshold': 120,
        }

        # Learning state
        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)

        # Battle state
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.gloves_used = 0
        self.hammer_used = False
        self.fog_used = False
        self.time_bonus_used = False
        self.power_ups_used: List[str] = []

        # Load learning state
        self._load_learning_state()

    def _load_learning_state(self):
        """Load learning state from database."""
        if self.db:
            self.learning_agent.load_from_db(self.db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.gloves_used = 0
        self.hammer_used = False
        self.fog_used = False
        self.time_bonus_used = False
        self.power_ups_used = []

    def decide_action(self, battle):
        """Strategic power-up deployment."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score
        lead = creator_score - opponent_score

        # Check boost status
        in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active
        in_final_30s = self.phase_manager.is_in_final_30s(current_time)

        # GLOVE: Use during boosts for guaranteed x5 activation (30s duration)
        if self.gloves_used < 2 and not self.phase_manager.active_glove_x5:
            # Use glove during boost (first priority)
            if in_boost:
                print(f"🧰 EvolvingLoadoutMaster: Deploying GLOVE during boost!")
                if self.phase_manager.use_power_up(PowerUpType.GLOVE, "creator", current_time):
                    self.gloves_used += 1
                    self.power_ups_used.append('GLOVE')
            # Use glove in final 30s (second priority)
            elif in_final_30s and self.gloves_used == 0:
                print(f"🧰 EvolvingLoadoutMaster: Deploying GLOVE in final 30s!")
                if self.phase_manager.use_power_up(PowerUpType.GLOVE, "creator", current_time):
                    self.gloves_used += 1
                    self.power_ups_used.append('GLOVE')

        # HAMMER: Counter OPPONENT's x5 only (not our own!)
        if self.params['hammer_when_x5'] and not self.hammer_used:
            # Only use Hammer if OPPONENT has an active glove
            if (self.phase_manager.active_glove_x5 and
                self.phase_manager.active_glove_owner == "opponent"):
                print(f"🧰 EvolvingLoadoutMaster: Deploying HAMMER against opponent's x5!")
                if self.phase_manager.use_power_up(PowerUpType.HAMMER, "creator", current_time):
                    self.hammer_used = True
                    self.power_ups_used.append('HAMMER')

        # FOG: When ahead, use in final 30s to hide lead
        if not self.fog_used and in_final_30s:
            if lead >= self.params['fog_lead_threshold']:
                print(f"🧰 EvolvingLoadoutMaster: Deploying FOG to hide lead!")
                if self.phase_manager.use_power_up(PowerUpType.FOG, "creator", current_time):
                    self.fog_used = True
                    self.power_ups_used.append('FOG')

        # TIME BONUS: Use in last 5 seconds ONLY (best strategy)
        if not self.time_bonus_used and time_remaining <= 5:
            print(f"🧰 EvolvingLoadoutMaster: Deploying TIME BONUS in final 5 seconds!")
            if self.phase_manager.use_power_up(PowerUpType.TIME_BONUS, "creator", current_time):
                self.time_bonus_used = True
                self.power_ups_used.append('TIME_BONUS')

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        # Adapt fog threshold based on outcome
        if won and 'FOG' in self.power_ups_used:
            # Fog helped, maybe use earlier
            self.params['fog_time_threshold'] = max(90, self.params['fog_time_threshold'] - 5)
        elif not won and 'FOG' not in self.power_ups_used:
            # Didn't use fog and lost, lower threshold
            self.params['fog_lead_threshold'] = max(3000, self.params['fog_lead_threshold'] - 1000)

        # Save learning state to database
        if self.db:
            self.learning_agent.save_to_db(self.db)

        return reward


def create_evolving_team(
    phase_manager: AdvancedPhaseManager,
    db: Optional[BattleHistoryDB] = None
) -> List:
    """Create a team of evolving agents."""
    kinetik = EvolvingKinetik(db=db)
    strike_master = EvolvingStrikeMaster(db=db)
    phase_tracker = EvolvingPhaseTracker(db=db)
    loadout_master = EvolvingLoadoutMaster(db=db)

    # Link to phase manager
    kinetik.set_phase_manager(phase_manager)
    strike_master.set_phase_manager(phase_manager)
    phase_tracker.set_phase_manager(phase_manager)
    loadout_master.set_phase_manager(phase_manager)

    return [kinetik, strike_master, phase_tracker, loadout_master]


def create_mixed_strategic_team(
    phase_manager: AdvancedPhaseManager,
    db: Optional[BattleHistoryDB] = None,
    budget_intelligence = None
) -> List:
    """
    Create a mixed team of strategic + persona agents.

    Team composition:
    - 4 Strategic agents (learning-based, phase-aware)
    - 3 Persona agents (personality-driven)

    Roles:
    🔫 Kinetik        - Final sniper (last 5s)
    🥊 StrikeMaster   - Glove expert (boosts + last 30s)
    ⏱️ PhaseTracker   - Boost #2 threshold (90-130s window)
    🧰 LoadoutMaster  - Power-ups (Hammer, Fog, Time)
    🚀 BoostResponder - Maximizes boosts + counters opponent
    🧚‍♀️ PixelPixie    - Early momentum (constant small gifts)
    🌀 GlitchMancer   - Chaos factor (random bursts)
    """
    # Create strategic agents
    kinetik = EvolvingKinetik(db=db)
    strike_master = EvolvingStrikeMaster(db=db)
    phase_tracker = EvolvingPhaseTracker(db=db)
    loadout_master = EvolvingLoadoutMaster(db=db)

    # Link strategic agents to phase manager
    kinetik.set_phase_manager(phase_manager)
    strike_master.set_phase_manager(phase_manager)
    phase_tracker.set_phase_manager(phase_manager)
    loadout_master.set_phase_manager(phase_manager)

    # Create persona agents (all need phase_manager for strategic decisions)
    # Pass budget_intelligence and db to agents that use them for learning
    boost_responder = BoostResponder(phase_manager=phase_manager, budget_intelligence=budget_intelligence, db=db)
    pixel_pixie = PixelPixie(phase_manager=phase_manager, db=db)

    # Use EvolvingGlitchMancer instead of regular GlitchMancer
    evolving_glitch_mancer = EvolvingGlitchMancer(
        phase_manager=phase_manager,
        budget_intelligence=budget_intelligence,
        db=db
    )

    # Set agent types for broadcasting
    boost_responder.agent_type = "boost_responder"
    pixel_pixie.agent_type = "threshold_helper"
    # EvolvingGlitchMancer already has agent_type = "burst_master"

    print("\n👥 Mixed Strategic Team Created:")
    print("   🔫 EvolvingKinetik      - Final sniper (last 5s)")
    print("   🥊 EvolvingStrikeMaster - Glove expert")
    print("   ⏱️  EvolvingPhaseTracker - Boost #2 threshold (big gifts)")
    print("   🧰 EvolvingLoadoutMaster - Power-ups (Hammer, Fog, Time)")
    print("   🚀 BoostResponder       - Boost/x5 maximizer + counter")
    print("   🧚‍♀️ PixelPixie           - Boost #2 threshold helper (roses)")
    print("   🌀 EvolvingGlitchMancer - LEARNING burst master (whale deployment)")

    return [kinetik, strike_master, phase_tracker, loadout_master, boost_responder, pixel_pixie, evolving_glitch_mancer]


def reset_evolving_team(agents: List):
    """Reset all evolving agents for new battle."""
    for agent in agents:
        if hasattr(agent, 'reset_for_battle'):
            agent.reset_for_battle()


def learn_from_battle_results(agents: List, won: bool, battle_stats: Dict) -> Dict[str, float]:
    """Have all agents learn from battle results."""
    rewards = {}
    for agent in agents:
        if hasattr(agent, 'learn_from_battle'):
            reward = agent.learn_from_battle(won, battle_stats)
            rewards[agent.name] = reward

    # Print learning summary
    print("\n📚 Learning Persistence Summary:")
    learning_agents = [a for a in agents if hasattr(a, 'learning_agent')]
    for agent in learning_agents:
        la = agent.learning_agent
        print(f"   {agent.emoji} {agent.name}: {la.total_battles} battles, {la.get_win_rate()*100:.1f}% win rate")

    return rewards


def get_team_learning_summary(db: 'BattleHistoryDB') -> Dict:
    """Get learning summary for all agents from database."""
    return db.get_all_agent_stats()


def get_team_evolution_status(agents: List) -> Dict:
    """Get evolution status for all agents."""
    status = {}
    for agent in agents:
        if hasattr(agent, 'get_evolution_status'):
            status[agent.name] = agent.get_evolution_status()
    return status


if __name__ == '__main__':
    print("Evolving Agents Demo")
    print("="*60)

    from core.advanced_phase_system import AdvancedPhaseManager

    # Create phase manager
    pm = AdvancedPhaseManager(battle_duration=180)

    # Create evolving team
    team = create_evolving_team(pm)

    print("\n👥 Evolving Team Created:")
    for agent in team:
        print(f"   {agent.emoji} {agent.name}")

    # Get initial evolution status
    print("\n📊 Initial Evolution Status:")
    status = get_team_evolution_status(team)
    for name, s in status.items():
        print(f"\n   {name}:")
        print(f"      Params: {s.get('params', {})}")
        print(f"      Battles: {s.get('battles', 0)}")
        print(f"      Win rate: {s.get('win_rate', 0)*100:.1f}%")

    # Simulate learning from battles
    print("\n🎓 Simulating Learning...")
    for i in range(5):
        reset_evolving_team(team)
        won = random.random() > 0.4
        battle_stats = {
            'points_donated': random.randint(50000, 300000),
            'boost2_triggered': random.random() > 0.5,
            'gloves_activated': random.randint(0, 2)
        }
        rewards = learn_from_battle_results(team, won, battle_stats)
        print(f"   Battle {i+1}: {'Win' if won else 'Loss'}")

    # Get updated evolution status
    print("\n📊 Updated Evolution Status:")
    status = get_team_evolution_status(team)
    for name, s in status.items():
        print(f"\n   {name}:")
        print(f"      Battles: {s.get('battles', 0)}")
        print(f"      Win rate: {s.get('win_rate', 0)*100:.1f}%")

    print("\n✅ Evolving Agents Demo Complete!")
