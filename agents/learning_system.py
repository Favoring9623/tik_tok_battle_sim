"""
Agent Learning System

Implements reinforcement learning and strategy optimization for agents:
- Q-Learning for action selection
- Strategy parameter optimization
- Performance tracking
- A/B testing framework
- Adaptive learning rates
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import json
from datetime import datetime

# Import database
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.battle_history import BattleHistoryDB, generate_battle_id


class ActionType(Enum):
    """Types of actions agents can take."""
    # === GIFT ACTIONS ===
    SEND_ROSE = "send_rose"
    SEND_GLOVE = "send_glove"
    SEND_SMALL_GIFT = "send_small_gift"
    SEND_MEDIUM_GIFT = "send_medium_gift"
    SEND_LARGE_GIFT = "send_large_gift"
    SEND_WHALE_GIFT = "send_whale_gift"

    # === POWER-UP ACTIONS ===
    USE_HAMMER = "use_hammer"
    USE_FOG = "use_fog"
    USE_TIME_BONUS = "use_time_bonus"

    # === COUNTER-STRATEGY ACTIONS (BoostResponder) ===
    COUNTER_SMALL = "counter_small"      # Counter with small gift
    COUNTER_MEDIUM = "counter_medium"    # Counter with medium gift
    COUNTER_WHALE = "counter_whale"      # Counter with whale gift
    WAIT_FOR_BOOST = "wait_for_boost"    # Conserve for upcoming boost

    # === SIGNAL ACTIONS (PixelPixie) ===
    SIGNAL_ROSE = "signal_rose"          # Send rose to signal for Boost #2
    QUALIFY_PUSH = "qualify_push"        # Send gift to help qualify

    # === PSYCHOLOGICAL WARFARE ACTIONS ===
    BLUFF_ACTIVITY = "bluff_activity"    # Small rapid gifts to fake aggression
    DECOY_WHALE = "decoy_whale"          # Medium gift disguised as whale incoming
    STRATEGIC_PAUSE = "strategic_pause"  # Go silent to create uncertainty
    FOG_BURST = "fog_burst"              # Rapid small gifts to obscure intent

    # === BASIC ===
    WAIT = "wait"


class StateFeature(Enum):
    """Features that define battle state."""
    TIME_REMAINING = "time_remaining"
    SCORE_DIFF = "score_diff"
    CURRENT_MULTIPLIER = "current_multiplier"
    IN_BOOST_PHASE = "in_boost_phase"
    BOOST2_AVAILABLE = "boost2_available"
    GLOVES_REMAINING = "gloves_remaining"
    OPPONENT_HAS_X5 = "opponent_has_x5"
    LAST_30_SECONDS = "last_30_seconds"
    WINNING = "winning"


@dataclass
class State:
    """Battle state representation for learning."""
    time_remaining: int
    score_diff: int  # positive = winning
    multiplier: float
    in_boost: bool
    boost2_triggered: bool
    phase: str
    gloves_available: int
    power_ups_available: List[str]
    # Budget-related state (optional for backward compatibility)
    budget_ratio: float = 1.0  # 0-1, remaining budget percentage
    budget_tier: str = "ABUNDANT"  # CRITICAL, LOW, MEDIUM, HEALTHY, ABUNDANT
    budget_advantage: float = 0.0  # positive = we have more budget than opponent

    def to_tuple(self) -> tuple:
        """Convert to hashable tuple for Q-table."""
        # Discretize continuous values
        time_bucket = self.time_remaining // 30  # 30-second buckets
        score_bucket = self._discretize_score(self.score_diff)
        mult_bucket = int(self.multiplier)
        budget_bucket = self._discretize_budget(self.budget_ratio)

        return (
            time_bucket,
            score_bucket,
            mult_bucket,
            self.in_boost,
            self.boost2_triggered,
            min(self.gloves_available, 3),
            len(self.power_ups_available) > 0,
            budget_bucket  # Add budget awareness to state
        )

    def _discretize_score(self, diff: int) -> int:
        """Convert score difference to discrete bucket."""
        if diff < -100000:
            return -3  # Losing badly
        elif diff < -50000:
            return -2  # Losing
        elif diff < -10000:
            return -1  # Slightly behind
        elif diff < 10000:
            return 0   # Close
        elif diff < 50000:
            return 1   # Slightly ahead
        elif diff < 100000:
            return 2   # Winning
        else:
            return 3   # Winning big

    def _discretize_budget(self, ratio: float) -> int:
        """Convert budget ratio (0-1) to discrete bucket."""
        if ratio <= 0.1:
            return 0  # CRITICAL - almost broke
        elif ratio <= 0.25:
            return 1  # LOW - conserve
        elif ratio <= 0.5:
            return 2  # MEDIUM - balanced
        elif ratio <= 0.75:
            return 3  # HEALTHY - can spend
        else:
            return 4  # ABUNDANT - free to spend


@dataclass
class Experience:
    """Single experience for learning."""
    state: State
    action: ActionType
    reward: float
    next_state: State
    done: bool


class QLearningAgent:
    """
    Q-Learning based agent that learns optimal strategies.

    Uses tabular Q-learning with:
    - Epsilon-greedy exploration
    - Adaptive learning rate
    - Experience replay
    """

    def __init__(
        self,
        agent_type: str,
        learning_rate: float = 0.12,      # BALANCE v1.1: was 0.1 - faster learning
        discount_factor: float = 0.95,
        epsilon: float = 0.35,            # BALANCE v1.1: was 0.3 - more exploration
        epsilon_decay: float = 0.992,     # BALANCE v1.1: was 0.995 - explore longer
        min_epsilon: float = 0.08         # BALANCE v1.1: was 0.05 - maintain some exploration
    ):
        self.agent_type = agent_type
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon

        # Q-table: state -> action -> value
        self.q_table: Dict[tuple, Dict[ActionType, float]] = {}

        # Experience buffer for replay
        self.experience_buffer: List[Experience] = []
        self.max_buffer_size = 1000

        # Statistics
        self.episodes = 0
        self.total_rewards = 0.0
        self.wins = 0

    def get_q_value(self, state: State, action: ActionType) -> float:
        """Get Q-value for state-action pair."""
        state_key = state.to_tuple()
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in ActionType}
        return self.q_table[state_key].get(action, 0.0)

    def get_best_action(self, state: State) -> ActionType:
        """Get action with highest Q-value."""
        state_key = state.to_tuple()
        if state_key not in self.q_table:
            return random.choice(list(ActionType))

        return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]

    def choose_action(self, state: State, available_actions: List[ActionType] = None) -> ActionType:
        """
        Choose action using epsilon-greedy policy.

        Args:
            state: Current battle state
            available_actions: List of valid actions (None = all)

        Returns:
            Selected action
        """
        if available_actions is None:
            available_actions = list(ActionType)

        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            return random.choice(available_actions)

        # Exploitation: choose best action
        state_key = state.to_tuple()
        if state_key not in self.q_table:
            return random.choice(available_actions)

        # Get best available action
        q_values = {a: self.q_table[state_key].get(a, 0.0) for a in available_actions}
        return max(q_values.items(), key=lambda x: x[1])[0]

    def update(self, experience: Experience):
        """Update Q-value based on experience."""
        state_key = experience.state.to_tuple()

        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in ActionType}

        # Current Q-value
        current_q = self.q_table[state_key][experience.action]

        # Calculate target Q-value
        if experience.done:
            target_q = experience.reward
        else:
            next_state_key = experience.next_state.to_tuple()
            if next_state_key in self.q_table:
                max_next_q = max(self.q_table[next_state_key].values())
            else:
                max_next_q = 0.0
            target_q = experience.reward + self.discount_factor * max_next_q

        # Update Q-value
        self.q_table[state_key][experience.action] = (
            current_q + self.learning_rate * (target_q - current_q)
        )

        # Store experience for replay
        self.experience_buffer.append(experience)
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)

    def experience_replay(self, batch_size: int = 32):
        """Learn from random batch of past experiences."""
        if len(self.experience_buffer) < batch_size:
            return

        batch = random.sample(self.experience_buffer, batch_size)
        for exp in batch:
            self.update(exp)

    def end_episode(self, won: bool, total_reward: float):
        """Called at end of each battle."""
        self.episodes += 1
        self.total_rewards += total_reward
        if won:
            self.wins += 1

        # Decay epsilon
        self.epsilon = max(
            self.min_epsilon,
            self.epsilon * self.epsilon_decay
        )

        # Experience replay
        self.experience_replay()

    def get_stats(self) -> Dict:
        """Get learning statistics."""
        return {
            'episodes': self.episodes,
            'win_rate': self.wins / max(self.episodes, 1),
            'avg_reward': self.total_rewards / max(self.episodes, 1),
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table)
        }

    def save(self, filepath: str):
        """Save Q-table to file."""
        data = {
            'agent_type': self.agent_type,
            'q_table': {
                str(k): {a.value: v for a, v in actions.items()}
                for k, actions in self.q_table.items()
            },
            'stats': self.get_stats(),
            'epsilon': self.epsilon
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str):
        """Load Q-table from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.epsilon = data.get('epsilon', self.epsilon)
        # Reconstruct Q-table
        for state_str, actions in data.get('q_table', {}).items():
            state_key = eval(state_str)  # Convert string back to tuple
            self.q_table[state_key] = {
                ActionType(a): v for a, v in actions.items()
            }

    def save_to_db(self, db: 'BattleHistoryDB'):
        """Save Q-table to database for persistence."""
        db.save_q_table(
            agent_type=self.agent_type,
            q_table=self.q_table,
            episodes=self.episodes,
            total_rewards=self.total_rewards,
            wins=self.wins,
            epsilon=self.epsilon
        )

    def load_from_db(self, db: 'BattleHistoryDB') -> bool:
        """Load Q-table from database. Returns True if loaded."""
        data = db.load_q_table(self.agent_type)
        if not data:
            return False

        self.epsilon = data.get('epsilon', self.epsilon)
        self.episodes = data.get('episodes', 0)
        self.total_rewards = data.get('total_rewards', 0.0)
        self.wins = data.get('wins', 0)

        # Reconstruct Q-table
        raw_q_table = data.get('q_table', {})
        for state_str, actions in raw_q_table.items():
            try:
                state_key = eval(state_str)  # Convert string back to tuple
                self.q_table[state_key] = {
                    ActionType(a): v for a, v in actions.items()
                }
            except:
                pass  # Skip invalid entries

        print(f"📚 {self.agent_type}: Loaded Q-table ({len(self.q_table)} states, {self.episodes} episodes)")
        return True


