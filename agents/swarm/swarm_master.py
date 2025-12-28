"""
Swarm Master for TikTok Battle Simulator
=========================================

Adapted from MIRR-OR's SwarmMaster for battle agent management.

Responsibilities:
- Agent population management
- Swarm coordination and emergent behavior
- Agent role assignment
- Network topology optimization
- Health monitoring
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from .swarm_coordinator import (
    SwarmCoordinator,
    SwarmConfig,
    SwarmState,
    BattleRole,
    AgentPosition
)

logger = logging.getLogger(__name__)


class CoordinationPattern(Enum):
    """Swarm coordination patterns."""
    DISTRIBUTED = "distributed"       # All agents act independently
    HIERARCHICAL = "hierarchical"     # Leader-follower structure
    CLUSTERED = "clustered"           # Role-based clusters
    SYNCHRONIZED = "synchronized"     # All agents act together


class SwarmMaster:
    """
    Master controller for battle agent swarm.

    Manages agent population, coordinates behavior,
    and optimizes collective performance.

    Usage:
        master = SwarmMaster()
        master.register_agent(agent)
        master.set_battle_context(context)

        # Get coordinated decision
        decision = master.get_swarm_decision()
    """

    def __init__(
        self,
        swarm_config: Optional[SwarmConfig] = None,
        coordination_pattern: CoordinationPattern = CoordinationPattern.DISTRIBUTED
    ):
        """Initialize swarm master."""
        self._config = swarm_config or SwarmConfig()
        self._pattern = coordination_pattern

        # Agent tracking
        self._agents: Dict[str, Any] = {}
        self._agent_roles: Dict[str, BattleRole] = {}
        self._agent_health: Dict[str, float] = {}

        # Swarm coordinator
        self._coordinator = SwarmCoordinator(self._config)

        # Population targets by role
        self._target_population: Dict[BattleRole, int] = {
            BattleRole.SNIPER: 1,
            BattleRole.STRIKER: 1,
            BattleRole.SCOUT: 1,
            BattleRole.SUPPORT: 1,
            BattleRole.LEADER: 0,
            BattleRole.GUARDIAN: 0
        }

        # Entanglement graph (agent relationships)
        self._entanglements: Dict[str, Set[str]] = {}

        # Stats
        self._decisions_made = 0
        self._successful_coordinations = 0

        # Battle context
        self._battle_context: Dict[str, Any] = {}

        logger.info(f"[SwarmMaster] Initialized with pattern={coordination_pattern.value}")

    def register_agent(self, agent: Any) -> bool:
        """
        Register an agent with the swarm.

        Args:
            agent: Battle agent to register

        Returns:
            True if registered successfully
        """
        agent_id = getattr(agent, 'name', str(id(agent)))

        if agent_id in self._agents:
            return False

        self._agents[agent_id] = agent
        self._agent_health[agent_id] = 1.0

        # Determine role
        role = self._determine_role(agent)
        self._agent_roles[agent_id] = role

        # Initialize entanglements
        self._entanglements[agent_id] = set()
        self._update_entanglements(agent_id)

        # Sync with coordinator
        self._sync_coordinator()

        logger.info(f"[SwarmMaster] Registered agent: {agent_id} as {role.value}")
        return True

    def unregister_agent(self, agent_id: str):
        """Remove an agent from the swarm."""
        if agent_id in self._agents:
            del self._agents[agent_id]

        if agent_id in self._agent_roles:
            del self._agent_roles[agent_id]

        if agent_id in self._agent_health:
            del self._agent_health[agent_id]

        # Remove from entanglements
        if agent_id in self._entanglements:
            for partner in self._entanglements[agent_id]:
                if partner in self._entanglements:
                    self._entanglements[partner].discard(agent_id)
            del self._entanglements[agent_id]

        self._sync_coordinator()
        logger.info(f"[SwarmMaster] Unregistered agent: {agent_id}")

    def _determine_role(self, agent: Any) -> BattleRole:
        """Determine agent's role based on type and capabilities."""
        agent_name = getattr(agent, 'name', '').lower()
        agent_type = getattr(agent, 'agent_type', '').lower()

        if 'kinetik' in agent_name:
            return BattleRole.SNIPER
        elif 'strike' in agent_name:
            return BattleRole.STRIKER
        elif 'phase' in agent_name:
            return BattleRole.SCOUT
        elif 'loadout' in agent_name:
            return BattleRole.SUPPORT
        elif 'boost' in agent_name:
            return BattleRole.LEADER

        return BattleRole.SUPPORT

    def _update_entanglements(self, new_agent_id: str):
        """Update entanglement graph for new agent."""
        if self._pattern == CoordinationPattern.HIERARCHICAL:
            # Connect to leader agents
            for agent_id, role in self._agent_roles.items():
                if agent_id != new_agent_id and role == BattleRole.LEADER:
                    self._create_entanglement(new_agent_id, agent_id)

        elif self._pattern == CoordinationPattern.CLUSTERED:
            # Connect to same-role agents
            new_role = self._agent_roles.get(new_agent_id)
            for agent_id, role in self._agent_roles.items():
                if agent_id != new_agent_id and role == new_role:
                    self._create_entanglement(new_agent_id, agent_id)

        elif self._pattern == CoordinationPattern.SYNCHRONIZED:
            # Connect to all agents
            for agent_id in self._agents:
                if agent_id != new_agent_id:
                    self._create_entanglement(new_agent_id, agent_id)

        else:  # DISTRIBUTED
            # Connect to a few agents
            import random
            other_agents = [
                aid for aid in self._agents.keys()
                if aid != new_agent_id
            ]
            partners = random.sample(other_agents, min(2, len(other_agents)))
            for partner in partners:
                self._create_entanglement(new_agent_id, partner)

    def _create_entanglement(self, agent_a: str, agent_b: str):
        """Create bidirectional entanglement between agents."""
        if agent_a not in self._entanglements:
            self._entanglements[agent_a] = set()
        if agent_b not in self._entanglements:
            self._entanglements[agent_b] = set()

        self._entanglements[agent_a].add(agent_b)
        self._entanglements[agent_b].add(agent_a)

    def _sync_coordinator(self):
        """Sync agents with swarm coordinator."""
        agents_list = list(self._agents.values())
        self._coordinator.sync_agents(agents_list)

    def set_battle_context(self, context: Dict[str, Any]):
        """
        Update battle context for swarm decisions.

        Args:
            context: Battle state (scores, time, boosts, etc.)
        """
        self._battle_context = context
        self._coordinator.update(context)

    def get_swarm_decision(self) -> Dict[str, Any]:
        """
        Get coordinated decision from swarm.

        Returns:
            Collective decision with action recommendations
        """
        decision = self._coordinator.get_collective_decision()
        self._decisions_made += 1

        # Add role-specific recommendations
        decision['role_recommendations'] = self._get_role_recommendations()

        # Add entanglement info
        decision['coordination'] = {
            'pattern': self._pattern.value,
            'entanglements': sum(len(e) for e in self._entanglements.values()) // 2,
            'agents': len(self._agents)
        }

        return decision

    def _get_role_recommendations(self) -> Dict[str, str]:
        """Get action recommendations by role."""
        state = self._coordinator.get_state()
        ctx = self._battle_context

        recommendations = {}
        time_remaining = ctx.get('time_remaining', 180)
        boost_active = ctx.get('boost_active', False)
        deficit = ctx.get('deficit', 0)

        for agent_id, role in self._agent_roles.items():
            if role == BattleRole.SNIPER:
                if time_remaining <= 5:
                    recommendations[agent_id] = "SNIPE_NOW"
                elif time_remaining <= 30:
                    recommendations[agent_id] = "PREPARE_SNIPE"
                else:
                    recommendations[agent_id] = "WAIT"

            elif role == BattleRole.STRIKER:
                if boost_active:
                    recommendations[agent_id] = "BURST_ATTACK"
                elif deficit > 100:
                    recommendations[agent_id] = "COUNTER_ATTACK"
                else:
                    recommendations[agent_id] = "HOLD"

            elif role == BattleRole.SCOUT:
                recommendations[agent_id] = "TRACK_PHASE"

            elif role == BattleRole.SUPPORT:
                if boost_active:
                    recommendations[agent_id] = "BOOST_SUPPORT"
                else:
                    recommendations[agent_id] = "STANDBY"

            elif role == BattleRole.LEADER:
                recommendations[agent_id] = "COORDINATE"

            elif role == BattleRole.GUARDIAN:
                if deficit > 500:
                    recommendations[agent_id] = "CONSERVE"
                else:
                    recommendations[agent_id] = "MONITOR"

        return recommendations

    def get_agent_by_role(self, role: BattleRole) -> List[Any]:
        """Get all agents with a specific role."""
        return [
            self._agents[aid]
            for aid, r in self._agent_roles.items()
            if r == role and aid in self._agents
        ]

    def broadcast_signal(self, signal: str, data: Dict[str, Any] = None):
        """
        Broadcast signal to all entangled agents.

        Args:
            signal: Signal type (e.g., "boost_detected", "snipe_window")
            data: Additional signal data
        """
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'receive_swarm_signal'):
                try:
                    agent.receive_swarm_signal(signal, data or {})
                except Exception as e:
                    logger.warning(f"[SwarmMaster] Signal to {agent_id} failed: {e}")

        logger.debug(f"[SwarmMaster] Broadcast signal: {signal}")

    def update_health(self, agent_id: str, health: float):
        """Update agent health score."""
        if agent_id in self._agent_health:
            self._agent_health[agent_id] = max(0, min(1, health))

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get complete swarm status."""
        return {
            'agents': len(self._agents),
            'by_role': {
                role.value: len([
                    1 for r in self._agent_roles.values() if r == role
                ])
                for role in BattleRole
            },
            'pattern': self._pattern.value,
            'state': self._coordinator.get_state().value,
            'metrics': self._coordinator.get_metrics(),
            'decisions_made': self._decisions_made,
            'entanglements': sum(len(e) for e in self._entanglements.values()) // 2,
            'avg_health': (
                sum(self._agent_health.values()) / len(self._agent_health)
                if self._agent_health else 0
            )
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all agent positions in swarm space."""
        return self._coordinator.get_positions()

    def set_coordination_pattern(self, pattern: CoordinationPattern):
        """Change coordination pattern."""
        self._pattern = pattern

        # Rebuild entanglements
        self._entanglements.clear()
        for agent_id in self._agents:
            self._entanglements[agent_id] = set()
            self._update_entanglements(agent_id)

        logger.info(f"[SwarmMaster] Pattern changed to {pattern.value}")


def create_swarm_master(
    agents: List[Any] = None,
    pattern: str = "distributed",
    config: Dict[str, Any] = None
) -> SwarmMaster:
    """
    Factory to create and configure a SwarmMaster.

    Args:
        agents: Optional list of agents to register
        pattern: Coordination pattern ("distributed", "hierarchical", "clustered", "synchronized")
        config: Optional swarm config overrides

    Returns:
        Configured SwarmMaster instance
    """
    # Map pattern string to enum
    pattern_map = {
        "distributed": CoordinationPattern.DISTRIBUTED,
        "hierarchical": CoordinationPattern.HIERARCHICAL,
        "clustered": CoordinationPattern.CLUSTERED,
        "synchronized": CoordinationPattern.SYNCHRONIZED
    }
    coord_pattern = pattern_map.get(pattern.lower(), CoordinationPattern.DISTRIBUTED)

    # Create config
    swarm_config = SwarmConfig()
    if config:
        for key, value in config.items():
            if hasattr(swarm_config, key):
                setattr(swarm_config, key, value)

    # Create master
    master = SwarmMaster(swarm_config, coord_pattern)

    # Register agents
    if agents:
        for agent in agents:
            master.register_agent(agent)

    return master
