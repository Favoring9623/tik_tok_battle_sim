#!/usr/bin/env python3
"""
TikTok Battle Rewards System

Simulates and tracks the TikTok Live battle reward system:
- Rewards earned from winning battles
- Power-up inventory management
- Multiplier effects (x2, x3, x5)
- Tournament integration (Best of 3, Best of 5)

Based on real TikTok Live battle mechanics:
- Winner gets random rewards (gloves, fog, hammer, time bonus)
- Rewards accumulate across battles
- Power-ups can be used strategically in future battles
"""

import random
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BattleRewards")


class PowerUpType(Enum):
    """Types of power-ups in TikTok battles."""
    GLOVE = "glove"           # Activates x5 multiplier for 30s
    HAMMER = "hammer"         # Cancels opponent's active glove/multiplier
    FOG = "fog"               # Hides scores from opponent for 30s
    TIME_BONUS = "time_bonus" # Adds 30s to battle duration
    SHIELD = "shield"         # Protects against hammer for 30s


class MultiplierType(Enum):
    """Active multiplier types during battle."""
    NONE = 1.0
    X2 = 2.0
    X3 = 3.0
    X5 = 5.0


@dataclass
class PowerUp:
    """A single power-up item."""
    type: PowerUpType
    acquired_at: datetime = field(default_factory=datetime.now)
    source: str = "battle_reward"  # battle_reward, purchase, gift
    used: bool = False
    used_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'acquired_at': self.acquired_at.isoformat(),
            'source': self.source,
            'used': self.used,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PowerUp':
        return cls(
            type=PowerUpType(data['type']),
            acquired_at=datetime.fromisoformat(data['acquired_at']),
            source=data.get('source', 'battle_reward'),
            used=data.get('used', False),
            used_at=datetime.fromisoformat(data['used_at']) if data.get('used_at') else None
        )


@dataclass
class BattleReward:
    """Rewards earned from winning a battle."""
    battle_id: str
    earned_at: datetime
    power_ups: List[PowerUp]
    coins_bonus: int = 0
    xp_bonus: int = 0

    def to_dict(self) -> Dict:
        return {
            'battle_id': self.battle_id,
            'earned_at': self.earned_at.isoformat(),
            'power_ups': [p.to_dict() for p in self.power_ups],
            'coins_bonus': self.coins_bonus,
            'xp_bonus': self.xp_bonus
        }


@dataclass
class MultiplierState:
    """Current multiplier state during a battle."""
    active: bool = False
    type: MultiplierType = MultiplierType.NONE
    owner: str = ""  # "creator" or "opponent"
    started_at: Optional[float] = None  # Battle time when activated
    duration: float = 30.0  # Seconds
    source: str = ""  # "glove", "boost", "system"

    def get_value(self) -> float:
        return self.type.value if self.active else 1.0

    def is_expired(self, current_time: float) -> bool:
        if not self.active or self.started_at is None:
            return True
        return (current_time - self.started_at) >= self.duration


@dataclass
class BattleConditions:
    """
    Real-time battle conditions including multipliers and power-ups.

    This tracks the actual state of a battle for AI decision making.
    """
    # Multiplier states
    creator_multiplier: MultiplierState = field(default_factory=MultiplierState)
    opponent_multiplier: MultiplierState = field(default_factory=MultiplierState)

    # System multipliers (boosts)
    boost_active: bool = False
    boost_multiplier: float = 1.0
    boost_phase: int = 0  # 0 = none, 1 = boost1, 2 = boost2

    # Fog state
    fog_active: bool = False
    fog_owner: str = ""
    fog_started_at: Optional[float] = None
    fog_duration: float = 30.0

    # Time modifications
    time_bonus_added: float = 0.0
    original_duration: float = 300.0

    # Battle phase
    time_elapsed: float = 0.0
    time_remaining: float = 300.0

    def get_effective_multiplier(self, team: str) -> float:
        """Get the effective multiplier for a team."""
        base = self.boost_multiplier if self.boost_active else 1.0

        if team == "creator" and self.creator_multiplier.active:
            return base * self.creator_multiplier.get_value()
        elif team == "opponent" and self.opponent_multiplier.active:
            return base * self.opponent_multiplier.get_value()

        return base

    def is_fog_active_for(self, team: str) -> bool:
        """Check if fog is hiding scores from a team."""
        return self.fog_active and self.fog_owner != team

    def to_dict(self) -> Dict:
        return {
            'creator_multiplier': self.creator_multiplier.get_value(),
            'opponent_multiplier': self.opponent_multiplier.get_value(),
            'boost_active': self.boost_active,
            'boost_multiplier': self.boost_multiplier,
            'boost_phase': self.boost_phase,
            'fog_active': self.fog_active,
            'fog_owner': self.fog_owner,
            'time_bonus_added': self.time_bonus_added,
            'time_elapsed': self.time_elapsed,
            'time_remaining': self.time_remaining
        }


