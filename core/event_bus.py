"""
Event Bus - Pub/Sub system for battle events.

This enables loose coupling between battle engine, agents, UI, analytics, etc.
Components subscribe to events they care about without knowing about each other.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List
from enum import Enum, auto
import time


class EventType(Enum):
    """All possible event types in the battle system."""

    # Battle lifecycle events
    BATTLE_STARTED = auto()
    BATTLE_ENDED = auto()
    BATTLE_TICK = auto()  # Every second

    # Score events
    SCORE_CHANGED = auto()
    CREATOR_LEADING = auto()
    OPPONENT_LEADING = auto()
    SCORE_TIED = auto()

    # Agent events
    AGENT_JOINED = auto()
    AGENT_ACTION = auto()
    GIFT_SENT = auto()
    MESSAGE_SENT = auto()

    # Strategic events
    MOMENTUM_SHIFT = auto()
    CRITICAL_MOMENT = auto()  # Last 10 seconds, close score
    COMEBACK_OPPORTUNITY = auto()

    # Emotional/narrative events
    EMOTION_CHANGED = auto()
    AGENT_DIALOGUE = auto()
    RIVALRY_DETECTED = auto()

    # System events
    ERROR_OCCURRED = auto()
    DEBUG_MESSAGE = auto()


@dataclass
class BattleEvent:
    """
    Immutable event object containing all event data.

    Attributes:
        event_type: The type of event
        timestamp: When the event occurred (battle time in seconds)
        data: Event-specific data dictionary
        source: Who/what generated this event
    """
    event_type: EventType
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"

    def __repr__(self):
        return f"BattleEvent({self.event_type.name}, t={self.timestamp:.1f}s, source={self.source})"


class EventBus:
    """
    Central event bus using the Observer pattern.

    Allows components to:
    - Publish events without knowing who's listening
    - Subscribe to specific event types
    - Unsubscribe when done

    Example:
        bus = EventBus()

        def on_gift(event):
            print(f"Gift sent: {event.data['amount']}")

        bus.subscribe(EventType.GIFT_SENT, on_gift)
        bus.publish(EventType.GIFT_SENT, {"amount": 100}, source="NovaWhale")
    """

    def __init__(self, debug=False):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[BattleEvent] = []
        self._debug = debug

    def subscribe(self, event_type: EventType, handler: Callable[[BattleEvent], None]):
        """
        Subscribe to a specific event type.

        Args:
            event_type: The type of event to listen for
            handler: Function to call when event occurs. Receives BattleEvent as argument.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

        if self._debug:
            print(f"[EventBus] Subscribed {handler.__name__} to {event_type.name}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                if self._debug:
                    print(f"[EventBus] Unsubscribed {handler.__name__} from {event_type.name}")
            except ValueError:
                pass

    def publish(self, event_type: EventType, data: Dict[str, Any] = None,
                source: str = "system", timestamp: float = None):
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            data: Event payload
            source: Who generated this event
            timestamp: Event time (auto-generated if not provided)
        """
        if timestamp is None:
            timestamp = time.time()

        event = BattleEvent(
            event_type=event_type,
            timestamp=timestamp,
            data=data or {},
            source=source
        )

        # Store in history
        self._event_history.append(event)

        # Notify all subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EventBus] Error in handler {handler.__name__}: {e}")

        if self._debug:
            print(f"[EventBus] Published: {event}")

    def get_history(self, event_type: EventType = None, since: float = None) -> List[BattleEvent]:
        """
        Get event history, optionally filtered.

        Args:
            event_type: Filter by specific event type
            since: Only return events after this timestamp

        Returns:
            List of matching events
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if since is not None:
            events = [e for e in events if e.timestamp >= since]

        return events

    def clear_history(self):
        """Clear all event history (useful between battles)."""
        self._event_history.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about events published."""
        stats = {}
        for event in self._event_history:
            event_name = event.event_type.name
            stats[event_name] = stats.get(event_name, 0) + 1
        return stats
