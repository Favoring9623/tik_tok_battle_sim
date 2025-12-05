"""
Memory System - Agent memory and learning.

Agents remember:
- Past battles
- Favorite creators
- Rivalries with other agents
- Successful strategies
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
import json


@dataclass
class BattleMemory:
    """Record of a single battle."""

    battle_id: str
    creator_name: str
    result: str  # "won", "lost", "tie"
    agent_contribution: int  # Points donated
    emotional_arc: List[str]  # Emotions experienced
    notable_moments: List[str] = field(default_factory=list)
    timestamp: float = 0.0


class MemorySystem:
    """
    Manages agent's long-term memory across battles.

    Memory influences future behavior:
    - Agents favor creators they've won with
    - Develop rivalries with other agents
    - Learn successful strategies
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.battle_history: List[BattleMemory] = []
        self.creator_relationships: Dict[str, float] = {}  # creator_name: affinity (-1 to 1)
        self.agent_rivalries: Dict[str, float] = {}        # agent_name: rivalry_level (0-1)
        self.learned_strategies: Dict[str, Any] = {}

    def record_battle(self, memory: BattleMemory):
        """Record a completed battle."""
        self.battle_history.append(memory)

        # Update creator relationship
        creator = memory.creator_name
        if creator not in self.creator_relationships:
            self.creator_relationships[creator] = 0.0

        # Adjust affinity based on result
        if memory.result == "won":
            self.creator_relationships[creator] += 0.2
        elif memory.result == "lost":
            self.creator_relationships[creator] -= 0.1

        # Clamp to [-1, 1]
        self.creator_relationships[creator] = max(-1.0, min(1.0, self.creator_relationships[creator]))

    def get_creator_affinity(self, creator_name: str) -> float:
        """Get affinity for a creator (-1 to 1)."""
        return self.creator_relationships.get(creator_name, 0.0)

    def add_rivalry(self, other_agent: str, intensity: float = 0.3):
        """Record a rivalry with another agent."""
        current = self.agent_rivalries.get(other_agent, 0.0)
        self.agent_rivalries[other_agent] = min(1.0, current + intensity)

    def get_rivalry_level(self, other_agent: str) -> float:
        """Get rivalry level with another agent (0-1)."""
        return self.agent_rivalries.get(other_agent, 0.0)

    def get_battle_count(self) -> int:
        """Total battles participated in."""
        return len(self.battle_history)

    def get_win_rate(self) -> float:
        """Calculate win rate (0-1)."""
        if not self.battle_history:
            return 0.0
        wins = sum(1 for b in self.battle_history if b.result == "won")
        return wins / len(self.battle_history)

    def get_total_contribution(self) -> int:
        """Total points donated across all battles."""
        return sum(b.agent_contribution for b in self.battle_history)

    def to_dict(self) -> dict:
        """Serialize to dictionary (for JSON storage)."""
        return {
            "agent_name": self.agent_name,
            "battle_count": self.get_battle_count(),
            "win_rate": self.get_win_rate(),
            "total_contribution": self.get_total_contribution(),
            "creator_relationships": self.creator_relationships,
            "agent_rivalries": self.agent_rivalries,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserialize from dictionary."""
        memory = cls(data["agent_name"])
        memory.creator_relationships = data.get("creator_relationships", {})
        memory.agent_rivalries = data.get("agent_rivalries", {})
        return memory

    def save(self, filepath: str):
        """Save memory to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str):
        """Load memory from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def __repr__(self):
        return f"MemorySystem({self.agent_name}, battles={self.get_battle_count()}, wr={self.get_win_rate():.1%})"
