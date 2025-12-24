"""
Smart Opponent AI with Strategy Profiles + Custom Opponent Builder

Sophisticated AI that simulates various opponent strategies:
- Multiple strategy profiles randomly selected each battle
- Phase-specific aggression levels (Boost #1, Boost #2, Final 5s)
- Smart glove timing and snipe reserves
- Budget-aware decision making
- CUSTOM OPPONENT BUILDER: Create your own strategies!

Strategy Profiles:
1. EARLY_AGGRESSOR - Aggressive Boost #1, conservative rest (limited budget)
2. LATE_DOMINATOR - Conservative early, aggressive Boost #2 + final 5s (large budget)
3. STEADY_PRESSURE - Balanced throughout (large budget)
4. SNIPER - Cautious boosts, all-in final 5s with gloves (limited budget)
5. BOOST2_SPECIALIST - Very aggressive Boost #2, aggressive final 5s (balanced budget)
6. MOMENTUM_RIDER - Adapts based on score lead/deficit
7. CHAOTIC - Unpredictable random behavior
8. CUSTOM - User-defined strategy via OpponentBuilder
"""

import random
from typing import Optional, Dict, List, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType

if TYPE_CHECKING:
    from core.budget_system import BudgetManager
    from core.strategic_intelligence import StrategicIntelligence
    from core.snipe_intelligence import SnipeIntelligence


class StrategyProfile(Enum):
    """Opponent strategy profiles."""
    EARLY_AGGRESSOR = "early_aggressor"
    LATE_DOMINATOR = "late_dominator"
    STEADY_PRESSURE = "steady_pressure"
    SNIPER = "sniper"
    BOOST2_SPECIALIST = "boost2_specialist"
    MOMENTUM_RIDER = "momentum_rider"
    CHAOTIC = "chaotic"
    CUSTOM = "custom"  # User-defined via OpponentBuilder


@dataclass
class PhaseAggression:
    """Aggression levels for different phases (0-1 scale)."""
    # BALANCE v1.3: Increased opponent strength (v1.2 creator won 86%, want ~55%)
    normal: float = 0.22         # Normal phase (orig: 0.2) - slight increase
    boost1: float = 0.55         # During Boost #1 (orig: 0.5) - increase
    boost2: float = 0.65         # During Boost #2 (orig: 0.6) - slight increase
    final_30s: float = 0.45      # Final 30 seconds (orig: 0.4) - increase
    final_5s: float = 0.85       # Final 5 seconds (orig: 0.8) - increase
    x5_active: float = 0.92      # When our x5 is active (orig: 0.9) - increase

    # Whale gift probability multipliers (increased for more aggressive opponent)
    whale_normal: float = 0.06   # orig: 0.05 - slight increase
    whale_boost: float = 0.18    # orig: 0.15 - increase
    whale_final: float = 0.24    # orig: 0.2 - increase
    whale_x5: float = 0.45       # orig: 0.4 - increase

    # Budget reserve ratios
    reserve_for_boost2: float = 0.3   # Save 30% for Boost #2
    reserve_for_snipe: float = 0.1    # Save 10% for final 5s

    # Glove timing preferences
    glove_in_boost1: float = 0.5      # Chance to use glove in Boost #1
    glove_in_boost2: float = 0.7      # Chance to use glove in Boost #2
    glove_in_final_30s: float = 0.6   # Chance to use glove in final 30s
    glove_in_final_5s: float = 0.9    # Chance to use glove in final 5s


