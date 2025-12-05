"""
Core battle simulation engine components.

This package contains the fundamental building blocks:
- EventBus: Event-driven communication system
- BattleEngine: Core battle simulation logic
- ScoreTracker: Score management and calculations
- TimeManager: Battle timing and phase management
- TeamCoordinator: Agent coordination system
"""

from .event_bus import EventBus, BattleEvent, EventType
from .battle_engine import BattleEngine
from .score_tracker import ScoreTracker
from .time_manager import TimeManager
from .team_coordinator import TeamCoordinator

__all__ = [
    "EventBus",
    "BattleEvent",
    "EventType",
    "BattleEngine",
    "ScoreTracker",
    "TimeManager",
    "TeamCoordinator",
]
