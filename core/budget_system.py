"""
Budget System for TikTok Battles

Each participant starts with a random coin budget.
Gifts cost coins - agents must learn to budget strategically.

Budget ranges:
- Low: 50,000 - 150,000 (conservative play required)
- Medium: 150,000 - 350,000 (balanced options)
- High: 350,000 - 600,000 (aggressive play possible)

Strategic implications:
- Can't send gifts you can't afford
- Save budget for boost windows (higher multipliers = better ROI)
- Whale gifts are high-risk/high-reward
- Budget exhaustion = game over for that team
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class BudgetTier(Enum):
    """Budget tier classification."""
    CRITICAL = "critical"      # < 10% remaining
    LOW = "low"                # 10-25% remaining
    MEDIUM = "medium"          # 25-50% remaining
    HEALTHY = "healthy"        # 50-75% remaining
    ABUNDANT = "abundant"      # > 75% remaining


@dataclass
class GiftCost:
    """Gift with its cost and point value."""
    name: str
    cost: int           # Cost in coins to send
    points: int         # Points awarded to recipient
    emoji: str = "🎁"
    tier: str = "small"  # small, medium, large, whale


# Real TikTok gift costs and values
GIFT_CATALOG = {
    # Small gifts (1-100 coins)
    "Rose": GiftCost("Rose", 1, 1, "🌹", "small"),
    "Heart": GiftCost("Heart", 5, 5, "❤️", "small"),
    "Doughnut": GiftCost("Doughnut", 30, 30, "🍩", "small"),
    "Cap": GiftCost("Cap", 99, 99, "🧢", "small"),

    # Medium gifts (100-1000 coins)
    "Rosa Nebula": GiftCost("Rosa Nebula", 299, 299, "🌸", "medium"),
    "Perfume": GiftCost("Perfume", 500, 500, "💐", "medium"),
    "Hand Heart": GiftCost("Hand Heart", 799, 799, "🫶", "medium"),

    # Large gifts (1000-10000 coins)
    "GG": GiftCost("GG", 1000, 1000, "🎮", "large"),
    "Corgi": GiftCost("Corgi", 2999, 2999, "🐕", "large"),
    "Money Gun": GiftCost("Money Gun", 5000, 5000, "💵", "large"),

    # Whale gifts (10000+ coins)
    "Dragon Flame": GiftCost("Dragon Flame", 10000, 10000, "🐉", "whale"),
    "Lion": GiftCost("Lion", 29999, 29999, "🦁", "whale"),
    "TikTok Universe": GiftCost("TikTok Universe", 44999, 44999, "🌌", "whale"),

    # Power-up costs (separate from gifts)
    "GLOVE": GiftCost("GLOVE", 100, 100, "🥊", "powerup"),
}


def get_gift_cost(gift_name: str) -> int:
    """Get the cost of a gift by name."""
    # Handle case-insensitive lookup
    for name, gift in GIFT_CATALOG.items():
        if name.lower() == gift_name.lower():
            return gift.cost
    # Default cost for unknown gifts
    return 100


def get_gift_info(gift_name: str) -> Optional[GiftCost]:
    """Get full gift info by name."""
    for name, gift in GIFT_CATALOG.items():
        if name.lower() == gift_name.lower():
            return gift
    return None


class BudgetManager:
    """
    Manages budgets for both teams in a battle.

    Features:
    - Random starting budgets
    - Spending tracking
    - Budget tiers for strategy decisions
    - Spending analytics
    """

    def __init__(
        self,
        creator_budget: Optional[int] = None,
        opponent_budget: Optional[int] = None,
        budget_range: Tuple[int, int] = (50000, 500000)
    ):
        """
        Initialize budgets for both teams.

        Args:
            creator_budget: Fixed budget for creator (or None for random)
            opponent_budget: Fixed budget for opponent (or None for random)
            budget_range: (min, max) range for random budgets
        """
        self.budget_range = budget_range

        # Starting budgets
        self.creator_starting = creator_budget or self._generate_random_budget()
        self.opponent_starting = opponent_budget or self._generate_random_budget()

        # Current budgets
        self.creator_budget = self.creator_starting
        self.opponent_budget = self.opponent_starting

        # Spending tracking
        self.creator_spent = 0
        self.opponent_spent = 0

        # Detailed spending history
        self.creator_spending_history: List[Dict] = []
        self.opponent_spending_history: List[Dict] = []

        # Spending by category
        self.creator_spending_by_tier = {"small": 0, "medium": 0, "large": 0, "whale": 0, "powerup": 0}
        self.opponent_spending_by_tier = {"small": 0, "medium": 0, "large": 0, "whale": 0, "powerup": 0}

        # Spending by phase
        self.creator_spending_by_phase = {"normal": 0, "boost": 0, "final_30s": 0}
        self.opponent_spending_by_phase = {"normal": 0, "boost": 0, "final_30s": 0}

        print(f"\n💰 Budget System Initialized:")
        print(f"   👤 Creator: {self.creator_starting:,} coins ({self._get_budget_description(self.creator_starting)})")
        print(f"   👻 Opponent: {self.opponent_starting:,} coins ({self._get_budget_description(self.opponent_starting)})")

    def _generate_random_budget(self) -> int:
        """Generate a random budget with weighted distribution."""
        roll = random.random()

        if roll < 0.20:  # 20% - Low budget
            return random.randint(50000, 150000)
        elif roll < 0.55:  # 35% - Medium budget
            return random.randint(150000, 350000)
        elif roll < 0.85:  # 30% - High budget
            return random.randint(350000, 500000)
        else:  # 15% - Very high budget
            return random.randint(500000, 750000)

    def _get_budget_description(self, budget: int) -> str:
        """Get human-readable budget description."""
        if budget < 100000:
            return "💸 LOW - Conservative play required"
        elif budget < 200000:
            return "📊 MEDIUM-LOW - Budget carefully"
        elif budget < 350000:
            return "📈 MEDIUM - Balanced options"
        elif budget < 500000:
            return "💎 HIGH - Aggressive play possible"
        else:
            return "🐋 WHALE BUDGET - Go all out!"

    def can_afford(self, team: str, gift_name: str) -> bool:
        """Check if team can afford a gift."""
        cost = get_gift_cost(gift_name)
        budget = self.creator_budget if team == "creator" else self.opponent_budget
        return budget >= cost

    def get_affordable_gifts(self, team: str) -> List[GiftCost]:
        """Get list of gifts the team can afford."""
        budget = self.creator_budget if team == "creator" else self.opponent_budget
        return [gift for gift in GIFT_CATALOG.values() if gift.cost <= budget]

    def get_best_affordable_gift(self, team: str, max_spend_ratio: float = 0.5) -> Optional[GiftCost]:
        """Get the best gift within budget constraints.

        Args:
            team: "creator" or "opponent"
            max_spend_ratio: Maximum portion of remaining budget to spend (0-1)
        """
        budget = self.creator_budget if team == "creator" else self.opponent_budget
        max_spend = int(budget * max_spend_ratio)

        affordable = [g for g in GIFT_CATALOG.values() if g.cost <= max_spend]
        if not affordable:
            return None

        # Return highest value affordable gift
        return max(affordable, key=lambda g: g.points)

    def spend(
        self,
        team: str,
        gift_name: str,
        current_time: int,
        phase: str = "normal"
    ) -> Tuple[bool, int]:
        """
        Attempt to spend budget on a gift.

        Returns:
            (success, cost) tuple
        """
        cost = get_gift_cost(gift_name)
        gift_info = get_gift_info(gift_name)
        tier = gift_info.tier if gift_info else "small"

        if team == "creator":
            if self.creator_budget < cost:
                return False, 0

            self.creator_budget -= cost
            self.creator_spent += cost
            self.creator_spending_by_tier[tier] = self.creator_spending_by_tier.get(tier, 0) + cost
            self.creator_spending_by_phase[phase] = self.creator_spending_by_phase.get(phase, 0) + cost
            self.creator_spending_history.append({
                "time": current_time,
                "gift": gift_name,
                "cost": cost,
                "phase": phase,
                "remaining": self.creator_budget
            })
        else:
            if self.opponent_budget < cost:
                return False, 0

            self.opponent_budget -= cost
            self.opponent_spent += cost
            self.opponent_spending_by_tier[tier] = self.opponent_spending_by_tier.get(tier, 0) + cost
            self.opponent_spending_by_phase[phase] = self.opponent_spending_by_phase.get(phase, 0) + cost
            self.opponent_spending_history.append({
                "time": current_time,
                "gift": gift_name,
                "cost": cost,
                "phase": phase,
                "remaining": self.opponent_budget
            })

        return True, cost

    def get_budget_tier(self, team: str) -> BudgetTier:
        """Get current budget tier for strategic decisions."""
        if team == "creator":
            ratio = self.creator_budget / max(self.creator_starting, 1)
        else:
            ratio = self.opponent_budget / max(self.opponent_starting, 1)

        if ratio < 0.10:
            return BudgetTier.CRITICAL
        elif ratio < 0.25:
            return BudgetTier.LOW
        elif ratio < 0.50:
            return BudgetTier.MEDIUM
        elif ratio < 0.75:
            return BudgetTier.HEALTHY
        else:
            return BudgetTier.ABUNDANT

    def get_remaining_ratio(self, team: str) -> float:
        """Get ratio of remaining budget (0-1)."""
        if team == "creator":
            return self.creator_budget / max(self.creator_starting, 1)
        else:
            return self.opponent_budget / max(self.opponent_starting, 1)

    def get_status(self, team: str) -> Dict:
        """Get detailed budget status for a team."""
        if team == "creator":
            ratio = self.get_remaining_ratio("creator")
            return {
                "starting": self.creator_starting,
                "current": self.creator_budget,
                "spent": self.creator_spent,
                "remaining_ratio": ratio,
                "percentage": ratio * 100,  # For UI display
                "tier": self.get_budget_tier("creator").value.upper(),
                "spending_by_tier": self.creator_spending_by_tier.copy(),
                "spending_by_phase": self.creator_spending_by_phase.copy()
            }
        else:
            ratio = self.get_remaining_ratio("opponent")
            return {
                "starting": self.opponent_starting,
                "current": self.opponent_budget,
                "spent": self.opponent_spent,
                "remaining_ratio": ratio,
                "percentage": ratio * 100,  # For UI display
                "tier": self.get_budget_tier("opponent").value.upper(),
                "spending_by_tier": self.opponent_spending_by_tier.copy(),
                "spending_by_phase": self.opponent_spending_by_phase.copy()
            }

    def get_analytics(self) -> Dict:
        """Get full budget analytics for battle end."""
        return {
            "creator": {
                "starting": self.creator_starting,
                "ending": self.creator_budget,
                "spent": self.creator_spent,
                "total_spent": self.creator_spent,  # Alias for compatibility
                "efficiency": self.creator_spent / max(self.creator_starting, 1),
                "spending_by_tier": self.creator_spending_by_tier,
                "spending_by_phase": self.creator_spending_by_phase,
                "whale_ratio": self.creator_spending_by_tier.get("whale", 0) / max(self.creator_spent, 1)
            },
            "opponent": {
                "starting": self.opponent_starting,
                "ending": self.opponent_budget,
                "spent": self.opponent_spent,
                "total_spent": self.opponent_spent,  # Alias for compatibility
                "efficiency": self.opponent_spent / max(self.opponent_starting, 1),
                "spending_by_tier": self.opponent_spending_by_tier,
                "spending_by_phase": self.opponent_spending_by_phase,
                "whale_ratio": self.opponent_spending_by_tier.get("whale", 0) / max(self.opponent_spent, 1)
            }
        }

    def print_status(self):
        """Print current budget status."""
        creator_pct = self.get_remaining_ratio("creator") * 100
        opponent_pct = self.get_remaining_ratio("opponent") * 100

        print(f"\n💰 Budget Status:")
        print(f"   👤 Creator: {self.creator_budget:,}/{self.creator_starting:,} ({creator_pct:.1f}%) [{self.get_budget_tier('creator').value}]")
        print(f"   👻 Opponent: {self.opponent_budget:,}/{self.opponent_starting:,} ({opponent_pct:.1f}%) [{self.get_budget_tier('opponent').value}]")


class BudgetStrategy:
    """
    Strategic budget allocation recommendations.

    Helps agents decide how much to spend in different phases.
    """

    @staticmethod
    def get_recommended_allocation(
        budget_tier: BudgetTier,
        phase: str,
        time_remaining: int,
        score_deficit: int
    ) -> Dict:
        """
        Get recommended spending strategy.

        Returns dict with:
        - max_gift_tier: Highest gift tier to consider
        - spend_ratio: Portion of remaining budget to spend this action
        - aggression: 0-1 scale of how aggressive to be
        """
        # Base allocations by budget tier
        base_allocations = {
            BudgetTier.CRITICAL: {"max_tier": "small", "spend_ratio": 0.05, "aggression": 0.2},
            BudgetTier.LOW: {"max_tier": "medium", "spend_ratio": 0.10, "aggression": 0.4},
            BudgetTier.MEDIUM: {"max_tier": "large", "spend_ratio": 0.15, "aggression": 0.6},
            BudgetTier.HEALTHY: {"max_tier": "whale", "spend_ratio": 0.20, "aggression": 0.8},
            BudgetTier.ABUNDANT: {"max_tier": "whale", "spend_ratio": 0.30, "aggression": 1.0}
        }

        allocation = base_allocations.get(budget_tier, base_allocations[BudgetTier.MEDIUM]).copy()

        # Adjust for phase
        if phase == "boost":
            allocation["spend_ratio"] *= 2.0  # Spend more during boosts
            allocation["aggression"] = min(1.0, allocation["aggression"] + 0.2)
        elif phase == "final_30s":
            allocation["spend_ratio"] *= 1.5
            allocation["aggression"] = min(1.0, allocation["aggression"] + 0.3)

        # Adjust for score deficit
        if score_deficit > 50000:
            allocation["aggression"] = min(1.0, allocation["aggression"] + 0.3)
            # Allow higher tier gifts when behind
            if allocation["max_tier"] == "small":
                allocation["max_tier"] = "medium"
            elif allocation["max_tier"] == "medium":
                allocation["max_tier"] = "large"

        # Adjust for time remaining
        if time_remaining < 60:
            allocation["spend_ratio"] *= 1.5  # Spend faster at end

        return allocation

    @staticmethod
    def select_gift_for_budget(
        affordable_gifts: List[GiftCost],
        allocation: Dict,
        current_budget: int
    ) -> Optional[GiftCost]:
        """Select best gift based on allocation strategy."""
        if not affordable_gifts:
            return None

        # Filter by max tier
        tier_order = ["small", "medium", "large", "whale"]
        max_tier_idx = tier_order.index(allocation["max_tier"]) if allocation["max_tier"] in tier_order else 3

        valid_gifts = [
            g for g in affordable_gifts
            if g.tier in tier_order[:max_tier_idx + 1]
            and g.cost <= current_budget * allocation["spend_ratio"]
        ]

        if not valid_gifts:
            # Fall back to cheapest affordable gift
            return min(affordable_gifts, key=lambda g: g.cost)

        # Pick based on aggression
        if allocation["aggression"] > 0.7:
            return max(valid_gifts, key=lambda g: g.points)
        elif allocation["aggression"] > 0.4:
            # Middle ground - pick median value
            sorted_gifts = sorted(valid_gifts, key=lambda g: g.points)
            return sorted_gifts[len(sorted_gifts) // 2]
        else:
            return min(valid_gifts, key=lambda g: g.cost)


class BudgetIntelligence:
    """
    Strategic budget intelligence system.

    Implements adaptive strategy based on:
    - First boost: Take lead, gauge opponent response
    - Opponent analysis: Track if they're competing or passive
    - Reserved budgets: Snipe (last 5s) + Glove (last 30s)
    - Adaptive spending: Adjust based on score and opponent behavior
    """

    def __init__(self, budget_manager: BudgetManager, team: str = "creator"):
        self.budget_manager = budget_manager
        self.team = team

        # Get starting budget
        self.starting_budget = (budget_manager.creator_starting
                                if team == "creator" else budget_manager.opponent_starting)

        # === BUDGET RESERVATIONS ===
        # Reserve for critical end-game phases
        self.snipe_reserve = min(30000, int(self.starting_budget * 0.10))  # 10% or 30k for last 5s
        self.glove_reserve = min(50000, int(self.starting_budget * 0.15))  # 15% or 50k for last 30s
        self.boost2_reserve = min(100000, int(self.starting_budget * 0.25))  # 25% or 100k for boost #2

        # Total reserved (don't spend below this until phase arrives)
        self.total_reserved = self.snipe_reserve + self.glove_reserve + self.boost2_reserve

        # === OPPONENT TRACKING ===
        self.opponent_spending_rate = 0  # Coins per second
        self.opponent_is_competing = False  # True if matching our spending
        self.opponent_last_check_time = 0
        self.opponent_last_spent = 0

        # === STRATEGY STATE ===
        self.boost1_strategy_set = False
        self.took_lead_in_boost1 = False
        self.opponent_responded_to_boost1 = False
        self.conservative_mode = False  # True if we should conserve

        # === PHASE TRACKING ===
        self.current_phase = "normal"
        self.boost1_completed = False
        self.boost2_completed = False

        print(f"\n🧠 Budget Intelligence Initialized ({team}):")
        print(f"   💰 Starting: {self.starting_budget:,}")
        print(f"   🎯 Reserved for Boost #2: {self.boost2_reserve:,}")
        print(f"   🥊 Reserved for Glove (30s): {self.glove_reserve:,}")
        print(f"   🔫 Reserved for Snipe (5s): {self.snipe_reserve:,}")
        print(f"   📊 Available for Boost #1: {self.starting_budget - self.total_reserved:,}")

    def get_available_budget(self, current_time: int, time_remaining: int) -> int:
        """Get budget available for spending (excluding reserves for later phases)."""
        current_budget = (self.budget_manager.creator_budget
                         if self.team == "creator" else self.budget_manager.opponent_budget)

        # In final 5s: Can use snipe reserve
        if time_remaining <= 5:
            return current_budget  # All-in

        # In final 30s: Can use glove + snipe reserves
        if time_remaining <= 30:
            reserved = self.boost2_reserve if not self.boost2_completed else 0
            return max(0, current_budget - reserved)

        # Before boost #2: Reserve for boost2 + glove + snipe
        if not self.boost2_completed:
            return max(0, current_budget - self.total_reserved)

        # After boost #2: Reserve glove + snipe
        return max(0, current_budget - self.snipe_reserve - self.glove_reserve)

    def update_opponent_analysis(self, current_time: int, opponent_spent: int,
                                  our_score: int, opponent_score: int):
        """Analyze opponent's spending behavior."""
        time_delta = current_time - self.opponent_last_check_time
        if time_delta > 0:
            spent_delta = opponent_spent - self.opponent_last_spent
            self.opponent_spending_rate = spent_delta / time_delta

            # Opponent is competing if they're spending at similar rate to us
            our_spent = (self.budget_manager.creator_spent
                        if self.team == "creator" else self.budget_manager.opponent_spent)
            our_rate = our_spent / max(current_time, 1)

            # Within 50% of our rate = competing
            self.opponent_is_competing = (
                self.opponent_spending_rate > our_rate * 0.5 and
                abs(our_score - opponent_score) < 50000
            )

        self.opponent_last_check_time = current_time
        self.opponent_last_spent = opponent_spent

    def analyze_boost1_response(self, our_score_before: int, our_score_after: int,
                                 opponent_score_before: int, opponent_score_after: int):
        """Analyze what happened during Boost #1 to set strategy."""
        our_gain = our_score_after - our_score_before
        opponent_gain = opponent_score_after - opponent_score_before

        # Did we take the lead?
        self.took_lead_in_boost1 = our_score_after > opponent_score_after

        # Did opponent respond aggressively?
        self.opponent_responded_to_boost1 = opponent_gain > our_gain * 0.5

        # Set strategy based on outcome
        if self.took_lead_in_boost1 and not self.opponent_responded_to_boost1:
            # We're ahead and opponent is passive - go conservative
            self.conservative_mode = True
            print(f"🧠 Strategy: CONSERVATIVE - Leading and opponent passive")
        elif not self.took_lead_in_boost1:
            # We're behind - need to be aggressive in Boost #2
            self.conservative_mode = False
            print(f"🧠 Strategy: AGGRESSIVE - Behind, need Boost #2")
        else:
            # Close battle - balanced approach
            self.conservative_mode = False
            print(f"🧠 Strategy: BALANCED - Competitive match")

        self.boost1_strategy_set = True
        self.boost1_completed = True

    def should_spend_in_phase(self, phase: str, time_remaining: int,
                               our_score: int, opponent_score: int,
                               multiplier: float) -> dict:
        """
        Get spending recommendation for current situation.

        Returns:
            dict with:
            - should_spend: bool
            - max_spend: int (maximum coins to spend this action)
            - gift_tier: str (recommended gift tier)
            - reason: str
        """
        available = self.get_available_budget(0, time_remaining)
        deficit = opponent_score - our_score

        # === FINAL 5 SECONDS - SNIPE MODE ===
        if time_remaining <= 5:
            if deficit > 0:  # We're behind
                return {
                    "should_spend": True,
                    "max_spend": available,  # All-in
                    "gift_tier": "whale",
                    "reason": f"SNIPE MODE - {deficit:,} behind"
                }
            else:  # We're ahead
                return {
                    "should_spend": False,
                    "max_spend": 0,
                    "gift_tier": None,
                    "reason": "SNIPE MODE - Protecting lead"
                }

        # === FINAL 30 SECONDS - GLOVE TERRITORY ===
        if time_remaining <= 30:
            # Reserve for potential x5 plays
            return {
                "should_spend": True,
                "max_spend": min(available, 50000),  # Controlled spending
                "gift_tier": "large" if multiplier >= 5 else "medium",
                "reason": f"FINAL 30s - x{int(multiplier)} active"
            }

        # === BOOST PHASE ===
        if phase == "boost":
            if multiplier >= 5:  # x5 active - maximize!
                return {
                    "should_spend": True,
                    "max_spend": available,
                    "gift_tier": "whale",
                    "reason": f"X5 ACTIVE - Maximum value!"
                }
            elif multiplier >= 3:  # x3 boost
                # Spend aggressively but not all-in
                spend_pct = 0.6 if not self.conservative_mode else 0.3
                return {
                    "should_spend": True,
                    "max_spend": int(available * spend_pct),
                    "gift_tier": "whale",
                    "reason": f"X3 BOOST - {'Aggressive' if not self.conservative_mode else 'Controlled'}"
                }
            else:  # x2 boost
                spend_pct = 0.4 if not self.conservative_mode else 0.2
                return {
                    "should_spend": True,
                    "max_spend": int(available * spend_pct),
                    "gift_tier": "large",
                    "reason": f"X2 BOOST - {'Aggressive' if not self.conservative_mode else 'Controlled'}"
                }

        # === NORMAL PHASE ===
        if self.conservative_mode:
            return {
                "should_spend": False,
                "max_spend": 0,
                "gift_tier": None,
                "reason": "CONSERVE - Waiting for boost"
            }

        # Only spend if significantly behind
        if deficit > 30000:
            return {
                "should_spend": True,
                "max_spend": min(available, 10000),
                "gift_tier": "medium",
                "reason": f"CATCH-UP - {deficit:,} behind"
            }

        return {
            "should_spend": False,
            "max_spend": 0,
            "gift_tier": None,
            "reason": "CONSERVE - Normal phase"
        }

    def select_gift(self, max_spend: int, tier: str) -> Optional[str]:
        """Select best gift within budget and tier constraints."""
        tier_order = {"small": 0, "medium": 1, "large": 2, "whale": 3}
        max_tier_idx = tier_order.get(tier, 3)

        best_gift = None
        best_value = 0

        for name, gift in GIFT_CATALOG.items():
            gift_tier_idx = tier_order.get(gift.tier, 0)
            if gift.cost <= max_spend and gift_tier_idx <= max_tier_idx:
                if gift.points > best_value:
                    best_value = gift.points
                    best_gift = name

        return best_gift

    def mark_boost2_complete(self):
        """Mark Boost #2 as completed to release reserved budget."""
        self.boost2_completed = True
        print(f"🧠 Boost #2 complete - Released {self.boost2_reserve:,} reserved coins")


