"""
Tests for New Agent Types (v1.3)

Tests for:
- DefenseMaster (counter-focused)
- BudgetOptimizer (efficiency specialist)
- ChaoticTrickster (psychological warfare)
- SynergyCoordinator (team combos)
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch

# Import agents
from agents.specialists.defense_master import DefenseMaster
from agents.specialists.budget_optimizer import BudgetOptimizer
from agents.specialists.chaotic_trickster import ChaoticTrickster
from agents.specialists.synergy_coordinator import SynergyCoordinator, ComboType

# Import dependencies
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.battle_history import BattleHistoryDB


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def phase_manager():
    """Create a phase manager for testing."""
    pm = AdvancedPhaseManager(battle_duration=180)
    # Add power-ups
    pm.add_power_up(PowerUpType.HAMMER, "creator")
    pm.add_power_up(PowerUpType.HAMMER, "creator")
    pm.add_power_up(PowerUpType.FOG, "creator")
    pm.add_power_up(PowerUpType.FOG, "creator")
    return pm


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
def mock_battle():
    """Create a mock battle engine."""
    battle = Mock()
    battle.time_manager = Mock()
    battle.time_manager.current_time = 100
    battle.time_manager.time_remaining.return_value = 80
    battle.score_tracker = Mock()
    battle.score_tracker.creator_score = 50000
    battle.score_tracker.opponent_score = 45000
    battle.score_tracker.add_creator_points = Mock()
    return battle


# ============================================================================
# TEST DEFENSEMASTER
# ============================================================================

class TestDefenseMaster:
    """Tests for DefenseMaster agent."""

    def test_defense_master_creation(self, phase_manager):
        """Test DefenseMaster can be created."""
        agent = DefenseMaster(phase_manager=phase_manager)
        assert agent.name == "DefenseMaster"
        assert agent.emoji == "🛡️"
        assert agent.hammers_available == 2
        assert agent.fogs_available == 2

    def test_defense_master_capabilities(self, phase_manager):
        """Test DefenseMaster has correct capabilities."""
        agent = DefenseMaster(phase_manager=phase_manager)
        caps = agent.get_capabilities()
        assert "HAMMER" in caps
        assert "FOG" in caps
        assert "COUNTER_STRATEGY" in caps

    def test_defense_master_threat_assessment(self, phase_manager, mock_battle):
        """Test DefenseMaster threat assessment."""
        agent = DefenseMaster(phase_manager=phase_manager)
        threat = agent._assess_threat_level(mock_battle)
        assert 0 <= threat <= 1.0

    def test_defense_master_hammer_detection(self, phase_manager):
        """Test DefenseMaster detects when to use hammer."""
        agent = DefenseMaster(phase_manager=phase_manager)

        # No x5 active - shouldn't use hammer
        phase_manager.active_glove_x5 = False
        assert not agent._should_use_hammer(None, 100)

        # Opponent x5 active - should consider hammer
        phase_manager.active_glove_x5 = True
        phase_manager.active_glove_owner = "opponent"
        # Probability-based, so may or may not trigger

    def test_defense_master_reset(self, phase_manager):
        """Test DefenseMaster reset for battle."""
        agent = DefenseMaster(phase_manager=phase_manager)
        agent.hammers_used = 1
        agent.fogs_used = 1
        agent.opponent_gift_count = 5

        agent.reset_for_battle()

        assert agent.hammers_used == 0
        assert agent.fogs_used == 0
        assert agent.opponent_gift_count == 0

    def test_defense_master_opponent_tracking(self, phase_manager):
        """Test DefenseMaster tracks opponent gifts."""
        agent = DefenseMaster(phase_manager=phase_manager)

        agent.on_opponent_gift(10000, 50, "normal", 130)

        assert agent.opponent_gift_count == 1
        assert agent.opponent_total_donated == 10000
        assert agent.opponent_whale_incoming == True


# ============================================================================
# TEST BUDGETOPTIMIZER
# ============================================================================

class TestBudgetOptimizer:
    """Tests for BudgetOptimizer agent."""

    def test_budget_optimizer_creation(self, phase_manager):
        """Test BudgetOptimizer can be created."""
        agent = BudgetOptimizer(phase_manager=phase_manager)
        assert agent.name == "BudgetOptimizer"
        assert agent.emoji == "💰"
        assert agent.starting_budget == 200000  # Increased budget for more activity

    def test_budget_optimizer_capabilities(self, phase_manager):
        """Test BudgetOptimizer has correct capabilities."""
        agent = BudgetOptimizer(phase_manager=phase_manager)
        caps = agent.get_capabilities()
        assert "BUDGET_MANAGEMENT" in caps
        assert "EFFICIENCY_TRACKING" in caps

    def test_budget_optimizer_phase_detection(self, phase_manager):
        """Test BudgetOptimizer detects current phase."""
        agent = BudgetOptimizer(phase_manager=phase_manager)

        # Normal phase
        phase_manager.boost1_active = False
        phase_manager.boost2_active = False
        assert agent._get_current_phase(50, 130) == "normal"

        # Boost phase
        phase_manager.boost1_active = True
        assert agent._get_current_phase(50, 130) == "boost"

        # Final 30s
        phase_manager.boost1_active = False
        assert agent._get_current_phase(160, 20) == "final_30s"

    def test_budget_optimizer_efficiency_tracking(self, phase_manager):
        """Test BudgetOptimizer tracks efficiency."""
        agent = BudgetOptimizer(phase_manager=phase_manager)

        # Initially 0 spent
        assert agent._calculate_current_efficiency() == 1.0

        # After spending
        agent.budget_spent = 10000
        agent.effective_points_this_battle = 20000
        assert agent._calculate_current_efficiency() == 2.0

    def test_budget_optimizer_gift_preferences(self, phase_manager):
        """Test BudgetOptimizer has phase-based preferences."""
        agent = BudgetOptimizer(phase_manager=phase_manager)

        assert "Rose" in agent.gift_preferences["normal"]
        assert "Dragon Flame" in agent.gift_preferences["x5_active"]  # Big gift for x5

    def test_budget_optimizer_reset(self, phase_manager):
        """Test BudgetOptimizer reset for battle."""
        agent = BudgetOptimizer(phase_manager=phase_manager)
        agent.gifts_sent_this_battle = 10
        agent.budget_spent = 50000

        agent.reset_for_battle()

        assert agent.gifts_sent_this_battle == 0
        assert agent.budget_spent == 0


# ============================================================================
# TEST CHAOTICTRICKSTER
# ============================================================================

class TestChaoticTrickster:
    """Tests for ChaoticTrickster agent."""

    def test_chaotic_trickster_creation(self, phase_manager):
        """Test ChaoticTrickster can be created."""
        agent = ChaoticTrickster(phase_manager=phase_manager)
        assert agent.name == "ChaoticTrickster"
        assert agent.emoji == "🎭"
        assert 0.5 <= agent.chaos_level <= 0.8  # Boosted chaos level

    def test_chaotic_trickster_capabilities(self, phase_manager):
        """Test ChaoticTrickster has correct capabilities."""
        agent = ChaoticTrickster(phase_manager=phase_manager)
        caps = agent.get_capabilities()
        assert "PSYCHOLOGICAL_WARFARE" in caps
        assert "BLUFF" in caps
        assert "CHAOS" in caps

    def test_chaotic_trickster_cooldowns(self, phase_manager):
        """Test ChaoticTrickster cooldown system."""
        agent = ChaoticTrickster(phase_manager=phase_manager)

        # Initially all tactics available
        for tactic in ["bluff", "decoy", "pause", "fog_burst"]:
            assert agent._can_use_tactic(tactic, 0)

        # Start cooldown
        agent._start_cooldown("bluff", 10)
        assert not agent._can_use_tactic("bluff", 15)
        assert agent._can_use_tactic("bluff", 50)  # After cooldown

    def test_chaotic_trickster_bluff_state(self, phase_manager, mock_battle):
        """Test ChaoticTrickster bluff activation."""
        agent = ChaoticTrickster(phase_manager=phase_manager)

        # Mock can_afford and send_gift
        agent.can_afford = Mock(return_value=True)
        agent.send_gift = Mock(return_value=True)
        agent.send_message = Mock()

        agent._execute_bluff(mock_battle, 50)

        assert agent.bluff_active == True
        assert agent.bluff_end_time == 55  # 50 + 5
        assert agent.tactic_success["bluff"]["uses"] == 1

    def test_chaotic_trickster_chaos_report(self, phase_manager):
        """Test ChaoticTrickster chaos report."""
        agent = ChaoticTrickster(phase_manager=phase_manager)
        agent.tactic_success["bluff"]["uses"] = 5
        agent.tactic_success["bluff"]["successes"] = 3

        report = agent.get_chaos_report()

        assert "chaos_level" in report
        assert "tactics_used" in report
        assert report["tactics_used"]["bluff"] == 5

    def test_chaotic_trickster_reset(self, phase_manager):
        """Test ChaoticTrickster reset for battle."""
        agent = ChaoticTrickster(phase_manager=phase_manager)
        agent.bluff_active = True
        agent.cooldowns["bluff"] = 100

        agent.reset_for_battle()

        assert agent.bluff_active == False
        assert agent.cooldowns["bluff"] == 0


# ============================================================================
# TEST SYNERGYCOORDINATOR
# ============================================================================

class TestSynergyCoordinator:
    """Tests for SynergyCoordinator agent."""

    def test_synergy_coordinator_creation(self, phase_manager):
        """Test SynergyCoordinator can be created."""
        agent = SynergyCoordinator(phase_manager=phase_manager)
        assert agent.name == "SynergyCoordinator"
        assert agent.emoji == "🎯"
        assert agent.combos_executed == 0

    def test_synergy_coordinator_capabilities(self, phase_manager):
        """Test SynergyCoordinator has correct capabilities."""
        agent = SynergyCoordinator(phase_manager=phase_manager)
        caps = agent.get_capabilities()
        assert "TEAM_COORDINATION" in caps
        assert "COMBO_ORCHESTRATION" in caps

    def test_synergy_coordinator_team_registration(self, phase_manager):
        """Test SynergyCoordinator team registration."""
        agent = SynergyCoordinator(phase_manager=phase_manager)

        # Create mock team
        mock_agents = [Mock(name="Agent1"), Mock(name="Agent2")]
        mock_agents[0].name = "Agent1"
        mock_agents[1].name = "Agent2"

        agent.register_team(mock_agents)

        assert len(agent.team_agents) == 2
        assert "Agent1" in agent.team_states
        assert "Agent2" in agent.team_states

    def test_synergy_coordinator_combo_types(self):
        """Test ComboType definitions exist."""
        assert ComboType.FOG_WHALE == "fog_whale"
        assert ComboType.GLOVE_WHALE == "glove_whale"
        assert ComboType.TRIPLE_THREAT == "triple_threat"
        assert ComboType.FINAL_PUSH == "final_push"

    def test_synergy_coordinator_combo_tracking(self, phase_manager):
        """Test SynergyCoordinator combo tracking."""
        agent = SynergyCoordinator(phase_manager=phase_manager)

        # Track combo success
        agent.combo_success[ComboType.FOG_WHALE]["uses"] = 3
        agent.combo_success[ComboType.FOG_WHALE]["points"] = 15000

        report = agent.get_combo_report()

        assert "combos_executed" in report
        assert "combo_effectiveness" in report

    def test_synergy_coordinator_ready_count(self, phase_manager):
        """Test SynergyCoordinator counts ready agents."""
        agent = SynergyCoordinator(phase_manager=phase_manager)
        agent.team_states = {
            "Agent1": {"ready": True},
            "Agent2": {"ready": True},
            "Agent3": {"ready": False}
        }

        assert agent._count_ready_agents() == 2

    def test_synergy_coordinator_reset(self, phase_manager):
        """Test SynergyCoordinator reset for battle."""
        agent = SynergyCoordinator(phase_manager=phase_manager)
        agent.active_combo = ComboType.BOOST_BLITZ
        agent.combos_executed = 5

        # Register mock team first
        mock_agents = [Mock(name="Agent1")]
        mock_agents[0].name = "Agent1"
        agent.register_team(mock_agents)

        agent.reset_for_battle()

        assert agent.active_combo is None
        assert agent.combo_cooldown == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestNewAgentsIntegration:
    """Integration tests for new agents working together."""

    def test_all_agents_can_be_imported(self):
        """Test all new agents can be imported from specialists."""
        from agents.specialists import (
            DefenseMaster,
            BudgetOptimizer,
            ChaoticTrickster,
            SynergyCoordinator
        )
        assert DefenseMaster is not None
        assert BudgetOptimizer is not None
        assert ChaoticTrickster is not None
        assert SynergyCoordinator is not None

    def test_agents_have_learning_systems(self, phase_manager):
        """Test all new agents have learning systems."""
        agents = [
            DefenseMaster(phase_manager=phase_manager),
            BudgetOptimizer(phase_manager=phase_manager),
            ChaoticTrickster(phase_manager=phase_manager),
            SynergyCoordinator(phase_manager=phase_manager)
        ]

        for agent in agents:
            assert hasattr(agent, 'learning_agent')
            assert hasattr(agent, 'q_learner')
            assert hasattr(agent, 'learn_from_battle')

    def test_agents_have_reset_methods(self, phase_manager):
        """Test all new agents have reset methods."""
        agents = [
            DefenseMaster(phase_manager=phase_manager),
            BudgetOptimizer(phase_manager=phase_manager),
            ChaoticTrickster(phase_manager=phase_manager),
            SynergyCoordinator(phase_manager=phase_manager)
        ]

        for agent in agents:
            assert hasattr(agent, 'reset_for_battle')
            # Call reset - should not raise
            agent.reset_for_battle()

    def test_agents_inherit_base_agent(self, phase_manager):
        """Test all new agents inherit from BaseAgent."""
        from agents.base_agent import BaseAgent

        agents = [
            DefenseMaster(phase_manager=phase_manager),
            BudgetOptimizer(phase_manager=phase_manager),
            ChaoticTrickster(phase_manager=phase_manager),
            SynergyCoordinator(phase_manager=phase_manager)
        ]

        for agent in agents:
            assert isinstance(agent, BaseAgent)
            assert hasattr(agent, 'emotion_system')
            assert hasattr(agent, 'memory_system')
            assert hasattr(agent, 'send_gift')

    def test_create_mixed_team(self, phase_manager):
        """Test creating a team with new and old agents."""
        from agents.specialists import AgentKinetik, AgentStrikeMaster

        team = [
            DefenseMaster(phase_manager=phase_manager),
            BudgetOptimizer(phase_manager=phase_manager),
            ChaoticTrickster(phase_manager=phase_manager),
            SynergyCoordinator(phase_manager=phase_manager),
            AgentKinetik(),
            AgentStrikeMaster()
        ]

        assert len(team) == 6

        # All should have decide_action method
        for agent in team:
            assert hasattr(agent, 'decide_action')
