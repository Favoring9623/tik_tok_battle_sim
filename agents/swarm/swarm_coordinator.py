"""
Swarm Coordinator for TikTok Battle Simulator
==============================================

Adapted from MIRR-OR's SwarmAdapter for battle coordination.

Maps battle concepts to swarm dynamics:
- Agent scores -> Swarm positions (normalized by contribution)
- Gift signals -> Swarm velocities (direction and magnitude)
- Budget levels -> Swarm energy
- Agent types -> Swarm roles

Enables:
- Coordinated multi-agent attacks
- Flocking behavior for boost phases
- Dispersion for coverage
- Hunting behavior for snipe opportunities
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class SwarmState(Enum):
    """Battle swarm states."""
    EXPLORING = "exploring"           # Scanning battle state
    CONVERGING = "converging"         # Concentrating for attack
    FLOCKING = "flocking"             # Following boost phase
    HUNTING = "hunting"               # Actively pursuing snipe
    DEFENDING = "defending"           # Preserving budget
    SCOUTING = "scouting"             # Testing opponent
    SNIPING = "sniping"               # Final seconds attack
    BOOSTING = "boosting"             # Exploiting multiplier
    SIGNALING = "signaling"           # Broadcasting opportunities
    RECOVERING = "recovering"         # Recovery from deficit


class BattleRole(Enum):
    """Agent roles in battle swarm."""
    SCOUT = "scout"                   # Early gift detection (PhaseTracker)
    LEADER = "leader"                 # Direction setting (Kinetik)
    STRIKER = "striker"               # Burst attacks (StrikeMaster)
    SUPPORT = "support"               # Boost maintenance (LoadoutMaster)
    GUARDIAN = "guardian"             # Budget management
    SNIPER = "sniper"                 # Final seconds specialist


@dataclass
class SwarmConfig:
    """Configuration for battle swarm."""
    # Swarm parameters (Boids algorithm)
    cohesion_weight: float = 0.3      # Tendency to stay together
    alignment_weight: float = 0.4     # Tendency to align actions
    separation_weight: float = 0.3    # Tendency to diversify

    # Battle-specific
    signal_decay_rate: float = 0.95   # How fast signals decay
    aggression_factor: float = 0.6    # Aggression in decisions
    confidence_threshold: float = 0.5 # Min confidence for action

    # Performance
    update_interval: float = 0.5      # Swarm update frequency
    neighbor_radius: float = 0.3      # Normalized space radius

    # Snipe coordination
    snipe_window: int = 5             # Seconds before end
    snipe_coordination: bool = True   # Enable coordinated snipe


@dataclass
class AgentPosition:
    """Battle agent position in swarm space."""
    agent_id: str
    agent_name: str

    # Position in normalized space (0-1 for each dimension)
    x: float = 0.5                    # Aggression dimension (0=passive, 1=aggressive)
    y: float = 0.5                    # Phase dimension (0=early, 1=late)
    z: float = 0.5                    # Budget dimension (0=spent, 1=full)

    # Velocity (action momentum)
    vx: float = 0.0                   # Aggression velocity
    vy: float = 0.0                   # Phase velocity
    vz: float = 0.0                   # Budget velocity

    # Battle state
    signal_strength: float = 0.0      # Current action strength
    signal_direction: float = 0.0     # -1 (defend) to 1 (attack)
    confidence: float = 0.5           # Action confidence
    energy: float = 1.0               # Budget remaining ratio

    # Contribution tracking
    points_contributed: int = 0
    gifts_sent: int = 0

    # Role
    role: BattleRole = BattleRole.SUPPORT

    # Metadata
    last_update: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "position": {"x": self.x, "y": self.y, "z": self.z},
            "velocity": {"vx": self.vx, "vy": self.vy, "vz": self.vz},
            "signal": {
                "strength": self.signal_strength,
                "direction": self.signal_direction,
                "confidence": self.confidence
            },
            "energy": self.energy,
            "role": self.role.value,
            "points": self.points_contributed,
            "gifts": self.gifts_sent,
            "last_update": self.last_update.isoformat()
        }


@dataclass
class SwarmMetrics:
    """Swarm performance metrics."""
    # Coherence
    position_coherence: float = 0.0   # How clustered positions are
    velocity_alignment: float = 0.0   # How aligned actions are
    signal_consensus: float = 0.0     # Agreement on attack/defend

    # Activity
    active_agents: int = 0
    avg_signal_strength: float = 0.0
    avg_confidence: float = 0.0

    # Performance
    collective_points: int = 0
    total_gifts: int = 0
    decisions_made: int = 0

    # Battle state
    current_deficit: int = 0
    time_remaining: int = 0
    boost_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coherence": {
                "position": round(self.position_coherence, 4),
                "velocity": round(self.velocity_alignment, 4),
                "signal": round(self.signal_consensus, 4)
            },
            "activity": {
                "active_agents": self.active_agents,
                "avg_signal": round(self.avg_signal_strength, 4),
                "avg_confidence": round(self.avg_confidence, 4)
            },
            "performance": {
                "collective_points": self.collective_points,
                "total_gifts": self.total_gifts,
                "decisions": self.decisions_made
            },
            "battle": {
                "deficit": self.current_deficit,
                "time_remaining": self.time_remaining,
                "boost_active": self.boost_active
            }
        }


# =============================================================================
# SWARM COORDINATOR
# =============================================================================

class SwarmCoordinator:
    """
    Coordinates battle agents using swarm intelligence.

    Adapted from MIRR-OR's SwarmAdapter for collective
    intelligence in TikTok battle decisions.

    Usage:
        coordinator = SwarmCoordinator(config)

        # Sync battle agents
        coordinator.sync_agents(agents)

        # Update swarm state
        state = coordinator.update(battle_context)

        # Get collective decision
        decision = coordinator.get_collective_decision()
    """

    def __init__(self, config: Optional[SwarmConfig] = None):
        """Initialize swarm coordinator."""
        self._config = config or SwarmConfig()

        # Agent positions
        self._positions: Dict[str, AgentPosition] = {}

        # Swarm state
        self._state = SwarmState.EXPLORING
        self._metrics = SwarmMetrics()

        # Battle context
        self._battle_context: Dict[str, Any] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Callbacks
        self._on_state_change: Optional[Callable] = None

        logger.info("[SwarmCoordinator] Initialized")

    def sync_agents(self, agents: List[Any]) -> int:
        """
        Sync battle agents into swarm positions.

        Args:
            agents: List of battle agents

        Returns:
            Number of agents synced
        """
        synced = 0

        for agent in agents:
            try:
                position = self._map_agent_to_position(agent)
                self._positions[position.agent_id] = position
                synced += 1
            except Exception as e:
                logger.warning(f"[SwarmCoordinator] Failed to sync agent: {e}")

        self._metrics.active_agents = synced
        logger.debug(f"[SwarmCoordinator] Synced {synced} agents")

        return synced

    def _map_agent_to_position(self, agent: Any) -> AgentPosition:
        """Map battle agent to swarm position."""
        agent_id = getattr(agent, 'name', str(id(agent)))
        agent_name = getattr(agent, 'name', 'Unknown')

        # Determine role based on agent type
        role = self._determine_role(agent)

        # Extract state
        aggression = self._extract_aggression(agent)
        phase_position = self._extract_phase_position(agent)
        budget_ratio = self._extract_budget_ratio(agent)

        # Get contribution stats
        points = getattr(agent, 'total_donated', 0)
        gifts = getattr(agent, 'gifts_sent', 0)

        return AgentPosition(
            agent_id=agent_id,
            agent_name=agent_name,
            x=aggression,
            y=phase_position,
            z=budget_ratio,
            signal_strength=aggression,
            signal_direction=1.0 if aggression > 0.5 else -1.0,
            confidence=0.5 + (aggression * 0.5),
            energy=budget_ratio,
            points_contributed=points,
            gifts_sent=gifts,
            role=role
        )

    def _determine_role(self, agent: Any) -> BattleRole:
        """Determine agent's role in swarm."""
        agent_name = getattr(agent, 'name', '').lower()
        agent_type = getattr(agent, 'agent_type', '').lower()

        if 'kinetik' in agent_name or 'snipe' in agent_type:
            return BattleRole.SNIPER
        elif 'strike' in agent_name or 'burst' in agent_type:
            return BattleRole.STRIKER
        elif 'phase' in agent_name or 'tracker' in agent_type:
            return BattleRole.SCOUT
        elif 'loadout' in agent_name or 'support' in agent_type:
            return BattleRole.SUPPORT
        elif 'boost' in agent_name:
            return BattleRole.LEADER

        return BattleRole.SUPPORT

    def _extract_aggression(self, agent: Any) -> float:
        """Extract aggression level from agent."""
        # Check for params
        if hasattr(agent, 'params'):
            params = agent.params
            if isinstance(params, dict):
                if params.get('early_aggression', False):
                    return 0.7
                threshold = params.get('early_deficit_threshold', 100)
                return min(1.0, 100 / max(1, threshold))

        # Check agent type
        agent_type = getattr(agent, 'agent_type', '').lower()
        if 'snipe' in agent_type or 'burst' in agent_type:
            return 0.8
        elif 'boost' in agent_type:
            return 0.6

        return 0.5

    def _extract_phase_position(self, agent: Any) -> float:
        """Extract phase position (early/late game preference)."""
        agent_type = getattr(agent, 'agent_type', '').lower()

        if 'snipe' in agent_type:
            return 0.9  # Late game
        elif 'burst' in agent_type or 'strike' in agent_type:
            return 0.7
        elif 'boost' in agent_type:
            return 0.5
        elif 'phase' in agent_type:
            return 0.3  # Early tracking

        return 0.5

    def _extract_budget_ratio(self, agent: Any) -> float:
        """Extract remaining budget ratio."""
        if hasattr(agent, 'budget_manager') and agent.budget_manager:
            try:
                status = agent.budget_manager.get_status(getattr(agent, 'team', 'creator'))
                current = status.get('current', float('inf'))
                initial = status.get('initial', current)
                if initial > 0:
                    return min(1.0, current / initial)
            except:
                pass

        return 1.0  # Default to full budget

    def update(self, battle_context: Dict[str, Any]) -> SwarmState:
        """
        Update swarm state based on battle context.

        Args:
            battle_context: Current battle state (scores, time, boosts)

        Returns:
            Current swarm state
        """
        self._battle_context = battle_context

        if not self._positions:
            return self._state

        # Update metrics from context
        self._metrics.current_deficit = battle_context.get('deficit', 0)
        self._metrics.time_remaining = battle_context.get('time_remaining', 0)
        self._metrics.boost_active = battle_context.get('boost_active', False)

        # Calculate swarm forces
        forces = self._calculate_swarm_forces()

        # Apply forces to positions
        self._apply_forces(forces)

        # Update metrics
        self._update_metrics()

        # Determine swarm state
        new_state = self._determine_state()

        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            logger.info(
                f"[SwarmCoordinator] State: {old_state.value} -> {new_state.value}"
            )

        return self._state

    def _calculate_swarm_forces(self) -> Dict[str, Tuple[float, float, float]]:
        """Calculate swarm forces for each agent using Boids algorithm."""
        forces = {}
        positions = list(self._positions.values())

        for pos in positions:
            neighbors = self._get_neighbors(pos, positions)

            if not neighbors:
                forces[pos.agent_id] = (0, 0, 0)
                continue

            # Cohesion: move toward center of neighbors
            cx, cy, cz = self._calculate_cohesion(pos, neighbors)

            # Alignment: align with neighbor velocities
            ax, ay, az = self._calculate_alignment(pos, neighbors)

            # Separation: avoid crowding
            sx, sy, sz = self._calculate_separation(pos, neighbors)

            # Weighted sum
            cfg = self._config
            fx = cfg.cohesion_weight * cx + cfg.alignment_weight * ax + cfg.separation_weight * sx
            fy = cfg.cohesion_weight * cy + cfg.alignment_weight * ay + cfg.separation_weight * sy
            fz = cfg.cohesion_weight * cz + cfg.alignment_weight * az + cfg.separation_weight * sz

            forces[pos.agent_id] = (fx, fy, fz)

        return forces

    def _get_neighbors(
        self,
        agent: AgentPosition,
        all_agents: List[AgentPosition]
    ) -> List[AgentPosition]:
        """Get neighbors within radius."""
        radius = self._config.neighbor_radius
        neighbors = []

        for other in all_agents:
            if other.agent_id == agent.agent_id:
                continue

            dist = math.sqrt(
                (other.x - agent.x) ** 2 +
                (other.y - agent.y) ** 2 +
                (other.z - agent.z) ** 2
            )

            if dist < radius:
                neighbors.append(other)

        return neighbors

    def _calculate_cohesion(
        self,
        agent: AgentPosition,
        neighbors: List[AgentPosition]
    ) -> Tuple[float, float, float]:
        """Calculate cohesion force (toward center of mass)."""
        if not neighbors:
            return (0, 0, 0)

        cx = sum(n.x for n in neighbors) / len(neighbors)
        cy = sum(n.y for n in neighbors) / len(neighbors)
        cz = sum(n.z for n in neighbors) / len(neighbors)

        return (cx - agent.x, cy - agent.y, cz - agent.z)

    def _calculate_alignment(
        self,
        agent: AgentPosition,
        neighbors: List[AgentPosition]
    ) -> Tuple[float, float, float]:
        """Calculate alignment force (match neighbor velocities)."""
        if not neighbors:
            return (0, 0, 0)

        avg_vx = sum(n.vx for n in neighbors) / len(neighbors)
        avg_vy = sum(n.vy for n in neighbors) / len(neighbors)
        avg_vz = sum(n.vz for n in neighbors) / len(neighbors)

        return (avg_vx - agent.vx, avg_vy - agent.vy, avg_vz - agent.vz)

    def _calculate_separation(
        self,
        agent: AgentPosition,
        neighbors: List[AgentPosition]
    ) -> Tuple[float, float, float]:
        """Calculate separation force (avoid crowding)."""
        if not neighbors:
            return (0, 0, 0)

        sx, sy, sz = 0, 0, 0

        for n in neighbors:
            dx = agent.x - n.x
            dy = agent.y - n.y
            dz = agent.z - n.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.001

            # Stronger repulsion when closer
            sx += dx / (dist * dist)
            sy += dy / (dist * dist)
            sz += dz / (dist * dist)

        return (sx, sy, sz)

    def _apply_forces(self, forces: Dict[str, Tuple[float, float, float]]):
        """Apply forces to update positions."""
        decay = self._config.signal_decay_rate

        for agent_id, (fx, fy, fz) in forces.items():
            if agent_id not in self._positions:
                continue

            pos = self._positions[agent_id]

            # Update velocity
            pos.vx = pos.vx * decay + fx * 0.1
            pos.vy = pos.vy * decay + fy * 0.1
            pos.vz = pos.vz * decay + fz * 0.1

            # Update position
            pos.x = max(0, min(1, pos.x + pos.vx))
            pos.y = max(0, min(1, pos.y + pos.vy))
            pos.z = max(0, min(1, pos.z + pos.vz))

            pos.last_update = datetime.now(timezone.utc)

    def _update_metrics(self):
        """Update swarm metrics."""
        positions = list(self._positions.values())
        n = len(positions)

        if n == 0:
            return

        # Position coherence (inverse of spread)
        mean_x = sum(p.x for p in positions) / n
        mean_y = sum(p.y for p in positions) / n
        mean_z = sum(p.z for p in positions) / n

        spread = sum(
            math.sqrt((p.x - mean_x)**2 + (p.y - mean_y)**2 + (p.z - mean_z)**2)
            for p in positions
        ) / n

        self._metrics.position_coherence = max(0, 1 - spread * 2)

        # Velocity alignment
        mean_vy = sum(p.vy for p in positions) / n
        velocity_var = sum((p.vy - mean_vy)**2 for p in positions) / n
        self._metrics.velocity_alignment = max(0, 1 - velocity_var * 10)

        # Signal consensus
        directions = [p.signal_direction for p in positions if p.signal_strength > 0.1]
        if directions:
            mean_dir = sum(directions) / len(directions)
            consensus_var = sum((d - mean_dir)**2 for d in directions) / len(directions)
            self._metrics.signal_consensus = max(0, 1 - consensus_var)
        else:
            self._metrics.signal_consensus = 0

        # Activity metrics
        self._metrics.avg_signal_strength = sum(p.signal_strength for p in positions) / n
        self._metrics.avg_confidence = sum(p.confidence for p in positions) / n

        # Performance
        self._metrics.collective_points = sum(p.points_contributed for p in positions)
        self._metrics.total_gifts = sum(p.gifts_sent for p in positions)

    def _determine_state(self) -> SwarmState:
        """Determine current swarm state based on battle context."""
        m = self._metrics
        ctx = self._battle_context

        time_remaining = ctx.get('time_remaining', 180)
        deficit = ctx.get('deficit', 0)
        boost_active = ctx.get('boost_active', False)

        # Snipe mode in final seconds
        if time_remaining <= self._config.snipe_window:
            return SwarmState.SNIPING

        # Boost mode when multiplier active
        if boost_active:
            return SwarmState.BOOSTING

        # Recovering if in significant deficit
        if deficit > 1000:
            return SwarmState.RECOVERING

        # High coherence + high alignment = flocking
        if m.position_coherence > 0.7 and m.velocity_alignment > 0.6:
            return SwarmState.FLOCKING

        # High consensus + high signal = converging for attack
        if m.signal_consensus > 0.7 and m.avg_signal_strength > 0.5:
            return SwarmState.CONVERGING

        # Low coherence = exploring
        if m.position_coherence < 0.3:
            return SwarmState.EXPLORING

        # High signal strength = hunting opportunities
        if m.avg_signal_strength > 0.7:
            return SwarmState.HUNTING

        return SwarmState.EXPLORING

    def get_collective_decision(self) -> Dict[str, Any]:
        """
        Get aggregate decision from swarm.

        Returns:
            Collective decision with action, strength, confidence
        """
        positions = list(self._positions.values())

        if not positions:
            return {
                "action": "wait",
                "strength": 0,
                "confidence": 0,
                "state": self._state.value,
                "agents": 0
            }

        # Weight by confidence and signal strength
        total_weight = 0
        weighted_direction = 0
        weighted_strength = 0

        for pos in positions:
            weight = pos.confidence * pos.signal_strength
            if weight > 0:
                weighted_direction += pos.signal_direction * weight
                weighted_strength += pos.signal_strength * weight
                total_weight += weight

        if total_weight > 0:
            direction = weighted_direction / total_weight
            strength = weighted_strength / total_weight
        else:
            direction = 0
            strength = 0

        # Collective confidence
        confidence = self._metrics.signal_consensus * self._metrics.avg_confidence

        # Determine action
        if strength < self._config.confidence_threshold:
            action = "wait"
        elif direction > 0.3:
            action = "attack"
        elif direction < -0.3:
            action = "defend"
        else:
            action = "scout"

        return {
            "action": action,
            "direction": round(direction, 4),
            "strength": round(strength, 4),
            "confidence": round(confidence, 4),
            "state": self._state.value,
            "agents": len(positions),
            "coherence": round(self._metrics.position_coherence, 4),
            "recommended_gift": self._recommend_gift(strength, direction)
        }

    def _recommend_gift(self, strength: float, direction: float) -> Optional[str]:
        """Recommend gift based on swarm decision."""
        if strength < 0.3:
            return None

        ctx = self._battle_context
        time_remaining = ctx.get('time_remaining', 180)
        boost_active = ctx.get('boost_active', False)

        # Snipe phase - big gifts
        if time_remaining <= self._config.snipe_window:
            if strength > 0.8:
                return "TikTok Universe"
            elif strength > 0.6:
                return "Lion"
            else:
                return "GG"

        # Boost phase - gloves
        if boost_active:
            return "GLOVE"

        # Normal phase
        if direction > 0.5 and strength > 0.6:
            return "Doughnut"

        return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all agent positions."""
        return [p.to_dict() for p in self._positions.values()]

    def get_metrics(self) -> Dict[str, Any]:
        """Get swarm metrics."""
        return self._metrics.to_dict()

    def get_state(self) -> SwarmState:
        """Get current swarm state."""
        return self._state

    def set_state_change_callback(self, callback: Callable):
        """Set callback for state changes."""
        self._on_state_change = callback