class StrategyOptimizer:
    """
    Optimizes strategy parameters using evolutionary approach.

    Parameters are evolved based on battle outcomes:
    - Successful strategies have higher reproduction probability
    - Mutation introduces variation
    - Selection pressure improves over time
    """

    def __init__(self, db: BattleHistoryDB, population_size: int = 10):
        self.db = db
        self.population_size = population_size
        self.generation = 0

    def optimize_sniper_params(self) -> Dict[str, float]:
        """Optimize Kinetik (sniper) parameters."""
        # Default params
        default_params = {
            'snipe_window': 5.0,
            'min_deficit_for_universe': 300000,
            'min_deficit_for_lion': 150000,
            'min_deficit_for_phoenix': 0
        }

        # Get historical data
        learning_data = self.db.get_learning_data('sniper', limit=50)
        if len(learning_data) < 10:
            return default_params

        # Analyze successful battles
        winning_battles = [b for b in learning_data if b['won']]
        losing_battles = [b for b in learning_data if not b['won']]

        if not winning_battles:
            return default_params

        # Calculate optimal parameters based on winning patterns
        avg_final_gifts_win = sum(b['final_phase_gifts'] for b in winning_battles) / len(winning_battles)
        avg_margin_win = sum(b['margin'] for b in winning_battles) / len(winning_battles)

        # Adjust snipe window based on success
        optimal_snipe_window = max(3, min(10, 5 + (avg_final_gifts_win - 1) * 2))

        # Adjust deficit thresholds based on margins
        optimal_params = {
            'snipe_window': optimal_snipe_window,
            'min_deficit_for_universe': int(avg_margin_win * 1.2),
            'min_deficit_for_lion': int(avg_margin_win * 0.6),
            'min_deficit_for_phoenix': int(avg_margin_win * 0.1)
        }

        return optimal_params

    def optimize_glove_params(self) -> Dict[str, float]:
        """Optimize StrikeMaster (glove expert) parameters."""
        default_params = {
            'prefer_boost_phase': 1.0,
            'prefer_last_30s': 0.5,
            'min_gloves_per_battle': 2,
            'max_gloves_per_battle': 5
        }

        # Analyze glove timing effectiveness
        timing_data = self.db.get_optimal_gift_timing('glove_expert')
        glove_timing = timing_data.get('glove_timing', {})

        if not glove_timing:
            return default_params

        # Find best phase for gloves
        boost_rate = glove_timing.get('BOOST', {}).get('activation_rate', 0.4)
        final_rate = glove_timing.get('FINAL', {}).get('activation_rate', 0.4)

        optimal_params = {
            'prefer_boost_phase': boost_rate / 0.4,  # Normalized to default
            'prefer_last_30s': final_rate / 0.4,
            'min_gloves_per_battle': 2 if boost_rate > 0.3 else 3,
            'max_gloves_per_battle': 5 if boost_rate > 0.5 else 4
        }

        return optimal_params

    def optimize_phase_tracker_params(self) -> Dict[str, float]:
        """Optimize PhaseTracker parameters."""
        default_params = {
            'roses_to_trigger': 5,
            'start_trigger_at': 60,
            'urgency_threshold': 75
        }

        # Analyze boost2 trigger success
        win_conditions = self.db.get_win_conditions()
        boost2_impact = win_conditions.get('boost2_impact', {})

        with_boost2 = boost2_impact.get('with_boost2', {})
        without_boost2 = boost2_impact.get('without_boost2', {})

        if not with_boost2:
            return default_params

        # If boost2 battles have better margins, prioritize triggering
        boost2_margin = with_boost2.get('avg_margin', 0)
        no_boost2_margin = without_boost2.get('avg_margin', 0)

        if boost2_margin > no_boost2_margin:
            # Boost2 is valuable, trigger early
            optimal_params = {
                'roses_to_trigger': 5,
                'start_trigger_at': 58,  # Start earlier
                'urgency_threshold': 70  # More urgent
            }
        else:
            # Boost2 less valuable, conserve resources
            optimal_params = {
                'roses_to_trigger': 5,
                'start_trigger_at': 65,  # Start later
                'urgency_threshold': 80  # Less urgent
            }

        return optimal_params

    def run_optimization_cycle(self) -> Dict[str, Dict]:
        """Run full optimization cycle for all agent types."""
        self.generation += 1

        optimized = {
            'sniper': self.optimize_sniper_params(),
            'glove_expert': self.optimize_glove_params(),
            'phase_tracker': self.optimize_phase_tracker_params()
        }

        print(f"\n🧬 Generation {self.generation} Optimization Complete")

        return optimized


