"""
BoostResponder - The EVOLVING Strategic Boost Maximizer 🚀

Personality:
- Calm and calculating during normal phases
- EXPLOSIVE during boost phases - sends whale gifts
- Responds aggressively to opponent scoring
- Maximizes multiplier windows with big gifts
- LEARNS optimal counter-attack and boost strategies!

Strategy:
- Conserve during normal phases (minimal activity)
- GO ALL-OUT during x2/x3 boosts (Dragon Flame, Lion, Universe)
- Counter opponent spikes with whale gifts
- Coordinate with glove power-ups for maximum impact

Learning:
- Q-learning for tactical decisions (counter vs wait vs boost)
- Adaptive aggression per phase
- Learned cooldowns and thresholds
- Performance tracking across battles
"""

import random
from typing import Dict, List, Optional
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState
from agents.learning_system import (
    QLearningAgent, State, ActionType, LearningAgent
)


class BoostResponder(BaseAgent):
    """Strategic EVOLVING agent that maximizes boost phases with whale gifts."""

    def __init__(self, phase_manager=None, budget_intelligence=None, db=None):
        super().__init__(name="BoostResponder", emoji="🚀")
        self.phase_manager = phase_manager
        self.budget_intelligence = budget_intelligence
        self.db = db
        self.agent_type = "boost_responder"

        # === LEARNABLE PARAMETERS ===
        self.params = {
            # Counter-attack configuration
            'counter_threshold': 5000,       # Opponent spike to trigger counter
            'counter_aggression': 0.8,       # How aggressive when countering

            # Cooldowns (seconds between actions)
            'cooldown_normal': 8.0,          # Normal phase cooldown
            'cooldown_boost': 3.0,           # Boost phase cooldown
            'cooldown_x5': 2.0,              # x5 phase cooldown (fastest!)
            'cooldown_final': 2.5,           # Final 30s cooldown

            # Phase aggression levels (0-1)
            'normal_aggression': 0.2,        # Stay relatively quiet
            'boost_aggression': 0.85,        # Very aggressive in boosts
            'x5_aggression': 0.95,           # Maximum during x5
            'final_aggression': 0.7,         # Strong final push

            # Whale thresholds (when to send big gifts)
            'whale_threshold_x5': 0.9,       # Almost always whale in x5
            'whale_threshold_boost': 0.6,    # Often whale in boost
            'whale_threshold_counter': 0.7,  # Counter with whales

            # Deficit-based adjustments
            'deficit_whale_boost': 0.15,     # +aggression when behind
            'deficit_threshold': 20000,      # Score diff to trigger deficit mode
        }

        # === LEARNING SYSTEMS ===
        self.learning_agent = LearningAgent(
            name=self.name,
            agent_type=self.agent_type
        )
        self.q_learner = QLearningAgent(
            agent_type=self.agent_type,
            learning_rate=0.12,
            discount_factor=0.9,
            epsilon=0.2  # 20% exploration
        )

        # === BATTLE STATE ===
        self.last_action_time = -100  # Ready to act immediately
        self.gifts_in_boost = 0
        self.opponent_last_score = 0
        self.total_donated = 0
        self.boost_gifts_sent = 0
        self.last_x5_state = False  # Track when x5 activates

        # === PERFORMANCE TRACKING ===
        self.phase_gifts = {
            'normal': 0, 'boost': 0, 'x5': 0,
            'final': 0, 'counter': 0
        }
        self.phase_points = {
            'normal': 0, 'boost': 0, 'x5': 0,
            'final': 0, 'counter': 0
        }
        self.counter_attacks = 0
        self.successful_counters = 0

        # Gift options (real TikTok values) - tiered for budget awareness
        self.normal_gifts = [
            ("Doughnut", 30),
            ("Cap", 99),
            ("Rosa Nebula", 299),
        ]
        # Boost gifts: ALWAYS big during multipliers
        self.boost_gifts = [
            ("Dragon Flame", 10000),   # 10k coins
            ("Lion", 29999),           # 30k coins
            ("TikTok Universe", 44999), # 45k coins
        ]
        self.counter_gifts = [
            ("Dragon Flame", 10000),
            ("Lion", 29999),
            ("TikTok Universe", 44999),
        ]

        # SUSPENSE: Wait before qualifying for Boost #2
        # BoostResponder waits 16-21s (1s after PixelPixie starts)
        self.qualification_delay = random.randint(16, 21)

        # Load learned state
        self._load_learned_params()
        self._load_learning_state()

    def _load_learned_params(self):
        """Load parameters from database if available."""
        if self.db:
            latest = self.db.get_latest_strategy_params(self.agent_type)
            if latest:
                self.params.update(latest['params'])
                print(f"🚀 BoostResponder: Loaded params v{latest['meta']['version']} "
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
        self.last_action_time = -100  # Ready to act immediately
        self.gifts_in_boost = 0
        self.opponent_last_score = 0
        self.total_donated = 0
        self.boost_gifts_sent = 0
        self.last_x5_state = False  # Track x5 state changes
        self.threshold_gift_sent = False  # One gift for threshold qualification
        # Randomize qualification delay (1s after PixelPixie)
        self.qualification_delay = random.randint(16, 21)

        # Reset performance tracking
        self.phase_gifts = {
            'normal': 0, 'boost': 0, 'x5': 0,
            'final': 0, 'counter': 0
        }
        self.phase_points = {
            'normal': 0, 'boost': 0, 'x5': 0,
            'final': 0, 'counter': 0
        }
        self.counter_attacks = 0
        self.successful_counters = 0

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
        if self.phase_manager.boost2_active or self.phase_manager.boost1_active:
            return "boost"

        # Check final phases
        if time_remaining <= 30:
            return "final"

        return "normal"

    def _build_state(self, battle, phase: str, time_remaining: int) -> State:
        """Build state for Q-learning."""
        multiplier = self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score

        return State(
            time_remaining=time_remaining,
            score_diff=creator_score - opponent_score,
            multiplier=multiplier,
            in_boost=phase == 'boost',
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
        """Strategic decision based on phase and opponent activity."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        opponent_score = battle.score_tracker.opponent_score
        creator_score = battle.score_tracker.creator_score

        # Check current phase status
        in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active
        multiplier = self.phase_manager.get_current_multiplier()
        time_remaining = battle.time_manager.time_remaining()
        in_final_30s = self.phase_manager.is_in_final_30s(current_time)
        deficit = opponent_score - creator_score

        # Check if OUR glove x5 is active - THIS IS CRITICAL!
        our_x5_active = (self.phase_manager.active_glove_x5 and
                         self.phase_manager.active_glove_owner == "creator")

        # Detect when x5 JUST activated - reset cooldown for immediate response!
        if our_x5_active and not self.last_x5_state:
            self.last_action_time = -100  # Force immediate action!
            print(f"🚀 BoostResponder: X5 DETECTED! Resetting cooldown for immediate whale attack!")
        self.last_x5_state = our_x5_active

        # Detect opponent spike
        opponent_spike = opponent_score - self.opponent_last_score
        self.opponent_last_score = opponent_score

        # === THRESHOLD WINDOW - Help PixelPixie with ONE gift ===
        # SUSPENSE: Wait 16-21 seconds into window before qualifying!
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

        # Choose cooldown based on phase (x5 is even faster!)
        if our_x5_active:
            cooldown = 2  # Super short - maximize the x5 window!
        elif in_boost:
            cooldown = self.boost_cooldown
        else:
            cooldown = self.normal_cooldown

        # Cooldown check
        if current_time - self.last_action_time < cooldown:
            return

        # === USE BUDGET INTELLIGENCE FOR SPENDING DECISIONS ===
        phase = "boost" if in_boost else ("final_30s" if in_final_30s else "normal")

        # Get spending recommendation from budget intelligence
        if self.budget_intelligence:
            recommendation = self.budget_intelligence.should_spend_in_phase(
                phase, time_remaining, creator_score, opponent_score, multiplier
            )

            # If budget intelligence says don't spend, obey (unless x5 is active)
            if not recommendation["should_spend"] and not our_x5_active:
                return

            max_spend = recommendation["max_spend"]
            gift_tier = recommendation["gift_tier"]
        else:
            # Fallback if no budget intelligence
            max_spend = 999999
            gift_tier = "whale"

        # GLOVE x5 MODE: Our x5 is active - GO ALL OUT with whale gifts!
        # This is the HIGHEST priority - maximize the x5 window!
        if our_x5_active:
            self._x5_attack_smart(battle, multiplier, deficit, current_time, max_spend)
            self.last_action_time = current_time
            return

        # Also trigger x5 attack during boost if x5 is active (belt and suspenders)
        if in_boost and self.phase_manager.active_glove_x5:
            if self.phase_manager.active_glove_owner == "creator":
                self._x5_attack_smart(battle, multiplier, deficit, current_time, max_spend)
                self.last_action_time = current_time
                return

        # COUNTER MODE: Only counter during strategic phases (boost, x5, or final 30s)
        if opponent_spike >= self.counter_threshold:
            if in_boost or in_final_30s:
                self._counter_attack_smart(battle, opponent_spike, deficit, multiplier, current_time, max_spend)
                self.last_action_time = current_time
                return

        # BOOST MODE: Go ALL-OUT during boosts with whale gifts!
        if in_boost:
            self._boost_attack_smart(battle, multiplier, deficit, current_time, max_spend, gift_tier)
            self.last_action_time = current_time
            self.gifts_in_boost += 1
            return

        # FINAL 30s MODE: Controlled push (respect budget intelligence)
        if in_final_30s:
            if random.random() < 0.6:
                self._final_push_smart(battle, deficit, current_time, max_spend, gift_tier)
                self.last_action_time = current_time
            return

        # NORMAL MODE: Budget intelligence already blocked us if we shouldn't spend

    def _counter_attack(self, battle, spike_size: int, deficit: int, multiplier: float, current_time: int):
        """Counter opponent spike with whale gift (budget-aware)."""
        self.emotion_system.force_emotion(EmotionalState.AGGRESSIVE, current_time)

        # Choose gift based on spike size AND affordability
        gift_options = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
            ("GG", 1000),
            ("Rosa Nebula", 299),
        ]

        # Find best affordable gift for the situation
        gift_name, points = None, 0
        for name, pts in gift_options:
            if self.can_afford(name):
                gift_name, points = name, pts
                # Prefer bigger if spike/deficit is big enough
                if spike_size >= 10000 or deficit >= 30000:
                    break  # Take first (biggest) affordable
                elif spike_size >= 5000 or deficit >= 15000:
                    if pts <= 29999:
                        break
                else:
                    if pts <= 10000:
                        break

        if not gift_name:
            return  # Can't afford anything

        effective = int(points * multiplier)
        print(f"\n🚀💥 BoostResponder COUNTER-ATTACK!")
        print(f"   Opponent spike: +{spike_size:,} | Deficit: {deficit:,}")
        print(f"   Deploying {gift_name}: {points:,} × {int(multiplier)} = {effective:,}")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points

    def _boost_attack(self, battle, multiplier: float, deficit: int, current_time: int):
        """AGGRESSIVE whale gift sending during boost phase (budget-aware)."""
        self.emotion_system.force_emotion(EmotionalState.FOCUSED, current_time)

        # During boosts: send biggest affordable whale gift
        gift_options = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
            ("GG", 1000),
        ]

        # Find best affordable gift
        gift_name, points = None, 0
        for name, pts in gift_options:
            if self.can_afford(name):
                gift_name, points = name, pts
                break  # Take biggest affordable

        if not gift_name:
            # Fallback to small gift
            gift_name, points = "Rosa Nebula", 299
            if not self.can_afford(gift_name):
                return

        effective = int(points * multiplier)
        print(f"\n🚀🔥 BoostResponder BOOST ATTACK #{self.boost_gifts_sent + 1}! (x{int(multiplier)})")
        print(f"   {gift_name}: {points:,} × {int(multiplier)} = {effective:,} effective!")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points
            self.boost_gifts_sent += 1

    def _x5_attack(self, battle, multiplier: float, deficit: int, current_time: int):
        """MAXIMUM whale gift sending when OUR x5 is active (budget-aware)."""
        self.emotion_system.force_emotion(EmotionalState.AGGRESSIVE, current_time)

        # During OUR x5: send biggest affordable gift!
        gift_options = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
            ("GG", 1000),
        ]

        gift_name, points = None, 0
        for name, pts in gift_options:
            if self.can_afford(name):
                gift_name, points = name, pts
                break

        if not gift_name:
            return

        effective = int(points * multiplier)
        print(f"\n🚀💥 BoostResponder X5 MAXIMIZER! (x{int(multiplier)})")
        print(f"   OUR GLOVE IS ACTIVE - SENDING WHALE GIFTS!")
        print(f"   {gift_name}: {points:,} × {int(multiplier)} = {effective:,} effective!")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points

    def _final_push(self, battle, deficit: int, current_time: int):
        """Final 30 seconds push with big gifts (budget-aware)."""
        self.emotion_system.force_emotion(EmotionalState.AGGRESSIVE, current_time)

        # Final 30s: use best affordable gift
        gift_options = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
            ("GG", 1000),
            ("Rosa Nebula", 299),
        ]

        gift_name, points = None, 0
        for name, pts in gift_options:
            if self.can_afford(name):
                gift_name, points = name, pts
                break

        if not gift_name:
            return

        multiplier = self.phase_manager.get_current_multiplier()
        effective = int(points * multiplier)

        print(f"\n🚀⚡ BoostResponder FINAL PUSH!")
        print(f"   Deficit: {deficit:,} | {gift_name}: {points:,} × {int(multiplier)} = {effective:,}")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points

    # === SMART ATTACK METHODS (Budget Intelligence Aware) ===

    def _select_gift_within_budget(self, max_spend: int, gift_tier: str = "whale") -> tuple:
        """Select best gift within budget limit and tier."""
        # Define gift tiers
        whale_gifts = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
        ]
        medium_gifts = [
            ("GG", 1000),
            ("Rosa Nebula", 299),
            ("Cap", 99),
        ]
        small_gifts = [
            ("Doughnut", 30),
            ("Heart", 5),
        ]

        # Build options based on tier
        if gift_tier == "whale":
            options = whale_gifts + medium_gifts + small_gifts
        elif gift_tier == "medium":
            options = medium_gifts + small_gifts
        else:
            options = small_gifts

        # Find best affordable gift within max_spend
        for name, points in options:
            if points <= max_spend and self.can_afford(name):
                return name, points

        return None, 0

    def _x5_attack_smart(self, battle, multiplier: float, deficit: int, current_time: int, max_spend: int):
        """MAXIMUM whale gift when OUR x5 is active (budget intelligence aware)."""
        self.emotion_system.force_emotion(EmotionalState.AGGRESSIVE, current_time)

        # During x5: send biggest affordable within budget limit
        gift_name, points = self._select_gift_within_budget(max_spend, "whale")

        if not gift_name:
            return

        effective = int(points * multiplier)
        print(f"\n🚀💥 BoostResponder X5 MAXIMIZER! (x{int(multiplier)})")
        print(f"   OUR GLOVE IS ACTIVE - Budget allows: {max_spend:,}")
        print(f"   {gift_name}: {points:,} × {int(multiplier)} = {effective:,} effective!")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points
            # Track for learning
            self.phase_gifts['x5'] = self.phase_gifts.get('x5', 0) + 1
            self.phase_points['x5'] = self.phase_points.get('x5', 0) + effective

    def _boost_attack_smart(self, battle, multiplier: float, deficit: int, current_time: int, max_spend: int, gift_tier: str):
        """AGGRESSIVE whale gift during boost phase (budget intelligence aware)."""
        self.emotion_system.force_emotion(EmotionalState.FOCUSED, current_time)

        # Select gift based on budget intelligence recommendation
        gift_name, points = self._select_gift_within_budget(max_spend, gift_tier)

        if not gift_name:
            return

        effective = int(points * multiplier)
        print(f"\n🚀🔥 BoostResponder BOOST ATTACK #{self.boost_gifts_sent + 1}! (x{int(multiplier)})")
        print(f"   Budget tier: {gift_tier} | Max spend: {max_spend:,}")
        print(f"   {gift_name}: {points:,} × {int(multiplier)} = {effective:,} effective!")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points
            self.boost_gifts_sent += 1
            # Track for learning
            self.phase_gifts['boost'] = self.phase_gifts.get('boost', 0) + 1
            self.phase_points['boost'] = self.phase_points.get('boost', 0) + effective

    def _counter_attack_smart(self, battle, spike_size: int, deficit: int, multiplier: float, current_time: int, max_spend: int):
        """Counter opponent spike (budget intelligence aware)."""
        self.emotion_system.force_emotion(EmotionalState.AGGRESSIVE, current_time)

        # Counter with appropriate size based on spike and budget
        # Bigger spikes warrant bigger counters, but respect max_spend
        if spike_size >= 20000:
            tier = "whale"
        elif spike_size >= 5000:
            tier = "medium"
        else:
            tier = "small"

        gift_name, points = self._select_gift_within_budget(max_spend, tier)

        if not gift_name:
            return

        effective = int(points * multiplier)
        print(f"\n🚀💥 BoostResponder COUNTER-ATTACK!")
        print(f"   Opponent spike: +{spike_size:,} | Deficit: {deficit:,}")
        print(f"   Budget limit: {max_spend:,}")
        print(f"   Deploying {gift_name}: {points:,} × {int(multiplier)} = {effective:,}")

        # Track counter-attack
        self.counter_attacks += 1
        score_before = battle.score_tracker.creator_score

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points
            # Track for learning
            self.phase_gifts['counter'] = self.phase_gifts.get('counter', 0) + 1
            self.phase_points['counter'] = self.phase_points.get('counter', 0) + effective
            # Check if counter was "successful" (we responded well to spike)
            if effective >= spike_size * 0.5:
                self.successful_counters += 1

    def _final_push_smart(self, battle, deficit: int, current_time: int, max_spend: int, gift_tier: str):
        """Final 30 seconds push (budget intelligence aware)."""
        self.emotion_system.force_emotion(EmotionalState.AGGRESSIVE, current_time)

        # Final push respects budget intelligence
        gift_name, points = self._select_gift_within_budget(max_spend, gift_tier)

        if not gift_name:
            return

        multiplier = self.phase_manager.get_current_multiplier()
        effective = int(points * multiplier)

        print(f"\n🚀⚡ BoostResponder FINAL PUSH!")
        print(f"   Deficit: {deficit:,} | Budget tier: {gift_tier}")
        print(f"   {gift_name}: {points:,} × {int(multiplier)} = {effective:,}")

        if self.send_gift(battle, gift_name, points):
            self.total_donated += points
            # Track for learning
            self.phase_gifts['final'] = self.phase_gifts.get('final', 0) + 1
            self.phase_points['final'] = self.phase_points.get('final', 0) + effective

    def _send_threshold_help(self, battle, current_time: int):
        """Send ONE gift to help PixelPixie with threshold qualification.

        REALISTIC: Gift size matches threshold needs.
        - Tiny threshold (< 10): Heart (5 coins)
        - Small threshold (< 100): Doughnut (30 coins)
        - Medium threshold (< 500): Cap (99 coins)
        - Large threshold: Rosa Nebula (299 coins)
        """
        threshold = self.phase_manager.boost2_threshold
        current_points = self.phase_manager.boost2_creator_points
        remaining = max(0, threshold - current_points)

        # Select gift based on REMAINING points needed (realistic matching)
        if remaining <= 0:
            return  # Already qualified
        elif remaining <= 10:
            # Tiny threshold: Heart (5) is enough
            if self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 50:
            # Small threshold: Doughnut or Heart
            if self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 150:
            # Medium threshold: Cap or Doughnut
            if self.can_afford("Cap"):
                gift_name, points = "Cap", 99
            elif self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        else:
            # Large threshold (150+): Rosa Nebula or Cap
            if self.can_afford("Rosa Nebula"):
                gift_name, points = "Rosa Nebula", 299
            elif self.can_afford("Cap"):
                gift_name, points = "Cap", 99
            elif self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return

        if self.send_gift(battle, gift_name, points):
            self.threshold_gift_sent = True
            self.total_donated += points
            print(f"🚀 BoostResponder: Helping with threshold! Sent {gift_name} ({points} coins) for {remaining} remaining")

    def _normal_send(self, battle):
        """Send during normal phase - medium gifts to build momentum (budget-aware)."""
        # Try medium gifts first, fall back to small
        gift_options = [
            ("Rosa Nebula", 299),
            ("Cap", 99),
            ("Doughnut", 30),
        ]

        for name, points in gift_options:
            if self.can_afford(name):
                if self.send_gift(battle, name, points):
                    self.total_donated += points
                return

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle - THE KEY EVOLUTION METHOD."""
        # Calculate reward
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        # === ANALYZE PHASE PERFORMANCE ===
        total_gifts = sum(self.phase_gifts.values())
        total_points = sum(self.phase_points.values())

        if total_gifts > 0:
            # Calculate efficiency per phase
            phase_efficiency = {}
            for phase in self.phase_gifts:
                if self.phase_gifts[phase] > 0:
                    phase_efficiency[phase] = (
                        self.phase_points[phase] / self.phase_gifts[phase]
                    )

            print(f"\n🚀 BoostResponder Learning:")
            print(f"   Total gifts: {total_gifts} | Counter-attacks: {self.counter_attacks}")
            print(f"   Total effective points: {total_points:,}")

            # === ADAPT PARAMETERS BASED ON OUTCOME ===
            if won:
                # Reinforce successful strategies
                for phase, efficiency in phase_efficiency.items():
                    if efficiency > 30000:  # High efficiency phase
                        aggression_key = f'{phase}_aggression'
                        if aggression_key in self.params:
                            self.params[aggression_key] = min(0.95,
                                self.params[aggression_key] + 0.02)
                            print(f"   📈 {phase}: efficiency={efficiency:,.0f} → aggression+")

                # Successful counter-attacks - reinforce threshold
                if self.counter_attacks > 0 and self.successful_counters > 0:
                    success_rate = self.successful_counters / self.counter_attacks
                    if success_rate > 0.6:
                        print(f"   📈 Counter success rate: {success_rate*100:.0f}% → threshold stable")
            else:
                # Lost - analyze what went wrong

                # If we countered too much without success, raise threshold
                if self.counter_attacks > 3 and self.successful_counters < self.counter_attacks * 0.3:
                    self.params['counter_threshold'] = min(15000,
                        self.params['counter_threshold'] + 1000)
                    print(f"   📉 Counter-attacks ineffective → threshold+")

                # If we didn't act enough in x5, increase aggression
                if self.phase_gifts.get('x5', 0) < 2:
                    self.params['x5_aggression'] = min(0.99,
                        self.params['x5_aggression'] + 0.03)
                    self.params['cooldown_x5'] = max(1.5,
                        self.params['cooldown_x5'] - 0.2)
                    print(f"   📈 Underperformed in x5 → aggression+, cooldown-")

                # If we spent too much in normal phase, reduce
                if self.phase_gifts.get('normal', 0) > 5:
                    self.params['normal_aggression'] = max(0.1,
                        self.params['normal_aggression'] - 0.03)
                    print(f"   📉 Too many normal gifts → normal_aggression-")

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
                'gifts': self.phase_gifts.copy(),
                'points': self.phase_points.copy(),
            },
            'counter_attacks_last_battle': self.counter_attacks,
        }

    def get_personality_prompt(self) -> str:
        return """You are BoostResponder, an EVOLVING strategic commander who LEARNS and ADAPTS.
        You MAXIMIZE every boost opportunity with devastating whale gifts.
        During normal phases you conserve resources, learning when to strike.
        When boosts activate, you UNLEASH Dragon Flame, Lion, Universe!
        You track opponent patterns and counter aggressively when needed.
        You speak in tactical terms: "Boost detected. Deploying Universe.", "Counter-strike: Lion deployed."
        Your strategies EVOLVE - you get smarter with every battle."""
