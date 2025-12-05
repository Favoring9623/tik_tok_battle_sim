"""
Agent BudgetOptimizer - The Efficiency Specialist

Master of cost-effective gifting. Maximizes points-per-coin ratio and
learns optimal spending patterns across different battle phases.

STRATEGY:
- Track ROI (Return on Investment) for each gift type
- Maximize spending during multiplier phases
- Use cheaper gifts during normal phases
- Learn optimal gift selection per phase
- Never overspend - always stay budget positive

MECHANICS:
- Calculates efficiency score for each gift
- Adjusts gift selection based on multiplier active
- Learns from historical efficiency data
- Coordinates with team to avoid redundant spending
"""

from agents.base_agent import BaseAgent
from agents.coordination_mixin import CoordinationMixin
from agents.learning_system import QLearningAgent, State, ActionType, LearningAgent
from core.gift_catalog import get_gift_catalog, Gift
from typing import Optional, List, Dict, Tuple
import random


class BudgetOptimizer(BaseAgent, CoordinationMixin):
    """
    Efficiency specialist that maximizes points-per-coin ratio.

    Learns optimal gift selection and timing for maximum ROI.
    """

    def __init__(self, phase_manager=None, db=None):
        super().__init__(name="BudgetOptimizer", emoji="💰")
        CoordinationMixin.__init__(self)

        self.phase_manager = phase_manager
        self.gift_catalog = get_gift_catalog()

        # Efficiency tracking
        self.gift_efficiency: Dict[str, Dict] = {}  # gift_name -> {uses, total_effective, avg_roi}
        self.phase_efficiency: Dict[str, float] = {
            "normal": 1.0,
            "boost": 2.5,
            "final_30s": 1.5,
            "x5_active": 5.0
        }

        # Learning system
        self.learning_agent = LearningAgent(
            name="BudgetOptimizer",
            agent_type="budget_optimizer"
        )
        self.q_learner = QLearningAgent(
            agent_type="budget_optimizer",
            learning_rate=0.15,
            epsilon=0.2  # Lower exploration - efficiency is key
        )

        # Load from DB if available
        if db:
            self.learning_agent.load_from_db(db)
            self.q_learner.load_from_db(db)

        # Budget management
        self.starting_budget = 200000  # Increased budget
        self.budget_spent = 0
        self.budget_reserved = 20000  # Lower reserve for more spending

        # Strategy parameters (learned) - BOOSTED for more activity
        self.spend_rate_normal = 0.25   # 25% chance per tick in normal phase
        self.spend_rate_boost = 0.55    # 55% chance during boosts
        self.spend_rate_final = 0.45    # 45% chance in final phase
        self.efficiency_threshold = 1.2  # Lower threshold to send more gifts

        # Gift tier preferences by phase (using actual catalog names) - EXPANDED
        self.gift_preferences = {
            "normal": ["Doughnut", "Heart", "Rose", "Perfume", "Butterfly"],
            "boost": ["Confetti", "Shooting Star", "Paper Crane", "Butterfly", "Galaxy"],
            "final_30s": ["Galaxy", "Sports Car", "Swan", "Fireworks", "Confetti"],
            "x5_active": ["Dragon Flame", "Castle", "Yacht", "Galaxy"]  # Go big during x5
        }

        # Efficiency messages
        self.efficiency_messages = [
            "💰 Maximum efficiency!",
            "📊 ROI optimized!",
            "💹 Smart spending!",
            "🎯 Value play!",
            "💎 Cost-effective!"
        ]

        # Session tracking
        self.gifts_sent_this_battle = 0
        self.effective_points_this_battle = 0

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities for coordination."""
        return ["BUDGET_MANAGEMENT", "EFFICIENCY_TRACKING", "ROI_OPTIMIZATION"]

    def decide_action(self, battle):
        """BudgetOptimizer decision logic - maximize efficiency."""

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        score_diff = battle.score_tracker.creator_score - battle.score_tracker.opponent_score

        # Determine current phase
        phase = self._get_current_phase(current_time, time_remaining)

        # Get current multiplier
        multiplier = self._get_current_multiplier()

        # Update emotion based on efficiency
        efficiency_ratio = self._calculate_current_efficiency()
        self.emotion_system.update_emotion({
            "winning": score_diff > 0,
            "score_difference": abs(score_diff),
            "time_remaining": time_remaining,
            "efficiency": efficiency_ratio
        })

        # Check if we should spend
        if not self._should_spend(phase, score_diff, time_remaining):
            return

        # Select optimal gift for current phase
        gift = self._select_optimal_gift(phase, multiplier)
        if not gift:
            return

        # Send the gift
        self._execute_efficient_gift(battle, gift, current_time, phase, multiplier)

    def _get_current_phase(self, current_time: int, time_remaining: int) -> str:
        """Determine current battle phase."""
        if self.phase_manager:
            if self.phase_manager.active_glove_x5:
                return "x5_active"
            if self.phase_manager.boost1_active or self.phase_manager.boost2_active:
                return "boost"
            if time_remaining <= 30:
                return "final_30s"
        elif time_remaining <= 30:
            return "final_30s"

        return "normal"

    def _get_current_multiplier(self) -> float:
        """Get current effective multiplier."""
        if self.phase_manager:
            return self.phase_manager.get_current_multiplier()
        return 1.0

    def _calculate_current_efficiency(self) -> float:
        """Calculate current efficiency ratio (effective points / spent)."""
        if self.budget_spent == 0:
            return 1.0
        return self.effective_points_this_battle / max(1, self.budget_spent)

    def _should_spend(self, phase: str, score_diff: int, time_remaining: int) -> bool:
        """Determine if we should spend this tick."""
        # Check budget availability
        available = self.starting_budget - self.budget_spent - self.budget_reserved
        if available < 10:
            return False

        # Phase-based spending rate
        rates = {
            "normal": self.spend_rate_normal,
            "boost": self.spend_rate_boost,
            "final_30s": self.spend_rate_final,
            "x5_active": 0.6  # High rate during x5
        }
        rate = rates.get(phase, 0.1)

        # Adjust based on score
        if score_diff < -10000:  # Losing badly
            rate *= 1.5
        elif score_diff > 10000:  # Winning comfortably
            rate *= 0.7

        # Release reserves in final 10 seconds
        if time_remaining <= 10:
            self.budget_reserved = 0
            rate = 0.5

        return random.random() < rate

    def _select_optimal_gift(self, phase: str, multiplier: float) -> Optional[Gift]:
        """Select the most efficient gift for current conditions."""
        preferred_gifts = self.gift_preferences.get(phase, ["Rose"])

        # Calculate expected ROI for each gift
        gift_scores: List[Tuple[Gift, float]] = []

        for gift_name in preferred_gifts:
            gift = self.gift_catalog.get_gift(gift_name)
            if gift and self.can_afford(gift_name):
                # Calculate expected effective points
                expected_points = gift.coins * multiplier

                # Get historical efficiency if available
                historical_efficiency = self._get_historical_efficiency(gift_name, phase)

                # ROI score = expected points / cost * historical factor
                roi = (expected_points / gift.cost) * historical_efficiency

                if roi >= self.efficiency_threshold or phase in ["boost", "x5_active"]:
                    gift_scores.append((gift, roi))

        if not gift_scores:
            # Fallback to Rose
            rose = self.gift_catalog.get_gift("Rose")
            if rose and self.can_afford("Rose"):
                return rose
            return None

        # Sort by ROI and pick best (with some randomness for exploration)
        gift_scores.sort(key=lambda x: x[1], reverse=True)

        if random.random() < self.q_learner.epsilon:
            # Exploration: random selection
            return random.choice(gift_scores)[0]
        else:
            # Exploitation: best ROI
            return gift_scores[0][0]

    def _get_historical_efficiency(self, gift_name: str, phase: str) -> float:
        """Get historical efficiency factor for a gift in a phase."""
        key = f"{gift_name}_{phase}"
        if key in self.gift_efficiency:
            data = self.gift_efficiency[key]
            if data['uses'] >= 3:
                return data['avg_roi']
        return 1.0  # Default

    def _execute_efficient_gift(self, battle, gift: Gift, current_time: int,
                                 phase: str, multiplier: float):
        """Execute gift and track efficiency."""

        # Calculate expected effective points
        effective_points = int(gift.coins * multiplier)

        # Send the gift
        if self.send_gift(battle, gift.name, gift.coins):
            self.gifts_sent_this_battle += 1
            self.budget_spent += gift.cost
            self.effective_points_this_battle += effective_points

            # Track efficiency
            key = f"{gift.name}_{phase}"
            if key not in self.gift_efficiency:
                self.gift_efficiency[key] = {'uses': 0, 'total_effective': 0, 'avg_roi': 1.0}

            self.gift_efficiency[key]['uses'] += 1
            self.gift_efficiency[key]['total_effective'] += effective_points

            # Update average ROI
            uses = self.gift_efficiency[key]['uses']
            total = self.gift_efficiency[key]['total_effective']
            total_cost = uses * gift.cost
            self.gift_efficiency[key]['avg_roi'] = total / max(1, total_cost)

            # Announce efficient plays
            roi = effective_points / gift.cost
            if roi >= 1.5:
                msg = random.choice(self.efficiency_messages)
                self.send_message(f"{msg} ({roi:.1f}x)", message_type="chat")
                print(f"   [{self.emoji} BudgetOptimizer: {gift.name} @ {roi:.1f}x ROI]")

    def get_efficiency_report(self) -> Dict:
        """Get efficiency report for this battle."""
        return {
            "gifts_sent": self.gifts_sent_this_battle,
            "budget_spent": self.budget_spent,
            "effective_points": self.effective_points_this_battle,
            "overall_efficiency": self._calculate_current_efficiency(),
            "top_gifts": self._get_top_efficient_gifts()
        }

    def _get_top_efficient_gifts(self) -> List[Dict]:
        """Get top 3 most efficient gifts."""
        sorted_gifts = sorted(
            self.gift_efficiency.items(),
            key=lambda x: x[1]['avg_roi'],
            reverse=True
        )[:3]

        return [
            {"gift": k, "roi": v['avg_roi'], "uses": v['uses']}
            for k, v in sorted_gifts
        ]

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.gifts_sent_this_battle = 0
        self.effective_points_this_battle = 0
        self.budget_spent = 0
        self.budget_reserved = 30000
        self.reset_pattern_tracking()

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Learn from battle outcome - adjust efficiency parameters."""
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=self.total_donated,
            battle_stats=battle_stats
        )

        # Calculate efficiency for this battle
        efficiency = self._calculate_current_efficiency()

        # Adjust spending rates based on outcome
        if won:
            if efficiency > 2.0:
                # Very efficient win - maintain conservative spending
                self.spend_rate_normal = max(0.05, self.spend_rate_normal - 0.02)
            else:
                # Won but could be more efficient
                self.efficiency_threshold = min(2.0, self.efficiency_threshold + 0.1)
        else:
            # Lost - need to be more aggressive
            self.spend_rate_boost = min(0.6, self.spend_rate_boost + 0.05)
            self.spend_rate_final = min(0.5, self.spend_rate_final + 0.05)

        return reward

    def save_learning(self, db):
        """Save learning state and efficiency data to database."""
        self.learning_agent.save_to_db(db)
        self.q_learner.save_to_db(db)
