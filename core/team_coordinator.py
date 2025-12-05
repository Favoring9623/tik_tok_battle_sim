"""
Team Coordinator - Optimizes agent coordination and strategy.

Provides:
- Centralized coordination state
- Team strategy patterns
- Action sequencing
- Resource conflict resolution
- Event-based coordination
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import time


class TeamPhase(Enum):
    """Team strategic phases during battle."""
    OPENING = auto()      # 0-60s: Build foundation
    MID_GAME = auto()     # 60-120s: Execute main strategy
    SETUP = auto()        # 120-150s: Prepare final push
    FINAL_PUSH = auto()   # 150-180s: All-in final attacks


class CoordinationPriority(Enum):
    """Action priority levels for conflict resolution."""
    CRITICAL = 5   # Final snipe, emergency defense
    HIGH = 4       # x5 strikes, bonus activation
    MEDIUM = 3     # Fog deployment, tactical gifts
    LOW = 2        # Standard gifts
    PASSIVE = 1    # Observation, waiting


@dataclass
class CoordinatedAction:
    """A planned action with timing and dependencies."""
    agent_name: str
    action_type: str
    scheduled_time: int
    priority: CoordinationPriority
    dependencies: List[str] = field(default_factory=list)  # Actions that must complete first
    status: str = "planned"  # planned, ready, executing, completed, cancelled

    def can_execute(self, completed_actions: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_actions for dep in self.dependencies)


class TeamCoordinator:
    """
    Centralized coordination system for agent teams.

    Manages:
    - Action sequencing (e.g., Fog BEFORE Snipe)
    - Resource conflicts (don't waste multiple gloves at once)
    - Team state sharing (who's doing what)
    - Strategic phase transitions
    """

    def __init__(self):
        # Team state
        self.current_phase = TeamPhase.OPENING
        self.team_strategy = "balanced"  # balanced, aggressive, defensive

        # Coordination state
        self.planned_actions: List[CoordinatedAction] = []
        self.completed_actions: Set[str] = set()
        self.active_actions: Dict[str, str] = {}  # agent -> current action

        # Resource tracking
        self.gloves_in_flight = 0  # Number of gloves being used this second
        self.fog_deployed = False
        self.bonus_session_triggered = False

        # Agent capabilities
        self.agent_capabilities: Dict[str, Set[str]] = {}

        # Communication log
        self.coordination_log: List[Dict[str, Any]] = []

    def register_agent(self, agent_name: str, capabilities: List[str]):
        """Register an agent and their capabilities."""
        self.agent_capabilities[agent_name] = set(capabilities)

    def update_phase(self, current_time: int, battle_duration: int):
        """Update team phase based on battle progress."""
        progress = current_time / battle_duration

        if progress <= 0.33:
            self.current_phase = TeamPhase.OPENING
        elif progress <= 0.67:
            self.current_phase = TeamPhase.MID_GAME
        elif progress <= 0.83:
            self.current_phase = TeamPhase.SETUP
        else:
            self.current_phase = TeamPhase.FINAL_PUSH

    def propose_action(self, agent_name: str, action_type: str,
                      scheduled_time: int, priority: CoordinationPriority,
                      dependencies: Optional[List[str]] = None) -> bool:
        """
        Propose an action for coordination approval.

        Returns True if action is approved, False if rejected/deferred.
        """
        action = CoordinatedAction(
            agent_name=agent_name,
            action_type=action_type,
            scheduled_time=scheduled_time,
            priority=priority,
            dependencies=dependencies or []
        )

        # Check for conflicts
        conflict = self._check_conflicts(action)
        if conflict:
            self._log(f"❌ Conflict: {agent_name}'s {action_type} conflicts with {conflict}")
            return False

        # Approve and schedule
        self.planned_actions.append(action)
        self._log(f"✅ Approved: {agent_name}'s {action_type} at t={scheduled_time}s")
        return True

    def _check_conflicts(self, proposed_action: CoordinatedAction) -> Optional[str]:
        """Check if action conflicts with existing plans."""
        # Conflict 1: Multiple gloves in same second (waste)
        if proposed_action.action_type == "glove_strike":
            same_time_gloves = [
                a for a in self.planned_actions
                if a.action_type == "glove_strike"
                and abs(a.scheduled_time - proposed_action.scheduled_time) <= 1
                and a.status not in ["completed", "cancelled"]
            ]
            if same_time_gloves:
                return f"glove already planned at t={same_time_gloves[0].scheduled_time}s"

        # Conflict 2: Snipe before fog (suboptimal)
        if proposed_action.action_type == "final_snipe":
            fog_ready = any(
                a.action_type == "fog_deploy"
                and a.status == "completed"
                for a in self.planned_actions
            )
            if not fog_ready and not self.fog_deployed:
                # Not a hard conflict, but warn
                self._log(f"⚠️  Warning: Snipe planned without fog cover")

        # Conflict 3: Multiple activators (redundant)
        if proposed_action.action_type == "bonus_activation":
            if self.bonus_session_triggered:
                return "bonus session already triggered"

        return None

    def mark_action_started(self, agent_name: str, action_type: str):
        """Mark an action as started."""
        self.active_actions[agent_name] = action_type

        # Update action status
        for action in self.planned_actions:
            if (action.agent_name == agent_name
                and action.action_type == action_type
                and action.status == "ready"):
                action.status = "executing"

    def mark_action_completed(self, agent_name: str, action_type: str):
        """Mark an action as completed."""
        action_id = f"{agent_name}_{action_type}"
        self.completed_actions.add(action_id)

        if agent_name in self.active_actions:
            del self.active_actions[agent_name]

        # Update action status
        for action in self.planned_actions:
            if (action.agent_name == agent_name
                and action.action_type == action_type
                and action.status == "executing"):
                action.status = "completed"

        # Update resource tracking
        if action_type == "fog_deploy":
            self.fog_deployed = True
        elif action_type == "bonus_activation":
            self.bonus_session_triggered = True

    def get_ready_actions(self, current_time: int) -> List[CoordinatedAction]:
        """Get actions that are ready to execute now."""
        ready = []

        for action in self.planned_actions:
            if action.status != "planned":
                continue

            # Check timing
            if action.scheduled_time > current_time:
                continue

            # Check dependencies
            if action.can_execute(self.completed_actions):
                action.status = "ready"
                ready.append(action)

        return ready

    def should_defer_action(self, agent_name: str, action_type: str,
                           current_time: int) -> tuple[bool, Optional[str]]:
        """
        Check if an agent should defer their action.

        Returns (should_defer, reason)
        """
        # Defer glove strikes if one just happened
        if action_type == "glove_strike":
            if self.gloves_in_flight > 0:
                return True, "Another glove active, wait 5s"

        # Defer if higher priority action is happening
        for other_agent, other_action in self.active_actions.items():
            if other_agent == agent_name:
                continue

            # Find action priority
            other_priority = self._get_action_priority(other_action)
            this_priority = self._get_action_priority(action_type)

            if other_priority.value > this_priority.value:
                return True, f"{other_agent}'s {other_action} has priority"

        return False, None

    def _get_action_priority(self, action_type: str) -> CoordinationPriority:
        """Get priority for an action type."""
        priority_map = {
            "final_snipe": CoordinationPriority.CRITICAL,
            "emergency_defense": CoordinationPriority.CRITICAL,
            "glove_strike": CoordinationPriority.HIGH,
            "bonus_activation": CoordinationPriority.HIGH,
            "fog_deploy": CoordinationPriority.MEDIUM,
            "hammer_deploy": CoordinationPriority.MEDIUM,
            "standard_gift": CoordinationPriority.LOW,
        }
        return priority_map.get(action_type, CoordinationPriority.PASSIVE)

    def get_team_state(self) -> Dict[str, Any]:
        """Get current team coordination state."""
        return {
            "phase": self.current_phase.name,
            "strategy": self.team_strategy,
            "active_actions": dict(self.active_actions),
            "fog_deployed": self.fog_deployed,
            "bonus_triggered": self.bonus_session_triggered,
            "gloves_in_flight": self.gloves_in_flight,
            "pending_actions": len([a for a in self.planned_actions if a.status == "planned"]),
        }

    def suggest_strategy(self, score_diff: int, time_remaining: int) -> str:
        """Suggest team strategy based on battle state."""
        if time_remaining <= 30:
            # Final push time
            if score_diff > 0:  # Losing
                return "all_in_offense"
            elif score_diff < -2000:  # Winning big
                return "defensive_hold"
            else:
                return "aggressive_close"

        elif time_remaining <= 60:
            # Setup phase
            if score_diff > 3000:  # Losing badly
                return "emergency_catch_up"
            else:
                return "setup_final_push"

        else:
            # Early/mid game
            if score_diff > 5000:
                return "aggressive_push"
            elif score_diff < -3000:
                return "defensive_cruise"
            else:
                return "balanced"

    def _log(self, message: str):
        """Log coordination event."""
        self.coordination_log.append({
            "timestamp": time.time(),
            "message": message
        })

    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get summary of coordination for end of battle."""
        return {
            "total_actions_coordinated": len(self.planned_actions),
            "completed_actions": len(self.completed_actions),
            "conflicts_prevented": sum(1 for log in self.coordination_log if "Conflict" in log["message"]),
            "final_phase": self.current_phase.name,
            "final_strategy": self.team_strategy,
        }


# Coordination Patterns - Common team strategies

class CoordinationPattern:
    """Pre-defined coordination patterns for common scenarios."""

    @staticmethod
    def stealth_snipe_pattern(coordinator: TeamCoordinator, fog_time: int, snipe_time: int):
        """
        Coordinate stealth snipe: Fog → Wait → Snipe

        Ensures Kinetik gets fog cover for final snipe.
        """
        # Step 1: Sentinel deploys fog
        coordinator.propose_action(
            agent_name="Sentinel",
            action_type="fog_deploy",
            scheduled_time=fog_time,
            priority=CoordinationPriority.MEDIUM
        )

        # Step 2: Kinetik snipes (depends on fog)
        coordinator.propose_action(
            agent_name="Kinetik",
            action_type="final_snipe",
            scheduled_time=snipe_time,
            priority=CoordinationPriority.CRITICAL,
            dependencies=["Sentinel_fog_deploy"]
        )

    @staticmethod
    def bonus_session_pattern(coordinator: TeamCoordinator, activation_time: int, strike_time: int):
        """
        Coordinate bonus session: Activate → Strike during session

        Activator triggers session, StrikeMaster strikes during it.
        """
        # Step 1: Activator triggers bonus session
        coordinator.propose_action(
            agent_name="Activator",
            action_type="bonus_activation",
            scheduled_time=activation_time,
            priority=CoordinationPriority.HIGH
        )

        # Step 2: StrikeMaster waits for session then strikes
        coordinator.propose_action(
            agent_name="StrikeMaster",
            action_type="glove_strike",
            scheduled_time=strike_time,
            priority=CoordinationPriority.HIGH,
            dependencies=["Activator_bonus_activation"]
        )

    @staticmethod
    def defensive_wall_pattern(coordinator: TeamCoordinator, threat_time: int):
        """
        Coordinate defensive response: Detect → Hammer → Support gifts

        Sentinel detects and counters, others provide backup.
        """
        coordinator.propose_action(
            agent_name="Sentinel",
            action_type="hammer_deploy",
            scheduled_time=threat_time,
            priority=CoordinationPriority.MEDIUM
        )
