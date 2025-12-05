"""
Coordination Mixin - Adds team coordination capabilities to agents.

Agents that use this mixin can:
- Propose actions to team coordinator
- Check for action conflicts
- Respond to team strategy changes
- Coordinate with other agents
"""

from typing import Optional, List
from core.team_coordinator import TeamCoordinator, CoordinationPriority


class CoordinationMixin:
    """
    Mixin to add coordination capabilities to agents.

    Usage:
        class MyAgent(BaseAgent, CoordinationMixin):
            def decide_action(self, battle):
                if self.should_coordinate_action("strike", battle.time_manager.current_time):
                    # Perform action
    """

    def __init__(self):
        self.coordinator: Optional[TeamCoordinator] = None
        self.coordination_enabled = True
        super().__init__()

    def set_coordinator(self, coordinator: TeamCoordinator):
        """Set the team coordinator for this agent."""
        self.coordinator = coordinator

        # Register capabilities
        if hasattr(self, 'get_capabilities'):
            capabilities = self.get_capabilities()
            self.coordinator.register_agent(self.name, capabilities)

    def propose_coordinated_action(self, action_type: str, scheduled_time: int,
                                   priority: CoordinationPriority,
                                   dependencies: Optional[List[str]] = None) -> bool:
        """
        Propose an action to the coordinator.

        Returns True if approved, False if rejected/deferred.
        """
        if not self.coordinator or not self.coordination_enabled:
            return True  # No coordination, always approve

        return self.coordinator.propose_action(
            agent_name=self.name,
            action_type=action_type,
            scheduled_time=scheduled_time,
            priority=priority,
            dependencies=dependencies
        )

    def mark_action_started(self, action_type: str):
        """Notify coordinator that action has started."""
        if self.coordinator:
            self.coordinator.mark_action_started(self.name, action_type)

    def mark_action_completed(self, action_type: str):
        """Notify coordinator that action has completed."""
        if self.coordinator:
            self.coordinator.mark_action_completed(self.name, action_type)

    def should_defer_action(self, action_type: str, current_time: int) -> tuple[bool, Optional[str]]:
        """
        Check if action should be deferred for coordination.

        Returns (should_defer, reason)
        """
        if not self.coordinator:
            return False, None

        return self.coordinator.should_defer_action(self.name, action_type, current_time)

    def get_team_strategy(self) -> str:
        """Get current team strategy."""
        if self.coordinator:
            return self.coordinator.team_strategy
        return "independent"

    def get_team_state(self) -> dict:
        """Get current team coordination state."""
        if self.coordinator:
            return self.coordinator.get_team_state()
        return {}

    def wait_for_action(self, agent_name: str, action_type: str) -> bool:
        """Check if a dependency action has completed."""
        if not self.coordinator:
            return True  # No coordination, don't wait

        action_id = f"{agent_name}_{action_type}"
        return action_id in self.coordinator.completed_actions

    def get_suggested_strategy(self, score_diff: int, time_remaining: int) -> str:
        """Get suggested strategy from coordinator."""
        if self.coordinator:
            return self.coordinator.suggest_strategy(score_diff, time_remaining)
        return "balanced"


class SpecialistCapabilities:
    """Standard capabilities for specialist agents."""

    KINETIK = ["final_snipe", "precision_strike", "stealth_attack"]
    STRIKE_MASTER = ["glove_strike", "x5_trigger", "lion_combo"]
    ACTIVATOR = ["bonus_activation", "session_trigger", "rose_spam"]
    SENTINEL = ["fog_deploy", "hammer_counter", "defense", "detection"]