# Strategy Profile Configurations
STRATEGY_PROFILES: Dict[StrategyProfile, PhaseAggression] = {

    # EARLY_AGGRESSOR: Limited budget, go hard in Boost #1, conserve rest
    StrategyProfile.EARLY_AGGRESSOR: PhaseAggression(
        normal=0.1,
        boost1=0.9,           # VERY aggressive in Boost #1
        boost2=0.3,           # Conservative in Boost #2
        final_30s=0.2,
        final_5s=0.4,         # Moderate snipe (budget depleted)
        x5_active=0.95,
        whale_normal=0.02,
        whale_boost=0.35,     # High whale chance in Boost #1
        whale_final=0.1,
        whale_x5=0.5,
        reserve_for_boost2=0.1,   # Don't save much
        reserve_for_snipe=0.05,
        glove_in_boost1=0.9,      # Use gloves early
        glove_in_boost2=0.2,
        glove_in_final_30s=0.1,
        glove_in_final_5s=0.3,
    ),

    # LATE_DOMINATOR: Large budget, conservative early, dominate late
    StrategyProfile.LATE_DOMINATOR: PhaseAggression(
        normal=0.1,
        boost1=0.3,           # Conservative in Boost #1
        boost2=0.85,          # VERY aggressive in Boost #2
        final_30s=0.7,
        final_5s=0.95,        # EXTREMELY aggressive final 5s
        x5_active=0.95,
        whale_normal=0.02,
        whale_boost=0.1,      # Save whales for later
        whale_final=0.4,      # Whale barrage at end
        whale_x5=0.6,
        reserve_for_boost2=0.4,   # Save heavily for Boost #2
        reserve_for_snipe=0.2,    # Save for snipe
        glove_in_boost1=0.2,      # Save gloves
        glove_in_boost2=0.8,      # Use gloves in Boost #2
        glove_in_final_30s=0.6,
        glove_in_final_5s=0.95,   # Glove + snipe combo
    ),

    # STEADY_PRESSURE: Large budget, consistent pressure throughout
    StrategyProfile.STEADY_PRESSURE: PhaseAggression(
        normal=0.35,          # Active even in normal phase
        boost1=0.6,
        boost2=0.65,
        final_30s=0.55,
        final_5s=0.6,
        x5_active=0.85,
        whale_normal=0.08,    # Occasional whales throughout
        whale_boost=0.2,
        whale_final=0.25,
        whale_x5=0.4,
        reserve_for_boost2=0.25,
        reserve_for_snipe=0.1,
        glove_in_boost1=0.5,
        glove_in_boost2=0.5,
        glove_in_final_30s=0.5,
        glove_in_final_5s=0.5,
    ),

    # SNIPER: Limited budget, cautious play, all-in final 5s with gloves
    StrategyProfile.SNIPER: PhaseAggression(
        normal=0.05,          # Almost no activity
        boost1=0.2,           # Cautious in Boost #1
        boost2=0.25,          # Cautious in Boost #2
        final_30s=0.3,
        final_5s=0.99,        # ALL-IN final 5 seconds!
        x5_active=0.95,
        whale_normal=0.01,
        whale_boost=0.05,
        whale_final=0.1,
        whale_x5=0.3,
        reserve_for_boost2=0.2,
        reserve_for_snipe=0.5,    # Save 50% for snipe!
        glove_in_boost1=0.1,
        glove_in_boost2=0.15,
        glove_in_final_30s=0.3,
        glove_in_final_5s=0.99,   # Always use glove in final 5s
    ),

    # BOOST2_SPECIALIST: Balanced budget, dominate Boost #2
    StrategyProfile.BOOST2_SPECIALIST: PhaseAggression(
        normal=0.15,
        boost1=0.4,           # Moderate in Boost #1
        boost2=0.95,          # DOMINATE Boost #2
        final_30s=0.5,
        final_5s=0.7,         # Aggressive snipe
        x5_active=0.95,
        whale_normal=0.03,
        whale_boost=0.3,      # Whales during boosts
        whale_final=0.25,
        whale_x5=0.5,
        reserve_for_boost2=0.45,  # Save heavily for Boost #2
        reserve_for_snipe=0.1,
        glove_in_boost1=0.3,
        glove_in_boost2=0.95,     # Always glove in Boost #2
        glove_in_final_30s=0.4,
        glove_in_final_5s=0.6,
    ),

    # MOMENTUM_RIDER: Adapts based on score (values modified at runtime)
    StrategyProfile.MOMENTUM_RIDER: PhaseAggression(
        normal=0.25,
        boost1=0.5,
        boost2=0.6,
        final_30s=0.5,
        final_5s=0.7,
        x5_active=0.9,
        whale_normal=0.05,
        whale_boost=0.2,
        whale_final=0.25,
        whale_x5=0.4,
        reserve_for_boost2=0.3,
        reserve_for_snipe=0.15,
        glove_in_boost1=0.5,
        glove_in_boost2=0.6,
        glove_in_final_30s=0.5,
        glove_in_final_5s=0.7,
    ),

    # CHAOTIC: Unpredictable (randomized each action)
    StrategyProfile.CHAOTIC: PhaseAggression(
        normal=0.3,
        boost1=0.5,
        boost2=0.5,
        final_30s=0.5,
        final_5s=0.5,
        x5_active=0.7,
        whale_normal=0.1,
        whale_boost=0.2,
        whale_final=0.2,
        whale_x5=0.3,
        reserve_for_boost2=0.2,
        reserve_for_snipe=0.1,
        glove_in_boost1=0.5,
        glove_in_boost2=0.5,
        glove_in_final_30s=0.5,
        glove_in_final_5s=0.5,
    ),
}

# Budget tier assignments for strategy profiles
STRATEGY_BUDGET_PREFERENCES = {
    StrategyProfile.EARLY_AGGRESSOR: "limited",     # 50k-150k
    StrategyProfile.LATE_DOMINATOR: "large",        # 350k-600k
    StrategyProfile.STEADY_PRESSURE: "large",       # 350k-600k
    StrategyProfile.SNIPER: "limited",              # 50k-150k
    StrategyProfile.BOOST2_SPECIALIST: "balanced",  # 150k-350k
    StrategyProfile.MOMENTUM_RIDER: "balanced",     # 150k-350k
    StrategyProfile.CHAOTIC: "random",              # Any budget
}


