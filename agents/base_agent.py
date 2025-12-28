"""
Base Agent - Abstract base class for all AI donors.

All agents inherit from this and implement their specific behavior.
Now with COUNTER-STRATEGY support via OpponentPatternTracker!
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, TYPE_CHECKING
import random

from core.event_bus import EventBus, EventType
from .emotion_system import EmotionSystem, EmotionalState
from .memory_system import MemorySystem
from .communication import CommunicationChannel
from .learning_system import OpponentPatternTracker, PATTERN_DETECTED_ANNOUNCEMENT

if TYPE_CHECKING:
    from core.budget_system import BudgetManager
    from core.strategic_intelligence import StrategicIntelligence


class BaseAgent(ABC):
    """
    Abstract base class for all AI battle agents.

    Provides:
    - Emotion system
    - Memory system
    - Communication capabilities
    - Event bus access
    - Budget awareness
    - Common utilities

    Subclasses must implement:
    - decide_action(): Core decision-making logic
    - get_personality_prompt(): Description for GPT (if using AI)
    """

    def __init__(self, name: str, emoji: str = "🤖"):
        self.name = name
        self.emoji = emoji

        # Core systems
        self.emotion_system = EmotionSystem()
        self.memory_system = MemorySystem(name)

        # Will be injected by BattleEngine or demo
        self.event_bus: Optional[EventBus] = None
        self.comm_channel: Optional[CommunicationChannel] = None
        self.budget_manager: Optional['BudgetManager'] = None
        self.team: str = "creator"  # Which team this agent belongs to

        # Internal state
        self.total_donated = 0
        self.total_spent = 0  # Track actual spending (coins)
        self.action_count = 0
        self.last_action_time = 0
        self.gifts_blocked_by_budget = 0  # Track budget failures

        # === COUNTER-STRATEGY: Opponent Pattern Tracking ===
        self.opponent_tracker = OpponentPatternTracker()
        self.detected_pattern = None
        self.counter_strategy = {}
        self.pattern_adaptation_active = False

        # === STRATEGIC INTELLIGENCE ===
        self.strategic_intel: Optional['StrategicIntelligence'] = None
        self.has_surrendered = False
        self.surrender_time = None
        self.current_strategy_mode = None

        # === SWARM INTELLIGENCE ===
        self.swarm_signals: list = []  # Queue of pending swarm signals
        self.agent_type: str = "generic"  # For swarm role detection

    def act(self, battle):
        """
        Main action method called each battle tick.

        Args:
            battle: BattleEngine instance with access to battle state
        """
        # Update emotional state based on battle context
        context = {
            "creator_score": battle.score_tracker.creator_score,
            "opponent_score": battle.score_tracker.opponent_score,
            "time_remaining": battle.time_manager.time_remaining(),
            "recent_events": []  # Could analyze event bus history
        }
        new_emotion = self.emotion_system.update_emotion(context)

        # Announce emotion changes
        if new_emotion and self.event_bus:
            self.event_bus.publish(
                EventType.EMOTION_CHANGED,
                {
                    "agent": self.name,
                    "emotion": new_emotion.name,
                    "emoji": self.emotion_system.get_emotion_display()
                },
                source=self.name
            )

        # Let subclass decide what to do
        self.decide_action(battle)

    @abstractmethod
    def decide_action(self, battle):
        """
        Core decision-making logic (implemented by subclasses).

        Args:
            battle: BattleEngine instance

        Example:
            if battle.time_manager.current_time > 50:
                self.send_gift(battle, "UNIVERSE", 1800)
        """
        pass

    def can_afford(self, gift_name: str) -> bool:
        """Check if agent's team can afford a gift."""
        if not self.budget_manager:
            return True  # No budget system = unlimited
        return self.budget_manager.can_afford(self.team, gift_name)

    def get_budget_status(self) -> dict:
        """Get current budget status for agent's team."""
        if not self.budget_manager:
            return {"current": float('inf'), "tier": "unlimited"}
        return self.budget_manager.get_status(self.team)

    def send_gift(self, battle, gift_name: str, points: int) -> bool:
        """
        Send a gift (donate points to creator).

        Args:
            battle: BattleEngine instance
            gift_name: Name of gift (e.g., "ROSE", "UNIVERSE")
            points: Point value (base value, multipliers applied by battle engine)

        Returns:
            True if gift was sent, False if blocked by budget
        """
        current_time = battle.time_manager.current_time

        # Check budget if budget system is active
        if self.budget_manager:
            # Determine phase for tracking
            phase = "normal"
            if hasattr(battle, 'phase_manager') and battle.phase_manager:
                pm = battle.phase_manager
                if pm.boost1_active or pm.boost2_active:
                    phase = "boost"
                elif pm.is_in_final_30s(current_time):
                    phase = "final_30s"

            # Try to spend
            success, cost = self.budget_manager.spend(
                self.team, gift_name, current_time, phase
            )

            if not success:
                self.gifts_blocked_by_budget += 1
                # Silent fail most of the time, occasional warning
                if self.gifts_blocked_by_budget <= 3 or self.gifts_blocked_by_budget % 10 == 0:
                    budget = self.budget_manager.get_status(self.team)
                    print(f"💸 {self.name}: Can't afford {gift_name}! (Budget: {budget['current']:,})")
                return False

            self.total_spent += cost

        # No emotion modifiers - use pure base value
        actual_points = points

        # Publish gift event
        if self.event_bus:
            self.event_bus.publish(
                EventType.GIFT_SENT,
                {
                    "agent": self.name,
                    "gift": gift_name,
                    "points": actual_points,
                    "emotion": self.emotion_system.current_state.name
                },
                source=self.name,
                timestamp=current_time
            )

        # Track stats
        self.total_donated += actual_points
        self.action_count += 1
        self.last_action_time = current_time

        # Console output
        emotion_emoji = self.emotion_system.get_emotion_display()
        print(f"{self.emoji} {self.name} {emotion_emoji}: Sends {gift_name} 🎁 (+{actual_points})")
        return True

    def send_message(self, message: str, to_agent: Optional[str] = None,
                     message_type: str = "chat"):
        """
        Send a message to other agents.

        Args:
            message: Message content
            to_agent: Recipient (None for broadcast)
            message_type: Type of message
        """
        if self.comm_channel:
            self.comm_channel.send(
                from_agent=self.name,
                message=message,
                to_agent=to_agent,
                message_type=message_type
            )

        # Also publish as event
        if self.event_bus:
            self.event_bus.publish(
                EventType.AGENT_DIALOGUE,
                {
                    "from": self.name,
                    "to": to_agent or "ALL",
                    "message": message,
                    "type": message_type
                },
                source=self.name
            )

    def get_personality_prompt(self) -> str:
        """
        Get personality description for GPT-based decision making.

        Override in subclasses to define unique personality.

        Returns:
            String describing agent's personality and strategy
        """
        return f"You are {self.name}, a TikTok battle supporter."

    def should_act_this_tick(self, probability: float = 0.1) -> bool:
        """
        Random chance to act this tick (modified by emotions).

        Args:
            probability: Base probability (0-1)

        Returns:
            True if should act
        """
        modifiers = self.emotion_system.get_modifiers()
        adjusted_prob = probability * modifiers.gift_frequency_multiplier
        return random.random() < adjusted_prob

    def get_stats(self) -> dict:
        """Get agent statistics."""
        return {
            "name": self.name,
            "total_donated": self.total_donated,
            "action_count": self.action_count,
            "current_emotion": self.emotion_system.current_state.name,
            "battles_participated": self.memory_system.get_battle_count(),
            "win_rate": self.memory_system.get_win_rate(),
            "detected_pattern": self.detected_pattern,
            "pattern_adaptation_active": self.pattern_adaptation_active,
        }

    # === COUNTER-STRATEGY: Pattern Detection Methods ===

    def on_opponent_gift(self, amount: int, current_time: int, phase: str, time_remaining: int):
        """
        Called when opponent sends a gift - track for pattern detection.

        Args:
            amount: Gift value in coins
            current_time: Battle time when gift was sent
            phase: Current battle phase
            time_remaining: Time remaining in battle
        """
        # Update pattern tracker
        self.opponent_tracker.update(current_time, amount, phase, time_remaining)

        # Check if pattern is detected
        pattern = self.opponent_tracker.detect_pattern()
        if pattern and pattern != self.detected_pattern:
            self.detected_pattern = pattern
            self.counter_strategy = self.opponent_tracker.get_counter_strategy()

            # Announce pattern detection (once per pattern)
            if not self.pattern_adaptation_active:
                self.pattern_adaptation_active = True
                self._announce_pattern_detection()

    def _announce_pattern_detection(self):
        """Announce that we've detected opponent's strategy!"""
        if not self.detected_pattern:
            return

        # Get counter-strategy description
        counter = self.counter_strategy.get('description', 'Adapting...')

        print(PATTERN_DETECTED_ANNOUNCEMENT.format(
            strategy=self.detected_pattern.upper().replace('_', ' '),
            confidence=self.opponent_tracker.confidence
        ))
        print(f"   📋 Counter-Strategy: {counter}")

    def get_counter_adjustments(self) -> Dict:
        """
        Get aggression adjustments based on detected opponent pattern.

        Returns dict with adjustment values like:
        {
            'aggression_early': 0.7,
            'aggression_boost': 0.9,
            ...
        }
        """
        if not self.counter_strategy:
            return {}
        return self.counter_strategy

    def reset_pattern_tracking(self):
        """Reset pattern tracking for new battle."""
        self.opponent_tracker.reset()
        self.detected_pattern = None
        self.counter_strategy = {}
        self.pattern_adaptation_active = False

    # === SWARM INTELLIGENCE METHODS ===

    def receive_swarm_signal(self, signal: str, data: Dict):
        """
        Receive a signal from the swarm coordinator.

        Signals:
        - boost_detected: A boost phase has started
        - snipe_window: Final seconds, time for snipe
        - deficit_alert: We're behind, need response
        - converge: Focus all agents on coordinated attack
        - scatter: Spread out actions
        - whale_incoming: Prepare for big gift

        Args:
            signal: Signal type
            data: Signal-specific data
        """
        self.swarm_signals.append({
            'signal': signal,
            'data': data,
            'processed': False
        })

    def process_swarm_signals(self) -> list:
        """
        Process pending swarm signals.

        Returns:
            List of signals that should influence action
        """
        active_signals = []
        for sig in self.swarm_signals:
            if not sig['processed']:
                active_signals.append(sig)
                sig['processed'] = True

        # Keep only recent unprocessed signals (max 5)
        self.swarm_signals = [s for s in self.swarm_signals if not s['processed']][-5:]

        return active_signals

    def has_swarm_signal(self, signal_type: str) -> bool:
        """Check if there's a pending signal of given type."""
        return any(
            s['signal'] == signal_type and not s['processed']
            for s in self.swarm_signals
        )

    def get_swarm_recommendation(self) -> Optional[str]:
        """
        Get the recommended action from swarm signals.

        Returns:
            Action string or None
        """
        for sig in self.swarm_signals:
            if not sig['processed']:
                data = sig.get('data', {})
                if 'recommendation' in data:
                    return data['recommendation']
        return None

    # === STRATEGIC INTELLIGENCE METHODS ===

    def init_strategic_intelligence(self, budget_manager: 'BudgetManager', battle_duration: int = 300):
        """
        Initialize strategic intelligence for this agent.

        Args:
            budget_manager: BudgetManager instance
            battle_duration: Total battle duration in seconds
        """
        try:
            from core.strategic_intelligence import StrategicIntelligence
            self.strategic_intel = StrategicIntelligence(
                budget_manager=budget_manager,
                team=self.team,
                battle_duration=battle_duration
            )
        except ImportError:
            pass

    def get_strategic_recommendation(self, battle) -> Dict:
        """
        Get strategic recommendation from intelligence system.

        Returns dict with:
        - mode: Current strategy mode (AGGRESSIVE, DEFENSIVE, etc.)
        - should_gift: Whether to send a gift now
        - max_spend: Maximum coins to spend
        - gift_tier: Recommended gift tier
        - reasoning: Explanation of recommendation
        """
        if not self.strategic_intel:
            return {
                'mode': None,
                'should_gift': True,
                'max_spend': float('inf'),
                'gift_tier': 'large',
                'reasoning': 'No strategic intelligence available'
            }

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # Update scores
        our_score = battle.score_tracker.creator_score if self.team == "creator" else battle.score_tracker.opponent_score
        their_score = battle.score_tracker.opponent_score if self.team == "creator" else battle.score_tracker.creator_score
        self.strategic_intel.update_scores(our_score, their_score, current_time)

        # Get phase info
        phase_info = {'multiplier': 1.0, 'name': 'Normal'}
        if hasattr(battle, 'phase_manager') and battle.phase_manager:
            pm = battle.phase_manager
            if pm.boost1_active:
                phase_info = {'multiplier': pm.boost1_multiplier, 'name': 'Boost #1'}
            elif pm.boost2_active:
                phase_info = {'multiplier': pm.boost2_multiplier, 'name': 'Boost #2'}
            elif pm.active_glove_x5:
                phase_info = {'multiplier': 5.0, 'name': 'x5 Active'}

        # Get recommendation
        recommendation = self.strategic_intel.get_recommended_strategy(
            current_time=current_time,
            time_remaining=time_remaining,
            phase_info=phase_info
        )

        # Update current mode
        self.current_strategy_mode = recommendation.get('mode')

        # Check for surrender
        recovery = recommendation.get('recovery_analysis')
        if recovery and not recovery.can_recover and recovery.confidence >= 0.80:
            if time_remaining > 30 and not self.has_surrendered:
                self.has_surrendered = True
                self.surrender_time = current_time
                print(f"\n🏳️ {self.name} SURRENDERED at t={current_time}s!")
                print(f"   Deficit: {recovery.deficit:,} | Max possible: {recovery.max_possible_points:,}")

        return recommendation

    def should_gift_strategically(self, battle) -> tuple:
        """
        Check if agent should send a gift based on strategic analysis.

        Returns:
            (should_gift: bool, max_spend: int, tier: str, reason: str)
        """
        if self.has_surrendered:
            return False, 0, None, "Surrendered - conserving budget"

        recommendation = self.get_strategic_recommendation(battle)
        return (
            recommendation.get('should_gift', True),
            recommendation.get('max_spend', float('inf')),
            recommendation.get('gift_tier', 'large'),
            recommendation.get('reasoning', '')
        )

    def select_gift_by_strategy(self, max_spend: int, tier: str) -> Optional[str]:
        """
        Select optimal gift based on strategic constraints.

        Args:
            max_spend: Maximum coins to spend
            tier: Maximum gift tier ('small', 'medium', 'large', 'whale')

        Returns:
            Gift name or None if no suitable gift
        """
        if self.strategic_intel:
            return self.strategic_intel.select_optimal_gift(max_spend, tier)

        # Fallback: simple selection
        tier_gifts = {
            'small': [('Rose', 1), ('Heart', 5), ('Doughnut', 30)],
            'medium': [('Rosa Nebula', 299), ('Perfume', 500), ('GG', 1000)],
            'large': [('Corgi', 2999), ('Money Gun', 5000)],
            'whale': [('Dragon Flame', 10000), ('Lion', 29999)]
        }

        tier_order = ['small', 'medium', 'large', 'whale']
        max_tier_idx = tier_order.index(tier) if tier in tier_order else 3

        # Find best affordable gift
        best_gift = None
        best_value = 0

        for t_idx in range(max_tier_idx, -1, -1):
            for name, cost in tier_gifts.get(tier_order[t_idx], []):
                if cost <= max_spend and cost > best_value:
                    best_gift = name
                    best_value = cost

        return best_gift

    def reset_strategic_state(self):
        """Reset strategic state for new battle."""
        self.has_surrendered = False
        self.surrender_time = None
        self.current_strategy_mode = None
        if self.strategic_intel:
            # Reset intel state
            self.strategic_intel.our_score = 0
            self.strategic_intel.opponent_score = 0
            self.strategic_intel.peak_lead = 0
            self.strategic_intel.max_deficit = 0
            self.strategic_intel.upcoming_boosts.clear()
            self.strategic_intel.strategy_changes.clear()

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, emotion={self.emotion_system.current_state.name})"


