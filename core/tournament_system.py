"""
Tournament System - Best of 3/5/7 Battle Series

Manages multi-battle tournaments with:
- Shared budget across battles (250,000 points)
- Reward distribution to winners
- Inventory persistence (gloves, fog, hammer, time extensions)
- Series tracking and statistics
- CARRYOVER LEARNING: Agents learn between battles!
- DRAMATIC ANNOUNCEMENTS: Match point, momentum shifts, clutch wins!
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import random


# ═══════════════════════════════════════════════════════════════════════════════
# DRAMATIC TOURNAMENT ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

TOURNAMENT_START_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏆🏆🏆  T O U R N A M E N T   M O D E  🏆🏆🏆                              ║
║                                                                              ║
║   Format: {format}                                                           ║
║   First to {wins_needed} wins takes the championship!                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

MATCH_POINT_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⚡⚡⚡  M A T C H   P O I N T  ⚡⚡⚡                                        ║
║                                                                              ║
║   {leader} leads {score}!                                                    ║
║   ONE MORE WIN and they take the championship!                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

CHAMPIONSHIP_POINT_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔥🔥🔥  C H A M P I O N S H I P   P O I N T  🔥🔥🔥                        ║
║                                                                              ║
║   {leader} can WIN IT ALL right now!                                         ║
║   {trailer} is fighting for survival!                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

MOMENTUM_SHIFT_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🌊🌊🌊  M O M E N T U M   S H I F T  🌊🌊🌊                                ║
║                                                                              ║
║   {team} wins {streak} IN A ROW!                                             ║
║   The tide is turning!                                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

COMEBACK_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔄🔄🔄  C O M E B A C K   A L E R T  🔄🔄🔄                                ║
║                                                                              ║
║   {team} was down {deficit} and ties the series {score}!                     ║
║   INCREDIBLE RESILIENCE!                                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

CHAMPION_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   👑👑👑  C H A M P I O N  👑👑👑                                            ║
║                                                                              ║
║   {winner} WINS THE TOURNAMENT!                                              ║
║   Final Score: {score}                                                       ║
║                                                                              ║
║   🏆 CONGRATULATIONS! 🏆                                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

LEARNING_BANNER = """
┌──────────────────────────────────────────────────────────────────────────────┐
│  🧠 CARRYOVER LEARNING ACTIVE                                                │
│  Agents are adapting between battles...                                      │
│  {agent_count} agents learning from Battle {battle_num} results              │
└──────────────────────────────────────────────────────────────────────────────┘
"""


class TournamentFormat(Enum):
    """Tournament format types."""
    BEST_OF_3 = 3
    BEST_OF_5 = 5
    BEST_OF_7 = 7


class RewardType(Enum):
    """Types of rewards available."""
    X5_GLOVE = "x5_glove"          # Can trigger x5 strike
    FOG = "fog"                     # Hide score from opponent
    HAMMER = "hammer"               # Counter opponent x5
    TIME_EXTENSION = "time_ext"    # +20 second bonus


@dataclass
class BattleReward:
    """Reward configuration for battle victory."""
    x5_gloves: int = 1
    fogs: int = 1
    hammers: int = 1
    time_extensions: int = 1

    def to_dict(self) -> Dict[str, int]:
        """Convert to inventory dictionary."""
        return {
            RewardType.X5_GLOVE.value: self.x5_gloves,
            RewardType.FOG.value: self.fogs,
            RewardType.HAMMER.value: self.hammers,
            RewardType.TIME_EXTENSION.value: self.time_extensions
        }


@dataclass
class TeamInventory:
    """Team's inventory of special items."""
    team_name: str
    x5_gloves: int = 0
    fogs: int = 0
    hammers: int = 0
    time_extensions: int = 0

    def add_reward(self, reward: BattleReward):
        """Add reward items to inventory."""
        self.x5_gloves += reward.x5_gloves
        self.fogs += reward.fogs
        self.hammers += reward.hammers
        self.time_extensions += reward.time_extensions

    def consume_item(self, item_type: RewardType, count: int = 1) -> bool:
        """
        Consume an item from inventory.

        Args:
            item_type: Type of item to consume
            count: Number of items to consume

        Returns:
            True if consumption successful, False if insufficient items
        """
        if item_type == RewardType.X5_GLOVE:
            if self.x5_gloves >= count:
                self.x5_gloves -= count
                return True
        elif item_type == RewardType.FOG:
            if self.fogs >= count:
                self.fogs -= count
                return True
        elif item_type == RewardType.HAMMER:
            if self.hammers >= count:
                self.hammers -= count
                return True
        elif item_type == RewardType.TIME_EXTENSION:
            if self.time_extensions >= count:
                self.time_extensions -= count
                return True
        return False

    def get_status(self) -> Dict[str, int]:
        """Get current inventory status."""
        return {
            "x5_gloves": self.x5_gloves,
            "fogs": self.fogs,
            "hammers": self.hammers,
            "time_extensions": self.time_extensions
        }

    def print_inventory(self):
        """Print formatted inventory."""
        print(f"\n📦 {self.team_name} Inventory:")
        print(f"   🥊 x5 Gloves: {self.x5_gloves}")
        print(f"   🌫️  Fogs: {self.fogs}")
        print(f"   🔨 Hammers: {self.hammers}")
        print(f"   ⏱️  Time Extensions: {self.time_extensions}")