class ABTestingFramework:
    """
    A/B testing framework for strategy comparison.

    Runs battles with different strategy variants
    and tracks statistical significance.
    """

    def __init__(self, db: BattleHistoryDB):
        self.db = db
        self.tests: Dict[str, Dict] = {}

    def create_test(
        self,
        test_name: str,
        variant_a: Dict[str, float],
        variant_b: Dict[str, float],
        agent_type: str
    ):
        """Create new A/B test."""
        self.tests[test_name] = {
            'agent_type': agent_type,
            'variant_a': variant_a,
            'variant_b': variant_b,
            'results_a': {'wins': 0, 'battles': 0, 'total_points': 0},
            'results_b': {'wins': 0, 'battles': 0, 'total_points': 0},
            'created_at': datetime.now().isoformat(),
            'status': 'running'
        }
        return test_name

    def record_result(
        self,
        test_name: str,
        variant: str,
        won: bool,
        points: int
    ):
        """Record battle result for A/B test."""
        if test_name not in self.tests:
            return

        key = f'results_{variant.lower()}'
        self.tests[test_name][key]['battles'] += 1
        self.tests[test_name][key]['total_points'] += points
        if won:
            self.tests[test_name][key]['wins'] += 1

    def get_test_results(self, test_name: str) -> Optional[Dict]:
        """Get A/B test results with statistical analysis."""
        if test_name not in self.tests:
            return None

        test = self.tests[test_name]
        results_a = test['results_a']
        results_b = test['results_b']

        # Calculate win rates
        win_rate_a = results_a['wins'] / max(results_a['battles'], 1)
        win_rate_b = results_b['wins'] / max(results_b['battles'], 1)

        # Calculate average points
        avg_points_a = results_a['total_points'] / max(results_a['battles'], 1)
        avg_points_b = results_b['total_points'] / max(results_b['battles'], 1)

        # Simple significance test (need more samples for real significance)
        total_battles = results_a['battles'] + results_b['battles']
        min_samples = 30

        return {
            'test_name': test_name,
            'agent_type': test['agent_type'],
            'variant_a': {
                'params': test['variant_a'],
                'battles': results_a['battles'],
                'wins': results_a['wins'],
                'win_rate': win_rate_a,
                'avg_points': avg_points_a
            },
            'variant_b': {
                'params': test['variant_b'],
                'battles': results_b['battles'],
                'wins': results_b['wins'],
                'win_rate': win_rate_b,
                'avg_points': avg_points_b
            },
            'winner': 'A' if win_rate_a > win_rate_b else 'B' if win_rate_b > win_rate_a else 'TIE',
            'confidence': 'HIGH' if total_battles >= min_samples else 'LOW',
            'recommendation': self._get_recommendation(win_rate_a, win_rate_b, total_battles)
        }

    def _get_recommendation(self, rate_a: float, rate_b: float, samples: int) -> str:
        """Get recommendation based on results."""
        if samples < 20:
            return "Need more data (min 20 battles)"

        diff = abs(rate_a - rate_b)
        if diff < 0.05:
            return "No significant difference - keep testing or use either"
        elif rate_a > rate_b:
            return f"Variant A is {diff*100:.1f}% better - consider adopting"
        else:
            return f"Variant B is {diff*100:.1f}% better - consider adopting"