class OpponentAI:
    """Smart opponent with strategy profiles, budget awareness, and surrender logic."""

    def __init__(
        self,
        phase_manager: AdvancedPhaseManager,
        difficulty: str = "medium",
        budget_manager: Optional['BudgetManager'] = None,
        strategy: Optional[StrategyProfile] = None,
        enable_strategic_intelligence: bool = True
    ):
        self.phase_manager = phase_manager
        self.difficulty = difficulty
        self.budget_manager = budget_manager

        # Select or assign strategy
        self.strategy = strategy or self._select_strategy()
        self.aggression = STRATEGY_PROFILES[self.strategy]

        # State tracking
        self.last_action_time = -10
        self.gloves_used = 0
        self.hammer_used = False
        self.fog_used = False
        self.total_donated = 0
        self.total_spent = 0
        self.whale_gifts_sent = 0
        self.gifts_blocked_by_budget = 0

        # Phase tracking for strategy
        self.boost1_participated = False
        self.boost2_participated = False
        self.snipe_mode_active = False

        # Budget tracking
        self.starting_budget = 0
        self.snipe_reserve = 0
        self.boost2_reserve = 0

        # Strategic Intelligence for surrender/adaptive logic
        self.strategic_intel: Optional['StrategicIntelligence'] = None
        self.enable_strategic_intelligence = enable_strategic_intelligence
        self.has_surrendered = False
        self.surrender_time = None
        self.surrender_reason = None

        # Snipe Intelligence for final seconds strategy
        self.snipe_intel: Optional['SnipeIntelligence'] = None
        self.snipe_reserve_locked = False
        self.snipe_executed = False
        self.snipe_glove_used = False

        # Gift options with costs
        self.small_gifts = [
            ("Rose", 1), ("Rose", 1), ("Rose", 1),
            ("Heart", 5), ("Heart", 5),
            ("Doughnut", 30),
            ("Cap", 99),
        ]
        self.medium_gifts = [
            ("Rosa Nebula", 299),
            ("Perfume", 500),
            ("GG", 1000),
        ]
        self.whale_gifts = [
            ("Dragon Flame", 10000),
            ("Lion", 29999),
            ("TikTok Universe", 44999),
        ]

        # Initialize budget reserves
        self._calculate_reserves()

        # Initialize strategic intelligence if enabled and budget manager available
        self._init_strategic_intelligence()

        # Announce strategy
        self._announce_strategy()

    def _select_strategy(self) -> StrategyProfile:
        """Randomly select a strategy profile based on budget."""
        if not self.budget_manager:
            return random.choice(list(StrategyProfile))

        budget = self.budget_manager.opponent_starting

        # Filter strategies by budget tier
        suitable_strategies = []

        for strategy, preference in STRATEGY_BUDGET_PREFERENCES.items():
            if preference == "random":
                suitable_strategies.append(strategy)
            elif preference == "limited" and budget < 180000:
                suitable_strategies.append(strategy)
            elif preference == "balanced" and 120000 <= budget <= 400000:
                suitable_strategies.append(strategy)
            elif preference == "large" and budget > 300000:
                suitable_strategies.append(strategy)

        # If no suitable strategy, allow any
        if not suitable_strategies:
            suitable_strategies = list(StrategyProfile)

        return random.choice(suitable_strategies)

    def _calculate_reserves(self):
        """Calculate budget reserves based on strategy."""
        if not self.budget_manager:
            return

        self.starting_budget = self.budget_manager.opponent_starting

        # Calculate reserves based on strategy profile
        self.boost2_reserve = int(self.starting_budget * self.aggression.reserve_for_boost2)
        self.snipe_reserve = int(self.starting_budget * self.aggression.reserve_for_snipe)

        # Cap reserves at reasonable amounts
        self.boost2_reserve = min(self.boost2_reserve, 150000)
        self.snipe_reserve = min(self.snipe_reserve, 80000)

    def _init_strategic_intelligence(self):
        """Initialize strategic intelligence for advanced decision making."""
        if not self.enable_strategic_intelligence or not self.budget_manager:
            return

        try:
            from core.strategic_intelligence import StrategicIntelligence
            self.strategic_intel = StrategicIntelligence(
                budget_manager=self.budget_manager,
                team="opponent",
                battle_duration=self.phase_manager.battle_duration
            )
        except ImportError:
            # Module not available, continue without it
            pass

        # Also initialize snipe intelligence
        try:
            from core.snipe_intelligence import SnipeIntelligence
            # Estimate creator's budget (we don't know exactly)
            estimated_creator_budget = self.budget_manager.creator_starting
            self.snipe_intel = SnipeIntelligence(
                our_budget=self.budget_manager.opponent_starting,
                opponent_estimated_budget=estimated_creator_budget,
                battle_duration=self.phase_manager.battle_duration
            )
        except ImportError:
            pass

    def _announce_strategy(self):
        """Print opponent strategy selection."""
        strategy_descriptions = {
            StrategyProfile.EARLY_AGGRESSOR: "🔥 Early Aggressor (All-in Boost #1)",
            StrategyProfile.LATE_DOMINATOR: "⏳ Late Dominator (Conserve early, dominate late)",
            StrategyProfile.STEADY_PRESSURE: "📈 Steady Pressure (Consistent throughout)",
            StrategyProfile.SNIPER: "🎯 Sniper (Save everything for final 5s)",
            StrategyProfile.BOOST2_SPECIALIST: "⚡ Boost #2 Specialist (Dominate second boost)",
            StrategyProfile.MOMENTUM_RIDER: "🌊 Momentum Rider (Adapts to score)",
            StrategyProfile.CHAOTIC: "🎲 Chaotic (Unpredictable)",
            StrategyProfile.CUSTOM: "🔧 Custom (User-defined strategy)",
        }

        budget_str = f"{self.starting_budget:,}" if self.starting_budget else "Unknown"
        print(f"\n👻 OPPONENT STRATEGY: {strategy_descriptions[self.strategy]}")
        print(f"   Budget: {budget_str} | Reserves: Boost #2={self.boost2_reserve:,}, Snipe={self.snipe_reserve:,}")

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.last_action_time = -10
        self.gloves_used = 0
        self.hammer_used = False
        self.fog_used = False
        self.total_donated = 0
        self.total_spent = 0
        self.whale_gifts_sent = 0
        self.gifts_blocked_by_budget = 0
        self.boost1_participated = False
        self.boost2_participated = False
        self.snipe_mode_active = False

        # Reset snipe state
        self.snipe_reserve_locked = False
        self.snipe_executed = False
        self.snipe_glove_used = False

        # Reset surrender state
        self.has_surrendered = False
        self.surrender_time = None
        self.surrender_reason = None

        # Reset snipe intelligence
        if self.snipe_intel:
            self.snipe_intel.reset()

        # Re-select strategy for new battle
        self.strategy = self._select_strategy()
        self.aggression = STRATEGY_PROFILES[self.strategy]
        self._calculate_reserves()
        self._announce_strategy()

    def can_afford(self, gift_name: str) -> bool:
        """Check if opponent can afford a gift."""
        if not self.budget_manager:
            return True
        return self.budget_manager.can_afford("opponent", gift_name)

    def get_budget_ratio(self) -> float:
        """Get remaining budget ratio (0-1)."""
        if not self.budget_manager:
            return 1.0
        return self.budget_manager.get_remaining_ratio("opponent")

    def get_current_budget(self) -> int:
        """Get current budget amount."""
        if not self.budget_manager:
            return 999999
        return self.budget_manager.opponent_budget

    def get_available_budget(self, time_remaining: int) -> int:
        """Get budget available for spending (accounting for reserves)."""
        current = self.get_current_budget()

        # In final 5s - all-in
        if time_remaining <= 5:
            return current

        # In final 30s - can use snipe reserve
        if time_remaining <= 30:
            return max(0, current - self.snipe_reserve)

        # Before Boost #2 - reserve for both
        if not self.phase_manager.boost2_triggered:
            return max(0, current - self.boost2_reserve - self.snipe_reserve)

        # After Boost #2 - only reserve snipe
        return max(0, current - self.snipe_reserve)

    def _get_current_aggression(self, current_time: int, time_remaining: int,
                                 in_boost: bool, deficit: int) -> float:
        """Get current aggression level based on phase and strategy."""

        # Check phase
        in_boost1 = self.phase_manager.boost1_active
        in_boost2 = self.phase_manager.boost2_active
        in_final_5s = time_remaining <= 5
        in_final_30s = time_remaining <= 30

        # Check if we have x5 active
        our_x5 = (self.phase_manager.active_glove_x5 and
                  self.phase_manager.active_glove_owner == "opponent")

        # Base aggression from strategy
        if our_x5:
            aggression = self.aggression.x5_active
        elif in_final_5s:
            aggression = self.aggression.final_5s
            self.snipe_mode_active = True
        elif in_boost2:
            aggression = self.aggression.boost2
            self.boost2_participated = True
        elif in_boost1:
            aggression = self.aggression.boost1
            self.boost1_participated = True
        elif in_final_30s:
            aggression = self.aggression.final_30s
        else:
            aggression = self.aggression.normal

        # MOMENTUM_RIDER adjustments
        if self.strategy == StrategyProfile.MOMENTUM_RIDER:
            if deficit > 30000:  # We're behind
                aggression = min(0.95, aggression * 1.4)
            elif deficit < -30000:  # We're ahead
                aggression = max(0.1, aggression * 0.6)

        # CHAOTIC randomization
        if self.strategy == StrategyProfile.CHAOTIC:
            aggression = aggression * random.uniform(0.3, 1.7)
            aggression = min(0.95, max(0.05, aggression))

        return aggression

    def _get_whale_chance(self, time_remaining: int, in_boost: bool) -> float:
        """Get whale gift probability based on phase."""
        in_final_5s = time_remaining <= 5
        in_final_30s = time_remaining <= 30

        our_x5 = (self.phase_manager.active_glove_x5 and
                  self.phase_manager.active_glove_owner == "opponent")

        if our_x5:
            return self.aggression.whale_x5
        elif in_final_5s:
            return self.aggression.whale_final * 1.5  # Extra chance in snipe
        elif in_final_30s:
            return self.aggression.whale_final
        elif in_boost:
            return self.aggression.whale_boost
        else:
            return self.aggression.whale_normal

    def _should_use_glove(self, time_remaining: int) -> float:
        """Get glove usage probability based on phase."""
        in_boost1 = self.phase_manager.boost1_active
        in_boost2 = self.phase_manager.boost2_active
        in_final_5s = time_remaining <= 5
        in_final_30s = time_remaining <= 30

        if in_final_5s:
            return self.aggression.glove_in_final_5s
        elif in_boost2:
            return self.aggression.glove_in_boost2
        elif in_boost1:
            return self.aggression.glove_in_boost1
        elif in_final_30s:
            return self.aggression.glove_in_final_30s
        else:
            return 0.1  # Low chance outside key phases

    def _spend_budget(self, gift_name: str, points: int, current_time: int, phase: str) -> bool:
        """Attempt to spend budget on a gift."""
        if not self.budget_manager:
            return True

        success, cost = self.budget_manager.spend("opponent", gift_name, current_time, phase)
        if success:
            self.total_spent += cost
            return True
        else:
            self.gifts_blocked_by_budget += 1
            return False

    def _select_gift(self, whale_chance: float, available_budget: int) -> tuple:
        """Select a gift based on chances and budget."""

        # Try whale gift
        if random.random() < whale_chance and available_budget >= 10000:
            affordable_whales = [
                (n, p) for n, p in self.whale_gifts
                if p <= available_budget and self.can_afford(n)
            ]
            if affordable_whales:
                # Prefer bigger whales for snipe mode
                if self.snipe_mode_active:
                    affordable_whales.sort(key=lambda x: x[1], reverse=True)
                    return affordable_whales[0]
                return random.choice(affordable_whales)

        # Try medium gift
        if available_budget >= 299 and random.random() < 0.4:
            affordable_medium = [
                (n, p) for n, p in self.medium_gifts
                if p <= available_budget and self.can_afford(n)
            ]
            if affordable_medium:
                return random.choice(affordable_medium)

        # Small gift
        affordable_small = [
            (n, p) for n, p in self.small_gifts
            if p <= available_budget and self.can_afford(n)
        ]
        if affordable_small:
            return random.choice(affordable_small)

        return ("Rose", 1)  # Fallback

    def update(self, current_time: int, creator_score: int, opponent_score: int) -> dict:
        """Make strategic decisions based on strategy profile."""
        result = {
            "gift_sent": False,
            "gift_name": None,
            "gift_points": 0,
            "power_up_used": None,
            "message": None,
            "surrendered": False
        }

        # Get game state
        time_remaining = self.phase_manager.battle_duration - current_time
        in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active
        in_final_30s = self.phase_manager.is_in_final_30s(current_time)
        in_final_5s = time_remaining <= 5
        deficit = creator_score - opponent_score  # Positive = we're behind
        phase = "boost" if in_boost else ("final_30s" if in_final_30s else "normal")

        # === STRATEGIC INTELLIGENCE: Check for surrender ===
        if self.strategic_intel and not self.has_surrendered:
            # Update scores in strategic intel
            self.strategic_intel.update_scores(opponent_score, creator_score, current_time)

            # Analyze if we should surrender (only check every 10 seconds to save computation)
            if current_time % 10 == 0 or deficit > 50000:
                recovery = self.strategic_intel.analyze_recovery(time_remaining)

                # Surrender if recovery is impossible and we're confident
                if not recovery.can_recover and recovery.confidence >= 0.85:
                    # Don't surrender in final 30s - always try to fight
                    if time_remaining > 30:
                        self.has_surrendered = True
                        self.surrender_time = current_time
                        self.surrender_reason = (
                            f"Deficit {recovery.deficit:,} unrecoverable. "
                            f"Max possible: {recovery.max_possible_points:,} "
                            f"({recovery.confidence*100:.0f}% confidence)"
                        )
                        result["surrendered"] = True
                        result["message"] = f"🏳️ Opponent SURRENDERED: {self.surrender_reason}"
                        print(f"\n🏳️ OPPONENT SURRENDERED at t={current_time}s!")
                        print(f"   Reason: {self.surrender_reason}")
                        return result

        # If already surrendered, stop gifting (but still allow defensive power-ups)
        if self.has_surrendered:
            result["surrendered"] = True
            # Still allow defensive actions like hammer against enemy x5
            creator_has_x5 = (self.phase_manager.active_glove_x5 and
                             self.phase_manager.active_glove_owner == "creator")
            if creator_has_x5 and not self.hammer_used:
                # Use hammer to deny enemy x5 even when surrendered
                if random.random() < 0.5:
                    if self.phase_manager.use_power_up(PowerUpType.HAMMER, "opponent", current_time):
                        self.hammer_used = True
                        result["power_up_used"] = "HAMMER"
                        result["message"] = "👻 Surrendered opponent used HAMMER defensively!"
                        return result
            return result

        # Get available budget (accounting for reserves)
        available_budget = self.get_available_budget(time_remaining)

        # Check if creator has active x5
        creator_has_x5 = (self.phase_manager.active_glove_x5 and
                         self.phase_manager.active_glove_owner == "creator")

        # Check if we have x5 active
        we_have_x5 = (self.phase_manager.active_glove_x5 and
                      self.phase_manager.active_glove_owner == "opponent")

        # === SNIPE INTELLIGENCE: Update tracking ===
        if self.snipe_intel:
            self.snipe_intel.update_scores(opponent_score, creator_score, current_time)
            self.snipe_intel.update_our_budget(self.get_current_budget())

        # === PRIORITY 0: SNIPE MODE (Final 5 seconds) ===
        if in_final_5s and not self.snipe_executed:
            snipe_result = self._execute_snipe_mode(
                current_time, time_remaining, creator_score, opponent_score,
                we_have_x5, result
            )
            if snipe_result:
                return snipe_result

        # === PRIORITY 1: Use Hammer against creator's x5 ===
        if creator_has_x5 and not self.hammer_used:
            hammer_chance = 0.7 if in_boost or in_final_30s else 0.4
            if random.random() < hammer_chance:
                if self.phase_manager.use_power_up(PowerUpType.HAMMER, "opponent", current_time):
                    self.hammer_used = True
                    result["power_up_used"] = "HAMMER"
                    result["message"] = "👻 Opponent used HAMMER to neutralize your x5!"
                    print(f"\n👻🔨 OPPONENT HAMMER! Creator's x5 NEUTRALIZED!")
                    return result

        # === PRIORITY 2: Use Glove based on strategy ===
        if self.gloves_used < 2 and not we_have_x5:
            glove_chance = self._should_use_glove(time_remaining)

            # SNIPER strategy: Save gloves for final 5s
            if self.strategy == StrategyProfile.SNIPER and not in_final_5s:
                glove_chance *= 0.1  # Almost never use before snipe

            # LATE_DOMINATOR: Save for Boost #2 and final
            if self.strategy == StrategyProfile.LATE_DOMINATOR:
                if not self.phase_manager.boost2_triggered and not in_final_30s:
                    glove_chance *= 0.2

            if random.random() < glove_chance:
                if self.phase_manager.use_power_up(PowerUpType.GLOVE, "opponent", current_time):
                    self.gloves_used += 1
                    result["power_up_used"] = "GLOVE"
                    phase_desc = "SNIPE MODE" if in_final_5s else ("Boost #2" if self.phase_manager.boost2_active else "boost")
                    result["message"] = f"👻 Opponent deployed GLOVE in {phase_desc}!"
                    return result

        # === PRIORITY 3: Send gifts based on aggression ===
        aggression = self._get_current_aggression(current_time, time_remaining, in_boost, deficit)

        # Check if we should act
        if random.random() > aggression:
            return result

        # Budget check (skip if no budget available for phase)
        if available_budget < 1 and not in_final_5s:
            return result

        # In final 5s, release all reserves
        if in_final_5s:
            available_budget = self.get_current_budget()

        # Get whale chance and select gift
        whale_chance = self._get_whale_chance(time_remaining, in_boost)

        # Boost whale chance if we have x5
        if we_have_x5:
            whale_chance = min(0.8, whale_chance * 2)

        gift_name, points = self._select_gift(whale_chance, available_budget)

        # Try to spend budget
        if not self._spend_budget(gift_name, points, current_time, phase):
            # Can't afford, try Rose
            if not self._spend_budget("Rose", 1, current_time, phase):
                return result
            gift_name, points = "Rose", 1

        # Record the gift
        self.phase_manager.record_gift(gift_name, points, "opponent", current_time)
        self.total_donated += points

        if points >= 10000:
            self.whale_gifts_sent += 1

        result["gift_sent"] = True
        result["gift_name"] = gift_name
        result["gift_points"] = points

        # Log whale gifts with strategy context
        if points >= 10000:
            multiplier = self.phase_manager.get_current_multiplier()
            effective = int(points * multiplier)
            remaining = self.get_current_budget()
            strategy_name = self.strategy.value.replace("_", " ").title()
            phase_str = "SNIPE" if in_final_5s else ("x5" if we_have_x5 else phase.upper())
            print(f"\n👻💰 OPPONENT [{strategy_name}] {phase_str}! {gift_name}: {points:,} × {int(multiplier)} = {effective:,} (Budget: {remaining:,})")
        elif points >= 1000:
            # Log large gifts too during key moments
            if in_boost or in_final_30s:
                multiplier = self.phase_manager.get_current_multiplier()
                print(f"[OPPONENT] {gift_name}: {points:,} × {int(multiplier)}")

        return result

    def _execute_snipe_mode(
        self,
        current_time: int,
        time_remaining: int,
        creator_score: int,
        opponent_score: int,
        we_have_x5: bool,
        result: dict
    ) -> Optional[dict]:
        """
        Execute snipe mode in final seconds.

        This is the critical moment - all strategy leads to this.
        TikTok battle reality: Most battles are won/lost in final 5 seconds.

        Returns result dict if action taken, None to continue normal flow.
        """
        deficit = creator_score - opponent_score  # Positive = we're behind
        our_budget = self.get_current_budget()
        multiplier = self.phase_manager.get_current_multiplier()

        # Calculate what we need to win
        points_needed = deficit + 1 if deficit > 0 else 0

        # With x5, our points are worth 5x
        effective_multiplier = 5.0 if we_have_x5 else multiplier

        print(f"\n{'='*60}")
        print(f"👻🎯 OPPONENT SNIPE MODE ACTIVATED!")
        print(f"   Time remaining: {time_remaining}s")
        print(f"   Deficit: {deficit:,} | Budget: {our_budget:,}")
        print(f"   Multiplier: x{effective_multiplier:.0f}")
        print(f"{'='*60}")

        # STEP 1: Deploy glove if we have one and don't have x5 yet
        if self.gloves_used < 2 and not we_have_x5 and not self.snipe_glove_used:
            if self.phase_manager.use_power_up(PowerUpType.GLOVE, "opponent", current_time):
                self.gloves_used += 1
                self.snipe_glove_used = True
                result["power_up_used"] = "GLOVE"
                result["message"] = "👻🥊 SNIPE GLOVE DEPLOYED! x5 ACTIVE!"
                print(f"   🥊 GLOVE DEPLOYED for x5 multiplier!")
                return result

        # STEP 2: Calculate optimal gift to send
        # We want to maximize points in remaining time
        # Prioritize biggest affordable whale gifts

        whale_gifts = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
        ]

        # Find biggest affordable gift
        chosen_gift = None
        chosen_cost = 0

        for name, cost in whale_gifts:
            if cost <= our_budget and self.can_afford(name):
                chosen_gift = name
                chosen_cost = cost
                break

        # Fallback to medium gifts
        if not chosen_gift:
            medium_gifts = [("GG", 1000), ("Rosa Nebula", 299)]
            for name, cost in medium_gifts:
                if cost <= our_budget and self.can_afford(name):
                    chosen_gift = name
                    chosen_cost = cost
                    break

        if not chosen_gift:
            # Even small gifts count in snipe
            if our_budget >= 1 and self.can_afford("Rose"):
                chosen_gift = "Rose"
                chosen_cost = 1

        if not chosen_gift:
            return None  # Nothing we can do

        # Calculate effective points
        effective_points = int(chosen_cost * effective_multiplier)

        # STEP 3: Send the gift
        phase = "final_5s"
        if self._spend_budget(chosen_gift, chosen_cost, current_time, phase):
            self.phase_manager.record_gift(chosen_gift, chosen_cost, "opponent", current_time)
            self.total_donated += chosen_cost

            if chosen_cost >= 10000:
                self.whale_gifts_sent += 1

            result["gift_sent"] = True
            result["gift_name"] = chosen_gift
            result["gift_points"] = chosen_cost

            # Determine if this is a winning snipe
            new_score = opponent_score + effective_points
            is_winning = new_score > creator_score

            # Epic snipe announcement
            if is_winning:
                print(f"   💀 KILLING BLOW! {chosen_gift}: {chosen_cost:,} × {effective_multiplier:.0f} = {effective_points:,}")
                print(f"   📊 Score: {opponent_score:,} + {effective_points:,} = {new_score:,} vs Creator: {creator_score:,}")
                result["message"] = f"👻💀 SNIPE SUCCESSFUL! {chosen_gift} for {effective_points:,} effective!"
            else:
                remaining_deficit = creator_score - new_score
                print(f"   🎯 SNIPE: {chosen_gift}: {chosen_cost:,} × {effective_multiplier:.0f} = {effective_points:,}")
                print(f"   📊 Still behind by {remaining_deficit:,}")
                result["message"] = f"👻🎯 Snipe: {chosen_gift} for {effective_points:,}"

            # Check if we should mark snipe as executed
            # Don't execute again if we've used most of budget
            remaining = self.get_current_budget()
            if remaining < 1000 or time_remaining <= 1:
                self.snipe_executed = True
                print(f"   ✅ Snipe sequence complete. Remaining budget: {remaining:,}")

            return result

        return None

    def get_stats(self) -> dict:
        """Get opponent stats for display."""
        stats = {
            "strategy": self.strategy.value,
            "total_donated": self.total_donated,
            "whale_gifts_sent": self.whale_gifts_sent,
            "gloves_used": self.gloves_used,
            "hammer_used": self.hammer_used,
            "fog_used": self.fog_used,
            "boost1_participated": self.boost1_participated,
            "boost2_participated": self.boost2_participated,
            "snipe_mode_activated": self.snipe_mode_active,
            # Surrender info
            "surrendered": self.has_surrendered,
            "surrender_time": self.surrender_time,
            "surrender_reason": self.surrender_reason,
        }

        # Add strategic intelligence analytics if available
        if self.strategic_intel:
            stats["strategic_analytics"] = self.strategic_intel.get_analytics()

        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM OPPONENT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class OpponentBuilder:
    """
    Build custom opponent strategies with fine-grained control.

    Usage:
        builder = OpponentBuilder("My Sniper Pro")
        builder.set_aggression(normal=0.1, boost1=0.2, final_5s=0.99)
        builder.set_whale_chances(normal=0.01, final=0.5)
        builder.set_glove_timing(boost2=0.9, final_5s=0.95)
        builder.set_reserves(boost2=0.3, snipe=0.4)

        opponent = builder.build(phase_manager, budget_manager)
    """

    # Preset templates for quick customization
    PRESETS = {
        "balanced": {
            "description": "Well-rounded strategy",
            "aggression": {"normal": 0.25, "boost1": 0.5, "boost2": 0.6, "final_30s": 0.5, "final_5s": 0.7},
            "whale": {"normal": 0.05, "boost": 0.2, "final": 0.25},
            "glove": {"boost1": 0.5, "boost2": 0.6, "final_30s": 0.5, "final_5s": 0.7},
            "reserve": {"boost2": 0.3, "snipe": 0.15}
        },
        "all_in_snipe": {
            "description": "Save everything for final 5 seconds",
            "aggression": {"normal": 0.05, "boost1": 0.1, "boost2": 0.15, "final_30s": 0.2, "final_5s": 0.99},
            "whale": {"normal": 0.01, "boost": 0.05, "final": 0.6},
            "glove": {"boost1": 0.1, "boost2": 0.1, "final_30s": 0.2, "final_5s": 0.99},
            "reserve": {"boost2": 0.1, "snipe": 0.6}
        },
        "boost_specialist": {
            "description": "Dominate during boost phases",
            "aggression": {"normal": 0.15, "boost1": 0.85, "boost2": 0.9, "final_30s": 0.5, "final_5s": 0.6},
            "whale": {"normal": 0.03, "boost": 0.4, "final": 0.2},
            "glove": {"boost1": 0.8, "boost2": 0.9, "final_30s": 0.4, "final_5s": 0.5},
            "reserve": {"boost2": 0.4, "snipe": 0.1}
        },
        "pressure_cooker": {
            "description": "Constant high pressure throughout",
            "aggression": {"normal": 0.5, "boost1": 0.7, "boost2": 0.75, "final_30s": 0.7, "final_5s": 0.8},
            "whale": {"normal": 0.15, "boost": 0.25, "final": 0.3},
            "glove": {"boost1": 0.6, "boost2": 0.6, "final_30s": 0.6, "final_5s": 0.6},
            "reserve": {"boost2": 0.2, "snipe": 0.1}
        },
        "whale_hunter": {
            "description": "Focus on sending whale gifts",
            "aggression": {"normal": 0.2, "boost1": 0.4, "boost2": 0.5, "final_30s": 0.5, "final_5s": 0.7},
            "whale": {"normal": 0.25, "boost": 0.5, "final": 0.6},
            "glove": {"boost1": 0.6, "boost2": 0.7, "final_30s": 0.5, "final_5s": 0.8},
            "reserve": {"boost2": 0.35, "snipe": 0.2}
        }
    }

    def __init__(self, name: str = "Custom Opponent"):
        """
        Initialize opponent builder.

        Args:
            name: Display name for this custom opponent
        """
        self.name = name
        self.description = "Custom strategy"

        # Start with balanced defaults
        self._aggression = PhaseAggression()
        self._budget_preference = "balanced"

    def from_preset(self, preset_name: str) -> 'OpponentBuilder':
        """
        Start from a preset template.

        Args:
            preset_name: One of "balanced", "all_in_snipe", "boost_specialist",
                        "pressure_cooker", "whale_hunter"
        """
        if preset_name not in self.PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(self.PRESETS.keys())}")

        preset = self.PRESETS[preset_name]
        self.description = preset["description"]

        # Apply preset values
        agg = preset["aggression"]
        self._aggression.normal = agg.get("normal", 0.25)
        self._aggression.boost1 = agg.get("boost1", 0.5)
        self._aggression.boost2 = agg.get("boost2", 0.6)
        self._aggression.final_30s = agg.get("final_30s", 0.5)
        self._aggression.final_5s = agg.get("final_5s", 0.7)

        whale = preset["whale"]
        self._aggression.whale_normal = whale.get("normal", 0.05)
        self._aggression.whale_boost = whale.get("boost", 0.2)
        self._aggression.whale_final = whale.get("final", 0.25)

        glove = preset["glove"]
        self._aggression.glove_in_boost1 = glove.get("boost1", 0.5)
        self._aggression.glove_in_boost2 = glove.get("boost2", 0.6)
        self._aggression.glove_in_final_30s = glove.get("final_30s", 0.5)
        self._aggression.glove_in_final_5s = glove.get("final_5s", 0.7)

        reserve = preset["reserve"]
        self._aggression.reserve_for_boost2 = reserve.get("boost2", 0.3)
        self._aggression.reserve_for_snipe = reserve.get("snipe", 0.15)

        return self

    def set_aggression(self, normal: float = None, boost1: float = None,
                       boost2: float = None, final_30s: float = None,
                       final_5s: float = None, x5_active: float = None) -> 'OpponentBuilder':
        """
        Set aggression levels for different phases (0-1 scale).

        Higher values = more likely to send gifts in that phase.
        """
        if normal is not None:
            self._aggression.normal = max(0, min(1, normal))
        if boost1 is not None:
            self._aggression.boost1 = max(0, min(1, boost1))
        if boost2 is not None:
            self._aggression.boost2 = max(0, min(1, boost2))
        if final_30s is not None:
            self._aggression.final_30s = max(0, min(1, final_30s))
        if final_5s is not None:
            self._aggression.final_5s = max(0, min(1, final_5s))
        if x5_active is not None:
            self._aggression.x5_active = max(0, min(1, x5_active))
        return self

    def set_whale_chances(self, normal: float = None, boost: float = None,
                          final: float = None, x5: float = None) -> 'OpponentBuilder':
        """
        Set whale gift probability for different phases (0-1 scale).

        Higher values = more likely to send expensive gifts.
        """
        if normal is not None:
            self._aggression.whale_normal = max(0, min(1, normal))
        if boost is not None:
            self._aggression.whale_boost = max(0, min(1, boost))
        if final is not None:
            self._aggression.whale_final = max(0, min(1, final))
        if x5 is not None:
            self._aggression.whale_x5 = max(0, min(1, x5))
        return self

    def set_glove_timing(self, boost1: float = None, boost2: float = None,
                         final_30s: float = None, final_5s: float = None) -> 'OpponentBuilder':
        """
        Set glove usage probability for different phases (0-1 scale).
        """
        if boost1 is not None:
            self._aggression.glove_in_boost1 = max(0, min(1, boost1))
        if boost2 is not None:
            self._aggression.glove_in_boost2 = max(0, min(1, boost2))
        if final_30s is not None:
            self._aggression.glove_in_final_30s = max(0, min(1, final_30s))
        if final_5s is not None:
            self._aggression.glove_in_final_5s = max(0, min(1, final_5s))
        return self

    def set_reserves(self, boost2: float = None, snipe: float = None) -> 'OpponentBuilder':
        """
        Set budget reserve ratios (0-1 scale).

        Higher values = save more budget for that phase.
        """
        if boost2 is not None:
            self._aggression.reserve_for_boost2 = max(0, min(0.6, boost2))
        if snipe is not None:
            self._aggression.reserve_for_snipe = max(0, min(0.6, snipe))
        return self

    def set_budget_preference(self, preference: str) -> 'OpponentBuilder':
        """
        Set budget tier preference: "limited", "balanced", "large", "random"
        """
        valid = ["limited", "balanced", "large", "random"]
        if preference not in valid:
            raise ValueError(f"Budget preference must be one of: {valid}")
        self._budget_preference = preference
        return self

    def preview(self) -> str:
        """Get a preview of the opponent configuration."""
        lines = [
            f"\n╔═══════════════════════════════════════════════════════════════╗",
            f"║  👻 CUSTOM OPPONENT: {self.name:<40} ║",
            f"║  📝 {self.description:<56} ║",
            f"╠═══════════════════════════════════════════════════════════════╣",
            f"║  📊 AGGRESSION LEVELS (chance to act per tick)               ║",
            f"║     Normal: {self._aggression.normal:>5.0%} │ Boost #1: {self._aggression.boost1:>5.0%} │ Boost #2: {self._aggression.boost2:>5.0%}  ║",
            f"║     Final 30s: {self._aggression.final_30s:>5.0%} │ Final 5s: {self._aggression.final_5s:>5.0%} │ x5 Active: {self._aggression.x5_active:>5.0%} ║",
            f"╠═══════════════════════════════════════════════════════════════╣",
            f"║  🐋 WHALE GIFT CHANCES                                        ║",
            f"║     Normal: {self._aggression.whale_normal:>5.0%} │ Boost: {self._aggression.whale_boost:>5.0%} │ Final: {self._aggression.whale_final:>5.0%}     ║",
            f"╠═══════════════════════════════════════════════════════════════╣",
            f"║  🥊 GLOVE TIMING                                              ║",
            f"║     Boost #1: {self._aggression.glove_in_boost1:>5.0%} │ Boost #2: {self._aggression.glove_in_boost2:>5.0%} │ Final 5s: {self._aggression.glove_in_final_5s:>5.0%} ║",
            f"╠═══════════════════════════════════════════════════════════════╣",
            f"║  💰 BUDGET RESERVES                                           ║",
            f"║     For Boost #2: {self._aggression.reserve_for_boost2:>5.0%} │ For Snipe: {self._aggression.reserve_for_snipe:>5.0%}            ║",
            f"╚═══════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)

    def build(self, phase_manager, budget_manager=None) -> OpponentAI:
        """
        Build the custom opponent AI.

        Args:
            phase_manager: AdvancedPhaseManager instance
            budget_manager: Optional BudgetManager instance

        Returns:
            OpponentAI configured with custom strategy
        """
        # Register custom strategy
        STRATEGY_PROFILES[StrategyProfile.CUSTOM] = self._aggression
        STRATEGY_BUDGET_PREFERENCES[StrategyProfile.CUSTOM] = self._budget_preference

        # Create opponent with custom strategy
        opponent = OpponentAI(
            phase_manager=phase_manager,
            budget_manager=budget_manager,
            strategy=StrategyProfile.CUSTOM
        )

        # Override the announcement
        print(f"\n👻 CUSTOM OPPONENT: {self.name}")
        print(f"   📝 {self.description}")

        return opponent

    def to_dict(self) -> Dict:
        """Export configuration to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "budget_preference": self._budget_preference,
            "aggression": {
                "normal": self._aggression.normal,
                "boost1": self._aggression.boost1,
                "boost2": self._aggression.boost2,
                "final_30s": self._aggression.final_30s,
                "final_5s": self._aggression.final_5s,
                "x5_active": self._aggression.x5_active,
            },
            "whale_chances": {
                "normal": self._aggression.whale_normal,
                "boost": self._aggression.whale_boost,
                "final": self._aggression.whale_final,
                "x5": self._aggression.whale_x5,
            },
            "glove_timing": {
                "boost1": self._aggression.glove_in_boost1,
                "boost2": self._aggression.glove_in_boost2,
                "final_30s": self._aggression.glove_in_final_30s,
                "final_5s": self._aggression.glove_in_final_5s,
            },
            "reserves": {
                "boost2": self._aggression.reserve_for_boost2,
                "snipe": self._aggression.reserve_for_snipe,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'OpponentBuilder':
        """Import configuration from dictionary."""
        builder = cls(name=data.get("name", "Custom"))
        builder.description = data.get("description", "Imported strategy")
        builder._budget_preference = data.get("budget_preference", "balanced")

        if "aggression" in data:
            builder.set_aggression(**data["aggression"])
        if "whale_chances" in data:
            builder.set_whale_chances(**data["whale_chances"])
        if "glove_timing" in data:
            builder.set_glove_timing(**data["glove_timing"])
        if "reserves" in data:
            builder.set_reserves(**data["reserves"])

        return builder

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"✅ Saved opponent config to: {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'OpponentBuilder':
        """Load configuration from JSON file."""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"📥 Loaded opponent config: {data.get('name', 'Unknown')}")
        return cls.from_dict(data)


# Helper function for quick custom opponent creation
def create_custom_opponent(
    name: str,
    phase_manager,
    budget_manager=None,
    preset: str = None,
    **overrides
) -> OpponentAI:
    """
    Quick helper to create a custom opponent.

    Args:
        name: Display name
        phase_manager: AdvancedPhaseManager
        budget_manager: Optional BudgetManager
        preset: Start from preset ("balanced", "all_in_snipe", etc.)
        **overrides: Override specific values

    Example:
        opponent = create_custom_opponent(
            "Snipe Master",
            phase_manager,
            preset="all_in_snipe",
            aggression_final_5s=0.99,
            whale_final=0.7
        )
    """
    builder = OpponentBuilder(name)

    if preset:
        builder.from_preset(preset)

    # Apply overrides
    aggression_keys = ["normal", "boost1", "boost2", "final_30s", "final_5s", "x5_active"]
    whale_keys = ["whale_normal", "whale_boost", "whale_final", "whale_x5"]
    glove_keys = ["glove_boost1", "glove_boost2", "glove_final_30s", "glove_final_5s"]
    reserve_keys = ["reserve_boost2", "reserve_snipe"]

    agg_overrides = {k.replace("aggression_", ""): v for k, v in overrides.items()
                     if k.replace("aggression_", "") in aggression_keys}
    whale_overrides = {k.replace("whale_", ""): v for k, v in overrides.items()
                       if k in whale_keys}
    glove_overrides = {k.replace("glove_", ""): v for k, v in overrides.items()
                       if k in glove_keys}
    reserve_overrides = {k.replace("reserve_", ""): v for k, v in overrides.items()
                         if k in reserve_keys}

    if agg_overrides:
        builder.set_aggression(**agg_overrides)
    if whale_overrides:
        builder.set_whale_chances(**{k.replace("whale_", ""): v for k, v in whale_overrides.items()})
    if glove_overrides:
        builder.set_glove_timing(**{k.replace("glove_", ""): v for k, v in glove_overrides.items()})
    if reserve_overrides:
        builder.set_reserves(**{k.replace("reserve_", ""): v for k, v in reserve_overrides.items()})

    print(builder.preview())
    return builder.build(phase_manager, budget_manager)