if __name__ == "__main__":
    print("Budget System Demo")
    print("=" * 60)

    # Create budget manager
    budget = BudgetManager()

    # Simulate some spending
    print("\n📍 Simulating spending...")

    # Creator sends some gifts
    budget.spend("creator", "Rose", 10, "normal")
    budget.spend("creator", "Doughnut", 20, "normal")
    budget.spend("creator", "Dragon Flame", 30, "boost")

    # Opponent sends gifts
    budget.spend("opponent", "Lion", 15, "normal")
    budget.spend("opponent", "TikTok Universe", 35, "boost")

    budget.print_status()

    print("\n📊 Analytics:")
    analytics = budget.get_analytics()
    print(f"   Creator efficiency: {analytics['creator']['efficiency']*100:.1f}%")
    print(f"   Opponent efficiency: {analytics['opponent']['efficiency']*100:.1f}%")

    print("\n🎯 Strategy recommendation for LOW budget:")
    allocation = BudgetStrategy.get_recommended_allocation(
        BudgetTier.LOW, "boost", 100, 10000
    )
    print(f"   Max tier: {allocation['max_tier']}")
    print(f"   Spend ratio: {allocation['spend_ratio']*100:.0f}%")
    print(f"   Aggression: {allocation['aggression']:.1f}")