@dataclass
class LearningAgent:
    """
    Self-improving agent that combines all learning systems.

    Features:
    - Q-learning for action selection
    - Parameter optimization
    - Performance tracking
    - Adaptive strategy switching
    """
    name: str
    agent_type: str
    q_learner: QLearningAgent = field(default_factory=lambda: None)
    current_params: Dict = field(default_factory=dict)
    performance_history: List[Dict] = field(default_factory=list)
    total_battles: int = 0
    total_wins: int = 0

    def __post_init__(self):
        if self.q_learner is None:
            self.q_learner = QLearningAgent(self.agent_type)

    def learn_from_battle(
        self,
        won: bool,
        points_donated: int,
        battle_stats: Dict
    ):
        """Update learning after a battle."""
        self.total_battles += 1
        if won:
            self.total_wins += 1

        # Calculate reward
        reward = self._calculate_reward(won, points_donated, battle_stats)

        # Record performance
        self.performance_history.append({
            'battle': self.total_battles,
            'won': won,
            'points': points_donated,
            'reward': reward,
            'win_rate': self.total_wins / self.total_battles
        })

        # Keep only last 100 records
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        return reward

    def _calculate_reward(self, won: bool, points: int, stats: Dict) -> float:
        """Calculate reward signal for learning."""
        reward = 0.0

        # Win/loss reward
        reward += 100 if won else -50

        # Points contributed (normalized)
        reward += points / 10000

        # Efficiency bonus
        if stats.get('gifts_sent', 0) > 0:
            efficiency = points / (stats['gifts_sent'] * 1000)
            reward += efficiency * 10

        # Phase timing bonus
        if stats.get('boost2_triggered', False):
            reward += 20

        # Glove success bonus
        if stats.get('gloves_activated', 0) > 0:
            reward += stats['gloves_activated'] * 15

        # BUDGET EFFICIENCY BONUS
        budget_efficiency = stats.get('creator_budget_efficiency', 0)
        opponent_efficiency = stats.get('opponent_budget_efficiency', 0)

        # Reward efficient spending (points per coin)
        if budget_efficiency > 0:
            reward += budget_efficiency * 5  # Bonus for good efficiency

        # Extra reward for outperforming opponent's efficiency
        if budget_efficiency > opponent_efficiency:
            reward += 15  # Beat opponent's efficiency

        # Budget conservation bonus - reward not running out
        budget_advantage = stats.get('budget_advantage', 0)
        if budget_advantage > 0:
            # Started with more budget - expect to use it well
            if won:
                reward += 10  # Converted advantage to win
            else:
                reward -= 20  # Wasted advantage
        elif budget_advantage < 0:
            # Started with less budget - reward efficiency
            if won:
                reward += 25  # Won despite disadvantage!

        return reward

    def get_win_rate(self) -> float:
        """Get current win rate."""
        return self.total_wins / max(self.total_battles, 1)

    def get_recent_performance(self, n: int = 10) -> Dict:
        """Get performance over last n battles."""
        recent = self.performance_history[-n:] if self.performance_history else []
        if not recent:
            return {'battles': 0, 'wins': 0, 'win_rate': 0, 'avg_reward': 0}

        wins = sum(1 for r in recent if r['won'])
        return {
            'battles': len(recent),
            'wins': wins,
            'win_rate': wins / len(recent),
            'avg_reward': sum(r['reward'] for r in recent) / len(recent)
        }

    def save_to_db(self, db: 'BattleHistoryDB'):
        """Save learning state to database for persistence."""
        db.save_agent_learning_state(
            agent_name=self.name,
            agent_type=self.agent_type,
            total_battles=self.total_battles,
            total_wins=self.total_wins,
            performance_history=self.performance_history,
            current_params=self.current_params,
            epsilon=self.q_learner.epsilon if self.q_learner else 0.3
        )

        # Also save Q-table if present
        if self.q_learner:
            self.q_learner.save_to_db(db)

    def load_from_db(self, db: 'BattleHistoryDB') -> bool:
        """Load learning state from database. Returns True if loaded."""
        data = db.load_agent_learning_state(self.name)
        if not data:
            return False

        self.total_battles = data.get('total_battles', 0)
        self.total_wins = data.get('total_wins', 0)
        self.performance_history = data.get('performance_history', [])
        self.current_params = data.get('current_params', {})

        # Also load Q-table if present
        if self.q_learner:
            self.q_learner.load_from_db(db)
            self.q_learner.epsilon = data.get('epsilon', 0.3)

        print(f"📚 {self.name}: Loaded state ({self.total_battles} battles, {self.get_win_rate()*100:.1f}% win rate)")
        return True