@dataclass
class SharedBudget:
    """
    Shared budget tracker across tournament battles.

    Teams draw from same pool of 250,000 points.
    Budget resets each tournament series.
    """
    total_budget: int = 250000
    spent: int = 0
    remaining: int = 250000

    def spend(self, amount: int, agent_name: str) -> bool:
        """
        Attempt to spend from budget.

        Args:
            amount: Points to spend
            agent_name: Agent making the purchase

        Returns:
            True if purchase successful, False if insufficient budget
        """
        if amount <= self.remaining:
            self.spent += amount
            self.remaining -= amount
            return True
        else:
            print(f"❌ {agent_name}: Insufficient budget! "
                  f"Need {amount:,}, only {self.remaining:,} remaining")
            return False

    def get_status(self) -> Dict[str, int]:
        """Get budget status."""
        return {
            "total": self.total_budget,
            "spent": self.spent,
            "remaining": self.remaining,
            "spent_percent": (self.spent / self.total_budget * 100) if self.total_budget > 0 else 0
        }

    def print_status(self):
        """Print formatted budget status."""
        status = self.get_status()
        print(f"\n💰 Tournament Budget:")
        print(f"   Total: {status['total']:,} points")
        print(f"   Spent: {status['spent']:,} points ({status['spent_percent']:.1f}%)")
        print(f"   Remaining: {status['remaining']:,} points")


@dataclass
class BattleResult:
    """Result of a single battle in tournament."""
    battle_number: int
    winner: str  # "creator" or "opponent"
    creator_score: int
    opponent_score: int
    score_diff: int
    duration: int
    budget_spent: int
    rewards_earned: Optional[BattleReward] = None
    top_contributor: Optional[str] = None  # Agent name
    top_contribution: int = 0  # Points contributed
    bonus_rewards_earned: bool = False  # 3x rewards if 80k+


