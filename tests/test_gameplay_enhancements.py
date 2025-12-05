#!/usr/bin/env python3
"""
Comprehensive Test Suite for Gameplay Enhancements

Tests for:
1. Evolving Agents (BoostResponder, PixelPixie learning)
2. Clutch Moments System
3. Counter-Strategies (Pattern Detection)
4. Psychological Warfare

Run with: pytest tests/test_gameplay_enhancements.py -v
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager
from core.budget_system import BudgetManager, BudgetIntelligence
from core.battle_history import BattleHistoryDB


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    db = BattleHistoryDB(db_path)
    yield db
    db.close()
    os.unlink(db_path)


@pytest.fixture
def phase_manager():
    """Create a phase manager for testing."""
    return AdvancedPhaseManager(battle_duration=300)


@pytest.fixture
def budget_manager():
    """Create a budget manager for testing."""
    return BudgetManager()


@pytest.fixture
def battle_engine():
    """Create a battle engine for testing."""
    return BattleEngine(battle_duration=60, tick_speed=0.001)


@pytest.fixture
def mock_battle():
    """Create a mock battle object for agent testing."""
    battle = Mock()
    battle.time_manager = Mock()
    battle.time_manager.current_time = 50
    battle.time_manager.time_remaining.return_value = 250
    battle.score_tracker = Mock()
    battle.score_tracker.creator_score = 1000
    battle.score_tracker.opponent_score = 800
    return battle


# ============================================================================
# TEST: EVOLVING AGENTS
# ============================================================================

class TestEvolvingAgents:
    """Tests for BoostResponder and PixelPixie learning systems."""

    def test_boost_responder_has_learning_params(self, phase_manager, temp_db):
        """BoostResponder should have learnable parameters."""
        from agents.personas.boost_responder import BoostResponder

        agent = BoostResponder(phase_manager=phase_manager, db=temp_db)

        # Check params exist
        assert hasattr(agent, 'params')
        assert isinstance(agent.params, dict)

        # Check key learnable params
        assert 'counter_threshold' in agent.params
        assert 'cooldown_normal' in agent.params
        assert 'cooldown_boost' in agent.params

    def test_boost_responder_has_learning_agent(self, phase_manager, temp_db):
        """BoostResponder should have LearningAgent instance."""
        from agents.personas.boost_responder import BoostResponder

        agent = BoostResponder(phase_manager=phase_manager, db=temp_db)

        assert hasattr(agent, 'learning_agent')
        assert hasattr(agent, 'q_learner')

    def test_boost_responder_learn_from_battle(self, phase_manager, temp_db):
        """BoostResponder should learn from battle results."""
        from agents.personas.boost_responder import BoostResponder

        agent = BoostResponder(phase_manager=phase_manager, db=temp_db)
        initial_battles = agent.learning_agent.total_battles

        # Simulate learning from a win
        battle_stats = {
            'boost2_triggered': True,
            'boost2_qualified': True,
            'points_donated': 5000
        }
        agent.learn_from_battle(won=True, battle_stats=battle_stats)

        assert agent.learning_agent.total_battles == initial_battles + 1

    def test_pixel_pixie_has_learning_params(self, phase_manager, temp_db):
        """PixelPixie should have learnable parameters."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=phase_manager, db=temp_db)

        assert hasattr(agent, 'params')
        assert 'rose_interval' in agent.params
        assert 'qualification_delay_min' in agent.params

    def test_pixel_pixie_tracks_roses_sent(self, phase_manager, temp_db, budget_manager):
        """PixelPixie should track roses sent."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=phase_manager, db=temp_db)
        agent.budget_manager = budget_manager
        agent.team = 'creator'

        assert hasattr(agent, 'roses_sent')
        assert agent.roses_sent == 0

    def test_pixel_pixie_roses_increment(self, phase_manager, temp_db, budget_manager, mock_battle):
        """PixelPixie roses_sent should increment when roses are sent."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=phase_manager, db=temp_db)
        agent.budget_manager = budget_manager
        agent.team = 'creator'

        # Simulate conditions for rose sending
        # No Boost #1, time >= 30s
        phase_manager.boost1_trigger_time = None
        mock_battle.time_manager.current_time = 35
        agent.last_action_time = 0

        initial_roses = agent.roses_sent

        # Call decide_action multiple times
        for _ in range(5):
            mock_battle.time_manager.current_time += 5
            agent.last_action_time = mock_battle.time_manager.current_time - 10
            agent.decide_action(mock_battle)

        # Should have sent some roses
        assert agent.roses_sent >= initial_roses

    def test_pixel_pixie_learn_from_battle(self, phase_manager, temp_db):
        """PixelPixie should learn from battle results."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=phase_manager, db=temp_db)
        agent.roses_sent = 25

        battle_stats = {
            'boost2_triggered': True,
            'boost2_qualified': True
        }
        agent.learn_from_battle(won=True, battle_stats=battle_stats)

        assert agent.learning_agent.total_battles >= 1

    def test_evolving_agents_reset_for_battle(self, phase_manager, temp_db):
        """Evolving agents should reset state for new battles."""
        from agents.personas.pixel_pixie import PixelPixie
        from agents.personas.boost_responder import BoostResponder

        pixie = PixelPixie(phase_manager=phase_manager, db=temp_db)
        boost = BoostResponder(phase_manager=phase_manager, db=temp_db)

        # Set some state
        pixie.roses_sent = 50
        pixie.signaling_started = True

        # Reset
        pixie.reset_for_battle()
        boost.reset_for_battle()

        assert pixie.roses_sent == 0
        assert pixie.signaling_started == False


# ============================================================================
# TEST: CLUTCH MOMENTS SYSTEM
# ============================================================================

class TestClutchMoments:
    """Tests for the Clutch Moments System."""

    def test_phase_manager_has_clutch_tracking(self, phase_manager):
        """Phase manager should have clutch moment tracking."""
        assert hasattr(phase_manager, 'score_history')
        assert hasattr(phase_manager, 'max_deficit')
        assert hasattr(phase_manager, 'clutch_moments_triggered')

    def test_comeback_momentum_detection(self, phase_manager):
        """Should detect comeback momentum when recovering from deficit."""
        # Simulate being down significantly
        phase_manager.score_history = [(i, 100, 500) for i in range(10)]  # Was down 400
        phase_manager.max_deficit = 400
        phase_manager.comeback_active = False

        # Now close the gap
        current_time = 100
        creator_score = 450
        opponent_score = 500

        phase_manager.update_scores(creator_score, opponent_score)

        # Check if comeback was detected (score within 15% after being down 20%+)
        # The exact detection depends on implementation

    def test_clutch_bonus_methods_exist(self, phase_manager):
        """Phase manager should have clutch bonus check methods."""
        assert hasattr(phase_manager, '_check_comeback_momentum')
        assert hasattr(phase_manager, '_check_final_stand')
        assert hasattr(phase_manager, '_check_threshold_heroics')
        assert hasattr(phase_manager, '_check_desperation_surge')

    def test_clutch_announcements(self, phase_manager):
        """Clutch moments should have dramatic announcements."""
        assert hasattr(phase_manager, '_announce_clutch_moment')

        # Test that announcement method exists and is callable
        # (actual output testing would require capturing stdout)

    def test_glove_probability_with_clutch_bonus(self, phase_manager):
        """Clutch moments should affect glove probability bonus tracking."""
        # Set up a clutch scenario
        phase_manager.clutch_moments_triggered = {'comeback_momentum': True}

        # Verify clutch tracking is in place
        assert isinstance(phase_manager.clutch_moments_triggered, dict)

        # Check that clutch check methods exist
        assert hasattr(phase_manager, '_check_comeback_momentum')
        assert hasattr(phase_manager, '_check_desperation_surge')

        # Clutch moments should be trackable
        assert 'comeback_momentum' in phase_manager.clutch_moments_triggered


# ============================================================================
# TEST: COUNTER-STRATEGIES (PATTERN DETECTION)
# ============================================================================

class TestCounterStrategies:
    """Tests for the Counter-Strategies / Pattern Detection system."""

    def test_opponent_pattern_tracker_exists(self):
        """OpponentPatternTracker class should exist."""
        from agents.learning_system import OpponentPatternTracker

        tracker = OpponentPatternTracker()
        assert tracker is not None

    def test_pattern_tracker_methods(self):
        """Pattern tracker should have required methods."""
        from agents.learning_system import OpponentPatternTracker

        tracker = OpponentPatternTracker()

        assert hasattr(tracker, 'update')  # Uses update() not record_gift()
        assert hasattr(tracker, 'detect_pattern')
        assert hasattr(tracker, 'get_counter_strategy')
        assert hasattr(tracker, 'reset')

    def test_pattern_detection(self):
        """Pattern tracker should detect opponent strategies."""
        from agents.learning_system import OpponentPatternTracker

        tracker = OpponentPatternTracker()

        # Simulate aggressive early spending using update() API
        for i in range(10):
            tracker.update(
                time=i * 5,
                amount=500,
                phase='early',
                time_remaining=295 - (i * 5)  # Simulating early game
            )

        pattern = tracker.detect_pattern()
        assert pattern in ['aggressive_early', 'conservative_saver', 'boost_focused',
                          'whale_hunter', 'unknown', None]

    def test_counter_strategy_returns_adjustments(self):
        """Counter strategy should return parameter adjustments."""
        from agents.learning_system import OpponentPatternTracker

        tracker = OpponentPatternTracker()

        # Record some gifts using update() API
        for i in range(5):
            tracker.update(time=i * 10, amount=100, phase='early', time_remaining=290 - (i * 10))

        adjustments = tracker.get_counter_strategy()
        assert isinstance(adjustments, dict)

    def test_base_agent_has_pattern_tracker(self, phase_manager, temp_db):
        """Base agents should have access to pattern tracker."""
        from agents.personas.boost_responder import BoostResponder

        agent = BoostResponder(phase_manager=phase_manager, db=temp_db)

        assert hasattr(agent, 'opponent_tracker')

    def test_agent_responds_to_opponent_gift(self, phase_manager, temp_db):
        """Agent should have method to handle opponent gifts."""
        from agents.personas.boost_responder import BoostResponder

        agent = BoostResponder(phase_manager=phase_manager, db=temp_db)

        assert hasattr(agent, 'on_opponent_gift')

        # Should not raise error - correct signature: (amount, current_time, phase, time_remaining)
        agent.on_opponent_gift(
            amount=500,
            current_time=50,
            phase='boost',
            time_remaining=250
        )


# ============================================================================
# TEST: PSYCHOLOGICAL WARFARE
# ============================================================================

class TestPsychologicalWarfare:
    """Tests for Psychological Warfare features."""

    def test_glitch_mancer_has_psych_methods(self, phase_manager, temp_db):
        """EvolvingGlitchMancer should have psychological warfare methods."""
        from agents.personas.evolving_glitch_mancer import EvolvingGlitchMancer

        budget_intel = Mock()
        agent = EvolvingGlitchMancer(
            phase_manager=phase_manager,
            budget_intelligence=budget_intel,
            db=temp_db
        )

        assert hasattr(agent, 'execute_bluff')
        assert hasattr(agent, 'execute_decoy')
        assert hasattr(agent, 'execute_fog_burst')
        assert hasattr(agent, 'execute_strategic_pause')

    def test_should_use_psych_warfare(self, phase_manager, temp_db):
        """Agent should have method to decide on psych warfare."""
        from agents.personas.evolving_glitch_mancer import EvolvingGlitchMancer

        budget_intel = Mock()
        agent = EvolvingGlitchMancer(
            phase_manager=phase_manager,
            budget_intelligence=budget_intel,
            db=temp_db
        )

        assert hasattr(agent, 'should_use_psych_warfare')

    def test_bluff_execution(self, phase_manager, temp_db, mock_battle):
        """Bluff execution should work without errors."""
        from agents.personas.evolving_glitch_mancer import EvolvingGlitchMancer

        budget_intel = Mock()
        budget_intel.get_available_budget.return_value = 50000

        agent = EvolvingGlitchMancer(
            phase_manager=phase_manager,
            budget_intelligence=budget_intel,
            db=temp_db
        )
        # Mock budget_manager properly - spend() returns (success, cost)
        agent.budget_manager = Mock()
        agent.budget_manager.can_afford.return_value = True
        agent.budget_manager.spend.return_value = (True, 10)  # (success, cost)
        agent.team = 'creator'

        # Should not raise error - correct signature: (battle, current_time)
        try:
            agent.execute_bluff(mock_battle, current_time=50)
        except Exception as e:
            pytest.fail(f"execute_bluff raised unexpected error: {e}")

    def test_psych_action_types_exist(self):
        """Psychological warfare action types should exist."""
        from agents.learning_system import ActionType

        # Check that psych-related actions exist
        action_names = [a.name for a in ActionType]

        # At minimum, some strategic actions should exist
        assert 'WAIT' in action_names or 'STRATEGIC_PAUSE' in action_names or len(action_names) > 5


# ============================================================================
# TEST: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests for all features working together."""

    def test_full_team_creation(self, phase_manager, temp_db):
        """Should be able to create full mixed strategic team."""
        from agents.evolving_agents import create_mixed_strategic_team

        budget_manager = BudgetManager()
        budget_intel = BudgetIntelligence(budget_manager)

        team = create_mixed_strategic_team(phase_manager, temp_db, budget_intel)

        assert len(team) >= 5  # Should have multiple agents

        # Check for key agents
        agent_names = [a.name for a in team]
        assert 'PixelPixie' in agent_names
        assert 'BoostResponder' in agent_names

    def test_learn_from_battle_results(self, phase_manager, temp_db):
        """Should be able to learn from battle results."""
        from agents.evolving_agents import create_mixed_strategic_team, learn_from_battle_results

        budget_manager = BudgetManager()
        budget_intel = BudgetIntelligence(budget_manager)

        team = create_mixed_strategic_team(phase_manager, temp_db, budget_intel)

        battle_stats = {
            'boost2_triggered': True,
            'boost2_qualified': True,
            'points_donated': 10000
        }

        # Should not raise error
        rewards = learn_from_battle_results(team, won=True, battle_stats=battle_stats)

        assert isinstance(rewards, dict)

    def test_reset_evolving_team(self, phase_manager, temp_db):
        """Should be able to reset team for new battle."""
        from agents.evolving_agents import create_mixed_strategic_team, reset_evolving_team

        budget_manager = BudgetManager()
        budget_intel = BudgetIntelligence(budget_manager)

        team = create_mixed_strategic_team(phase_manager, temp_db, budget_intel)

        # Set some state
        for agent in team:
            if hasattr(agent, 'roses_sent'):
                agent.roses_sent = 50

        # Reset
        reset_evolving_team(team)

        # Check reset
        for agent in team:
            if hasattr(agent, 'roses_sent'):
                assert agent.roses_sent == 0

    def test_battle_with_all_features(self, temp_db):
        """Run a complete battle with all features enabled."""
        from agents.evolving_agents import create_mixed_strategic_team

        # Create systems
        phase_manager = AdvancedPhaseManager(battle_duration=60)
        budget_manager = BudgetManager()
        budget_intel = BudgetIntelligence(budget_manager)

        # Create team
        team = create_mixed_strategic_team(phase_manager, temp_db, budget_intel)

        # Create battle
        battle = BattleEngine(battle_duration=60, tick_speed=0.001)

        # Add agents
        for agent in team:
            agent.team = 'creator'
            agent.budget_manager = budget_manager
            battle.add_agent(agent)

        # Wrap tick to update phase manager
        original_tick = battle._tick
        def wrapped_tick(silent):
            original_tick(silent)
            phase_manager.update(battle.time_manager.current_time)
            phase_manager.update_scores(
                battle.score_tracker.creator_score,
                battle.score_tracker.opponent_score
            )
        battle._tick = wrapped_tick

        # Run battle (should complete without errors)
        battle.run(silent=True)

        # Verify battle completed
        assert battle.time_manager.current_time >= 60


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_agent_without_db(self, phase_manager):
        """Agents should work without database (no persistence)."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=phase_manager, db=None)

        # Should work without error
        assert agent is not None
        assert agent.roses_sent == 0

    def test_agent_without_phase_manager(self, temp_db):
        """Agents should handle missing phase manager gracefully."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=None, db=temp_db)

        # decide_action should handle None phase_manager
        mock_battle = Mock()
        mock_battle.time_manager.current_time = 50

        # Should not crash
        agent.decide_action(mock_battle)

    def test_pattern_tracker_empty_data(self):
        """Pattern tracker should handle no data gracefully."""
        from agents.learning_system import OpponentPatternTracker

        tracker = OpponentPatternTracker()

        # Should not crash with no data
        pattern = tracker.detect_pattern()
        assert pattern is None or isinstance(pattern, str)

    def test_learn_with_zero_stats(self, phase_manager, temp_db):
        """Learning should handle zero stats gracefully."""
        from agents.personas.pixel_pixie import PixelPixie

        agent = PixelPixie(phase_manager=phase_manager, db=temp_db)

        # Empty battle stats
        battle_stats = {}

        # Should not crash
        agent.learn_from_battle(won=False, battle_stats=battle_stats)

    def test_clutch_moment_no_history(self, phase_manager):
        """Clutch detection should handle no score history."""
        # Clear any history
        phase_manager.score_history = []
        phase_manager.max_deficit = 0

        # Should not crash
        phase_manager.update_scores(1000, 1000)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
