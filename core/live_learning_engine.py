#!/usr/bin/env python3
"""
Live Learning Engine - Train AI agents on real TikTok battles

This module enables agents to learn from live battles using virtual gifts:
- Connects to real TikTok live streams
- Reads actual battle scores in real-time
- Agents make decisions as if they were sending real gifts
- Virtual gifts are tracked (no real spending)
- Learning persists across sessions
- Tracks real battle conditions (multipliers, power-ups)
- Simulates TikTok reward system
- Supports Best of X tournaments

The agents learn:
- Optimal gift timing based on score gaps
- Best strategies for different battle phases
- When to be aggressive vs defensive
- Snipe timing for final seconds
- Power-up usage optimization
- Multiplier exploitation
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Callable, Any
from pathlib import Path

from playwright.async_api import Page

# Import existing components
from core.ai_battle_controller import (
    BattleScoreReader,
    BattleScore,
    BattleState,
    AIStrategy
)
from core.battle_rewards_system import (
    BattleConditions,
    MultiplierState,
    MultiplierType,
    PowerUpType,
    PowerUpInventory,
    BattleRewardsEngine,
    BestOfTournament
)
from core.battle_conditions_reader import (
    BattleConditionsReader,
    EnhancedBattleReader
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveLearningEngine")


class TrainingMode(Enum):
    """Training operation modes."""
    OBSERVE_ONLY = "observe_only"      # Just watch and record
    VIRTUAL_GIFTS = "virtual_gifts"     # Simulate gift decisions
    SHADOW_MODE = "shadow_mode"         # Compare AI vs actual gifters


@dataclass
class VirtualGift:
    """A virtual gift decision (not actually sent)."""
    timestamp: datetime
    gift_name: str
    gift_cost: int
    quantity: int
    reason: str
    battle_state: str
    our_score: int
    opponent_score: int
    gap: int
    time_remaining: int
    would_have_points: int  # Points that would have been added

    # Battle conditions at time of decision
    our_multiplier: float = 1.0
    opponent_multiplier: float = 1.0
    boost_active: bool = False
    boost_phase: int = 0
    effective_points: int = 0  # Points with multiplier applied

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'gift_name': self.gift_name,
            'gift_cost': self.gift_cost,
            'quantity': self.quantity,
            'reason': self.reason,
            'battle_state': self.battle_state,
            'our_score': self.our_score,
            'opponent_score': self.opponent_score,
            'gap': self.gap,
            'time_remaining': self.time_remaining,
            'would_have_points': self.would_have_points,
            'our_multiplier': self.our_multiplier,
            'opponent_multiplier': self.opponent_multiplier,
            'boost_active': self.boost_active,
            'boost_phase': self.boost_phase,
            'effective_points': self.effective_points
        }


@dataclass
class VirtualPowerUpUsage:
    """A virtual power-up usage decision."""
    timestamp: datetime
    power_up_type: PowerUpType
    reason: str
    battle_state: str
    our_score: int
    opponent_score: int
    gap: int
    time_remaining: int
    opponent_multiplier: float = 1.0  # For hammer decisions

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'power_up_type': self.power_up_type.value,
            'reason': self.reason,
            'battle_state': self.battle_state,
            'our_score': self.our_score,
            'opponent_score': self.opponent_score,
            'gap': self.gap,
            'time_remaining': self.time_remaining,
            'opponent_multiplier': self.opponent_multiplier
        }


@dataclass
class BattleExperience:
    """A complete battle experience for learning."""
    battle_id: str
    streamer: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Score trajectory
    score_history: List[Dict] = field(default_factory=list)

    # Virtual gifts sent
    virtual_gifts: List[VirtualGift] = field(default_factory=list)

    # Virtual power-up usage
    virtual_power_ups: List[VirtualPowerUpUsage] = field(default_factory=list)

    # Battle conditions history
    conditions_history: List[Dict] = field(default_factory=list)

    # Outcome
    final_our_score: int = 0
    final_opponent_score: int = 0
    won: Optional[bool] = None

    # Strategy used
    strategy: str = "smart"

    # Learning metrics
    total_virtual_spent: int = 0
    total_virtual_points: int = 0
    total_effective_points: int = 0  # With multipliers
    decisions_made: int = 0
    aggressive_decisions: int = 0
    defensive_decisions: int = 0
    multiplier_decisions: int = 0  # Decisions during multiplier
    power_up_decisions: int = 0

    # Conditions tracking
    max_multiplier_used: float = 1.0
    boost_phases_seen: List[int] = field(default_factory=list)
    opponent_multipliers_seen: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'battle_id': self.battle_id,
            'streamer': self.streamer,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'score_history': self.score_history,
            'virtual_gifts': [g.to_dict() for g in self.virtual_gifts],
            'virtual_power_ups': [p.to_dict() for p in self.virtual_power_ups],
            'conditions_history': self.conditions_history,
            'final_our_score': self.final_our_score,
            'final_opponent_score': self.final_opponent_score,
            'won': self.won,
            'strategy': self.strategy,
            'total_virtual_spent': self.total_virtual_spent,
            'total_virtual_points': self.total_virtual_points,
            'total_effective_points': self.total_effective_points,
            'decisions_made': self.decisions_made,
            'aggressive_decisions': self.aggressive_decisions,
            'defensive_decisions': self.defensive_decisions,
            'multiplier_decisions': self.multiplier_decisions,
            'power_up_decisions': self.power_up_decisions,
            'max_multiplier_used': self.max_multiplier_used,
            'boost_phases_seen': self.boost_phases_seen,
            'opponent_multipliers_seen': self.opponent_multipliers_seen
        }


@dataclass
class AgentLearningState:
    """Persistent learning state for an agent."""
    agent_name: str
    agent_type: str

    # Experience counters
    total_battles: int = 0
    wins: int = 0
    losses: int = 0

    # Learning parameters (evolved over time)
    params: Dict = field(default_factory=dict)

    # Q-values for state-action pairs
    q_values: Dict = field(default_factory=dict)

    # Performance history
    recent_rewards: List[float] = field(default_factory=list)

    # Timing patterns learned
    best_gift_timings: Dict = field(default_factory=dict)  # state -> best_action

    def get_win_rate(self) -> float:
        if self.total_battles == 0:
            return 0.0
        return self.wins / self.total_battles

    def to_dict(self) -> Dict:
        return {
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'total_battles': self.total_battles,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': self.get_win_rate(),
            'params': self.params,
            'q_values': self.q_values,
            'recent_rewards': self.recent_rewards[-100:],  # Keep last 100
            'best_gift_timings': self.best_gift_timings
        }


class VirtualGiftDecider:
    """
    Makes virtual gift decisions based on battle state and conditions.

    This is the core AI that learns from live battles, considering:
    - Score gaps and time remaining
    - Active multipliers (x2, x3, x5)
    - Boost phases
    - Power-up availability
    """

    def __init__(self, strategy: AIStrategy = AIStrategy.SMART):
        self.strategy = strategy
        self.learning_state = AgentLearningState(
            agent_name="VirtualGiftDecider",
            agent_type="live_learner"
        )

        # Power-up inventory for virtual usage
        self.inventory = PowerUpInventory("ai_agent")

        # Default learnable parameters
        self.params = {
            'emergency_threshold': -5000,      # Gap to trigger emergency
            'comfortable_threshold': 3000,      # Gap for comfortable lead
            'snipe_window': 10,                 # Seconds for snipe mode
            'aggressive_multiplier': 1.5,       # Gift multiplier in aggressive mode
            'defensive_multiplier': 0.5,        # Gift multiplier in defensive mode
            'min_gap_to_send': 100,             # Minimum gap to trigger send
            # Multiplier-aware parameters
            'multiplier_boost_threshold': 2.0,  # Send more when we have x2+
            'counter_opponent_x5': True,        # Use hammer on opponent x5
            'use_glove_in_snipe': True,         # Use glove in final seconds
            'fog_lead_threshold': 5000,         # Use fog when ahead by this much
        }

        # Gift selection based on urgency
        self.gift_tiers = {
            'critical': [
                ('TikTok Universe', 44999),
                ('Lion', 29999),
                ('Dragon Flame', 10000),
            ],
            'high': [
                ('Dragon Flame', 10000),
                ('GG', 1000),
                ('Rosa Nebula', 299),
            ],
            'medium': [
                ('Rosa Nebula', 299),
                ('Cap', 99),
                ('Fest Pop', 39),
            ],
            'low': [
                ('Fest Pop', 39),
                ('Doughnut', 30),
                ('Rose', 1),
            ],
            # Multiplier-optimized tiers (bigger gifts during multipliers)
            'multiplier_critical': [
                ('TikTok Universe', 44999),
                ('Lion', 29999),
            ],
            'multiplier_high': [
                ('Lion', 29999),
                ('Dragon Flame', 10000),
            ]
        }

        # Current conditions cache
        self._current_conditions: Optional[BattleConditions] = None

    def set_conditions(self, conditions: BattleConditions):
        """Update current battle conditions."""
        self._current_conditions = conditions

    def decide(
        self,
        score: BattleScore,
        state: BattleState,
        conditions: BattleConditions = None
    ) -> Optional[VirtualGift]:
        """
        Decide whether to send a virtual gift.

        Args:
            score: Current battle score
            state: Current battle state
            conditions: Current battle conditions (multipliers, power-ups)

        Returns VirtualGift if should send, None otherwise.
        """
        if not score.battle_active:
            return None

        # Use provided conditions or cached
        cond = conditions or self._current_conditions or BattleConditions()

        # Determine urgency (conditions-aware)
        urgency = self._calculate_urgency(score, state, cond)

        # Get decision based on strategy
        if self.strategy == AIStrategy.SMART:
            return self._smart_decision(score, state, urgency, cond)
        elif self.strategy == AIStrategy.AGGRESSIVE:
            return self._aggressive_decision(score, state, urgency, cond)
        elif self.strategy == AIStrategy.DEFENSIVE:
            return self._defensive_decision(score, state, urgency, cond)
        elif self.strategy == AIStrategy.SNIPER:
            return self._sniper_decision(score, state, urgency, cond)
        else:  # CONSERVATIVE
            return self._conservative_decision(score, state, urgency, cond)

    def decide_power_up(
        self,
        score: BattleScore,
        state: BattleState,
        conditions: BattleConditions = None
    ) -> Optional[VirtualPowerUpUsage]:
        """
        Decide whether to use a power-up.

        Returns VirtualPowerUpUsage if should use, None otherwise.
        """
        if not score.battle_active:
            return None

        cond = conditions or self._current_conditions or BattleConditions()
        gap = score.gap
        time_remaining = score.time_remaining

        # HAMMER: Counter opponent's x5
        if (self.params['counter_opponent_x5'] and
            cond.opponent_multiplier.active and
            cond.opponent_multiplier.type == MultiplierType.X5 and
            self.inventory.get_available(PowerUpType.HAMMER) > 0):

            self.inventory.use_power_up(PowerUpType.HAMMER)
            return VirtualPowerUpUsage(
                timestamp=datetime.now(),
                power_up_type=PowerUpType.HAMMER,
                reason=f"Counter opponent x5! (gap: {gap:+,})",
                battle_state=state.value,
                our_score=score.our_score,
                opponent_score=score.opponent_score,
                gap=gap,
                time_remaining=time_remaining,
                opponent_multiplier=cond.opponent_multiplier.get_value()
            )

        # GLOVE: Use in snipe window for x5
        if (self.params['use_glove_in_snipe'] and
            time_remaining <= self.params['snipe_window'] and
            not cond.creator_multiplier.active and
            self.inventory.get_available(PowerUpType.GLOVE) > 0):

            self.inventory.use_power_up(PowerUpType.GLOVE)
            return VirtualPowerUpUsage(
                timestamp=datetime.now(),
                power_up_type=PowerUpType.GLOVE,
                reason=f"Snipe mode x5! ({time_remaining}s left)",
                battle_state=state.value,
                our_score=score.our_score,
                opponent_score=score.opponent_score,
                gap=gap,
                time_remaining=time_remaining
            )

        # FOG: Hide lead in final seconds
        if (gap >= self.params['fog_lead_threshold'] and
            time_remaining <= 30 and
            self.inventory.get_available(PowerUpType.FOG) > 0):

            self.inventory.use_power_up(PowerUpType.FOG)
            return VirtualPowerUpUsage(
                timestamp=datetime.now(),
                power_up_type=PowerUpType.FOG,
                reason=f"Hide lead of {gap:,} in final {time_remaining}s",
                battle_state=state.value,
                our_score=score.our_score,
                opponent_score=score.opponent_score,
                gap=gap,
                time_remaining=time_remaining
            )

        # TIME BONUS: Use in last 5 seconds if behind
        if (time_remaining <= 5 and gap < 0 and
            self.inventory.get_available(PowerUpType.TIME_BONUS) > 0):

            self.inventory.use_power_up(PowerUpType.TIME_BONUS)
            return VirtualPowerUpUsage(
                timestamp=datetime.now(),
                power_up_type=PowerUpType.TIME_BONUS,
                reason=f"Need more time! Behind by {abs(gap):,}",
                battle_state=state.value,
                our_score=score.our_score,
                opponent_score=score.opponent_score,
                gap=gap,
                time_remaining=time_remaining
            )

        return None

    def _calculate_urgency(
        self,
        score: BattleScore,
        state: BattleState,
        conditions: BattleConditions = None
    ) -> str:
        """Calculate urgency level based on score, time, and conditions."""
        gap = score.gap
        time_remaining = score.time_remaining
        cond = conditions or BattleConditions()

        # If opponent has multiplier advantage, increase urgency
        opponent_mult = cond.opponent_multiplier.get_value()
        our_mult = cond.creator_multiplier.get_value()

        # Adjust gap perception based on multiplier disadvantage
        effective_gap = gap
        if opponent_mult > our_mult:
            # Opponent earning faster, situation is worse
            effective_gap = gap - (opponent_mult - our_mult) * 1000

        # Critical: Behind significantly OR opponent has x5 OR final seconds
        if effective_gap < self.params['emergency_threshold']:
            return 'critical'
        if opponent_mult >= 5.0 and gap < 0:
            return 'critical'
        if time_remaining <= 10 and gap < 0:
            return 'critical'

        # High: Behind and time running out OR opponent has multiplier
        if effective_gap < -1000 and time_remaining <= 60:
            return 'high'
        if gap < 0 and time_remaining <= 30:
            return 'high'
        if opponent_mult >= 3.0 and gap < 0:
            return 'high'

        # Multiplier opportunity: We have multiplier, send more
        if our_mult >= self.params['multiplier_boost_threshold']:
            if gap >= 0:
                return 'multiplier_high'  # Extend lead with multiplier
            else:
                return 'critical'  # Catch up with multiplier

        # Medium: Close battle or boost active
        if abs(gap) < self.params['comfortable_threshold']:
            return 'medium'
        if cond.boost_active:
            return 'medium'  # Take advantage of boost

        # Low: Comfortable lead
        return 'low'

    def _select_gift(self, urgency: str, conditions: BattleConditions = None) -> tuple:
        """Select appropriate gift based on urgency and conditions."""
        cond = conditions or BattleConditions()

        # Use multiplier-optimized tiers when we have multiplier
        our_mult = cond.creator_multiplier.get_value()
        if our_mult >= 3.0:
            if urgency in ['critical', 'multiplier_critical']:
                tier_key = 'multiplier_critical'
            elif urgency in ['high', 'multiplier_high']:
                tier_key = 'multiplier_high'
            else:
                tier_key = urgency
        else:
            tier_key = urgency

        tier = self.gift_tiers.get(tier_key, self.gift_tiers['medium'])
        return tier[0]

    def _smart_decision(
        self,
        score: BattleScore,
        state: BattleState,
        urgency: str,
        conditions: BattleConditions
    ) -> Optional[VirtualGift]:
        """Smart strategy: Adapt based on situation and conditions."""
        gap = score.gap
        our_mult = conditions.creator_multiplier.get_value()

        # Always send in critical
        if urgency == 'critical':
            gift_name, gift_cost = self._select_gift('critical', conditions)
            reason = f"CRITICAL: Behind by {abs(gap):,}!"
            if our_mult > 1:
                reason += f" (x{our_mult:.0f} active)"
            return self._create_virtual_gift(
                gift_name, gift_cost, 1, reason,
                score, state, conditions
            )

        # Multiplier opportunity
        if urgency in ['multiplier_high', 'multiplier_critical']:
            gift_name, gift_cost = self._select_gift(urgency, conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"MULTIPLIER x{our_mult:.0f}: Maximize points!",
                score, state, conditions
            )

        # Send in high urgency
        if urgency == 'high':
            gift_name, gift_cost = self._select_gift('high', conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"High urgency: Gap {gap:+,}",
                score, state, conditions
            )

        # Boost phase: send more frequently
        if conditions.boost_active and score.time_remaining % 5 == 0:
            gift_name, gift_cost = self._select_gift('medium', conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"Boost phase {conditions.boost_phase}: x{conditions.boost_multiplier}",
                score, state, conditions
            )

        # Medium: occasional sends
        if urgency == 'medium' and score.time_remaining % 10 == 0:
            gift_name, gift_cost = self._select_gift('medium', conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"Maintaining position: Gap {gap:+,}",
                score, state, conditions
            )

        return None

    def _aggressive_decision(
        self,
        score: BattleScore,
        state: BattleState,
        urgency: str,
        conditions: BattleConditions
    ) -> Optional[VirtualGift]:
        """Aggressive strategy: Always push for lead, maximize multipliers."""
        gap = score.gap
        our_mult = conditions.creator_multiplier.get_value()

        # Always send something, bigger gifts during multiplier
        if urgency in ['critical', 'high'] or our_mult >= 2:
            gift_name, gift_cost = self._select_gift('critical', conditions)
        else:
            gift_name, gift_cost = self._select_gift('high', conditions)

        reason = f"AGGRESSIVE: Pushing lead! Gap {gap:+,}"
        if our_mult > 1:
            reason = f"AGGRESSIVE x{our_mult:.0f}: Maximum pressure!"

        return self._create_virtual_gift(
            gift_name, gift_cost, 1, reason,
            score, state, conditions
        )

    def _defensive_decision(
        self,
        score: BattleScore,
        state: BattleState,
        urgency: str,
        conditions: BattleConditions
    ) -> Optional[VirtualGift]:
        """Defensive strategy: Only send when behind, counter opponent multipliers."""
        gap = score.gap
        opponent_mult = conditions.opponent_multiplier.get_value()

        # Counter when opponent has multiplier
        if opponent_mult >= 3.0:
            gift_name, gift_cost = self._select_gift('high', conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"DEFENSIVE: Counter opponent x{opponent_mult:.0f}!",
                score, state, conditions
            )

        if gap >= 0:
            return None  # Don't send when ahead

        if urgency in ['critical', 'high']:
            gift_name, gift_cost = self._select_gift(urgency, conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"DEFENSIVE: Counter-attack! Gap {gap:+,}",
                score, state, conditions
            )

        return None

    def _sniper_decision(
        self,
        score: BattleScore,
        state: BattleState,
        urgency: str,
        conditions: BattleConditions
    ) -> Optional[VirtualGift]:
        """Sniper strategy: Wait for final moments, maximize with x5."""
        time_remaining = score.time_remaining
        our_mult = conditions.creator_multiplier.get_value()

        if time_remaining > self.params['snipe_window']:
            return None  # Wait for snipe window

        # In snipe window: go all out with biggest gifts
        gift_name, gift_cost = self._select_gift('critical', conditions)

        reason = f"SNIPE: {time_remaining}s left!"
        if our_mult >= 5:
            reason = f"SNIPE x{our_mult:.0f}: KILLING BLOW!"

        return self._create_virtual_gift(
            gift_name, gift_cost, 1, reason,
            score, state, conditions
        )

    def _conservative_decision(
        self,
        score: BattleScore,
        state: BattleState,
        urgency: str,
        conditions: BattleConditions
    ) -> Optional[VirtualGift]:
        """Conservative strategy: Minimal intervention, only multiplier opportunities."""
        our_mult = conditions.creator_multiplier.get_value()

        # Send during high multiplier even in conservative mode
        if our_mult >= 5:
            gift_name, gift_cost = self._select_gift('high', conditions)
            return self._create_virtual_gift(
                gift_name, gift_cost, 1,
                f"CONSERVATIVE: x{our_mult:.0f} opportunity!",
                score, state, conditions
            )

        if urgency != 'critical':
            return None

        gift_name, gift_cost = self._select_gift('medium', conditions)
        return self._create_virtual_gift(
            gift_name, gift_cost, 1,
            f"CONSERVATIVE: Emergency only! Gap {score.gap:+,}",
            score, state, conditions
        )

    def _create_virtual_gift(
        self,
        gift_name: str,
        gift_cost: int,
        quantity: int,
        reason: str,
        score: BattleScore,
        state: BattleState,
        conditions: BattleConditions = None
    ) -> VirtualGift:
        """Create a virtual gift record with conditions."""
        cond = conditions or BattleConditions()
        our_mult = cond.creator_multiplier.get_value()
        effective_points = int(gift_cost * quantity * our_mult)

        return VirtualGift(
            timestamp=datetime.now(),
            gift_name=gift_name,
            gift_cost=gift_cost,
            quantity=quantity,
            reason=reason,
            battle_state=state.value,
            our_score=score.our_score,
            opponent_score=score.opponent_score,
            gap=score.gap,
            time_remaining=score.time_remaining,
            would_have_points=gift_cost * quantity,
            our_multiplier=our_mult,
            opponent_multiplier=cond.opponent_multiplier.get_value(),
            boost_active=cond.boost_active,
            boost_phase=cond.boost_phase,
            effective_points=effective_points
        )

    def learn_from_battle(self, experience: BattleExperience) -> float:
        """
        Learn from a completed battle experience.

        Returns reward value for this battle.
        """
        won = experience.won

        # Update win/loss counts
        self.learning_state.total_battles += 1
        if won:
            self.learning_state.wins += 1
        else:
            self.learning_state.losses += 1

        # Calculate reward
        reward = self._calculate_reward(experience)
        self.learning_state.recent_rewards.append(reward)

        # Update parameters based on outcome
        self._update_params(experience, reward)

        # Update Q-values for state-action pairs
        self._update_q_values(experience, reward)

        return reward

    def _calculate_reward(self, exp: BattleExperience) -> float:
        """Calculate learning reward from battle."""
        reward = 0.0

        # Win/loss base reward
        if exp.won:
            reward += 1.0
        else:
            reward -= 0.5

        # Efficiency bonus: won with less spending
        if exp.won and exp.total_virtual_spent > 0:
            efficiency = exp.final_our_score / exp.total_virtual_spent
            reward += min(0.5, efficiency * 0.1)

        # Close battle bonus
        final_gap = exp.final_our_score - exp.final_opponent_score
        if abs(final_gap) < 5000:
            reward += 0.2  # Close battles are more informative

        return reward

    def _update_params(self, exp: BattleExperience, reward: float):
        """Update learning parameters based on experience."""
        # If lost while being aggressive, reduce aggression
        if not exp.won and exp.aggressive_decisions > exp.defensive_decisions:
            self.params['aggressive_multiplier'] *= 0.95
            self.params['min_gap_to_send'] = min(500, self.params['min_gap_to_send'] + 50)

        # If lost while being defensive, increase responsiveness
        if not exp.won and exp.defensive_decisions > exp.aggressive_decisions:
            self.params['emergency_threshold'] = max(-3000, self.params['emergency_threshold'] + 500)

        # If won with sniping, reinforce snipe window
        snipe_gifts = [g for g in exp.virtual_gifts if g.time_remaining <= 10]
        if exp.won and len(snipe_gifts) > 0:
            self.params['snipe_window'] = min(15, self.params['snipe_window'] + 1)

    def _update_q_values(self, exp: BattleExperience, reward: float):
        """Update Q-values for state-action pairs."""
        learning_rate = 0.1
        discount = 0.9

        for gift in exp.virtual_gifts:
            # Create state key
            state_key = f"{gift.battle_state}_{gift.gap // 1000}k_{gift.time_remaining // 30}phase"
            action_key = gift.gift_name

            # Get current Q-value
            current_q = self.learning_state.q_values.get(state_key, {}).get(action_key, 0.0)

            # Update Q-value
            new_q = current_q + learning_rate * (reward - current_q)

            if state_key not in self.learning_state.q_values:
                self.learning_state.q_values[state_key] = {}
            self.learning_state.q_values[state_key][action_key] = new_q


class LiveLearningEngine:
    """
    Main engine for training AI agents on live TikTok battles.

    Usage:
        engine = LiveLearningEngine(page)
        await engine.train_on_stream("@username", duration=300)
    """

    def __init__(
        self,
        page: Page,
        strategy: AIStrategy = AIStrategy.SMART,
        mode: TrainingMode = TrainingMode.VIRTUAL_GIFTS
    ):
        self.page = page
        self.strategy = strategy
        self.mode = mode

        # Components
        self.score_reader = BattleScoreReader(page)
        self.gift_decider = VirtualGiftDecider(strategy)

        # Current battle tracking
        self.current_experience: Optional[BattleExperience] = None
        self.battle_count = 0

        # Callbacks
        self._on_virtual_gift: List[Callable] = []
        self._on_battle_end: List[Callable] = []
        self._on_learning_update: List[Callable] = []

        # State
        self._running = False
        self._paused = False

        # Persistence
        self.data_dir = Path("data/learning")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def on_virtual_gift(self, callback: Callable[[VirtualGift], Any]):
        """Register callback for virtual gift decisions."""
        self._on_virtual_gift.append(callback)
        return self

    def on_battle_end(self, callback: Callable[[BattleExperience], Any]):
        """Register callback for battle end."""
        self._on_battle_end.append(callback)
        return self

    def on_learning_update(self, callback: Callable[[Dict], Any]):
        """Register callback for learning updates."""
        self._on_learning_update.append(callback)
        return self

    async def train_on_stream(
        self,
        username: str,
        duration: int = 300,
        save_experiences: bool = True
    ) -> Dict:
        """
        Train on a live stream for specified duration.

        Args:
            username: Streamer to watch
            duration: Training duration in seconds
            save_experiences: Whether to save battle experiences

        Returns:
            Training statistics
        """
        logger.info(f"""
{'='*60}
LIVE LEARNING ENGINE - TRAINING MODE
{'='*60}
Streamer: @{username}
Strategy: {self.strategy.value}
Mode: {self.mode.value}
Duration: {duration}s