class TournamentManager:
    """
    Manages multi-battle tournament series.

    Features:
    - Best of 3, 5, or 7 format
    - Shared budget tracking (250,000 points)
    - Reward distribution to winners
    - Series statistics and analytics
    - CARRYOVER LEARNING: Agents evolve between battles!
    - DRAMATIC ANNOUNCEMENTS: Match point, momentum shifts, comebacks!
    """

    def __init__(self,
                 format: TournamentFormat = TournamentFormat.BEST_OF_3,
                 total_budget: int = 250000,
                 battle_duration: int = 180,
                 reward_config: Optional[BattleReward] = None,
                 enable_carryover_learning: bool = True):
        """
        Initialize tournament manager.

        Args:
            format: BEST_OF_3, BEST_OF_5, or BEST_OF_7
            total_budget: Shared budget for entire series (default 250k)
            battle_duration: Duration of each battle in seconds
            reward_config: Reward configuration for battle winners
            enable_carryover_learning: Allow agents to learn between battles
        """
        self.format = format
        self.battle_duration = battle_duration
        self.battles_to_win = (format.value // 2) + 1  # 2 for BO3, 3 for BO5, 4 for BO7

        # Budget and inventory
        self.shared_budget = SharedBudget(total_budget=total_budget)
        self.creator_inventory = TeamInventory("Creator Team")
        self.opponent_inventory = TeamInventory("Opponent Team")

        # Rewards
        self.reward_config = reward_config or BattleReward()

        # Battle tracking
        self.battles: List[BattleResult] = []
        self.creator_wins = 0
        self.opponent_wins = 0
        self.current_battle = 0
        self.tournament_winner: Optional[str] = None

        # Random budget scenarios
        self.use_random_budgets = False
        self.budget_scenarios = []

        # === CARRYOVER LEARNING ===
        self.enable_carryover_learning = enable_carryover_learning
        self.learning_callback: Optional[Callable] = None
        self.agents: List[Any] = []  # Will be set via set_agents()

        # === MOMENTUM TRACKING ===
        self.creator_streak = 0
        self.opponent_streak = 0
        self.max_deficit_overcome = {"creator": 0, "opponent": 0}
        self.last_winner: Optional[str] = None

        # === DRAMATIC STATE ===
        self.match_point_announced = False
        self.championship_point_announced = False

    def enable_random_budgets(self, scenarios: Optional[List[str]] = None):
        """
        Enable random budget allocation for varied gameplay.

        Args:
            scenarios: Optional list of scenario names to use
                      Default: ["aggressive", "balanced", "conservative", "clutch"]
        """
        self.use_random_budgets = True

        # Define budget scenarios
        all_scenarios = {
            "aggressive": {
                "name": "🔥 Aggressive",
                "description": "High spending (80-120k)",
                "min": 80000,
                "max": 120000
            },
            "balanced": {
                "name": "⚖️ Balanced",
                "description": "Moderate spending (50-80k)",
                "min": 50000,
                "max": 80000
            },
            "conservative": {
                "name": "🛡️ Conservative",
                "description": "Low spending (30-50k)",
                "min": 30000,
                "max": 50000
            },
            "clutch": {
                "name": "⚡ Clutch",
                "description": "All-in (100-150k)",
                "min": 100000,
                "max": 150000
            }
        }

        # Use specified scenarios or all by default
        if scenarios:
            self.budget_scenarios = [all_scenarios[s] for s in scenarios if s in all_scenarios]
        else:
            self.budget_scenarios = list(all_scenarios.values())

    def get_random_budget_limit(self) -> tuple:
        """
        Generate random budget limit for current battle.

        Returns:
            Tuple of (scenario_name, budget_limit)
        """
        if not self.use_random_budgets or not self.budget_scenarios:
            return "Standard", None

        # Pick random scenario
        scenario = random.choice(self.budget_scenarios)
        budget_limit = random.randint(scenario["min"], scenario["max"])

        return scenario["name"], budget_limit

    # ═══════════════════════════════════════════════════════════════════════════
    # CARRYOVER LEARNING SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════

    def set_agents(self, agents: List[Any]):
        """
        Set agents for carryover learning.

        Args:
            agents: List of agent objects with learn_from_battle() method
        """
        self.agents = agents

    def set_learning_callback(self, callback: Callable):
        """
        Set custom learning callback for between-battle learning.

        Args:
            callback: Function(agents, won, battle_stats) -> None
        """
        self.learning_callback = callback

    def _trigger_carryover_learning(self, battle_result: 'BattleResult'):
        """Trigger learning for all agents after a battle."""
        if not self.enable_carryover_learning:
            return

        if not self.agents:
            return

        # Count learning agents
        learning_agents = [a for a in self.agents if hasattr(a, 'learn_from_battle')]
        if not learning_agents:
            return

        print(LEARNING_BANNER.format(
            agent_count=len(learning_agents),
            battle_num=battle_result.battle_number
        ))

        # Build battle stats
        battle_stats = {
            'points_donated': battle_result.creator_score,
            'battle_number': battle_result.battle_number,
            'series_score': f"{self.creator_wins}-{self.opponent_wins}",
            'is_match_point': self._is_match_point(),
            'momentum': 'creator' if self.creator_streak > 1 else ('opponent' if self.opponent_streak > 1 else 'neutral'),
        }

        # Use custom callback or default learning
        if self.learning_callback:
            self.learning_callback(
                self.agents,
                battle_result.winner == "creator",
                battle_stats
            )
        else:
            # Default: call learn_from_battle on each agent
            won = battle_result.winner == "creator"
            for agent in learning_agents:
                try:
                    agent.learn_from_battle(won, battle_stats)
                except Exception as e:
                    print(f"   ⚠️ {agent.name} learning error: {e}")

        print(f"   ✅ Learning complete for {len(learning_agents)} agents\n")

    # ═══════════════════════════════════════════════════════════════════════════
    # DRAMATIC ANNOUNCEMENTS
    # ═══════════════════════════════════════════════════════════════════════════

    def _is_match_point(self) -> bool:
        """Check if either team is at match point."""
        return (self.creator_wins == self.battles_to_win - 1 or
                self.opponent_wins == self.battles_to_win - 1)

    def _announce_pre_battle_drama(self):
        """Announce dramatic situation before a battle starts."""
        creator_at_mp = self.creator_wins == self.battles_to_win - 1
        opponent_at_mp = self.opponent_wins == self.battles_to_win - 1

        # Both at match point = Championship point!
        if creator_at_mp and opponent_at_mp:
            if not self.championship_point_announced:
                self.championship_point_announced = True
                print(CHAMPIONSHIP_POINT_BANNER.format(
                    leader="BOTH TEAMS",
                    trailer="THE LOSER"
                ))
                print("   🔥 WINNER TAKES ALL! 🔥\n")
            return

        # One team at match point
        if creator_at_mp or opponent_at_mp:
            if not self.match_point_announced:
                self.match_point_announced = True
                leader = "CREATOR" if creator_at_mp else "OPPONENT"
                trailer = "OPPONENT" if creator_at_mp else "CREATOR"
                score = f"{self.creator_wins}-{self.opponent_wins}"
                print(MATCH_POINT_BANNER.format(
                    leader=leader,
                    score=score
                ))
            return

        # Check for momentum (3+ win streak)
        if self.creator_streak >= 3:
            print(MOMENTUM_SHIFT_BANNER.format(
                team="CREATOR",
                streak=self.creator_streak
            ))
        elif self.opponent_streak >= 3:
            print(MOMENTUM_SHIFT_BANNER.format(
                team="OPPONENT",
                streak=self.opponent_streak
            ))

    def _check_comeback(self, winner: str):
        """Check and announce comebacks."""
        # Track max deficit overcome
        if winner == "creator":
            deficit_before = self.opponent_wins - (self.creator_wins - 1)
            if deficit_before >= 2 and self.creator_wins == self.opponent_wins:
                print(COMEBACK_BANNER.format(
                    team="CREATOR",
                    deficit=f"0-{deficit_before}",
                    score=f"{self.creator_wins}-{self.opponent_wins}"
                ))
                self.max_deficit_overcome["creator"] = max(
                    self.max_deficit_overcome["creator"], deficit_before
                )
        else:
            deficit_before = self.creator_wins - (self.opponent_wins - 1)
            if deficit_before >= 2 and self.opponent_wins == self.creator_wins:
                print(COMEBACK_BANNER.format(
                    team="OPPONENT",
                    deficit=f"0-{deficit_before}",
                    score=f"{self.opponent_wins}-{self.creator_wins}"
                ))
                self.max_deficit_overcome["opponent"] = max(
                    self.max_deficit_overcome["opponent"], deficit_before
                )

    def _update_streaks(self, winner: str):
        """Update win streaks."""
        if winner == "creator":
            self.creator_streak += 1
            self.opponent_streak = 0
        else:
            self.opponent_streak += 1
            self.creator_streak = 0
        self.last_winner = winner

    def get_series_status_text(self) -> str:
        """Get formatted series status for display."""
        lines = []
        lines.append(f"Series: {self.creator_wins}-{self.opponent_wins}")

        if self._is_match_point():
            if self.creator_wins == self.battles_to_win - 1:
                lines.append("⚡ CREATOR at MATCH POINT!")
            if self.opponent_wins == self.battles_to_win - 1:
                lines.append("⚡ OPPONENT at MATCH POINT!")

        if self.creator_streak >= 2:
            lines.append(f"🔥 Creator on {self.creator_streak}-win streak")
        elif self.opponent_streak >= 2:
            lines.append(f"🔥 Opponent on {self.opponent_streak}-win streak")

        return "\n".join(lines)

    def start_tournament(self):
        """Initialize tournament."""
        # Print dramatic banner
        format_str = self.format.name.replace("_", " ")
        print(TOURNAMENT_START_BANNER.format(
            format=format_str,
            wins_needed=self.battles_to_win
        ))

        print(f"📋 Tournament Details:")
        print(f"   Format: First to {self.battles_to_win} wins")
        print(f"   Battle Duration: {self.battle_duration}s")
        print(f"   Shared Budget: {self.shared_budget.total_budget:,} points")
        print(f"   Carryover Learning: {'✅ ENABLED' if self.enable_carryover_learning else '❌ Disabled'}")
        print(f"   Rewards per victory: {self.reward_config.to_dict()}")
        if self.use_random_budgets:
            print(f"   ⚡ Random Battle Budgets: ENABLED")
            print(f"      Scenarios: {', '.join(s['name'] for s in self.budget_scenarios)}")
        print("")

    def can_continue(self) -> bool:
        """Check if tournament can continue."""
        # Tournament over if someone reached required wins
        if self.creator_wins >= self.battles_to_win:
            return False
        if self.opponent_wins >= self.battles_to_win:
            return False

        # Tournament over if max battles reached
        if len(self.battles) >= self.format.value:
            return False

        return True

    def record_battle_result(self, winner: str, creator_score: int,
                            opponent_score: int, budget_spent_this_battle: int,
                            agent_performance: Optional[Dict[str, Dict]] = None):
        """
        Record result of a battle with performance-based rewards.

        Args:
            winner: "creator" or "opponent"
            creator_score: Final creator score
            opponent_score: Final opponent score
            budget_spent_this_battle: Budget spent in this battle
            agent_performance: Dict of agent stats from analytics
        """
        self.current_battle += 1

        # Update wins
        if winner == "creator":
            self.creator_wins += 1
        else:
            self.opponent_wins += 1

        # Update streaks and check for comebacks
        self._update_streaks(winner)
        self._check_comeback(winner)

        # Calculate performance-based rewards
        bonus_rewards = False
        top_contributor = None
        top_contribution = 0

        if agent_performance:
            # Find top contributor
            for agent, stats in agent_performance.items():
                contribution = stats.get('total_donated', 0)
                if contribution > top_contribution:
                    top_contribution = contribution
                    top_contributor = agent

            # Award bonus rewards if top contributor spent 80k+
            if top_contribution >= 80000:
                bonus_rewards = True
                # 3 récompenses: 1 glove + 1 fog + 1 hammer
                rewards = BattleReward(
                    x5_gloves=1,
                    fogs=1,
                    hammers=1,
                    time_extensions=0
                )
            else:
                # Standard: 1 time extension
                rewards = BattleReward(
                    x5_gloves=0,
                    fogs=0,
                    hammers=0,
                    time_extensions=1
                )
        else:
            # No performance data: standard reward
            rewards = BattleReward(
                x5_gloves=0,
                fogs=0,
                hammers=0,
                time_extensions=1
            )

        # Create result
        result = BattleResult(
            battle_number=self.current_battle,
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score,
            score_diff=abs(creator_score - opponent_score),
            duration=self.battle_duration,
            budget_spent=budget_spent_this_battle,
            rewards_earned=rewards,
            top_contributor=top_contributor,
            top_contribution=top_contribution,
            bonus_rewards_earned=bonus_rewards
        )
        self.battles.append(result)

        # Award rewards to winner
        if winner == "creator":
            self.creator_inventory.add_reward(rewards)
        else:
            self.opponent_inventory.add_reward(rewards)

        # Print battle summary
        self._print_battle_summary(result)

        # === CARRYOVER LEARNING ===
        self._trigger_carryover_learning(result)

        # Check for tournament end
        if not self.can_continue():
            self._end_tournament()
        else:
            # Announce drama for next battle
            self._announce_pre_battle_drama()

    def _print_battle_summary(self, result: BattleResult):
        """Print summary of battle result."""
        print("\n" + "=" * 70)
        print(f"📊 BATTLE {result.battle_number} RESULTS")
        print("=" * 70)
        print(f"Winner: {result.winner.upper()}")
        print(f"Score: Creator {result.creator_score:,} vs Opponent {result.opponent_score:,}")
        print(f"Margin: {result.score_diff:,} points")
        print(f"Budget Spent: {result.budget_spent:,} points")

        # Show top contributor
        if result.top_contributor:
            print(f"\n⭐ Top Contributor: {result.top_contributor}")
            print(f"   Contribution: {result.top_contribution:,} points")
            if result.bonus_rewards_earned:
                print(f"   🎉 BONUS! Spent 80k+ → 3 récompenses!")

        print(f"\n🏆 Current Series Score:")
        print(f"   Creator: {self.creator_wins} wins")
        print(f"   Opponent: {self.opponent_wins} wins")
        print(f"   (First to {self.battles_to_win} wins)")

        # Show rewards earned
        if result.rewards_earned:
            if result.bonus_rewards_earned:
                print(f"\n🎁 Rewards Earned by {result.winner.title()} (Performance Bonus!):")
            else:
                print(f"\n🎁 Rewards Earned by {result.winner.title()}:")

            rewards = result.rewards_earned.to_dict()
            for reward_type, count in rewards.items():
                if count > 0:
                    print(f"   +{count} {reward_type}")

        print("=" * 70 + "\n")

    def _end_tournament(self):
        """Finalize tournament and declare winner."""
        if self.creator_wins > self.opponent_wins:
            self.tournament_winner = "creator"
        else:
            self.tournament_winner = "opponent"

        # Print champion banner
        score = f"{self.creator_wins}-{self.opponent_wins}" if self.tournament_winner == "creator" else f"{self.opponent_wins}-{self.creator_wins}"
        print(CHAMPION_BANNER.format(
            winner=self.tournament_winner.upper(),
            score=score
        ))

        print(f"📊 Final Series Score:")
        print(f"   Creator: {self.creator_wins} wins")
        print(f"   Opponent: {self.opponent_wins} wins")

        # Print inventories
        self.creator_inventory.print_inventory()
        self.opponent_inventory.print_inventory()

        # Budget summary
        self.shared_budget.print_status()

        # Battle-by-battle summary
        print(f"\n📋 Battle Summary:")
        for battle in self.battles:
            winner_icon = "✅" if battle.winner == self.tournament_winner else "❌"
            print(f"   Battle {battle.battle_number}: {winner_icon} "
                  f"{battle.winner.title()} wins "
                  f"({battle.creator_score:,} vs {battle.opponent_score:,})")

        print("\n" + "=" * 70 + "\n")

    def get_tournament_stats(self) -> Dict[str, Any]:
        """Get complete tournament statistics."""
        return {
            "format": self.format.name,
            "battles_to_win": self.battles_to_win,
            "total_battles": len(self.battles),
            "creator_wins": self.creator_wins,
            "opponent_wins": self.opponent_wins,
            "tournament_winner": self.tournament_winner,
            "budget": self.shared_budget.get_status(),
            "creator_inventory": self.creator_inventory.get_status(),
            "opponent_inventory": self.opponent_inventory.get_status(),
            "battles": [
                {
                    "number": b.battle_number,
                    "winner": b.winner,
                    "creator_score": b.creator_score,
                    "opponent_score": b.opponent_score,
                    "score_diff": b.score_diff,
                    "budget_spent": b.budget_spent,
                    "top_contributor": b.top_contributor,
                    "top_contribution": b.top_contribution,
                    "bonus_rewards_earned": b.bonus_rewards_earned
                }
                for b in self.battles
            ]
        }

    def get_available_time_extensions(self, team: str) -> int:
        """
        Get number of time extensions available for team.

        Args:
            team: "creator" or "opponent"

        Returns:
            Number of time extensions available
        """
        if team == "creator":
            return self.creator_inventory.time_extensions
        else:
            return self.opponent_inventory.time_extensions

    def print_series_status(self):
        """Print current series status between battles."""
        print("\n" + "=" * 70)
        print(f"📊 SERIES STATUS: Battle {len(self.battles) + 1}")
        print("=" * 70)
        print(f"Creator: {self.creator_wins} wins | Opponent: {self.opponent_wins} wins")
        print(f"(First to {self.battles_to_win} wins the tournament)")

        # Inventories
        self.creator_inventory.print_inventory()
        self.opponent_inventory.print_inventory()

        # Budget
        self.shared_budget.print_status()
        print("=" * 70 + "\n")

    # ═══════════════════════════════════════════════════════════════════════════
    # SAVE/LOAD SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════

    def save_tournament(self, save_name: str = None, save_dir: str = "data/saves") -> str:
        """
        Save current tournament state to JSON file.

        Args:
            save_name: Optional custom save name
            save_dir: Directory to save to

        Returns:
            Path to saved file
        """
        import os
        import json
        from datetime import datetime

        # Create save directory if needed
        os.makedirs(save_dir, exist_ok=True)

        # Generate save name if not provided
        if not save_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"SAVE_{timestamp}_{self.format.name}"

        filepath = os.path.join(save_dir, f"{save_name}.json")

        # Build save state
        save_state = {
            'version': '1.0',
            'save_id': save_name,
            'timestamp': datetime.now().isoformat(),

            # Tournament config
            'format': self.format.name,
            'battle_duration': self.battle_duration,
            'battles_to_win': self.battles_to_win,
            'enable_carryover_learning': self.enable_carryover_learning,

            # Current state
            'current_battle': self.current_battle,
            'creator_wins': self.creator_wins,
            'opponent_wins': self.opponent_wins,
            'tournament_winner': self.tournament_winner,

            # Budget
            'shared_budget': {
                'total_budget': self.shared_budget.total_budget,
                'spent': self.shared_budget.spent,
                'remaining': self.shared_budget.remaining
            },

            # Inventories
            'creator_inventory': self.creator_inventory.get_status(),
            'opponent_inventory': self.opponent_inventory.get_status(),

            # Reward config
            'reward_config': {
                'x5_gloves': self.reward_config.x5_gloves,
                'fogs': self.reward_config.fogs,
                'hammers': self.reward_config.hammers,
                'time_extensions': self.reward_config.time_extensions
            },

            # Battle history
            'battles': [
                {
                    'battle_number': b.battle_number,
                    'winner': b.winner,
                    'creator_score': b.creator_score,
                    'opponent_score': b.opponent_score,
                    'score_diff': b.score_diff,
                    'duration': b.duration,
                    'budget_spent': b.budget_spent,
                    'top_contributor': b.top_contributor,
                    'top_contribution': b.top_contribution,
                    'bonus_rewards_earned': b.bonus_rewards_earned
                }
                for b in self.battles
            ],

            # Momentum tracking
            'creator_streak': self.creator_streak,
            'opponent_streak': self.opponent_streak,
            'max_deficit_overcome': self.max_deficit_overcome,
            'last_winner': self.last_winner,

            # Dramatic state
            'match_point_announced': self.match_point_announced,
            'championship_point_announced': self.championship_point_announced,

            # Agent states (if agents have saveable state)
            'agent_states': self._get_agent_states()
        }

        with open(filepath, 'w') as f:
            json.dump(save_state, f, indent=2)

        print(f"\n💾 Tournament saved to: {filepath}")
        return filepath

    def _get_agent_states(self) -> List[Dict]:
        """Get saveable state from agents."""
        agent_states = []
        for agent in self.agents:
            state = {
                'name': getattr(agent, 'name', 'Unknown'),
                'emoji': getattr(agent, 'emoji', '🤖'),
                'agent_type': getattr(agent, 'agent_type', 'unknown')
            }
            # Save Q-table if agent has one
            if hasattr(agent, 'q_table'):
                state['q_table'] = dict(agent.q_table)
            # Save learning params if available
            if hasattr(agent, 'learning_rate'):
                state['learning_rate'] = agent.learning_rate
            if hasattr(agent, 'epsilon'):
                state['epsilon'] = agent.epsilon
            agent_states.append(state)
        return agent_states

    @classmethod
    def load_tournament(cls, filepath: str) -> 'TournamentManager':
        """
        Load tournament from save file.

        Args:
            filepath: Path to save file

        Returns:
            TournamentManager instance with restored state
        """
        import json

        with open(filepath, 'r') as f:
            save_state = json.load(f)

        # Create tournament with saved config
        format_enum = TournamentFormat[save_state['format']]
        tournament = cls(
            format=format_enum,
            total_budget=save_state['shared_budget']['total_budget'],
            battle_duration=save_state['battle_duration'],
            reward_config=BattleReward(
                x5_gloves=save_state['reward_config']['x5_gloves'],
                fogs=save_state['reward_config']['fogs'],
                hammers=save_state['reward_config']['hammers'],
                time_extensions=save_state['reward_config']['time_extensions']
            ),
            enable_carryover_learning=save_state['enable_carryover_learning']
        )

        # Restore current state
        tournament.current_battle = save_state['current_battle']
        tournament.creator_wins = save_state['creator_wins']
        tournament.opponent_wins = save_state['opponent_wins']
        tournament.tournament_winner = save_state.get('tournament_winner')

        # Restore budget
        tournament.shared_budget.spent = save_state['shared_budget']['spent']
        tournament.shared_budget.remaining = save_state['shared_budget']['remaining']

        # Restore inventories
        inv = save_state['creator_inventory']
        tournament.creator_inventory.x5_gloves = inv['x5_gloves']
        tournament.creator_inventory.fogs = inv['fogs']
        tournament.creator_inventory.hammers = inv['hammers']
        tournament.creator_inventory.time_extensions = inv['time_extensions']

        inv = save_state['opponent_inventory']
        tournament.opponent_inventory.x5_gloves = inv['x5_gloves']
        tournament.opponent_inventory.fogs = inv['fogs']
        tournament.opponent_inventory.hammers = inv['hammers']
        tournament.opponent_inventory.time_extensions = inv['time_extensions']

        # Restore battle history
        for b in save_state['battles']:
            result = BattleResult(
                battle_number=b['battle_number'],
                winner=b['winner'],
                creator_score=b['creator_score'],
                opponent_score=b['opponent_score'],
                score_diff=b['score_diff'],
                duration=b['duration'],
                budget_spent=b['budget_spent'],
                top_contributor=b.get('top_contributor'),
                top_contribution=b.get('top_contribution', 0),
                bonus_rewards_earned=b.get('bonus_rewards_earned', False)
            )
            tournament.battles.append(result)

        # Restore momentum
        tournament.creator_streak = save_state.get('creator_streak', 0)
        tournament.opponent_streak = save_state.get('opponent_streak', 0)
        tournament.max_deficit_overcome = save_state.get('max_deficit_overcome', {"creator": 0, "opponent": 0})
        tournament.last_winner = save_state.get('last_winner')

        # Restore dramatic state
        tournament.match_point_announced = save_state.get('match_point_announced', False)
        tournament.championship_point_announced = save_state.get('championship_point_announced', False)

        print(f"\n📂 Tournament loaded from: {filepath}")
        print(f"   Format: {tournament.format.name}")
        print(f"   Progress: Battle {tournament.current_battle} of {tournament.format.value}")
        print(f"   Score: Creator {tournament.creator_wins} - {tournament.opponent_wins} Opponent")

        return tournament

    @staticmethod
    def list_saves(save_dir: str = "data/saves") -> List[Dict]:
        """
        List available save files.

        Args:
            save_dir: Directory to search

        Returns:
            List of save file info dicts
        """
        import os
        import json

        saves = []
        if not os.path.exists(save_dir):
            return saves

        for filename in os.listdir(save_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(save_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    saves.append({
                        'filename': filename,
                        'filepath': filepath,
                        'save_id': data.get('save_id', filename),
                        'timestamp': data.get('timestamp', 'Unknown'),
                        'format': data.get('format', 'Unknown'),
                        'progress': f"{data.get('current_battle', 0)}/{data.get('battles_to_win', 0) * 2 - 1}",
                        'score': f"{data.get('creator_wins', 0)}-{data.get('opponent_wins', 0)}",
                        'complete': data.get('tournament_winner') is not None
                    })
                except Exception:
                    continue

        # Sort by timestamp (newest first)
        saves.sort(key=lambda x: x['timestamp'], reverse=True)
        return saves

    @staticmethod
    def print_saves(save_dir: str = "data/saves"):
        """Print formatted list of available saves."""
        saves = TournamentManager.list_saves(save_dir)

        print("\n" + "=" * 75)
        print("💾 AVAILABLE SAVE FILES")
        print("=" * 75)

        if not saves:
            print("   No save files found.")
            print(f"   (Looking in: {save_dir})")
        else:
            print(f"\n   {'#':<4}{'Save ID':<25}{'Format':<12}{'Score':<10}{'Status':<15}{'Date':<20}")
            print("   " + "-" * 70)

            for i, save in enumerate(saves, 1):
                status = "✅ Complete" if save['complete'] else f"🎮 Battle {save['progress']}"
                date = save['timestamp'][:19] if len(save['timestamp']) > 19 else save['timestamp']

                print(f"   {i:<4}{save['save_id'][:24]:<25}{save['format']:<12}"
                      f"{save['score']:<10}{status:<15}{date:<20}")

        print("=" * 75 + "\n")
