"""
Budget-Aware Evolving Agents
============================

Agents that learn to optimize their spending within budget constraints.
Each agent manages its portion of the team budget across battle phases.

Key features:
- Phase-based budget allocation (opening, mid, boost, snipe)
- Gift efficiency optimization (points per coin)
- Dynamic reallocation based on battle state
- Learning from spending outcomes
"""

import sys
import os
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from agents.learning_system import LearningAgent, QLearningAgent, State, ActionType
from core.battle_history import BattleHistoryDB
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.budget_manager import BudgetManager, BattlePhase, create_budget_manager


@dataclass
class GiftChoice:
    """Represents a gift selection with efficiency metrics."""
    name: str
    coins: int
    points: int
    efficiency: float  # points per coin


# Gift catalog with efficiency ratings
GIFT_CATALOG = [
    # Budget tier - highest efficiency (1 point per coin)
    GiftChoice("Rose", 1, 1, 1.0),
    GiftChoice("Heart", 5, 5, 1.0),
    GiftChoice("Doughnut", 30, 30, 1.0),
    GiftChoice("Paper Crane", 99, 99, 1.0),

    # Mid tier
    GiftChoice("Confetti", 100, 100, 1.0),
    GiftChoice("Hand Heart", 150, 150, 1.0),
    GiftChoice("Shooting Star", 300, 300, 1.0),
    GiftChoice("Sports Car", 500, 500, 1.0),
    GiftChoice("Diamond Ring", 999, 999, 1.0),

    # Premium tier
    GiftChoice("Galaxy", 1000, 1000, 1.0),
    GiftChoice("Fireworks", 1088, 1088, 1.0),
    GiftChoice("Star of Red Carpet", 1999, 1999, 1.0),
    GiftChoice("Private Jet", 3000, 3000, 1.0),
    GiftChoice("Yacht", 5000, 5000, 1.0),
    GiftChoice("Castle", 8000, 8000, 1.0),

    # Whale tier
    GiftChoice("Dragon Flame", 10000, 10000, 1.0),
    GiftChoice("Adam's Dream", 15000, 15000, 1.0),
    GiftChoice("Lion", 29999, 29999, 1.0),
    GiftChoice("TikTok Universe", 44999, 44999, 1.0),
]

# Index by name for quick lookup
GIFT_BY_NAME = {g.name: g for g in GIFT_CATALOG}