NOTE: Virtual gifts only - no real spending!
{'='*60}
        """)

        self._running = True
        self._paused = False
        start_time = datetime.now()
        last_battle_active = False

        stats = {
            'battles_observed': 0,
            'virtual_gifts_decided': 0,
            'total_virtual_spent': 0,
            'decisions_per_battle': [],
            'learning_updates': 0
        }

        while self._running:
            elapsed = (datetime.now() - start_time).seconds
            if elapsed >= duration:
                logger.info("Training duration reached")
                break

            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                # Read current score
                score = await self.score_reader.read_score()
                state = await self.score_reader.detect_battle_state()

                # Detect battle start
                if score.battle_active and not last_battle_active:
                    self._start_new_battle(username, score)
                    stats['battles_observed'] += 1
                    logger.info(f"Battle #{stats['battles_observed']} started!")

                # Detect battle end
                if not score.battle_active and last_battle_active:
                    await self._end_battle(score, save_experiences)
                    if self.current_experience:
                        stats['decisions_per_battle'].append(
                            self.current_experience.decisions_made
                        )
                        stats['learning_updates'] += 1

                last_battle_active = score.battle_active

                # Record score history
                if score.battle_active and self.current_experience:
                    self.current_experience.score_history.append({
                        'time': datetime.now().isoformat(),
                        'our_score': score.our_score,
                        'opponent_score': score.opponent_score,
                        'gap': score.gap,
                        'time_remaining': score.time_remaining
                    })

                    # Make virtual gift decision
                    if self.mode in [TrainingMode.VIRTUAL_GIFTS, TrainingMode.SHADOW_MODE]:
                        virtual_gift = self.gift_decider.decide(score, state)

                        if virtual_gift:
                            self._record_virtual_gift(virtual_gift)
                            stats['virtual_gifts_decided'] += 1
                            stats['total_virtual_spent'] += virtual_gift.gift_cost

                            # Log decision
                            logger.info(
                                f"[VIRTUAL] {virtual_gift.gift_name} ({virtual_gift.gift_cost:,} coins) - "
                                f"{virtual_gift.reason}"
                            )

                            # Emit callback
                            for cb in self._on_virtual_gift:
                                try:
                                    result = cb(virtual_gift)
                                    if asyncio.iscoroutine(result):
                                        await result
                                except Exception as e:
                                    logger.error(f"Virtual gift callback error: {e}")

                # Status update every 30 seconds
                if elapsed > 0 and elapsed % 30 == 0:
                    logger.info(
                        f"Training: {elapsed}s elapsed | "
                        f"Battles: {stats['battles_observed']} | "
                        f"Virtual gifts: {stats['virtual_gifts_decided']}"
                    )

                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Training loop error: {e}")
                await asyncio.sleep(5)

        self._running = False

        # Final stats
        total_time = (datetime.now() - start_time).seconds

        logger.info(f"""
{'='*60}
TRAINING SESSION COMPLETE
{'='*60}
Duration: {total_time}s
Battles observed: {stats['battles_observed']}
Virtual gifts decided: {stats['virtual_gifts_decided']}
Total virtual spent: {stats['total_virtual_spent']:,} coins
Learning updates: {stats['learning_updates']}
Win rate: {self.gift_decider.learning_state.get_win_rate()*100:.1f}%
{'='*60}
        """)

        return stats

    def _start_new_battle(self, username: str, score: BattleScore):
        """Start tracking a new battle."""
        self.battle_count += 1
        self.current_experience = BattleExperience(
            battle_id=f"battle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.battle_count}",
            streamer=username,
            start_time=datetime.now(),
            strategy=self.strategy.value
        )

        # Initial score
        self.current_experience.score_history.append({
            'time': datetime.now().isoformat(),
            'our_score': score.our_score,
            'opponent_score': score.opponent_score,
            'gap': score.gap,
            'time_remaining': score.time_remaining
        })

    def _record_virtual_gift(self, gift: VirtualGift):
        """Record a virtual gift decision."""
        if not self.current_experience:
            return

        self.current_experience.virtual_gifts.append(gift)
        self.current_experience.total_virtual_spent += gift.gift_cost
        self.current_experience.total_virtual_points += gift.would_have_points
        self.current_experience.decisions_made += 1

        # Track decision type
        if "AGGRESSIVE" in gift.reason or "CRITICAL" in gift.reason:
            self.current_experience.aggressive_decisions += 1
        else:
            self.current_experience.defensive_decisions += 1

    async def _end_battle(self, score: BattleScore, save: bool):
        """End current battle and learn from it."""
        if not self.current_experience:
            return

        # Record final state
        self.current_experience.end_time = datetime.now()
        self.current_experience.final_our_score = score.our_score
        self.current_experience.final_opponent_score = score.opponent_score
        self.current_experience.won = score.our_score > score.opponent_score

        # Learn from experience
        reward = self.gift_decider.learn_from_battle(self.current_experience)

        logger.info(
            f"Battle ended: {'WIN' if self.current_experience.won else 'LOSS'} | "
            f"Score: {score.our_score:,} vs {score.opponent_score:,} | "
            f"Reward: {reward:.2f}"
        )

        # Save experience
        if save:
            self._save_experience(self.current_experience)

        # Emit callbacks
        for cb in self._on_battle_end:
            try:
                result = cb(self.current_experience)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Battle end callback error: {e}")

        # Emit learning update
        learning_state = self.gift_decider.learning_state.to_dict()
        for cb in self._on_learning_update:
            try:
                result = cb(learning_state)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Learning update callback error: {e}")

    def _save_experience(self, exp: BattleExperience):
        """Save battle experience to disk."""
        filepath = self.data_dir / f"{exp.battle_id}.json"
        with open(filepath, 'w') as f:
            json.dump(exp.to_dict(), f, indent=2)
        logger.info(f"Experience saved: {filepath}")

    def save_learning_state(self):
        """Save current learning state."""
        filepath = self.data_dir / "learning_state.json"
        with open(filepath, 'w') as f:
            json.dump(self.gift_decider.learning_state.to_dict(), f, indent=2)
        logger.info(f"Learning state saved: {filepath}")

    def load_learning_state(self) -> bool:
        """Load previous learning state."""
        filepath = self.data_dir / "learning_state.json"
        if not filepath.exists():
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            state = self.gift_decider.learning_state
            state.total_battles = data.get('total_battles', 0)
            state.wins = data.get('wins', 0)
            state.losses = data.get('losses', 0)
            state.params = data.get('params', {})
            state.q_values = data.get('q_values', {})
            state.recent_rewards = data.get('recent_rewards', [])

            logger.info(
                f"Loaded learning state: {state.total_battles} battles, "
                f"{state.get_win_rate()*100:.1f}% win rate"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load learning state: {e}")
            return False

    def pause(self):
        """Pause training."""
        self._paused = True
        logger.info("Training paused")

    def resume(self):
        """Resume training."""
        self._paused = False
        logger.info("Training resumed")

    def stop(self):
        """Stop training."""
        self._running = False
        logger.info("Training stopping...")

    def get_learning_stats(self) -> Dict:
        """Get current learning statistics."""
        state = self.gift_decider.learning_state
        return {
            'total_battles': state.total_battles,
            'wins': state.wins,
            'losses': state.losses,
            'win_rate': state.get_win_rate(),
            'params': self.gift_decider.params,
            'strategy': self.strategy.value,
            'mode': self.mode.value
        }


# === Convenience Functions ===

async def train_on_live(
    page: Page,
    username: str,
    strategy: str = "smart",
    duration: int = 300
) -> Dict:
    """
    Quick start live training.

    Args:
        page: Playwright page connected to TikTok
        username: Streamer to watch
        strategy: AI strategy to use
        duration: Training duration in seconds

    Returns:
        Training statistics
    """
    try:
        strat = AIStrategy(strategy.lower())
    except:
        strat = AIStrategy.SMART

    engine = LiveLearningEngine(page, strategy=strat)
    engine.load_learning_state()

    try:
        stats = await engine.train_on_stream(username, duration)
        engine.save_learning_state()
        return stats
    except Exception as e:
        logger.error(f"Training error: {e}")
        return {'error': str(e)}
