"""
AI Agent system for TikTok battle simulation.

Components:
- BaseAgent: Abstract base class for all agents
- EmotionSystem: Emotion modeling for agent personalities
- MemorySystem: Agent memory and learning
- Communication: Inter-agent messaging
"""

from .base_agent import BaseAgent
from .emotion_system import EmotionSystem, EmotionalState
from .memory_system import MemorySystem
from .communication import AgentMessage, CommunicationChannel

__all__ = [
    "BaseAgent",
    "EmotionSystem",
    "EmotionalState",
    "MemorySystem",
    "AgentMessage",
    "CommunicationChannel",
]