# =============================================================================
# AGENT PROFILE SYSTEM
# =============================================================================

class AgentProfileLoader:
    """
    Load and manage agent configurations from JSON profiles.

    Profile Schema:
    {
        "identity": {
            "name": "Custom Agent",
            "emoji": "🎯",
            "agent_type": "boost_responder",
            "description": "A custom agent..."
        },
        "strategy": {
            "aggression": {
                "normal": 0.15,
                "boost1": 0.70,
                "boost2": 0.85,
                "final_5s": 0.95,
                "final_30s": 0.50
            },
            "cooldowns": {
                "normal": 10.0,
                "boost": 2.5,
                "final": 1.0
            },
            "whale_chances": {
                "normal": 0.05,
                "boost": 0.40,
                "final": 0.30
            },
            "gift_preferences": {
                "default": "ROSE",
                "boost": "LION",
                "whale": "UNIVERSE"
            }
        },
        "learning": {
            "enabled": true,
            "learning_rate": 0.15,
            "epsilon": 0.20,
            "discount_factor": 0.95
        },
        "personality": {
            "aggression_style": "calculated",
            "risk_tolerance": 0.5,
            "team_player": true
        }
    }
    """

    # Default profile values
    DEFAULTS = {
        'identity': {
            'name': 'Agent',
            'emoji': '🤖',
            'agent_type': 'generic',
            'description': 'A battle agent'
        },
        'strategy': {
            'aggression': {
                'normal': 0.20,
                'boost1': 0.60,
                'boost2': 0.75,
                'final_5s': 0.90,
                'final_30s': 0.45
            },
            'cooldowns': {
                'normal': 8.0,
                'boost': 3.0,
                'final': 1.5
            },
            'whale_chances': {
                'normal': 0.05,
                'boost': 0.25,
                'final': 0.20
            },
            'gift_preferences': {
                'default': 'ROSE',
                'boost': 'LION',
                'whale': 'UNIVERSE'
            }
        },
        'learning': {
            'enabled': False,
            'learning_rate': 0.10,
            'epsilon': 0.15,
            'discount_factor': 0.90
        },
        'personality': {
            'aggression_style': 'balanced',
            'risk_tolerance': 0.5,
            'team_player': True
        }
    }

    # Preset profiles for common agent types
    PRESETS = {
        'aggressive_whale': {
            'identity': {'name': 'Aggressive Whale', 'emoji': '🐋', 'agent_type': 'whale'},
            'strategy': {
                'aggression': {'normal': 0.10, 'boost1': 0.95, 'boost2': 0.99, 'final_5s': 0.99, 'final_30s': 0.60},
                'whale_chances': {'normal': 0.20, 'boost': 0.70, 'final': 0.50}
            }
        },
        'budget_saver': {
            'identity': {'name': 'Budget Saver', 'emoji': '💰', 'agent_type': 'budget'},
            'strategy': {
                'aggression': {'normal': 0.05, 'boost1': 0.30, 'boost2': 0.40, 'final_5s': 0.80, 'final_30s': 0.20},
                'whale_chances': {'normal': 0.01, 'boost': 0.10, 'final': 0.15}
            }
        },
        'snipe_master': {
            'identity': {'name': 'Snipe Master', 'emoji': '🎯', 'agent_type': 'sniper'},
            'strategy': {
                'aggression': {'normal': 0.02, 'boost1': 0.15, 'boost2': 0.20, 'final_5s': 0.99, 'final_30s': 0.05},
                'whale_chances': {'normal': 0.00, 'boost': 0.10, 'final': 0.80}
            }
        },
        'chaos_agent': {
            'identity': {'name': 'Chaos Agent', 'emoji': '🌀', 'agent_type': 'chaos'},
            'strategy': {
                'aggression': {'normal': 0.30, 'boost1': 0.50, 'boost2': 0.60, 'final_5s': 0.70, 'final_30s': 0.40},
                'whale_chances': {'normal': 0.15, 'boost': 0.35, 'final': 0.25}
            },
            'learning': {'enabled': True, 'epsilon': 0.40}
        },
        'learning_agent': {
            'identity': {'name': 'Learning Agent', 'emoji': '🧠', 'agent_type': 'q_learning'},
            'learning': {'enabled': True, 'learning_rate': 0.20, 'epsilon': 0.25, 'discount_factor': 0.95}
        }
    }

    def __init__(self, profile_dir: str = "data/agent_profiles"):
        """Initialize profile loader with profile directory."""
        self.profile_dir = profile_dir
        self.loaded_profiles: Dict[str, dict] = {}

    def load_profile(self, filepath: str) -> dict:
        """
        Load an agent profile from JSON file.

        Args:
            filepath: Path to profile JSON

        Returns:
            Merged profile with defaults
        """
        import json
        import os

        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.profile_dir, filepath)

        if not filepath.endswith('.json'):
            filepath += '.json'

        with open(filepath, 'r') as f:
            profile = json.load(f)

        # Validate and merge with defaults
        merged = self._merge_with_defaults(profile)

        # Cache the profile
        name = merged['identity']['name']
        self.loaded_profiles[name] = merged

        return merged

    def load_from_preset(self, preset_name: str) -> dict:
        """
        Load a profile from preset.

        Args:
            preset_name: Name of preset (e.g., 'aggressive_whale')

        Returns:
            Profile dict
        """
        if preset_name not in self.PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(self.PRESETS.keys())}")

        return self._merge_with_defaults(self.PRESETS[preset_name])

    def _merge_with_defaults(self, profile: dict) -> dict:
        """Recursively merge profile with defaults."""
        result = {}

        for key, default_value in self.DEFAULTS.items():
            if key in profile:
                if isinstance(default_value, dict) and isinstance(profile[key], dict):
                    # Recursive merge for nested dicts
                    result[key] = self._deep_merge(default_value, profile[key])
                else:
                    result[key] = profile[key]
            else:
                result[key] = default_value.copy() if isinstance(default_value, dict) else default_value

        return result

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dicts."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def validate_profile(self, profile: dict) -> tuple:
        """
        Validate a profile structure.

        Returns:
            (is_valid, list of errors)
        """
        errors = []

        # Check required sections
        for section in ['identity', 'strategy']:
            if section not in profile:
                errors.append(f"Missing required section: {section}")

        # Validate identity
        if 'identity' in profile:
            if 'name' not in profile['identity']:
                errors.append("Identity missing 'name'")

        # Validate aggression values (0-1)
        if 'strategy' in profile and 'aggression' in profile['strategy']:
            for key, val in profile['strategy']['aggression'].items():
                if not isinstance(val, (int, float)) or not 0 <= val <= 1:
                    errors.append(f"Aggression '{key}' must be 0-1, got {val}")

        # Validate whale chances (0-1)
        if 'strategy' in profile and 'whale_chances' in profile['strategy']:
            for key, val in profile['strategy']['whale_chances'].items():
                if not isinstance(val, (int, float)) or not 0 <= val <= 1:
                    errors.append(f"Whale chance '{key}' must be 0-1, got {val}")

        return len(errors) == 0, errors

    def save_profile(self, profile: dict, filename: str):
        """
        Save a profile to JSON file.

        Args:
            profile: Profile dict
            filename: Output filename
        """
        import os
        import json

        os.makedirs(self.profile_dir, exist_ok=True)

        if not filename.endswith('.json'):
            filename += '.json'

        filepath = os.path.join(self.profile_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(profile, f, indent=2)

        print(f"💾 Profile saved to: {filepath}")

    def list_profiles(self) -> list:
        """List available profile files."""
        import os

        profiles = []

        if not os.path.exists(self.profile_dir):
            return profiles

        for filename in os.listdir(self.profile_dir):
            if filename.endswith('.json'):
                profiles.append(filename[:-5])  # Remove .json

        return profiles

    def print_profile(self, profile: dict):
        """Print formatted profile info."""
        identity = profile.get('identity', {})
        strategy = profile.get('strategy', {})
        learning = profile.get('learning', {})

        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  {identity.get('emoji', '🤖')} {identity.get('name', 'Agent'):<56} ║
╠══════════════════════════════════════════════════════════════════╣
║  Type: {identity.get('agent_type', 'generic'):<55} ║
║  {identity.get('description', '')[:60]:<62} ║
╠══════════════════════════════════════════════════════════════════╣
║  AGGRESSION                                                      ║
║    Normal:  {strategy.get('aggression', {}).get('normal', 0):.0%}   Boost1: {strategy.get('aggression', {}).get('boost1', 0):.0%}   Boost2: {strategy.get('aggression', {}).get('boost2', 0):.0%}                     ║
║    Final5s: {strategy.get('aggression', {}).get('final_5s', 0):.0%}  Final30: {strategy.get('aggression', {}).get('final_30s', 0):.0%}                              ║
╠══════════════════════════════════════════════════════════════════╣
║  WHALE CHANCES                                                   ║
║    Normal: {strategy.get('whale_chances', {}).get('normal', 0):.0%}   Boost: {strategy.get('whale_chances', {}).get('boost', 0):.0%}   Final: {strategy.get('whale_chances', {}).get('final', 0):.0%}                       ║
╠══════════════════════════════════════════════════════════════════╣
║  LEARNING: {'✅ ENABLED' if learning.get('enabled') else '❌ Disabled':<52} ║
║    Rate: {learning.get('learning_rate', 0):.2f}   Epsilon: {learning.get('epsilon', 0):.2f}   γ: {learning.get('discount_factor', 0):.2f}                       ║
╚══════════════════════════════════════════════════════════════════╝
""")