class OpponentPatternTracker:
    """
    Track and analyze opponent spending patterns for counter-strategies.

    Detects patterns like:
    - aggressive_early: Heavy spending in first 60s
    - conservative_saver: Minimal spending until boosts
    - boost_focused: Only spends during multiplier phases
    - whale_hunter: Sends whales to trigger x5
    - random: No clear pattern
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset for new battle."""
        self.phase_spending = {
            'early': 0,      # First 60s
            'middle': 0,     # 60s-180s
            'boost': 0,      # During boost phases
            'final': 0,      # Last 30s
        }
        self.gift_events = []       # (time, amount, phase)
        self.gift_intervals = []    # Time between gifts
        self.whale_events = []      # When they send whales (10k+)
        self.last_gift_time = None
        self.detected_strategy = None
        self.confidence = 0.0
        self.pattern_announced = False

    def update(self, time: int, amount: int, phase: str, time_remaining: int):
        """Update pattern data from gift event."""
        # Track gift timing
        if self.last_gift_time is not None:
            interval = time - self.last_gift_time
            self.gift_intervals.append(interval)
        self.last_gift_time = time

        # Categorize by game phase
        if time_remaining > 240:
            phase_key = 'early'
        elif time_remaining > 120:
            phase_key = 'middle'
        elif time_remaining <= 30:
            phase_key = 'final'
        else:
            phase_key = 'boost' if 'boost' in phase.lower() else 'middle'

        self.phase_spending[phase_key] = self.phase_spending.get(phase_key, 0) + amount
        self.gift_events.append((time, amount, phase_key))

        # Track whale gifts
        if amount >= 10000:
            self.whale_events.append((time, amount))

        # Re-detect pattern every 5 gifts
        if len(self.gift_events) % 5 == 0 and len(self.gift_events) >= 5:
            self._detect_pattern()

    def _detect_pattern(self):
        """Identify opponent strategy based on spending patterns."""
        total = sum(self.phase_spending.values())
        if total < 1000:
            self.detected_strategy = 'unknown'
            self.confidence = 0.0
            return

        # Calculate percentages
        early_pct = self.phase_spending['early'] / total if total > 0 else 0
        boost_pct = self.phase_spending['boost'] / total if total > 0 else 0
        final_pct = self.phase_spending['final'] / total if total > 0 else 0

        # Detect patterns
        if early_pct > 0.5:
            self.detected_strategy = 'aggressive_early'
            self.confidence = min(0.9, early_pct)
        elif boost_pct > 0.6:
            self.detected_strategy = 'boost_focused'
            self.confidence = min(0.9, boost_pct)
        elif final_pct > 0.4:
            self.detected_strategy = 'final_push'
            self.confidence = min(0.85, final_pct)
        elif len(self.whale_events) >= 3:
            self.detected_strategy = 'whale_hunter'
            self.confidence = min(0.8, len(self.whale_events) * 0.15)
        elif total < 5000 and len(self.gift_events) > 10:
            self.detected_strategy = 'conservative_saver'
            self.confidence = 0.7
        else:
            self.detected_strategy = 'balanced'
            self.confidence = 0.5

    def detect_pattern(self) -> str:
        """Get detected strategy (call after enough data)."""
        if len(self.gift_events) < 5:
            return None
        return self.detected_strategy if self.confidence > 0.5 else None

    def get_counter_strategy(self) -> Dict:
        """Return counter-strategy adjustments based on detected pattern."""
        if not self.detected_strategy or self.confidence < 0.5:
            return {}

        counters = {
            'aggressive_early': {
                'description': 'Match early aggression, conserve for boosts',
                'aggression_early': 0.7,
                'aggression_boost': 0.9,
                'conserve_for_boost': True,
            },
            'conservative_saver': {
                'description': 'Build lead early, pressure them to spend',
                'aggression_early': 0.8,
                'aggression_boost': 0.7,
                'conserve_for_boost': False,
            },
            'boost_focused': {
                'description': 'Counter their boosts with bigger gifts',
                'aggression_early': 0.3,
                'aggression_boost': 0.95,
                'whale_in_boost': True,
            },
            'whale_hunter': {
                'description': 'Match whales, save for x5 response',
                'aggression_early': 0.4,
                'aggression_boost': 0.85,
                'counter_whale': True,
            },
            'final_push': {
                'description': 'Build lead early, defend in final',
                'aggression_early': 0.7,
                'aggression_boost': 0.7,
                'aggression_final': 0.95,
            },
            'balanced': {
                'description': 'Standard strategy',
                'aggression_early': 0.5,
                'aggression_boost': 0.8,
            },
        }

        return counters.get(self.detected_strategy, {})

    def get_status(self) -> Dict:
        """Get current tracking status."""
        return {
            'events_tracked': len(self.gift_events),
            'total_spending': sum(self.phase_spending.values()),
            'phase_breakdown': self.phase_spending.copy(),
            'whale_count': len(self.whale_events),
            'detected_strategy': self.detected_strategy,
            'confidence': self.confidence,
            'avg_interval': sum(self.gift_intervals) / len(self.gift_intervals) if self.gift_intervals else 0,
        }


