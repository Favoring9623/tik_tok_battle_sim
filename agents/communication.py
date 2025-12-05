"""
Communication System - Inter-agent messaging.

Allows agents to "talk" to each other during battles, creating drama and coordination.
"""

from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class AgentMessage:
    """A message from one agent to another (or broadcast to all)."""

    from_agent: str
    to_agent: Optional[str]  # None = broadcast to all
    message: str
    timestamp: float
    message_type: str = "chat"  # chat, coordination, taunt, cheer

    def is_broadcast(self) -> bool:
        """Returns True if this is a broadcast message."""
        return self.to_agent is None


class CommunicationChannel:
    """
    Shared communication channel for all agents in a battle.

    Agents can:
    - Send messages to specific agents
    - Broadcast to everyone
    - Read recent messages
    - React to messages directed at them
    """

    def __init__(self):
        self._messages = []

    def send(self, from_agent: str, message: str,
             to_agent: Optional[str] = None,
             message_type: str = "chat"):
        """
        Send a message.

        Args:
            from_agent: Sender's name
            message: Message content
            to_agent: Recipient (None for broadcast)
            message_type: Type of message (chat, coordination, taunt, cheer)
        """
        msg = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message=message,
            timestamp=time.time(),
            message_type=message_type
        )
        self._messages.append(msg)

        # Print to console for drama
        if to_agent:
            print(f"💬 {from_agent} → {to_agent}: \"{message}\"")
        else:
            print(f"📢 {from_agent}: \"{message}\"")

    def get_messages(self, for_agent: Optional[str] = None,
                     since: Optional[float] = None,
                     message_type: Optional[str] = None) -> list:
        """
        Retrieve messages, optionally filtered.

        Args:
            for_agent: Only messages to this agent or broadcasts
            since: Only messages after this timestamp
            message_type: Only messages of this type

        Returns:
            List of matching messages
        """
        messages = self._messages

        if for_agent:
            messages = [m for m in messages if m.to_agent is None or m.to_agent == for_agent]

        if since is not None:
            messages = [m for m in messages if m.timestamp >= since]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        return messages

    def clear(self):
        """Clear all messages (used between battles)."""
        self._messages.clear()

    def get_dialogue_history(self) -> list:
        """Get all messages formatted for display/lore generation."""
        return [
            f"{msg.from_agent} → {msg.to_agent or 'ALL'}: {msg.message}"
            for msg in self._messages
        ]
