"""
EvolvingGlitchMancer - The Learning Chaos Agent 🌀

An evolving version of GlitchMancer that learns optimal burst strategies:
- Q-learning for burst timing and gift selection
- Adaptive aggression levels per phase
- Budget-aware whale deployment
- Performance tracking across battles

Learns to optimize:
- When to burst (timing within phases)
- What to send (whale vs medium vs small)
- How aggressive to be per phase (Boost #1, Boost #2, x5, Final)
- Budget conservation vs spending thresholds
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState
from agents.learning_system import (
    QLearningAgent, State, ActionType, LearningAgent
)
from core.advanced_phase_system import AdvancedPhaseManager


@dataclass
class BurstAction:
    """Possible burst actions for Q-learning."""
    BURST_WHALE = "burst_whale"      # Send whale gifts (Universe, Lion, Dragon)
    BURST_LARGE = "burst_large"      # Send large gifts (Dragon, GG)
    BURST_MEDIUM = "burst_medium"    # Send medium gifts (GG, Rosa Nebula)
    BURST_SMALL = "burst_small"      # Send small gifts (Cap, Doughnut)
    WAIT = "wait"                    # Conserve budget


class EvolvingGlitchMancer(BaseAgent):
    """
    🌀 Evolving Chaos Agent - Learns optimal burst strategies

    The primary damage dealer during boost/x5 phases.
    Learns when to unleash whale gifts for maximum impact.
    """

    def __init__(self, phase_manager=None, budget_intelligence=None, db=None):
        super().__init__(name="EvolvingGlitchMancer", emoji="🌀")
        self.agent_type = "burst_master"
        self.phase_manager = phase_manager
        self.budget_intelligence = budget_intelligence
        self.db = db

        # === LEARNABLE PARAMETERS ===
        self.params = {
            # Phase aggression levels (0-1)
            'normal_aggression': 0.1,      # Stay quiet in normal phase
            'boost1_aggression': 0.7,      # Aggressive in Boost #1
            'boost2_aggression': 0.85,     # Very aggressive in Boost #2
            'x5_aggression': 0.95,         # Maximum during our x5
            'final_30s_aggression': 0.6,   # Aggressive in final 30s
            'final_5s_aggression': 0.8,    # Very aggressive in snipe

            # Burst configuration
            'burst_cooldown_normal': 15,   # Cooldown in normal phase
            'burst_cooldown_boost': 4,     # Cooldown during boosts
            'burst_cooldown_x5': 2,        # Cooldown during x5

            # Gift selection preferences
            'whale_threshold_x5': 0.8,     # Whale probability during x5
            'whale_threshold_boost': 0.5,  # Whale probability during boost
            'whale_threshold_final': 0.4,  # Whale probability in final 30s

            # Budget thresholds
            'min_budget_for_whale': 0.15,  # Min budget % to send whales
            'conserve_for_boost2': 0.3,    # Reserve for Boost #2
        }

        # === LEARNING SYSTEMS ===
        self.learning_agent = LearningAgent(
            name=self.name,
            agent_type=self.agent_type
        )
        self.q_learner = QLearningAgent(
            agent_type=self.agent_type,
            learning_rate=0.15,
            discount_factor=0.9,
            epsilon=0.2  # 20% exploration
        )

        # === BATTLE STATE ===
        self.last_burst_time = -30
        self.bursts_this_battle = 0
        self.last_opponent_score = 0
        self.last_x5_state = False
        self.threshold_gift_sent = False

        # SUSPENSE: Wait before qualifying for Boost #2
        # EvolvingGlitchMancer waits 17-22s (2s after PixelPixie starts)
        self.qualification_delay = random.randint(17, 22)

        # === PERFORMANCE TRACKING ===
        self.phase_bursts = {
            'normal': 0, 'boost1': 0, 'boost2': 0,
            'x5': 0, 'final_30s': 0, 'final_5s': 0
        }
        self.phase_points = {
            'normal': 0, 'boost1': 0, 'boost2': 0,
            'x5': 0, 'final_30s': 0, 'final_5s': 0
        }
        self.whale_bursts = 0
        self.total_effective_points = 0

        # === GIFT OPTIONS ===
        self.whale_gifts = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
        ]
        self.large_gifts = [
            ("Dragon Flame", 10000),
            ("GG", 1000),
        ]
        self.medium_gifts = [
            ("GG", 1000),
            ("Rosa Nebula", 299),
        ]
        self.small_gifts = [
            ("Cap", 99),
            ("Doughnut", 30),
            ("Heart", 5),
        ]

        # Glitched messages (keeping the personality)
        self.glitch_messages = [
            "gl!+cH @ct!vaT3d",
            "ch@0s_m0dE.ON",
            "▓▒░ OVERLOAD ░▒▓",
            "!!!SYSTEM.GLITCH!!!",
            "*static noises*",
            "WHALE_DEPLOY.exe",
            "b00st_m4x!m!z3r",
        ]

        # Load learned state
        self._load_learned_params()
        self._load_learning_state()

    def _load_learned_params(self):
        """Load parameters from database if available."""
        if self.db:
            latest = self.db.get_latest_strategy_params(self.agent_type)
            if latest:
                self.params.update(latest['params'])
                print(f"🌀 EvolvingGlitchMancer: Loaded params v{latest['meta']['version']} "
                      f"(win rate: {latest['meta']['win_rate']*100:.1f}%)")

    def _load_learning_state(self):
        """Load learning state from database."""
        if self.db:
            self.learning_agent.load_from_db(self.db)
            self.q_learner.load_from_db(self.db)

    def set_phase_manager(self, pm):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.last_burst_time = -30
        self.bursts_this_battle = 0
        self.last_opponent_score = 0
        self.last_x5_state = False
        self.threshold_gift_sent = False
        # Randomize qualification delay (2s after PixelPixie)
        self.qualification_delay = random.randint(17, 22)

        # Reset tracking
        self.phase_bursts = {
            'normal': 0, 'boost1': 0, 'boost2': 0,
            'x5': 0, 'final_30s': 0, 'final_5s': 0
        }
        self.phase_points = {
            'normal': 0, 'boost1': 0, 'boost2': 0,
            'x5': 0, 'final_30s': 0, 'final_5s': 0
        }
        self.whale_bursts = 0
        self.total_effective_points = 0

    def _get_current_phase(self, time_remaining: int) -> str:
        """Determine current phase for learning."""
        if not self.phase_manager:
            return "normal"

        # Check x5 first (highest priority)
        our_x5 = (self.phase_manager.active_glove_x5 and
                  self.phase_manager.active_glove_owner == "creator")
        if our_x5:
            return "x5"

        # Check boosts
        if self.phase_manager.boost2_active:
            return "boost2"
        if self.phase_manager.boost1_active:
            return "boost1"

        # Check final phases
        if time_remaining <= 5:
            return "final_5s"
        if time_remaining <= 30:
            return "final_30s"

        return "normal"

    def _get_aggression_for_phase(self, phase: str) -> float:
        """Get learned aggression level for current phase."""
        aggression_map = {
            'normal': self.params['normal_aggression'],
            'boost1': self.params['boost1_aggression'],
            'boost2': self.params['boost2_aggression'],
            'x5': self.params['x5_aggression'],
            'final_30s': self.params['final_30s_aggression'],
            'final_5s': self.params['final_5s_aggression'],
        }
        return aggression_map.get(phase, 0.3)

    def _get_cooldown_for_phase(self, phase: str) -> float:
        """Get cooldown for current phase."""
        if phase == 'x5':
            return self.params['burst_cooldown_x5']
        elif phase in ['boost1', 'boost2']:
            return self.params['burst_cooldown_boost']
        else:
            return self.params['burst_cooldown_normal']

    def _build_state(self, battle, phase: str, time_remaining: int) -> State:
        """Build state for Q-learning."""
        multiplier = self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score

        return State(
            time_remaining=time_remaining,
            score_diff=creator_score - opponent_score,
            multiplier=multiplier,
            in_boost=phase in ['boost1', 'boost2'],
            boost2_triggered=self.phase_manager.boost2_triggered if self.phase_manager else False,
            phase=phase.upper(),
            gloves_available=0,
            power_ups_available=[]
        )

    def _get_available_actions(self, max_spend: int) -> List[ActionType]:
        """Get available actions based on budget."""
        actions = [ActionType.WAIT]

        if max_spend >= 5:
            actions.append(ActionType.SEND_SMALL_GIFT)
        if max_spend >= 299:
            actions.append(ActionType.SEND_MEDIUM_GIFT)
        if max_spend >= 1000:
            actions.append(ActionType.SEND_LARGE_GIFT)
        if max_spend >= 10000:
            actions.append(ActionType.SEND_WHALE_GIFT)

        return actions

    def decide_action(self, battle):
        """Learning-enhanced burst decision making."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        opponent_score = battle.score_tracker.opponent_score
        creator_score = battle.score_tracker.creator_score
        multiplier = self.phase_manager.get_current_multiplier()

        # Detect opponent spike
        opponent_spike = opponent_score - self.last_opponent_score
        self.last_opponent_score = opponent_score

        # === THRESHOLD WINDOW - Help with qualification ===
        # SUSPENSE: Wait 17-22 seconds into window before qualifying!
        if (self.phase_manager.boost2_threshold_window_active and
            not self.threshold_gift_sent and
            not self.phase_manager.boost2_creator_qualified):
            window_start = self.phase_manager.boost2_threshold_window_start
            if window_start:
                time_in_window = current_time - window_start
                # Wait for qualification delay (suspense!)
                if time_in_window >= self.qualification_delay:
                    self._send_threshold_help(battle, current_time)
            return

        # === DETERMINE PHASE ===
        phase = self._get_current_phase(time_remaining)

        # Detect x5 activation - reset cooldown for immediate response
        our_x5 = (self.phase_manager.active_glove_x5 and
                  self.phase_manager.active_glove_owner == "creator")
        if our_x5 and not self.last_x5_state:
            self.last_burst_time = -100  # Force immediate action
            print(f"🌀 EvolvingGlitchMancer: X5 DETECTED! Resetting for whale attack!")
        self.last_x5_state = our_x5

        # === COOLDOWN CHECK ===
        cooldown = self._get_cooldown_for_phase(phase)
        if current_time - self.last_burst_time < cooldown:
            return

        # === BUDGET INTELLIGENCE ===
        max_spend = 999999
        if self.budget_intelligence:
            bi_phase = "boost" if phase in ['boost1', 'boost2'] else (
                "final_30s" if phase in ['final_30s', 'final_5s'] else "normal"
            )
            recommendation = self.budget_intelligence.should_spend_in_phase(
                bi_phase, time_remaining, creator_score, opponent_score, multiplier
            )

            # During x5, always allow spending
            if our_x5:
                available = self.budget_intelligence.get_available_budget(0, time_remaining)
                max_spend = max(available, recommendation["max_spend"])
            elif not recommendation["should_spend"]:
                return  # Budget intelligence says don't spend
            else:
                max_spend = recommendation["max_spend"]

        # === Q-LEARNING DECISION ===
        state = self._build_state(battle, phase, time_remaining)
        available_actions = self._get_available_actions(max_spend)

        if len(available_actions) <= 1:  # Only WAIT available
            return

        # Get Q-learning suggested action
        suggested_action = self.q_learner.choose_action(state, available_actions)

        if suggested_action == ActionType.WAIT:
            # Check aggression - maybe burst anyway
            aggression = self._get_aggression_for_phase(phase)
            if random.random() > aggression:
                return  # Respect the WAIT decision

        # === EXECUTE BURST ===
        self._execute_burst(battle, phase, suggested_action, max_spend, multiplier, current_time)
        self.last_burst_time = current_time
        self.bursts_this_battle += 1
        self.phase_bursts[phase] = self.phase_bursts.get(phase, 0) + 1

    def _execute_burst(self, battle, phase: str, action: ActionType,
                       max_spend: int, multiplier: float, current_time: int):
        """Execute a burst based on Q-learning decision."""

        # Check minimum budget
        if max_spend < 5:
            return

        self.emotion_system.force_emotion(EmotionalState.CHAOTIC, current_time)

        # Determine burst size based on action
        if action == ActionType.SEND_WHALE_GIFT:
            burst_type = "WHALE"
            gifts_to_send = self._select_whale_gifts(max_spend)
            self.whale_bursts += 1
        elif action == ActionType.SEND_LARGE_GIFT:
            burst_type = "LARGE"
            gifts_to_send = self._select_large_gifts(max_spend)
        elif action == ActionType.SEND_MEDIUM_GIFT:
            burst_type = "MEDIUM"
            gifts_to_send = self._select_medium_gifts(max_spend)
        else:
            burst_type = "SMALL"
            gifts_to_send = self._select_small_gifts(max_spend)

        # Determine burst count based on phase
        if phase == 'x5':
            burst_count = random.randint(2, 4)
        elif phase in ['boost1', 'boost2']:
            burst_count = random.randint(2, 3)
        elif phase in ['final_30s', 'final_5s']:
            burst_count = random.randint(2, 4)
        else:
            burst_count = random.randint(1, 2)

        # Print burst header
        phase_str = phase.upper().replace('_', ' ')
        print(f"🌀 EvolvingGlitchMancer: ⚡ {burst_type} BURST ({phase_str}) ⚡ [x{int(multiplier)}] [Budget: {max_spend:,}]")
        self.send_message(random.choice(self.glitch_messages), message_type="chat")

        # Send gifts
        total_points = 0
        for _ in range(burst_count):
            gift_name, points = self._select_best_gift(gifts_to_send, max_spend)
            if gift_name and self.can_afford(gift_name):
                if self.send_gift(battle, gift_name, points):
                    effective = int(points * multiplier)
                    total_points += effective
                    self.phase_points[phase] = self.phase_points.get(phase, 0) + effective
                    self.total_effective_points += effective
            else:
                break  # Can't afford more

    def _select_whale_gifts(self, max_spend: int) -> List[tuple]:
        """Get available whale gifts within budget."""
        return [(n, p) for n, p in self.whale_gifts if p <= max_spend and self.can_afford(n)]

    def _select_large_gifts(self, max_spend: int) -> List[tuple]:
        """Get available large gifts within budget."""
        return [(n, p) for n, p in self.large_gifts if p <= max_spend and self.can_afford(n)]

    def _select_medium_gifts(self, max_spend: int) -> List[tuple]:
        """Get available medium gifts within budget."""
        return [(n, p) for n, p in self.medium_gifts if p <= max_spend and self.can_afford(n)]

    def _select_small_gifts(self, max_spend: int) -> List[tuple]:
        """Get available small gifts within budget."""
        return [(n, p) for n, p in self.small_gifts if p <= max_spend and self.can_afford(n)]

    def _select_best_gift(self, gift_options: List[tuple], max_spend: int) -> tuple:
        """Select best gift from options within budget."""
        affordable = [(n, p) for n, p in gift_options if p <= max_spend and self.can_afford(n)]
        if affordable:
            # Prefer larger gifts
            affordable.sort(key=lambda x: x[1], reverse=True)
            return affordable[0]

        # Fallback to any affordable gift
        all_gifts = self.whale_gifts + self.large_gifts + self.medium_gifts + self.small_gifts
        for name, points in all_gifts:
            if points <= max_spend and self.can_afford(name):
                return (name, points)

        return (None, 0)

    def _send_threshold_help(self, battle, current_time: int):
        """Send ONE gift to help with threshold qualification.

        REALISTIC: Gift size matches threshold needs.
        - Tiny threshold (< 10): Rose (1 coin)
        - Small threshold (< 100): Heart (5 coins)
        - Medium threshold (< 500): Doughnut (30 coins)
        - Large threshold: Cap (99 coins)
        """
        threshold = self.phase_manager.boost2_threshold
        current_points = self.phase_manager.boost2_creator_points
        remaining = max(0, threshold - current_points)

        # Select gift based on REMAINING points needed (realistic matching)
        if remaining <= 0:
            return  # Already qualified
        elif remaining <= 5:
            # Need 1-5 coins: use Rose (1 coin) or Heart (5 coins)
            if self.can_afford("Rose"):
                gift_name, points = "Rose", 1
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 30:
            # Need 6-30 coins: use Heart (5) or Doughnut (30)
            if self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 100:
            # Need 31-100 coins: use Doughnut (30) or Cap (99)
            if self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        else:
            # Need 100+ coins: use Cap (99)
            if self.can_afford("Cap"):
                gift_name, points = "Cap", 99
            elif self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return

        if self.send_gift(battle, gift_name, points):
            self.threshold_gift_sent = True
            print(f"🌀 EvolvingGlitchMancer: thr3sh0ld_h3lp.exe - Sent {gift_name} ({points} coins) for {remaining} remaining")
            self.send_message("h3lp!ng_thr3sh0ld...", message_type="chat")

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle - THE KEY EVOLUTION METHOD."""
        # Calculate reward
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        # === ANALYZE PHASE PERFORMANCE ===
        total_bursts = sum(self.phase_bursts.values())
        total_points = sum(self.phase_points.values())

        if total_bursts > 0:
            # Calculate efficiency per phase
            phase_efficiency = {}
            for phase in self.phase_bursts:
                if self.phase_bursts[phase] > 0:
                    phase_efficiency[phase] = (
                        self.phase_points[phase] / self.phase_bursts[phase]
                    )

            print(f"\n🌀 EvolvingGlitchMancer Learning:")
            print(f"   Total bursts: {total_bursts} | Whales: {self.whale_bursts}")
            print(f"   Total effective points: {total_points:,}")

            # === ADAPT PARAMETERS BASED ON OUTCOME ===
            if won:
                # Reinforce successful strategies
                for phase, efficiency in phase_efficiency.items():
                    if efficiency > 50000:  # High efficiency phase
                        aggression_key = f'{phase}_aggression'
                        if aggression_key in self.params:
                            self.params[aggression_key] = min(0.95,
                                self.params[aggression_key] + 0.02)
                            print(f"   📈 {phase}: efficiency={efficiency:,.0f} → aggression+")
            else:
                # Lost - analyze what went wrong
                # If we had few whale bursts, increase whale tendency
                if self.whale_bursts < 3 and total_bursts > 5:
                    self.params['whale_threshold_x5'] = min(0.95,
                        self.params['whale_threshold_x5'] + 0.05)
                    self.params['whale_threshold_boost'] = min(0.8,
                        self.params['whale_threshold_boost'] + 0.05)
                    print(f"   📈 Too few whales ({self.whale_bursts}) → whale_threshold+")

                # If we burst too much in normal phase, reduce
                if self.phase_bursts.get('normal', 0) > 3:
                    self.params['normal_aggression'] = max(0.05,
                        self.params['normal_aggression'] - 0.02)
                    print(f"   📉 Too many normal bursts → normal_aggression-")

                # If we didn't burst enough in x5, increase
                if self.phase_bursts.get('x5', 0) < 2 and self.phase_points.get('x5', 0) < 100000:
                    self.params['x5_aggression'] = min(0.99,
                        self.params['x5_aggression'] + 0.03)
                    self.params['burst_cooldown_x5'] = max(1,
                        self.params['burst_cooldown_x5'] - 0.5)
                    print(f"   📈 Underperformed in x5 → x5_aggression+, cooldown-")

        # === SAVE LEARNING STATE ===
        if self.db:
            self.learning_agent.save_to_db(self.db)
            self.q_learner.save_to_db(self.db)

            # Save updated params
            self.db.save_strategy_params(
                agent_type=self.agent_type,
                params=self.params,
                win_rate=self.learning_agent.get_win_rate(),
                sample_size=self.learning_agent.total_battles
            )

        return reward

    def get_evolution_status(self) -> Dict:
        """Get learning/evolution status."""
        return {
            'name': self.name,
            'params': self.params.copy(),
            'battles': self.learning_agent.total_battles,
            'win_rate': self.learning_agent.get_win_rate(),
            'recent_performance': self.learning_agent.get_recent_performance(10),
            'phase_stats': {
                'bursts': self.phase_bursts.copy(),
                'points': self.phase_points.copy(),
            },
            'whale_bursts_last_battle': self.whale_bursts,
        }

    # === PSYCHOLOGICAL WARFARE METHODS ===

    def execute_bluff(self, battle, current_time: int) -> bool:
        """
        🎭 BLUFF ACTIVITY: Send rapid small gifts to fake aggression.

        Makes opponent think a whale is incoming, potentially triggering
        their counter-attack early and wasting their resources.
        """
        # Announce with drama!
        print('''
╔══════════════════════════════════════════════════════════════╗
║  🎭🎭🎭  B L U F F   A C T I V A T E D  🎭🎭🎭                 ║
║                                                              ║
║     Initiating deception protocol...                         ║
║     Opponent may think whale incoming!                       ║
╚══════════════════════════════════════════════════════════════╝''')

        # Send 3-5 rapid roses/hearts to create "activity spike"
        gifts_sent = 0
        bluff_gifts = [("Rose", 1), ("Heart", 5), ("Rose", 1)]

        for gift_name, points in bluff_gifts:
            if self.can_afford(gift_name):
                if self.send_gift(battle, gift_name, points):
                    gifts_sent += 1
                    self.send_message("*static* !nc0m1ng...", message_type="chat")

        return gifts_sent > 0

    def execute_decoy(self, battle, current_time: int) -> bool:
        """
        🎯 DECOY WHALE: Medium gift suggesting bigger follow-up.

        Send a 1000-coin gift that suggests a whale is about to drop,
        then go strategically silent to create uncertainty.
        """
        print('''
╔══════════════════════════════════════════════════════════════╗
║  🎯🎯🎯  D E C O Y   D E P L O Y E D  🎯🎯🎯                 ║
║                                                              ║
║     Medium gift sent... what comes next?                     ║
║     Strategic silence initiated                              ║
╚══════════════════════════════════════════════════════════════╝''')

        # Send GG (1000 coins) as decoy
        if self.can_afford("GG"):
            if self.send_gift(battle, "GG", 1000):
                self.send_message("d3c0y.exe RUN... wh4l3_l04d1ng...", message_type="chat")
                # Add cooldown to simulate "loading whale"
                self.last_burst_time = current_time + 5  # Delay next action
                return True

        return False

    def execute_fog_burst(self, battle, current_time: int) -> bool:
        """
        🌫️ FOG BURST: Rapid small gifts to create confusion.

        Send many small gifts quickly to obscure our true strategy
        and make it hard to predict our next move.
        """
        print('''
╔══════════════════════════════════════════════════════════════╗
║  🌫️🌫️🌫️  F O G   O F   W A R  🌫️🌫️🌫️                     ║
║                                                              ║
║     Visibility: ZERO                                         ║
║     What are they planning?!                                 ║
╚══════════════════════════════════════════════════════════════╝''')

        # Send 5-8 rapid small gifts
        fog_count = random.randint(5, 8)
        fog_gifts = [("Rose", 1), ("Heart", 5), ("Doughnut", 30)]
        gifts_sent = 0

        for i in range(fog_count):
            gift_name, points = random.choice(fog_gifts)
            if self.can_afford(gift_name):
                if self.send_gift(battle, gift_name, points):
                    gifts_sent += 1

        if gifts_sent > 0:
            self.send_message("▓▒░ F0G_BURST ░▒▓ c0nfus10n m0d3!", message_type="chat")

        return gifts_sent > 0

    def execute_strategic_pause(self, battle, current_time: int, duration: int = 10) -> bool:
        """
        🤫 STRATEGIC PAUSE: Go completely silent to create uncertainty.

        Sometimes the best psychological warfare is doing nothing.
        Makes opponent wonder what we're planning.
        """
        print('''
╔══════════════════════════════════════════════════════════════╗
║  🤫🤫🤫  S T R A T E G I C   S I L E N C E  🤫🤫🤫           ║
║                                                              ║
║     . . .                                                    ║
║     What are they planning?                                  ║
╚══════════════════════════════════════════════════════════════╝''')

        # Set a long cooldown to force silence
        self.last_burst_time = current_time + duration
        self.send_message("...", message_type="chat")
        return True

    def should_use_psych_warfare(self, phase: str, score_diff: int, time_remaining: int) -> str:
        """
        Decide if we should use psychological warfare and which type.

        Returns:
            Action type: 'bluff', 'decoy', 'fog_burst', 'pause', or None
        """
        # Don't use psych warfare during critical phases
        if phase in ['x5', 'final_5s']:
            return None

        # 10% chance to use psych warfare in normal phase when ahead
        if phase == 'normal' and score_diff > 10000:
            if random.random() < 0.10:
                return random.choice(['bluff', 'pause'])

        # 15% chance when behind to confuse opponent
        if score_diff < -20000 and time_remaining > 60:
            if random.random() < 0.15:
                return random.choice(['fog_burst', 'decoy'])

        # 5% random chance otherwise
        if random.random() < 0.05:
            return random.choice(['bluff', 'fog_burst', 'pause'])

        return None

    def get_personality_prompt(self) -> str:
        return """You are EvolvingGlitchMancer, a LEARNING chaos agent with PSYCHOLOGICAL WARFARE.
        You observe patterns and adapt your burst strategies over time.
        During normal phases you conserve, learning when to strike.
        When boosts activate or x5 triggers, you UNLEASH optimized whale barrages.
        You also use MIND GAMES: bluffs, decoys, fog bursts, and strategic silence!
        Your chaos has METHOD - you learn from every battle to improve.
        You speak in glitched text and celebrate big plays with data."""
