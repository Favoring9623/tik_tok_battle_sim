#!/usr/bin/env python3
"""
Battle Conditions Reader

Reads real-time battle conditions from TikTok Live:
- Active multipliers (x2, x3, x5)
- Power-up usage (gloves, hammers, fog)
- Boost phases
- Time remaining with bonuses

This module extends the score reader to capture the full battle state.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from enum import Enum

from playwright.async_api import Page

from core.battle_rewards_system import (
    BattleConditions,
    MultiplierState,
    MultiplierType,
    PowerUpType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BattleConditionsReader")


@dataclass
class DetectedPowerUp:
    """A power-up detected on screen."""
    type: PowerUpType
    owner: str  # "creator" or "opponent"
    active: bool
    remaining_time: Optional[float] = None
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class DetectedMultiplier:
    """A multiplier detected on screen."""
    value: float  # 2.0, 3.0, 5.0
    owner: str
    source: str  # "boost", "glove", "system"
    detected_at: datetime = field(default_factory=datetime.now)


class BattleConditionsReader:
    """
    Reads battle conditions from TikTok Live page.

    Detects:
    - Multiplier indicators (x2, x3, x5)
    - Power-up icons and timers
    - Boost phase indicators
    - Fog effects
    """

    def __init__(self, page: Page):
        self.page = page

        # Cached conditions
        self._last_conditions: Optional[BattleConditions] = None
        self._last_read_time: Optional[datetime] = None

        # Detection history
        self._multiplier_history: List[DetectedMultiplier] = []
        self._power_up_history: List[DetectedPowerUp] = []

        # JavaScript for reading conditions
        self._js_read_conditions = """
        () => {
            const result = {
                multipliers: [],
                powerUps: [],
                boostActive: false,
                boostPhase: 0,
                fogActive: false,
                timeBonus: false
            };

            // Look for multiplier indicators (x2, x3, x5)
            const allText = document.body.innerText;

            // Check for x5 (glove active)
            if (allText.includes('x5') || allText.includes('×5')) {
                result.multipliers.push({value: 5, source: 'glove'});
            }

            // Check for x3 (boost phase 2)
            if (allText.includes('x3') || allText.includes('×3')) {
                result.multipliers.push({value: 3, source: 'boost'});
                result.boostPhase = 2;
                result.boostActive = true;
            }

            // Check for x2 (boost phase 1)
            if (allText.includes('x2') || allText.includes('×2')) {
                result.multipliers.push({value: 2, source: 'boost'});
                result.boostPhase = 1;
                result.boostActive = true;
            }

            // Look for power-up indicators
            // Glove icon/text
            const gloveElements = document.querySelectorAll('[class*="glove"], [class*="punch"]');
            if (gloveElements.length > 0) {
                result.powerUps.push({type: 'glove', active: true});
            }

            // Hammer icon/text
            if (allText.toLowerCase().includes('hammer') || allText.includes('🔨')) {
                result.powerUps.push({type: 'hammer', active: true});
            }

            // Fog icon/text
            if (allText.toLowerCase().includes('fog') || allText.includes('🌫')) {
                result.fogActive = true;
                result.powerUps.push({type: 'fog', active: true});
            }

            // Time bonus indicator
            if (allText.includes('+30') || allText.includes('bonus')) {
                result.timeBonus = true;
                result.powerUps.push({type: 'time_bonus', active: true});
            }

            // Look for BOOST text indicators
            if (allText.toUpperCase().includes('BOOST')) {
                result.boostActive = true;
            }

            return result;
        }
        """

        self._js_read_multiplier_display = """
        () => {
            // Look for multiplier display elements
            const elements = document.querySelectorAll('*');
            const multipliers = [];

            for (const el of elements) {
                const text = el.innerText?.trim() || '';
                // Match x2, x3, x5, ×2, ×3, ×5
                const match = text.match(/[x×]([235])/i);
                if (match) {
                    const rect = el.getBoundingClientRect();
                    // Only consider visible elements in battle area
                    if (rect.y > 0 && rect.y < 200 && rect.width > 0) {
                        multipliers.push({
                            value: parseInt(match[1]),
                            x: rect.x,
                            y: rect.y,
                            text: text
                        });
                    }
                }
            }

            return multipliers;
        }
        """

    async def read_conditions(self) -> BattleConditions:
        """
        Read current battle conditions from page.

        Returns:
            BattleConditions with detected state
        """
        conditions = BattleConditions()

        try:
            # Read raw conditions
            raw = await self.page.evaluate(self._js_read_conditions)

            # Parse multipliers
            for mult in raw.get('multipliers', []):
                value = mult.get('value', 1)
                source = mult.get('source', 'unknown')

                if value == 5:
                    # x5 from glove
                    conditions.creator_multiplier = MultiplierState(
                        active=True,
                        type=MultiplierType.X5,
                        owner="unknown",  # Can't always determine owner
                        source="glove"
                    )
                elif value == 3:
                    conditions.boost_active = True
                    conditions.boost_multiplier = 3.0
                    conditions.boost_phase = 2
                elif value == 2:
                    conditions.boost_active = True
                    conditions.boost_multiplier = 2.0
                    conditions.boost_phase = 1

            # Parse power-ups
            conditions.fog_active = raw.get('fogActive', False)

            # Try to read multiplier display for more accuracy
            multiplier_elements = await self.page.evaluate(self._js_read_multiplier_display)

            for mult in multiplier_elements:
                value = mult.get('value', 1)
                x_pos = mult.get('x', 0)

                # Determine owner based on x position
                # Left side (x < 640) = creator, right side = opponent
                owner = "creator" if x_pos < 640 else "opponent"

                detected = DetectedMultiplier(
                    value=float(value),
                    owner=owner,
                    source="display"
                )
                self._multiplier_history.append(detected)

                # Update conditions based on position
                if value == 5:
                    if owner == "creator":
                        conditions.creator_multiplier = MultiplierState(
                            active=True,
                            type=MultiplierType.X5,
                            owner=owner,
                            source="glove"
                        )
                    else:
                        conditions.opponent_multiplier = MultiplierState(
                            active=True,
                            type=MultiplierType.X5,
                            owner=owner,
                            source="glove"
                        )

            self._last_conditions = conditions
            self._last_read_time = datetime.now()

            return conditions

        except Exception as e:
            logger.error(f"Error reading conditions: {e}")
            return conditions

    async def detect_power_up_usage(self) -> List[DetectedPowerUp]:
        """
        Detect recent power-up usage.

        Returns:
            List of detected power-ups
        """
        detected = []

        try:
            raw = await self.page.evaluate(self._js_read_conditions)

            for pu in raw.get('powerUps', []):
                pu_type_str = pu.get('type', '')
                if pu_type_str:
                    try:
                        pu_type = PowerUpType(pu_type_str)
                        detected_pu = DetectedPowerUp(
                            type=pu_type,
                            owner="unknown",
                            active=pu.get('active', False)
                        )
                        detected.append(detected_pu)
                        self._power_up_history.append(detected_pu)
                    except ValueError:
                        pass

        except Exception as e:
            logger.error(f"Error detecting power-ups: {e}")

        return detected

    async def is_boost_active(self) -> Tuple[bool, int]:
        """
        Check if a boost phase is active.

        Returns:
            (is_active, phase_number)
        """
        conditions = await self.read_conditions()
        return (conditions.boost_active, conditions.boost_phase)

    async def get_active_multiplier(self, team: str = "creator") -> float:
        """
        Get the active multiplier for a team.

        Args:
            team: "creator" or "opponent"

        Returns:
            Active multiplier value (1.0 if none)
        """
        conditions = await self.read_conditions()
        return conditions.get_effective_multiplier(team)

    async def is_fog_active(self) -> bool:
        """Check if fog is active."""
        conditions = await self.read_conditions()
        return conditions.fog_active

    def get_conditions_summary(self) -> Dict:
        """Get summary of last read conditions."""
        if not self._last_conditions:
            return {'status': 'no_data'}

        c = self._last_conditions
        return {
            'creator_multiplier': c.creator_multiplier.get_value(),
            'opponent_multiplier': c.opponent_multiplier.get_value(),
            'boost_active': c.boost_active,
            'boost_phase': c.boost_phase,
            'boost_multiplier': c.boost_multiplier,
            'fog_active': c.fog_active,
            'last_read': self._last_read_time.isoformat() if self._last_read_time else None
        }

    def get_multiplier_history(self, limit: int = 20) -> List[Dict]:
        """Get recent multiplier detection history."""
        return [
            {
                'value': m.value,
                'owner': m.owner,
                'source': m.source,
                'time': m.detected_at.isoformat()
            }
            for m in self._multiplier_history[-limit:]
        ]


class EnhancedBattleReader:
    """
    Combined reader for scores and conditions.

    Provides a unified view of the battle state including:
    - Scores (from BattleScoreReader)
    - Conditions (from BattleConditionsReader)
    - Effective points calculation with multipliers
    """

    def __init__(self, page: Page):
        self.page = page

        # Import here to avoid circular imports
        from core.ai_battle_controller import BattleScoreReader

        self.score_reader = BattleScoreReader(page)
        self.conditions_reader = BattleConditionsReader(page)

    async def read_full_state(self) -> Dict:
        """
        Read complete battle state.

        Returns:
            Dict with scores, conditions, and calculations
        """
        # Read both in parallel
        score, conditions = await asyncio.gather(
            self.score_reader.read_score(),
            self.conditions_reader.read_conditions()
        )

        # Calculate effective values
        creator_mult = conditions.get_effective_multiplier("creator")
        opponent_mult = conditions.get_effective_multiplier("opponent")

        return {
            'score': {
                'our_score': score.our_score,
                'opponent_score': score.opponent_score,
                'gap': score.gap,
                'gap_percentage': score.gap_percentage,
                'time_remaining': score.time_remaining,
                'battle_active': score.battle_active
            },
            'conditions': conditions.to_dict(),
            'multipliers': {
                'creator': creator_mult,
                'opponent': opponent_mult,
                'boost_active': conditions.boost_active,
                'boost_phase': conditions.boost_phase
            },
            'effective_rates': {
                # How many points per coin each side gets
                'creator_rate': creator_mult,
                'opponent_rate': opponent_mult,
                'advantage': creator_mult - opponent_mult
            }
        }

    async def get_optimal_action(self) -> Dict:
        """
        Analyze current state and suggest optimal action.

        Returns:
            Dict with recommended action and reasoning
        """
        state = await self.read_full_state()

        score = state['score']
        mults = state['multipliers']

        recommendation = {
            'action': 'wait',
            'urgency': 'low',
            'reason': '',
            'suggested_gift': None
        }

        # If we have multiplier advantage, send gifts
        if mults['advantage'] > 0:
            recommendation['action'] = 'send'
            recommendation['urgency'] = 'high'
            recommendation['reason'] = f"Multiplier advantage: x{mults['creator']}"
            recommendation['suggested_gift'] = 'Dragon Flame' if mults['creator'] >= 3 else 'Rosa Nebula'

        # If behind and opponent has multiplier, counter
        elif score['gap'] < 0 and mults['opponent'] > 1:
            recommendation['action'] = 'counter'
            recommendation['urgency'] = 'critical'
            recommendation['reason'] = f"Behind with opponent at x{mults['opponent']}"
            recommendation['suggested_gift'] = 'Hammer'  # To cancel their multiplier

        # If behind significantly, emergency
        elif score['gap'] < -5000:
            recommendation['action'] = 'send'
            recommendation['urgency'] = 'critical'
            recommendation['reason'] = f"Emergency: behind by {abs(score['gap']):,}"
            recommendation['suggested_gift'] = 'Lion' if score['gap'] < -20000 else 'Dragon Flame'

        # If winning and have multiplier, extend lead
        elif score['gap'] > 0 and mults['creator'] > 1:
            recommendation['action'] = 'send'
            recommendation['urgency'] = 'medium'
            recommendation['reason'] = f"Extend lead with x{mults['creator']}"
            recommendation['suggested_gift'] = 'GG'

        # Default: wait for better opportunity
        else:
            recommendation['reason'] = "Wait for multiplier or better opportunity"

        return recommendation


# === Demo ===

if __name__ == "__main__":
    print("Battle Conditions Reader Demo")
    print("=" * 60)
    print("This module reads real-time battle conditions from TikTok Live")
    print("\nDetects:")
    print("  - Multipliers (x2, x3, x5)")
    print("  - Power-ups (gloves, hammers, fog)")
    print("  - Boost phases")
    print("  - Time bonuses")