class PowerUpInventory:
    """
    Manages a player's power-up inventory across battles.

    Power-ups are:
    - Earned from winning battles
    - Carried over between battles
    - Used strategically during battles
    - Tracked for tournament statistics
    """

    def __init__(self, owner: str = "player"):
        self.owner = owner
        self.inventory: Dict[PowerUpType, List[PowerUp]] = {
            PowerUpType.GLOVE: [],
            PowerUpType.HAMMER: [],
            PowerUpType.FOG: [],
            PowerUpType.TIME_BONUS: [],
            PowerUpType.SHIELD: []
        }
        self.history: List[BattleReward] = []
        self.total_earned: Dict[PowerUpType, int] = {t: 0 for t in PowerUpType}
        self.total_used: Dict[PowerUpType, int] = {t: 0 for t in PowerUpType}

    def add_power_up(self, power_up_type: PowerUpType, source: str = "battle_reward") -> PowerUp:
        """Add a power-up to inventory."""
        power_up = PowerUp(type=power_up_type, source=source)
        self.inventory[power_up_type].append(power_up)
        self.total_earned[power_up_type] += 1
        logger.info(f"Added {power_up_type.value} to {self.owner}'s inventory (source: {source})")
        return power_up

    def use_power_up(self, power_up_type: PowerUpType) -> Optional[PowerUp]:
        """Use a power-up from inventory. Returns the used power-up or None."""
        available = [p for p in self.inventory[power_up_type] if not p.used]
        if not available:
            logger.warning(f"No {power_up_type.value} available in {self.owner}'s inventory")
            return None

        power_up = available[0]
        power_up.used = True
        power_up.used_at = datetime.now()
        self.total_used[power_up_type] += 1

        logger.info(f"{self.owner} used {power_up_type.value}")
        return power_up

    def get_available(self, power_up_type: PowerUpType) -> int:
        """Get count of available (unused) power-ups of a type."""
        return len([p for p in self.inventory[power_up_type] if not p.used])

    def get_all_available(self) -> Dict[PowerUpType, int]:
        """Get counts of all available power-ups."""
        return {t: self.get_available(t) for t in PowerUpType}

    def clear_used(self):
        """Remove used power-ups from inventory."""
        for power_up_type in PowerUpType:
            self.inventory[power_up_type] = [
                p for p in self.inventory[power_up_type] if not p.used
            ]

    def to_dict(self) -> Dict:
        return {
            'owner': self.owner,
            'inventory': {
                t.value: [p.to_dict() for p in self.inventory[t]]
                for t in PowerUpType
            },
            'available': self.get_all_available(),
            'total_earned': {t.value: c for t, c in self.total_earned.items()},
            'total_used': {t.value: c for t, c in self.total_used.items()}
        }

    def save(self, filepath: Path):
        """Save inventory to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def load(self, filepath: Path) -> bool:
        """Load inventory from file."""
        if not filepath.exists():
            return False
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.owner = data.get('owner', self.owner)
            for type_str, power_ups in data.get('inventory', {}).items():
                power_up_type = PowerUpType(type_str)
                self.inventory[power_up_type] = [
                    PowerUp.from_dict(p) for p in power_ups
                ]
            for type_str, count in data.get('total_earned', {}).items():
                self.total_earned[PowerUpType(type_str)] = count
            for type_str, count in data.get('total_used', {}).items():
                self.total_used[PowerUpType(type_str)] = count

            return True
        except Exception as e:
            logger.error(f"Failed to load inventory: {e}")
            return False


class BattleRewardsEngine:
    """
    Engine for calculating and distributing battle rewards.

    Based on TikTok's actual reward system:
    - Winners receive 1-3 random power-ups
    - Larger victories = better rewards
    - Streak bonuses for consecutive wins
    """

    # Reward probability tables
    REWARD_PROBABILITIES = {
        'dominant': {  # Win by > 50%
            PowerUpType.GLOVE: 0.4,
            PowerUpType.HAMMER: 0.3,
            PowerUpType.FOG: 0.4,
            PowerUpType.TIME_BONUS: 0.3,
            PowerUpType.SHIELD: 0.2
        },
        'solid': {  # Win by 20-50%
            PowerUpType.GLOVE: 0.3,
            PowerUpType.HAMMER: 0.25,
            PowerUpType.FOG: 0.3,
            PowerUpType.TIME_BONUS: 0.25,
            PowerUpType.SHIELD: 0.15
        },
        'close': {  # Win by < 20%
            PowerUpType.GLOVE: 0.2,
            PowerUpType.HAMMER: 0.2,
            PowerUpType.FOG: 0.2,
            PowerUpType.TIME_BONUS: 0.2,
            PowerUpType.SHIELD: 0.1
        }
    }

    # Streak bonuses
    STREAK_BONUS = {
        1: 0,      # No streak
        2: 0.1,    # 2-win streak: +10% chance
        3: 0.2,    # 3-win streak: +20% chance
        4: 0.3,    # 4-win streak: +30% chance
        5: 0.4     # 5+ win streak: +40% chance
    }

    def __init__(self):
        self.current_streak = 0
        self.total_battles = 0
        self.total_wins = 0
        self.rewards_history: List[BattleReward] = []

    def calculate_rewards(
        self,
        winner_score: int,
        loser_score: int,
        battle_id: str,
        streak: int = 0
    ) -> BattleReward:
        """
        Calculate rewards for a battle winner.

        Args:
            winner_score: Winner's final score
            loser_score: Loser's final score
            battle_id: Unique battle identifier
            streak: Current win streak

        Returns:
            BattleReward with earned power-ups
        """
        # Determine victory margin
        total = winner_score + loser_score
        if total == 0:
            margin = 0
        else:
            margin = (winner_score - loser_score) / total

        # Select reward tier
        if margin > 0.5:
            tier = 'dominant'
        elif margin > 0.2:
            tier = 'solid'
        else:
            tier = 'close'

        # Get base probabilities
        probs = self.REWARD_PROBABILITIES[tier].copy()

        # Apply streak bonus
        streak_bonus = self.STREAK_BONUS.get(min(streak, 5), 0.4)
        for power_up_type in probs:
            probs[power_up_type] = min(0.9, probs[power_up_type] + streak_bonus)

        # Roll for each reward
        earned_power_ups = []
        for power_up_type, probability in probs.items():
            if random.random() < probability:
                earned_power_ups.append(PowerUp(
                    type=power_up_type,
                    source=f"battle_reward_{tier}"
                ))

        # Guarantee at least one reward
        if not earned_power_ups:
            random_type = random.choice(list(PowerUpType))
            earned_power_ups.append(PowerUp(
                type=random_type,
                source="battle_reward_guaranteed"
            ))

        # Calculate bonus coins/XP
        coins_bonus = int(winner_score * 0.01)  # 1% of score
        xp_bonus = int(margin * 100)  # Based on margin

        reward = BattleReward(
            battle_id=battle_id,
            earned_at=datetime.now(),
            power_ups=earned_power_ups,
            coins_bonus=coins_bonus,
            xp_bonus=xp_bonus
        )

        self.rewards_history.append(reward)

        logger.info(
            f"Battle rewards: {len(earned_power_ups)} power-ups "
            f"({', '.join(p.type.value for p in earned_power_ups)}), "
            f"+{coins_bonus} coins, +{xp_bonus} XP"
        )

        return reward

    def apply_rewards_to_inventory(
        self,
        reward: BattleReward,
        inventory: PowerUpInventory
    ):
        """Add earned rewards to player's inventory."""
        for power_up in reward.power_ups:
            inventory.add_power_up(power_up.type, power_up.source)

    def record_battle_result(self, won: bool) -> int:
        """Record battle result and return current streak."""
        self.total_battles += 1

        if won:
            self.total_wins += 1
            self.current_streak += 1
        else:
            self.current_streak = 0

        return self.current_streak