# === DRAMATIC ANNOUNCEMENTS ===
PATTERN_DETECTED_ANNOUNCEMENT = '''
╔══════════════════════════════════════════════════════════════╗
║  🎯🎯🎯  P A T T E R N   D E T E C T E D  🎯🎯🎯             ║
║                                                              ║
║     Enemy Strategy Identified: {strategy}                    ║
║     Confidence: {confidence:.0%}                                       ║
║     Counter-measures ENGAGED!                                ║
╚══════════════════════════════════════════════════════════════╝'''


if __name__ == '__main__':
    print("Agent Learning System Demo")
    print("="*60)

    # Test Q-Learning Agent
    print("\n🤖 Testing Q-Learning Agent...")
    q_agent = QLearningAgent('test_agent')

    # Create sample state
    state = State(
        time_remaining=30,
        score_diff=-50000,
        multiplier=3.0,
        in_boost=True,
        boost2_triggered=False,
        phase="BOOST_1",
        gloves_available=2,
        power_ups_available=['HAMMER', 'FOG']
    )

    print(f"   State tuple: {state.to_tuple()}")

    # Choose action
    action = q_agent.choose_action(state)
    print(f"   Chosen action: {action.value}")

    # Create experience
    next_state = State(
        time_remaining=29,
        score_diff=-40000,
        multiplier=3.0,
        in_boost=True,
        boost2_triggered=False,
        phase="BOOST_1",
        gloves_available=1,
        power_ups_available=['HAMMER', 'FOG']
    )

    exp = Experience(
        state=state,
        action=action,
        reward=50.0,
        next_state=next_state,
        done=False
    )

    q_agent.update(exp)
    q_agent.end_episode(won=True, total_reward=150.0)

    print(f"   Stats: {q_agent.get_stats()}")

    # Test Strategy Optimizer
    print("\n🧬 Testing Strategy Optimizer...")
    db = BattleHistoryDB("data/test_learning.db")
    optimizer = StrategyOptimizer(db, population_size=5)

    optimized = optimizer.run_optimization_cycle()
    for agent_type, params in optimized.items():
        print(f"   {agent_type}: {params}")

    # Test A/B Framework
    print("\n📊 Testing A/B Testing Framework...")
    ab_test = ABTestingFramework(db)

    test_name = ab_test.create_test(
        test_name="snipe_window_test",
        variant_a={'snipe_window': 5},
        variant_b={'snipe_window': 8},
        agent_type='sniper'
    )

    # Simulate some results
    for _ in range(15):
        ab_test.record_result(test_name, 'A', random.random() > 0.4, random.randint(100000, 300000))
        ab_test.record_result(test_name, 'B', random.random() > 0.5, random.randint(100000, 300000))

    results = ab_test.get_test_results(test_name)
    print(f"   Test: {results['test_name']}")
    print(f"   Variant A win rate: {results['variant_a']['win_rate']*100:.1f}%")
    print(f"   Variant B win rate: {results['variant_b']['win_rate']*100:.1f}%")
    print(f"   Winner: {results['winner']}")
    print(f"   Recommendation: {results['recommendation']}")

    # Test Learning Agent
    print("\n🎓 Testing Learning Agent...")
    learning_agent = LearningAgent(name="TestAgent", agent_type="sniper")

    # Simulate battles
    for i in range(5):
        won = random.random() > 0.4
        points = random.randint(50000, 300000)
        reward = learning_agent.learn_from_battle(
            won=won,
            points_donated=points,
            battle_stats={'gifts_sent': random.randint(1, 5), 'boost2_triggered': random.random() > 0.5}
        )
        print(f"   Battle {i+1}: {'Win' if won else 'Loss'}, Points: {points:,}, Reward: {reward:.1f}")

    print(f"\n   Overall win rate: {learning_agent.get_win_rate()*100:.1f}%")
    print(f"   Recent performance: {learning_agent.get_recent_performance(5)}")

    db.close()
    print("\n✅ Learning System Demo Complete!")