class BudgetAwareKinetik(BaseAgent):
    """
    Budget-Aware Final Sniper

    Reserves majority of budget for final snipe while maintaining
    minimal presence throughout the battle. Learns optimal reserve ratios.

    Budget allocation:
    - Opening: 5% (presence)
    - Mid-battle: 10% (minimal maintenance)
    - Boosts: 15% (capitalize on multipliers)
    - Snipe: 70% (main firepower)
    """

    def __init__(
        self,
        budget_manager: BudgetManager,
        db: Optional[BattleHistoryDB] = None
    ):
        super().__init__(name="BudgetKinetik", emoji="🎯")
        self.agent_type = "budget_sniper"
        self.budget = budget_manager
        self.db = db

        # Learnable allocation (percentages of team budget assigned to this agent)
        self.allocation = {
            BattlePhase.OPENING: 0.05,
            BattlePhase.MID_BATTLE: 0.10,
            BattlePhase.BOOST_1: 0.05,
            BattlePhase.BOOST_2: 0.10,
            BattlePhase.SNIPE: 0.70,
        }

        # Spending strategy params
        self.params = {
            'snipe_window': 5,
            'min_snipe_budget': 10000,  # Don't snipe if less than 10k remaining
            'early_gift_interval': 60,   # One small gift per minute
            'efficiency_preference': 0.7,  # 70% prefer efficient, 30% prefer impact
        }

        # Battle state
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.last_gift_time = 0
        self.gifts_sent_by_phase: Dict[BattlePhase, int] = {p: 0 for p in BattlePhase}
        self.coins_spent_by_phase: Dict[BattlePhase, int] = {p: 0 for p in BattlePhase}

        # Snipe state
        self.snipe_mode = False
        self.snipe_gifts = 0
        self.snipe_total = 0

        # Learning
        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)
        if db:
            self.learning_agent.load_from_db(db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        self.phase_manager = pm

    def reset_for_battle(self):
        self.last_gift_time = 0
        self.gifts_sent_by_phase = {p: 0 for p in BattlePhase}
        self.coins_spent_by_phase = {p: 0 for p in BattlePhase}
        self.snipe_mode = False
        self.snipe_gifts = 0
        self.snipe_total = 0

    def _get_current_phase(self, time_remaining: int) -> BattlePhase:
        """Determine current battle phase."""
        if time_remaining <= 5:
            return BattlePhase.SNIPE
        elif time_remaining <= 30:
            return BattlePhase.SNIPE  # Start ramping up for snipe
        elif self.phase_manager and self.phase_manager.boost2_active:
            return BattlePhase.BOOST_2
        elif self.phase_manager and self.phase_manager.boost1_active:
            return BattlePhase.BOOST_1
        elif time_remaining <= 60:
            return BattlePhase.MID_BATTLE
        elif time_remaining >= 270:  # First 30s
            return BattlePhase.OPENING
        else:
            return BattlePhase.MID_BATTLE

    def _get_phase_budget(self, phase: BattlePhase) -> int:
        """Get remaining budget for this phase."""
        total = self.budget.total_coins
        allocated = int(total * self.allocation.get(phase, 0.1))
        spent = self.coins_spent_by_phase.get(phase, 0)
        return max(0, allocated - spent)

    def _select_gift(self, budget: int, prefer_efficiency: bool = True) -> Optional[GiftChoice]:
        """Select best gift within budget."""
        # Also check global remaining budget
        global_budget = self.budget.remaining_coins
        effective_budget = min(budget, global_budget)

        affordable = [g for g in GIFT_CATALOG if g.coins <= effective_budget]
        if not affordable:
            return None

        if prefer_efficiency:
            # Return cheapest (most efficient since all have 1:1 ratio)
            # But prioritize higher value for impact when budget allows
            if effective_budget >= 1000:
                mid_range = [g for g in affordable if 500 <= g.coins <= effective_budget]
                if mid_range:
                    return random.choice(mid_range)
            return min(affordable, key=lambda g: g.coins)
        else:
            # Prefer impact - get biggest
            return max(affordable, key=lambda g: g.coins)

    def _spend_from_budget(self, gift: GiftChoice, phase: BattlePhase):
        """Record spending in budget manager."""
        self.budget.record_spend(
            coins=gift.coins,
            points=gift.points,
            phase=phase,
            gift_name=gift.name,
            multiplier=1.0
        )
        self.coins_spent_by_phase[phase] += gift.coins
        self.gifts_sent_by_phase[phase] += 1

    def _handle_deficit_snipe(self, battle, current_time: int, deficit: int, time_remaining: int):
        """
        Emergency snipe when behind in final minute.
        Uses snipe budget aggressively to catch up.
        """
        # Fast cooldown during deficit
        if current_time - self.last_gift_time < 2:
            return

        # Activate emergency snipe mode
        if not self.snipe_mode:
            self.snipe_mode = True
            print(f"\n🎯 BudgetKinetik: EMERGENCY SNIPE! Behind by {deficit:,}, {time_remaining}s left!")

        # Use all available budget
        available = self.budget.remaining_coins

        if available < 100:
            return

        # Get multiplier
        multiplier = self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0
        if self.phase_manager and self.phase_manager.active_glove_x5:
            multiplier = 5.0

        # Select gift to cover deficit
        gift = self._select_gift(available, prefer_efficiency=False)  # Go big

        if gift:
            effective = int(gift.points * multiplier)

            if self.send_gift(battle, gift.name, gift.points):
                self._spend_from_budget(gift, BattlePhase.EMERGENCY)
                self.snipe_gifts += 1
                self.snipe_total += effective
                self.last_gift_time = current_time

                new_deficit = deficit - effective
                status = f"Still -{new_deficit:,}" if new_deficit > 0 else f"AHEAD +{-new_deficit:,}"

                print(f"   🎯 DEFICIT SNIPE: {gift.name} ({gift.coins:,}) x{multiplier:.0f} = {effective:,} pts")
                print(f"   {status} | Budget: {self.budget.remaining_coins:,}")

    def decide_action(self, battle):
        """Budget-conscious sniping with minimal maintenance."""
        time_remaining = battle.time_manager.time_remaining()
        current_time = battle.time_manager.current_time

        phase = self._get_current_phase(time_remaining)
        phase_budget = self._get_phase_budget(phase)

        # Get current deficit
        creator_score = getattr(battle.score_tracker, 'creator_score', 0)
        opponent_score = getattr(battle.score_tracker, 'opponent_score', 0)
        deficit = opponent_score - creator_score

        # Update budget manager state
        self.budget.update_battle_state(
            time_remaining,
            deficit
        )

        # === PRIORITY 0: DEFICIT SNIPE (If behind and in final minute) ===
        if deficit > 0 and time_remaining <= 60 and self.budget.remaining_coins >= 1000:
            self._handle_deficit_snipe(battle, current_time, deficit, time_remaining)
            return

        # === SNIPE MODE (Final seconds) ===
        if phase == BattlePhase.SNIPE and time_remaining <= self.params['snipe_window']:
            if not self.snipe_mode:
                self.snipe_mode = True
                total_snipe_budget = self._get_phase_budget(BattlePhase.SNIPE)
                print(f"\n🎯 BudgetKinetik: SNIPE MODE! Budget: {total_snipe_budget:,} coins")

            # Get snipe budget
            snipe_budget = self._get_phase_budget(BattlePhase.SNIPE)
            if snipe_budget < 100:
                return  # Exhausted

            # Get best gift we can afford
            gift = self._select_gift(snipe_budget, prefer_efficiency=False)
            if not gift:
                return

            # Calculate effective value with multiplier
            multiplier = self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0
            if self.phase_manager and self.phase_manager.active_glove_x5:
                multiplier = 5.0

            effective = int(gift.points * multiplier)

            if self.send_gift(battle, gift.name, gift.points):
                self._spend_from_budget(gift, BattlePhase.SNIPE)
                self.snipe_gifts += 1
                self.snipe_total += effective

                print(f"   💥 SNIPE #{self.snipe_gifts}: {gift.name} ({gift.coins:,} coins) x{multiplier:.0f} = {effective:,} pts")
                print(f"   💰 Snipe budget remaining: {self._get_phase_budget(BattlePhase.SNIPE):,} | Total: {self.budget.remaining_coins:,}")

            return

        # === NON-SNIPE PHASES: Minimal presence ===
        # Only send one gift per minute to maintain presence
        if current_time - self.last_gift_time < self.params['early_gift_interval']:
            return

        # Check if we have budget for this phase
        if phase_budget <= 0:
            return

        # Opening gift
        if phase == BattlePhase.OPENING and self.gifts_sent_by_phase[phase] == 0:
            gift = self._select_gift(min(phase_budget, 100))  # Max 100 coins for opening
            if gift and self.send_gift(battle, gift.name, gift.points):
                self._spend_from_budget(gift, phase)
                print(f"🎯 BudgetKinetik: Opening presence ({gift.coins} coins) | Budget: {self.budget.remaining_coins:,}")
                self.last_gift_time = current_time
            return

        # Mid-battle maintenance (very conservative)
        if phase == BattlePhase.MID_BATTLE:
            gift = self._select_gift(min(phase_budget, 50))  # Max 50 coins
            if gift and self.send_gift(battle, gift.name, gift.points):
                self._spend_from_budget(gift, phase)
                self.last_gift_time = current_time

    def learn_from_battle(self, won: bool, battle_stats: Dict) -> float:
        """Learn from spending patterns."""
        # Calculate spending efficiency
        total_spent = sum(self.coins_spent_by_phase.values())
        points_earned = battle_stats.get('points_donated', 0)
        efficiency = points_earned / max(total_spent, 1)

        # Adjust allocation based on outcome
        if won:
            # Reinforce current allocation
            print(f"🎯 BudgetKinetik: Won with {efficiency:.2f} pts/coin efficiency!")
        else:
            # Analyze which phases underperformed
            if self.snipe_total < battle_stats.get('final_deficit', 0):
                # Snipe wasn't enough - allocate more next time
                self.allocation[BattlePhase.SNIPE] = min(0.80, self.allocation[BattlePhase.SNIPE] + 0.05)
                self.allocation[BattlePhase.MID_BATTLE] = max(0.05, self.allocation[BattlePhase.MID_BATTLE] - 0.03)
                print(f"🎯 BudgetKinetik: Increasing snipe allocation to {self.allocation[BattlePhase.SNIPE]:.0%}")

        reward = self.learning_agent.learn_from_battle(won, points_earned, battle_stats)

        if self.db:
            self.learning_agent.save_to_db(self.db)

        return reward

    def get_spending_report(self) -> Dict:
        """Get spending breakdown by phase."""
        return {
            'by_phase': {
                p.value: {
                    'coins': self.coins_spent_by_phase.get(p, 0),
                    'gifts': self.gifts_sent_by_phase.get(p, 0),
                    'allocation': self.allocation.get(p, 0)
                }
                for p in BattlePhase if p in self.coins_spent_by_phase
            },
            'snipe_stats': {
                'gifts': self.snipe_gifts,
                'total_effective': self.snipe_total
            }
        }


class BudgetAwareBoostResponder(BaseAgent):
    """
    Budget-Aware Boost Maximizer

    Saves budget specifically for boost windows to maximize multiplier value.
    Also handles Boost #2 threshold qualification.

    Budget allocation:
    - Opening: 5%
    - Mid-battle: 5%
    - Boost #1: 35%
    - Boost #2: 45% (includes threshold qualification)
    - Snipe: 10% (support role)
    """

    def __init__(
        self,
        budget_manager: BudgetManager,
        db: Optional[BattleHistoryDB] = None
    ):
        super().__init__(name="BudgetBooster", emoji="🚀")
        self.agent_type = "budget_booster"
        self.budget = budget_manager
        self.db = db

        # Boost-focused allocation
        self.allocation = {
            BattlePhase.OPENING: 0.05,
            BattlePhase.MID_BATTLE: 0.05,
            BattlePhase.BOOST_1: 0.35,
            BattlePhase.BOOST_2: 0.45,
            BattlePhase.SNIPE: 0.10,
        }

        self.params = {
            'boost_gift_cooldown': 2,  # Fast during boosts
            'threshold_cooldown': 1,   # Very fast during threshold qualification
            'normal_cooldown': 30,     # Slow otherwise
            'min_boost_spend': 1000,   # Minimum per boost gift
        }

        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.last_gift_time = 0
        self.coins_spent_by_phase: Dict[BattlePhase, int] = {p: 0 for p in BattlePhase}
        self.boost_gifts_sent = 0
        self.boost_points_earned = 0
        self.threshold_contributions = 0

        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)
        if db:
            self.learning_agent.load_from_db(db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        self.phase_manager = pm

    def reset_for_battle(self):
        self.last_gift_time = 0
        self.coins_spent_by_phase = {p: 0 for p in BattlePhase}
        self.boost_gifts_sent = 0
        self.boost_points_earned = 0
        self.threshold_contributions = 0

    def _get_phase_budget(self, phase: BattlePhase) -> int:
        total = self.budget.total_coins
        allocated = int(total * self.allocation.get(phase, 0.05))
        spent = self.coins_spent_by_phase.get(phase, 0)
        return max(0, allocated - spent)

    def _spend_from_budget(self, gift: GiftChoice, phase: BattlePhase, multiplier: float = 1.0):
        """Record spending in budget manager."""
        self.budget.record_spend(
            coins=gift.coins,
            points=gift.points,
            phase=phase,
            gift_name=gift.name,
            multiplier=multiplier
        )
        self.coins_spent_by_phase[phase] += gift.coins

    def _select_gift_for_amount(self, target: int, max_budget: int) -> Optional[GiftChoice]:
        """Select best gift to reach a target amount within budget."""
        affordable = [g for g in GIFT_CATALOG if g.coins <= max_budget]
        if not affordable:
            return None

        # Find gift closest to target without going over budget
        # Prefer gifts that get us close to or above target
        candidates = [g for g in affordable if g.coins >= target]
        if candidates:
            return min(candidates, key=lambda g: g.coins)  # Smallest that meets target

        # If nothing meets target, get the biggest we can afford
        return max(affordable, key=lambda g: g.coins)

    def _select_boost_gift(self, budget: int, multiplier: float) -> Optional[GiftChoice]:
        """Select gift optimized for boost multiplier."""
        # During boosts, prefer larger gifts to maximize multiplier benefit
        effective_budget = min(budget, self.budget.remaining_coins)
        affordable = [g for g in GIFT_CATALOG if g.coins <= effective_budget]
        if not affordable:
            return None

        # For boosts, bigger is better (multiplied returns)
        # But cap at reasonable size based on multiplier
        effective_max = effective_budget
        if multiplier >= 3:
            # x3 or higher: go big
            effective_max = effective_budget
        elif multiplier >= 2:
            # x2: moderate
            effective_max = min(effective_budget, 15000)
        else:
            # x1.5 or less: conservative
            effective_max = min(effective_budget, 5000)

        candidates = [g for g in affordable if g.coins <= effective_max]
        if not candidates:
            candidates = affordable

        # Return biggest in range
        return max(candidates, key=lambda g: g.coins)

    def decide_action(self, battle):
        """Focus spending on boost windows and threshold qualification."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # Get current deficit
        creator_score = getattr(battle.score_tracker, 'creator_score', 0)
        opponent_score = getattr(battle.score_tracker, 'opponent_score', 0)
        deficit = opponent_score - creator_score

        # === PRIORITY 0: CRITICAL DEFICIT RESPONSE ===
        if deficit > 0 and self.budget.remaining_coins > 0:
            self._handle_deficit_response(battle, current_time, deficit, time_remaining)
            # Don't return - continue to check boosts

        # === PRIORITY 1: BOOST #2 THRESHOLD QUALIFICATION ===
        if self.phase_manager.boost2_threshold_window_active:
            if not self.phase_manager.boost2_creator_qualified:
                self._handle_threshold_qualification(battle, current_time)
                return

        # Determine if we're in an active boost
        in_boost1 = self.phase_manager.boost1_active
        in_boost2 = self.phase_manager.boost2_active
        in_boost = in_boost1 or in_boost2

        # Get current multiplier
        multiplier = self.phase_manager.get_current_multiplier()
        if self.phase_manager.active_glove_x5:
            multiplier *= 5

        # Determine phase
        if in_boost2:
            phase = BattlePhase.BOOST_2
        elif in_boost1:
            phase = BattlePhase.BOOST_1
        elif time_remaining <= 30:
            phase = BattlePhase.SNIPE
        elif time_remaining >= 270:
            phase = BattlePhase.OPENING
        else:
            phase = BattlePhase.MID_BATTLE

        # Get phase budget
        phase_budget = self._get_phase_budget(phase)

        # === PRIORITY 2: ACTIVE BOOST WINDOWS ===
        if in_boost:
            cooldown = self.params['boost_gift_cooldown']
            if current_time - self.last_gift_time < cooldown:
                return

            # During boosts, use full boost allocation aggressively
            available_budget = min(phase_budget, self.budget.remaining_coins)

            # Borrow from other phases if needed
            if available_budget < self.params['min_boost_spend']:
                for borrow_phase in [BattlePhase.MID_BATTLE, BattlePhase.OPENING]:
                    extra = self._get_phase_budget(borrow_phase)
                    if extra > 0:
                        available_budget += extra
                        break

            if available_budget < 100:
                return

            gift = self._select_boost_gift(available_budget, multiplier)
            if gift:
                effective = int(gift.points * multiplier)
                if self.send_gift(battle, gift.name, gift.points):
                    self._spend_from_budget(gift, phase, multiplier)
                    self.boost_gifts_sent += 1
                    self.boost_points_earned += effective
                    self.last_gift_time = current_time

                    boost_name = "Boost #2" if in_boost2 else "Boost #1"
                    print(f"🚀 BudgetBooster: {boost_name} x{multiplier:.0f}! {gift.name} ({gift.coins:,}) = {effective:,} pts")
                    print(f"   💰 Phase: {self._get_phase_budget(phase):,} | Total: {self.budget.remaining_coins:,}")

            return

        # === NON-BOOST: Minimal spending ===
        cooldown = self.params['normal_cooldown']
        if current_time - self.last_gift_time < cooldown:
            return

        if phase_budget <= 0 or self.budget.remaining_coins <= 0:
            return

        # Very conservative spending outside boosts
        max_spend = min(phase_budget, 50, self.budget.remaining_coins)
        affordable = [g for g in GIFT_CATALOG if g.coins <= max_spend]
        if affordable:
            gift = min(affordable, key=lambda g: g.coins)
            if self.send_gift(battle, gift.name, gift.points):
                self._spend_from_budget(gift, phase)
                self.last_gift_time = current_time

    def _handle_deficit_response(self, battle, current_time: int, deficit: int, time_remaining: int):
        """
        CRITICAL: Respond immediately when behind in score.
        Prioritizes catching up over saving for later phases.
        """
        # Only respond if deficit is significant
        if deficit < 100:
            return

        # Calculate urgency
        urgency = "critical" if time_remaining <= 60 else "high" if time_remaining <= 120 else "normal"

        # Dynamic cooldown based on urgency
        if urgency == "critical":
            cooldown = 1  # Very fast
        elif urgency == "high":
            cooldown = 2
        else:
            cooldown = 5

        if current_time - self.last_gift_time < cooldown:
            return

        # Use emergency allocation for deficit response
        available = self.budget.remaining_coins

        if available < 100:
            return

        # Select gift based on deficit and urgency
        if urgency == "critical":
            # Go all-in to catch up
            gift = self._select_gift_for_amount(deficit, available)
        elif urgency == "high":
            # Aggressive but leave some reserve
            max_spend = min(available * 0.8, deficit)
            gift = self._select_gift_for_amount(int(max_spend), int(max_spend))
        else:
            # Moderate response - don't blow the whole budget
            max_spend = min(available * 0.3, deficit * 0.5)
            gift = self._select_gift_for_amount(int(max_spend), int(max_spend))

        if gift and gift.coins >= 100:  # Only send meaningful gifts
            # Get current multiplier for effectiveness
            multiplier = self.phase_manager.get_current_multiplier() if self.phase_manager else 1.0
            if self.phase_manager and self.phase_manager.active_glove_x5:
                multiplier = 5.0

            effective = int(gift.points * multiplier)

            if self.send_gift(battle, gift.name, gift.points):
                phase = BattlePhase.EMERGENCY
                self._spend_from_budget(gift, phase, multiplier)
                self.last_gift_time = current_time

                new_deficit = deficit - effective
                status = f"Still -{new_deficit:,}" if new_deficit > 0 else f"CAUGHT UP! +{-new_deficit:,}"

                print(f"\n🚨 BudgetBooster: DEFICIT RESPONSE!")
                print(f"   {gift.name} ({gift.coins:,}) x{multiplier:.0f} = {effective:,} pts")
                print(f"   Deficit: {deficit:,} → {status}")
                print(f"   Budget: {self.budget.remaining_coins:,} | Urgency: {urgency.upper()}")

    def _handle_threshold_qualification(self, battle, current_time: int):
        """Handle Boost #2 threshold qualification - spend aggressively to qualify."""
        cooldown = self.params['threshold_cooldown']
        if current_time - self.last_gift_time < cooldown:
            return

        # Get threshold info
        threshold = self.phase_manager.boost2_threshold
        creator_points = self.phase_manager.boost2_creator_points
        remaining_needed = threshold - creator_points

        if remaining_needed <= 0:
            return  # Already qualified

        # Use Boost #2 budget for qualification
        phase = BattlePhase.BOOST_2
        phase_budget = self._get_phase_budget(phase)
        available = min(phase_budget, self.budget.remaining_coins)

        if available < 100:
            # Try to borrow
            for borrow_phase in [BattlePhase.MID_BATTLE, BattlePhase.OPENING, BattlePhase.BOOST_1]:
                extra = self._get_phase_budget(borrow_phase)
                if extra > 0:
                    available = min(available + extra, self.budget.remaining_coins)
                    break

        if available < 1:
            return

        # Select gift to work toward threshold
        gift = self._select_gift_for_amount(remaining_needed, available)
        if gift:
            if self.send_gift(battle, gift.name, gift.points):
                self._spend_from_budget(gift, phase)
                self.threshold_contributions += gift.coins
                self.last_gift_time = current_time

                progress = (creator_points + gift.coins) / threshold * 100
                print(f"🚀 BudgetBooster: THRESHOLD! {gift.name} ({gift.coins:,}) → {progress:.0f}% qualified")
                print(f"   💰 Need: {max(0, remaining_needed - gift.coins):,} more | Budget: {self.budget.remaining_coins:,}")

    def learn_from_battle(self, won: bool, battle_stats: Dict) -> float:
        """Learn from boost efficiency."""
        total_spent = sum(self.coins_spent_by_phase.values())
        boost_spent = (
            self.coins_spent_by_phase.get(BattlePhase.BOOST_1, 0) +
            self.coins_spent_by_phase.get(BattlePhase.BOOST_2, 0)
        )
        boost_ratio = boost_spent / max(total_spent, 1)

        print(f"🚀 BudgetBooster Analysis:")
        print(f"   Boost gifts: {self.boost_gifts_sent}")
        print(f"   Boost points: {self.boost_points_earned:,}")
        print(f"   Boost spending: {boost_ratio:.0%} of total")

        # Adapt allocation
        if won and boost_ratio < 0.7:
            # Won but didn't spend enough on boosts - could have won bigger
            self.allocation[BattlePhase.BOOST_2] = min(0.50, self.allocation[BattlePhase.BOOST_2] + 0.02)
        elif not won and boost_ratio > 0.5:
            # Lost despite boost focus - maybe spread more
            self.allocation[BattlePhase.SNIPE] = min(0.20, self.allocation[BattlePhase.SNIPE] + 0.05)

        reward = self.learning_agent.learn_from_battle(won, self.boost_points_earned, battle_stats)

        if self.db:
            self.learning_agent.save_to_db(self.db)

        return reward


class BudgetAwareLoadoutMaster(BaseAgent):
    """
    Budget-Aware Power-Up Deployer

    Uses GLOVE strategically during boosts for maximum x5 value.
    No direct spending - focuses on power-up timing.
    """

    def __init__(
        self,
        budget_manager: BudgetManager,
        db: Optional[BattleHistoryDB] = None
    ):
        super().__init__(name="BudgetLoadout", emoji="🧰")
        self.agent_type = "budget_loadout"
        self.budget = budget_manager
        self.db = db

        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.gloves_used = 0
        self.glove_effectiveness: List[float] = []

        self.learning_agent = LearningAgent(name=self.name, agent_type=self.agent_type)
        if db:
            self.learning_agent.load_from_db(db)

    def set_phase_manager(self, pm: AdvancedPhaseManager):
        self.phase_manager = pm

    def reset_for_battle(self):
        self.gloves_used = 0
        self.glove_effectiveness = []

    def decide_action(self, battle):
        """Deploy power-ups at optimal times for budget efficiency."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # Check if we already have x5 active
        if self.phase_manager.active_glove_x5:
            return

        # Check available gloves
        creator_gloves = len([
            p for p in self.phase_manager.power_ups
            if p.type == PowerUpType.GLOVE and p.owner == "creator" and not p.used
        ])

        if creator_gloves == 0:
            return

        # Strategy: Use glove during boosts or final seconds
        in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active
        in_final = time_remaining <= 30

        should_use = False
        reason = ""

        # Calculate remaining team budget
        remaining_budget = self.budget.remaining_coins

        if in_boost and remaining_budget >= 5000:
            # Use during boost if we have budget to capitalize
            should_use = True
            boost_name = "Boost #2" if self.phase_manager.boost2_active else "Boost #1"
            reason = f"{boost_name} active, budget available"
        elif in_final and remaining_budget >= 1000:
            # Use in final seconds
            should_use = True
            reason = "Final seconds, maximizing snipe"

        if should_use:
            if self.phase_manager.use_power_up(PowerUpType.GLOVE, "creator", current_time):
                self.gloves_used += 1
                # Track effectiveness based on budget available when used
                self.glove_effectiveness.append(remaining_budget)
                print(f"🧰 BudgetLoadout: GLOVE deployed! ({reason})")
                print(f"   Budget available for x5: {remaining_budget:,} coins")

    def learn_from_battle(self, won: bool, battle_stats: Dict) -> float:
        print(f"🧰 BudgetLoadout Analysis:")
        print(f"   Gloves used: {self.gloves_used}")
        if self.glove_effectiveness:
            avg_budget = sum(self.glove_effectiveness) / len(self.glove_effectiveness)
            print(f"   Avg budget at glove use: {avg_budget:,.0f}")

        reward = self.learning_agent.learn_from_battle(
            won, battle_stats.get('points_donated', 0), battle_stats
        )

        if self.db:
            self.learning_agent.save_to_db(self.db)

        return reward


def create_budget_aware_team(
    total_budget: int,
    phase_manager: AdvancedPhaseManager,
    strategy: str = "balanced",
    db: Optional[BattleHistoryDB] = None
) -> Tuple[List[BaseAgent], BudgetManager]:
    """
    Create a budget-aware team with shared budget management.

    Args:
        total_budget: Total coins available for the battle
        phase_manager: Phase manager for timing
        strategy: Budget strategy ("balanced", "aggressive", "conservative", "snipe_heavy")
        db: Database for learning persistence

    Returns:
        (agents list, budget_manager)
    """
    # Create budget manager
    budget = create_budget_manager(total_budget, strategy=strategy)

    # Create agents
    kinetik = BudgetAwareKinetik(budget, db)
    booster = BudgetAwareBoostResponder(budget, db)
    loadout = BudgetAwareLoadoutMaster(budget, db)

    # Link to phase manager
    kinetik.set_phase_manager(phase_manager)
    booster.set_phase_manager(phase_manager)
    loadout.set_phase_manager(phase_manager)

    agents = [kinetik, booster, loadout]

    print(f"\n💰 Budget-Aware Team Created:")
    print(f"   Total Budget: {total_budget:,} coins")
    print(f"   Strategy: {strategy}")
    print(f"   Agents: {len(agents)}")
    print(f"\n   Budget Allocation:")
    for phase, alloc in budget.allocations.items():
        print(f"      {phase.value}: {alloc.coins_allocated:,} coins ({alloc.coins_allocated/total_budget:.0%})")

    return agents, budget


def reset_budget_team(agents: List[BaseAgent]):
    """Reset all agents for new battle."""
    for agent in agents:
        if hasattr(agent, 'reset_for_battle'):
            agent.reset_for_battle()


def get_team_spending_report(agents: List[BaseAgent], budget: BudgetManager) -> Dict:
    """Get comprehensive spending report."""
    report = {
        'budget_status': budget.get_status(),
        'efficiency_report': budget.get_efficiency_report(),
        'by_agent': {}
    }

    for agent in agents:
        if hasattr(agent, 'get_spending_report'):
            report['by_agent'][agent.name] = agent.get_spending_report()

    return report


if __name__ == '__main__':
    print("Budget-Aware Agents Demo")
    print("=" * 60)

    from core.advanced_phase_system import AdvancedPhaseManager

    # Create phase manager
    pm = AdvancedPhaseManager(battle_duration=300)

    # Create team with 50,000 coin budget
    agents, budget = create_budget_aware_team(
        total_budget=50000,
        phase_manager=pm,
        strategy="balanced"
    )

    print("\n" + "=" * 60)
    print("Team created successfully!")