@dataclass
class TournamentMatch:
    """A single match in a tournament."""
    match_id: str
    player1: str
    player2: str
    player1_score: int = 0
    player2_score: int = 0
    winner: Optional[str] = None
    battle_conditions: Optional[BattleConditions] = None
    rewards_earned: Optional[BattleReward] = None
    played_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            'match_id': self.match_id,
            'player1': self.player1,
            'player2': self.player2,
            'player1_score': self.player1_score,
            'player2_score': self.player2_score,
            'winner': self.winner,
            'played_at': self.played_at.isoformat() if self.played_at else None
        }


@dataclass
class TournamentRound:
    """A round in a Best of X tournament."""
    round_number: int
    matches: List[TournamentMatch] = field(default_factory=list)
    player1_wins: int = 0
    player2_wins: int = 0

    def get_round_winner(self) -> Optional[str]:
        """Get winner of this round based on match results."""
        if not self.matches:
            return None

        last_match = self.matches[-1]
        return last_match.winner


class BestOfTournament:
    """
    Best of X tournament system with power-up accumulation.

    Features:
    - Best of 3, 5, 7 formats
    - Power-ups carry over between rounds
    - Rewards accumulate with wins
    - Strategic power-up usage across matches
    """

    def __init__(
        self,
        player1: str,
        player2: str,
        best_of: int = 3,
        tournament_id: str = None
    ):
        self.tournament_id = tournament_id or f"tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.player1 = player1
        self.player2 = player2
        self.best_of = best_of
        self.wins_needed = (best_of // 2) + 1

        # Inventories
        self.player1_inventory = PowerUpInventory(player1)
        self.player2_inventory = PowerUpInventory(player2)

        # Rewards engine
        self.rewards_engine = BattleRewardsEngine()

        # Tournament state
        self.rounds: List[TournamentRound] = []
        self.player1_wins = 0
        self.player2_wins = 0
        self.current_round = 0
        self.winner: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None

        # Statistics
        self.total_points_p1 = 0
        self.total_points_p2 = 0
        self.power_ups_used_p1: Dict[PowerUpType, int] = {t: 0 for t in PowerUpType}
        self.power_ups_used_p2: Dict[PowerUpType, int] = {t: 0 for t in PowerUpType}

    def start(self):
        """Start the tournament."""
        self.started_at = datetime.now()
        logger.info(f"""
{'='*60}
TOURNAMENT STARTED: Best of {self.best_of}
{'='*60}
{self.player1} vs {self.player2}
First to {self.wins_needed} wins!
{'='*60}
        """)

    def record_match(
        self,
        player1_score: int,
        player2_score: int,
        conditions: BattleConditions = None
    ) -> TournamentMatch:
        """
        Record a match result.

        Args:
            player1_score: Player 1's final score
            player2_score: Player 2's final score
            conditions: Battle conditions at end of match

        Returns:
            The recorded match
        """
        self.current_round += 1
        match_id = f"{self.tournament_id}_round{self.current_round}"

        # Determine winner
        if player1_score > player2_score:
            winner = self.player1
            self.player1_wins += 1
            winner_score = player1_score
            loser_score = player2_score
            winner_inventory = self.player1_inventory
        else:
            winner = self.player2
            self.player2_wins += 1
            winner_score = player2_score
            loser_score = player1_score
            winner_inventory = self.player2_inventory

        # Update totals
        self.total_points_p1 += player1_score
        self.total_points_p2 += player2_score

        # Calculate rewards for winner
        streak = self.rewards_engine.record_battle_result(winner == self.player1)
        rewards = self.rewards_engine.calculate_rewards(
            winner_score=winner_score,
            loser_score=loser_score,
            battle_id=match_id,
            streak=streak if winner == self.player1 else 0
        )

        # Apply rewards to winner's inventory
        self.rewards_engine.apply_rewards_to_inventory(rewards, winner_inventory)

        # Create match record
        match = TournamentMatch(
            match_id=match_id,
            player1=self.player1,
            player2=self.player2,
            player1_score=player1_score,
            player2_score=player2_score,
            winner=winner,
            battle_conditions=conditions,
            rewards_earned=rewards,
            played_at=datetime.now()
        )

        # Create or update round
        if not self.rounds or len(self.rounds[-1].matches) >= 1:
            self.rounds.append(TournamentRound(round_number=self.current_round))
        self.rounds[-1].matches.append(match)

        # Update round wins
        if winner == self.player1:
            self.rounds[-1].player1_wins += 1
        else:
            self.rounds[-1].player2_wins += 1

        # Log result
        logger.info(f"""
┌──────────────────────────────────────────────────────────────────────┐
│ ROUND {self.current_round} COMPLETE
├──────────────────────────────────────────────────────────────────────┤
│ {self.player1}: {player1_score:,} | {self.player2}: {player2_score:,}
│ Winner: {winner}
├──────────────────────────────────────────────────────────────────────┤
│ Series: {self.player1} {self.player1_wins} - {self.player2_wins} {self.player2}
│ Rewards: {', '.join(p.type.value for p in rewards.power_ups)}
└──────────────────────────────────────────────────────────────────────┘
        """)

        # Check for tournament winner
        if self.player1_wins >= self.wins_needed:
            self.winner = self.player1
            self._end_tournament()
        elif self.player2_wins >= self.wins_needed:
            self.winner = self.player2
            self._end_tournament()

        return match

    def use_power_up(self, player: str, power_up_type: PowerUpType) -> bool:
        """Use a power-up from a player's inventory."""
        if player == self.player1:
            inventory = self.player1_inventory
            usage_tracker = self.power_ups_used_p1
        else:
            inventory = self.player2_inventory
            usage_tracker = self.power_ups_used_p2

        power_up = inventory.use_power_up(power_up_type)
        if power_up:
            usage_tracker[power_up_type] += 1
            return True
        return False

    def get_available_power_ups(self, player: str) -> Dict[PowerUpType, int]:
        """Get available power-ups for a player."""
        if player == self.player1:
            return self.player1_inventory.get_all_available()
        else:
            return self.player2_inventory.get_all_available()

    def _end_tournament(self):
        """End the tournament."""
        self.ended_at = datetime.now()

        logger.info(f"""
╔══════════════════════════════════════════════════════════════════════╗
║ TOURNAMENT COMPLETE: {self.winner} WINS!
╠══════════════════════════════════════════════════════════════════════╣
║ Final Score: {self.player1} {self.player1_wins} - {self.player2_wins} {self.player2}
║ Total Points: {self.total_points_p1:,} vs {self.total_points_p2:,}
╠══════════════════════════════════════════════════════════════════════╣
║ Power-ups Earned:
║   {self.player1}: {dict(self.player1_inventory.total_earned)}
║   {self.player2}: {dict(self.player2_inventory.total_earned)}
╚══════════════════════════════════════════════════════════════════════╝
        """)

    def is_complete(self) -> bool:
        """Check if tournament is complete."""
        return self.winner is not None

    def get_status(self) -> Dict:
        """Get current tournament status."""
        return {
            'tournament_id': self.tournament_id,
            'player1': self.player1,
            'player2': self.player2,
            'best_of': self.best_of,
            'wins_needed': self.wins_needed,
            'player1_wins': self.player1_wins,
            'player2_wins': self.player2_wins,
            'current_round': self.current_round,
            'winner': self.winner,
            'is_complete': self.is_complete(),
            'total_points': {
                self.player1: self.total_points_p1,
                self.player2: self.total_points_p2
            },
            'inventories': {
                self.player1: self.player1_inventory.get_all_available(),
                self.player2: self.player2_inventory.get_all_available()
            },
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }

    def to_dict(self) -> Dict:
        """Convert tournament to dictionary for serialization."""
        return {
            **self.get_status(),
            'rounds': [
                {
                    'round_number': r.round_number,
                    'matches': [m.to_dict() for m in r.matches],
                    'player1_wins': r.player1_wins,
                    'player2_wins': r.player2_wins
                }
                for r in self.rounds
            ],
            'player1_inventory': self.player1_inventory.to_dict(),
            'player2_inventory': self.player2_inventory.to_dict()
        }

    def save(self, filepath: Path):
        """Save tournament to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


# === Convenience Functions ===

def create_best_of_3(player1: str, player2: str) -> BestOfTournament:
    """Create a Best of 3 tournament."""
    return BestOfTournament(player1, player2, best_of=3)


def create_best_of_5(player1: str, player2: str) -> BestOfTournament:
    """Create a Best of 5 tournament."""
    return BestOfTournament(player1, player2, best_of=5)


def create_best_of_7(player1: str, player2: str) -> BestOfTournament:
    """Create a Best of 7 tournament."""
    return BestOfTournament(player1, player2, best_of=7)


# === Demo ===

if __name__ == "__main__":
    print("Battle Rewards System Demo")
    print("=" * 60)

    # Create a Best of 5 tournament
    tournament = create_best_of_5("Creator", "Opponent")
    tournament.start()

    # Simulate matches
    match_scores = [
        (150000, 120000),  # Creator wins
        (80000, 95000),    # Opponent wins
        (200000, 180000),  # Creator wins
        (175000, 160000),  # Creator wins - tournament over
    ]

    for p1_score, p2_score in match_scores:
        if tournament.is_complete():
            break

        match = tournament.record_match(p1_score, p2_score)

        # Show available power-ups
        print(f"\nPower-ups available:")
        print(f"  Creator: {tournament.get_available_power_ups('Creator')}")
        print(f"  Opponent: {tournament.get_available_power_ups('Opponent')}")

    # Final status
    print("\n" + "=" * 60)
    print("Tournament Status:")
    status = tournament.get_status()
    print(f"  Winner: {status['winner']}")
    print(f"  Final: {status['player1_wins']} - {status['player2_wins']}")
    print(f"  Total Points: {status['total_points']}")
