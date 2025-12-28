"""
Swarm Intelligence Module for TikTok Battle Simulator
======================================================

Ported from MIRR-OR's Orion Agents swarm system.

Provides collective intelligence for battle agents:
- Swarm coordination and emergent behavior
- Collective decision making
- Agent role specialization
- Coordinated attack/defense patterns
"""

from .swarm_coordinator import (
    SwarmCoordinator,
    SwarmState,
    BattleRole,
    AgentPosition,
    SwarmMetrics,
    SwarmConfig
)

from .swarm_master import (
    SwarmMaster,
    create_swarm_master
)

__all__ = [
    'SwarmCoordinator',
    'SwarmState',
    'BattleRole',
    'AgentPosition',
    'SwarmMetrics',
    'SwarmConfig',
    'SwarmMaster',
    'create_swarm_master'
]
