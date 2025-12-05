"""
Tournament Leaderboard System

Track and rank performance across multiple tournaments.

Features:
- ELO-style rating system
- Win/loss records
- Tournament history
- Performance statistics
- Rankings and standings
- PER-AGENT STATS: Track individual agent performance!
- HISTORICAL TRENDS: Performance over time
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json
import os


@dataclass
class TournamentRecord:
    """Record of a single tournament."""
    tournament_id: str
    date: str
    format: str  # "BEST_OF_3", "BEST_OF_5", or "BEST_OF_7"
    winner: str  # "creator" or "opponent"
    final_score: str  # e.g., "2-1"
    creator_wins: int
    opponent_wins: int
    total_battles: int
    average_score_per_battle: float
    total_points_spent: int
    mvp_agent: Optional[str] = None
    mvp_contribution: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# PER-AGENT STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentPerformance:
    """Performance record for a single agent in a single battle."""
    battle_id: str
    tournament_id: str
    date: str
    points_donated: int
    gifts_sent: int
    whale_gifts: int
    won: bool
    was_mvp: bool


@dataclass
class AgentStats:
    """Statistics for a single agent across all tournaments."""
    agent_name: str
    emoji: str = "🤖"

    # Battle stats
    battles_participated: int = 0
    battles_won: int = 0
    battles_lost: int = 0

    # Contribution stats
    total_points_donated: int = 0
    total_gifts_sent: int = 0
    total_whale_gifts: int = 0

    # MVP tracking
    mvp_count: int = 0
    highest_single_contribution: int = 0
    highest_contribution_battle: str = ""

    # Recent performance (last 10 battles)
    recent_contributions: List[int] = field(default_factory=list)

    # Performance history for trends
    performance_history: List[AgentPerformance] = field(default_factory=list)

    def win_rate(self) -> float:
        """Calculate battle win rate."""
        if self.battles_participated == 0:
            return 0.0
        return (self.battles_won / self.battles_participated) * 100

    def average_contribution(self) -> float:
        """Calculate average points per battle."""
        if self.battles_participated == 0:
            return 0.0
        return self.total_points_donated / self.battles_participated

    def recent_average(self, n: int = 10) -> float:
        """Calculate average of last N battles."""
        if not self.recent_contributions:
            return 0.0
        recent = self.recent_contributions[-n:]
        return sum(recent) / len(recent)

    def trend(self) -> str:
        """Get performance trend indicator."""
        if len(self.recent_contributions) < 5:
            return "📊 Insufficient data"

        recent_5 = self.recent_contributions[-5:]
        older_5 = self.recent_contributions[-10:-5] if len(self.recent_contributions) >= 10 else self.recent_contributions[:5]

        recent_avg = sum(recent_5) / len(recent_5)
        older_avg = sum(older_5) / len(older_5) if older_5 else recent_avg

        if recent_avg > older_avg * 1.2:
            return "📈 Improving (+{:.0f}%)".format((recent_avg / older_avg - 1) * 100)
        elif recent_avg < older_avg * 0.8:
            return "📉 Declining ({:.0f}%)".format((1 - recent_avg / older_avg) * 100)
        else:
            return "➡️ Stable"

    def record_battle(self, perf: AgentPerformance):
        """Record a battle performance."""
        self.battles_participated += 1
        if perf.won:
            self.battles_won += 1
        else:
            self.battles_lost += 1

        self.total_points_donated += perf.points_donated
        self.total_gifts_sent += perf.gifts_sent
        self.total_whale_gifts += perf.whale_gifts

        if perf.was_mvp:
            self.mvp_count += 1

        if perf.points_donated > self.highest_single_contribution:
            self.highest_single_contribution = perf.points_donated
            self.highest_contribution_battle = perf.battle_id

        # Track recent contributions (keep last 50)
        self.recent_contributions.append(perf.points_donated)
        if len(self.recent_contributions) > 50:
            self.recent_contributions = self.recent_contributions[-50:]

        # Track history (keep last 100)
        self.performance_history.append(perf)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]


class AgentLeaderboard:
    """
    Track individual agent performance across tournaments.

    Provides rankings, trends, and detailed statistics for each agent.
    """

    def __init__(self, save_file: str = "agent_leaderboard.json"):
        self.save_file = save_file
        self.agents: Dict[str, AgentStats] = {}
        self._load_data()

    def record_agent_performance(
        self,
        agent_name: str,
        emoji: str,
        battle_id: str,
        tournament_id: str,
        points_donated: int,
        gifts_sent: int,
        whale_gifts: int,
        won: bool,
        was_mvp: bool
    ):
        """Record an agent's performance in a battle."""
        # Create agent if not exists
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentStats(agent_name=agent_name, emoji=emoji)

        # Create performance record
        perf = AgentPerformance(
            battle_id=battle_id,
            tournament_id=tournament_id,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            points_donated=points_donated,
            gifts_sent=gifts_sent,
            whale_gifts=whale_gifts,
            won=won,
            was_mvp=was_mvp
        )

        # Record
        self.agents[agent_name].emoji = emoji  # Update emoji in case it changed
        self.agents[agent_name].record_battle(perf)

        self._save_data()

    def get_rankings(self, sort_by: str = "contribution") -> List[Dict]:
        """
        Get agent rankings.

        Args:
            sort_by: "contribution", "win_rate", "mvp_count", or "recent"
        """
        rankings = []

        for name, stats in self.agents.items():
            rankings.append({
                "rank": 0,  # Will be set after sorting
                "name": name,
                "emoji": stats.emoji,
                "battles": stats.battles_participated,
                "win_rate": stats.win_rate(),
                "total_contribution": stats.total_points_donated,
                "average_contribution": stats.average_contribution(),
                "mvp_count": stats.mvp_count,
                "recent_avg": stats.recent_average(10),
                "trend": stats.trend(),
                "highest_ever": stats.highest_single_contribution,
            })

        # Sort based on criteria
        if sort_by == "contribution":
            rankings.sort(key=lambda x: x["total_contribution"], reverse=True)
        elif sort_by == "win_rate":
            rankings.sort(key=lambda x: (x["win_rate"], x["battles"]), reverse=True)
        elif sort_by == "mvp_count":
            rankings.sort(key=lambda x: x["mvp_count"], reverse=True)
        elif sort_by == "recent":
            rankings.sort(key=lambda x: x["recent_avg"], reverse=True)
        else:
            rankings.sort(key=lambda x: x["total_contribution"], reverse=True)

        # Assign ranks
        for i, r in enumerate(rankings):
            r["rank"] = i + 1

        return rankings

    def print_leaderboard(self, sort_by: str = "contribution", top_n: int = 10):
        """Print formatted agent leaderboard."""
        rankings = self.get_rankings(sort_by)[:top_n]

        print("\n" + "=" * 85)
        print("🏅 AGENT LEADERBOARD")
        print("=" * 85)

        if not rankings:
            print("   No agent data yet. Play some battles!")
            print("=" * 85)
            return

        # Header
        print(f"{'Rank':<6}{'Agent':<25}{'Battles':<10}{'Win%':<8}{'Total Pts':<12}{'MVP':<6}{'Trend':<15}")
        print("-" * 85)

        for r in rankings:
            rank_str = f"#{r['rank']}"
            agent_str = f"{r['emoji']} {r['name']}"
            print(f"{rank_str:<6}{agent_str:<25}{r['battles']:<10}{r['win_rate']:.1f}%{'':<3}{r['total_contribution']:>10,}{'':<2}{r['mvp_count']:<6}{r['trend']:<15}")

        print("=" * 85)

        # Show top performer highlight
        if rankings:
            top = rankings[0]
            print(f"\n🌟 TOP PERFORMER: {top['emoji']} {top['name']}")
            print(f"   Total Contribution: {top['total_contribution']:,} points")
            print(f"   Highest Single Battle: {top['highest_ever']:,} points")
            print(f"   MVP Awards: {top['mvp_count']}")
            print("")

    def get_agent_details(self, agent_name: str) -> Optional[Dict]:
        """Get detailed stats for a specific agent."""
        if agent_name not in self.agents:
            return None

        stats = self.agents[agent_name]
        return {
            "name": stats.agent_name,
            "emoji": stats.emoji,
            "battles_participated": stats.battles_participated,
            "battles_won": stats.battles_won,
            "battles_lost": stats.battles_lost,
            "win_rate": stats.win_rate(),
            "total_points_donated": stats.total_points_donated,
            "average_contribution": stats.average_contribution(),
            "total_gifts_sent": stats.total_gifts_sent,
            "total_whale_gifts": stats.total_whale_gifts,
            "mvp_count": stats.mvp_count,
            "highest_single_contribution": stats.highest_single_contribution,
            "highest_contribution_battle": stats.highest_contribution_battle,
            "recent_average": stats.recent_average(10),
            "trend": stats.trend(),
            "recent_contributions": stats.recent_contributions[-10:],
        }

    def print_agent_card(self, agent_name: str):
        """Print detailed card for a specific agent."""
        details = self.get_agent_details(agent_name)
        if not details:
            print(f"❌ Agent '{agent_name}' not found in leaderboard.")
            return

        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  {details['emoji']} {details['name']:<56} ║
╠══════════════════════════════════════════════════════════════════╣
║  📊 BATTLE RECORD                                                ║
║     Battles: {details['battles_participated']}  ({details['battles_won']}W - {details['battles_lost']}L)                                     ║
║     Win Rate: {details['win_rate']:.1f}%                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  💰 CONTRIBUTION STATS                                           ║
║     Total Points: {details['total_points_donated']:,}                                     ║
║     Average/Battle: {details['average_contribution']:,.0f}                                    ║
║     Highest Ever: {details['highest_single_contribution']:,}                                      ║
╠══════════════════════════════════════════════════════════════════╣
║  🏆 ACHIEVEMENTS                                                 ║
║     MVP Awards: {details['mvp_count']}                                                ║
║     Whale Gifts: {details['total_whale_gifts']}                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  📈 RECENT PERFORMANCE                                           ║
║     Recent Avg (10): {details['recent_average']:,.0f}                                    ║
║     Trend: {details['trend']:<20}                               ║
╚══════════════════════════════════════════════════════════════════╝
""")

    def _save_data(self):
        """Save agent data to file."""
        data = {}
        for name, stats in self.agents.items():
            data[name] = {
                "agent_name": stats.agent_name,
                "emoji": stats.emoji,
                "battles_participated": stats.battles_participated,
                "battles_won": stats.battles_won,
                "battles_lost": stats.battles_lost,
                "total_points_donated": stats.total_points_donated,
                "total_gifts_sent": stats.total_gifts_sent,
                "total_whale_gifts": stats.total_whale_gifts,
                "mvp_count": stats.mvp_count,
                "highest_single_contribution": stats.highest_single_contribution,
                "highest_contribution_battle": stats.highest_contribution_battle,
                "recent_contributions": stats.recent_contributions,
            }

        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self):
        """Load agent data from file."""
        if not os.path.exists(self.save_file):
            return

        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)

            for name, d in data.items():
                self.agents[name] = AgentStats(
                    agent_name=d.get("agent_name", name),
                    emoji=d.get("emoji", "🤖"),
                    battles_participated=d.get("battles_participated", 0),
                    battles_won=d.get("battles_won", 0),
                    battles_lost=d.get("battles_lost", 0),
                    total_points_donated=d.get("total_points_donated", 0),
                    total_gifts_sent=d.get("total_gifts_sent", 0),
                    total_whale_gifts=d.get("total_whale_gifts", 0),
                    mvp_count=d.get("mvp_count", 0),
                    highest_single_contribution=d.get("highest_single_contribution", 0),
                    highest_contribution_battle=d.get("highest_contribution_battle", ""),
                    recent_contributions=d.get("recent_contributions", []),
                )

            print(f"📥 Loaded agent leaderboard: {len(self.agents)} agents")
        except Exception as e:
            print(f"⚠️ Could not load agent leaderboard: {e}")


@dataclass
class TeamStats:
    """Statistics for a team across all tournaments."""
    team_name: str
    tournaments_played: int = 0
    tournaments_won: int = 0
    tournaments_lost: int = 0
    total_battles: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    total_points_scored: int = 0
    total_points_spent: int = 0
    rating: float = 1500.0  # ELO-style rating
    highest_rating: float = 1500.0
    lowest_rating: float = 1500.0
    win_streak: int = 0
    longest_win_streak: int = 0
    tournaments: List[TournamentRecord] = field(default_factory=list)

    def win_rate(self) -> float:
        """Calculate tournament win rate."""
        if self.tournaments_played == 0:
            return 0.0
        return (self.tournaments_won / self.tournaments_played) * 100

    def battle_win_rate(self) -> float:
        """Calculate individual battle win rate."""
        if self.total_battles == 0:
            return 0.0
        return (self.battles_won / self.total_battles) * 100

    def average_points_per_tournament(self) -> float:
        """Calculate average points scored per tournament."""
        if self.tournaments_played == 0:
            return 0.0
        return self.total_points_scored / self.tournaments_played


class TournamentLeaderboard:
    """
    Manages leaderboard across multiple tournaments.

    Features:
    - ELO rating system
    - Comprehensive statistics
    - Historical tracking
    - Rankings
    """

    def __init__(self, save_file: str = "tournament_leaderboard.json"):
        """
        Initialize leaderboard.

        Args:
            save_file: File path to save/load leaderboard data
        """
        self.save_file = save_file
        self.creator_stats = TeamStats(team_name="Creator")
        self.opponent_stats = TeamStats(team_name="Opponent")
        self.tournament_count = 0

        # Load existing data if available
        self._load_data()

    def record_tournament(self, tournament_data: Dict[str, Any]):
        """
        Record a completed tournament.

        Args:
            tournament_data: Tournament statistics from TournamentManager
        """
        self.tournament_count += 1
        tournament_id = f"T{self.tournament_count:04d}"

        # Extract data
        winner = tournament_data.get("tournament_winner")
        format_name = tournament_data.get("format")
        creator_wins = tournament_data.get("creator_wins", 0)
        opponent_wins = tournament_data.get("opponent_wins", 0)
        total_battles = tournament_data.get("total_battles", 0)
        budget_data = tournament_data.get("budget", {})

        # Calculate average scores
        battles = tournament_data.get("battles", [])
        total_creator_score = sum(b.get("creator_score", 0) for b in battles)
        total_opponent_score = sum(b.get("opponent_score", 0) for b in battles)
        avg_score = ((total_creator_score + total_opponent_score) / total_battles) if total_battles > 0 else 0

        # Find MVP
        mvp_agent = None
        mvp_contribution = 0
        for battle in battles:
            if battle.get("top_contributor") and battle.get("top_contribution", 0) > mvp_contribution:
                mvp_agent = battle["top_contributor"]
                mvp_contribution = battle["top_contribution"]

        # Create record
        record = TournamentRecord(
            tournament_id=tournament_id,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            format=format_name,
            winner=winner,
            final_score=f"{creator_wins}-{opponent_wins}" if winner == "creator" else f"{opponent_wins}-{creator_wins}",
            creator_wins=creator_wins,
            opponent_wins=opponent_wins,
            total_battles=total_battles,
            average_score_per_battle=avg_score,
            total_points_spent=budget_data.get("spent", 0),
            mvp_agent=mvp_agent,
            mvp_contribution=mvp_contribution
        )

        # Update stats
        self._update_stats(record, total_creator_score, total_opponent_score)

        # Update ELO ratings
        self._update_ratings(winner)

        # Save data
        self._save_data()

        print(f"\n✅ Tournament {tournament_id} recorded to leaderboard!")

    def _update_stats(self, record: TournamentRecord,
                     creator_total_score: int, opponent_total_score: int):
        """Update team statistics."""

        # Add record to history
        self.creator_stats.tournaments.append(record)
        self.opponent_stats.tournaments.append(record)

        # Update creator stats
        self.creator_stats.tournaments_played += 1
        self.creator_stats.total_battles += record.total_battles
        self.creator_stats.battles_won += record.creator_wins
        self.creator_stats.battles_lost += record.opponent_wins
        self.creator_stats.total_points_scored += creator_total_score
        self.creator_stats.total_points_spent += record.total_points_spent

        if record.winner == "creator":
            self.creator_stats.tournaments_won += 1
            self.creator_stats.win_streak += 1
            self.creator_stats.longest_win_streak = max(
                self.creator_stats.longest_win_streak,
                self.creator_stats.win_streak
            )
            self.opponent_stats.win_streak = 0
        else:
            self.creator_stats.tournaments_lost += 1
            self.creator_stats.win_streak = 0

        # Update opponent stats
        self.opponent_stats.tournaments_played += 1
        self.opponent_stats.total_battles += record.total_battles
        self.opponent_stats.battles_won += record.opponent_wins
        self.opponent_stats.battles_lost += record.creator_wins
        self.opponent_stats.total_points_scored += opponent_total_score
        self.opponent_stats.total_points_spent += record.total_points_spent

        if record.winner == "opponent":
            self.opponent_stats.tournaments_won += 1
            self.opponent_stats.win_streak += 1
            self.opponent_stats.longest_win_streak = max(
                self.opponent_stats.longest_win_streak,
                self.opponent_stats.win_streak
            )
        else:
            self.opponent_stats.tournaments_lost += 1

    def _update_ratings(self, winner: str):
        """
        Update ELO ratings based on match result.

        Args:
            winner: "creator" or "opponent"
        """
        K = 32  # K-factor for rating adjustments

        # Calculate expected scores
        creator_expected = 1 / (1 + 10 ** ((self.opponent_stats.rating - self.creator_stats.rating) / 400))
        opponent_expected = 1 - creator_expected

        # Actual scores
        creator_actual = 1.0 if winner == "creator" else 0.0
        opponent_actual = 1.0 if winner == "opponent" else 0.0

        # Update ratings
        self.creator_stats.rating += K * (creator_actual - creator_expected)
        self.opponent_stats.rating += K * (opponent_actual - opponent_expected)

        # Track highs and lows
        self.creator_stats.highest_rating = max(self.creator_stats.highest_rating, self.creator_stats.rating)
        self.creator_stats.lowest_rating = min(self.creator_stats.lowest_rating, self.creator_stats.rating)
        self.opponent_stats.highest_rating = max(self.opponent_stats.highest_rating, self.opponent_stats.rating)
        self.opponent_stats.lowest_rating = min(self.opponent_stats.lowest_rating, self.opponent_stats.rating)

    def print_leaderboard(self):
        """Print formatted leaderboard."""
        print("\n" + "=" * 80)
        print("🏆 TOURNAMENT LEADERBOARD")
        print("=" * 80)

        # Ratings
        print(f"\n📊 ELO RATINGS:")
        print(f"   Creator:  {self.creator_stats.rating:.0f}  "
              f"(High: {self.creator_stats.highest_rating:.0f}, Low: {self.creator_stats.lowest_rating:.0f})")
        print(f"   Opponent: {self.opponent_stats.rating:.0f}  "
              f"(High: {self.opponent_stats.highest_rating:.0f}, Low: {self.opponent_stats.lowest_rating:.0f})")

        # Tournament records
        print(f"\n🏆 TOURNAMENT RECORD:")
        self._print_team_record(self.creator_stats)
        self._print_team_record(self.opponent_stats)

        # Battle records
        print(f"\n⚔️ BATTLE RECORD:")
        print(f"   Creator:  {self.creator_stats.battles_won}W - {self.creator_stats.battles_lost}L "
              f"({self.creator_stats.battle_win_rate():.1f}%)")
        print(f"   Opponent: {self.opponent_stats.battles_won}W - {self.opponent_stats.battles_lost}L "
              f"({self.opponent_stats.battle_win_rate():.1f}%)")

        # Streaks
        print(f"\n🔥 WIN STREAKS:")
        if self.creator_stats.win_streak > 0:
            print(f"   Creator: {self.creator_stats.win_streak} current (Longest: {self.creator_stats.longest_win_streak})")
        elif self.opponent_stats.win_streak > 0:
            print(f"   Opponent: {self.opponent_stats.win_streak} current (Longest: {self.opponent_stats.longest_win_streak})")
        else:
            print(f"   Creator longest: {self.creator_stats.longest_win_streak}")
            print(f"   Opponent longest: {self.opponent_stats.longest_win_streak}")

        # Recent tournaments
        if self.creator_stats.tournaments:
            print(f"\n📋 RECENT TOURNAMENTS:")
            for record in reversed(self.creator_stats.tournaments[-5:]):
                winner_icon = "✅" if record.winner == "creator" else "❌"
                print(f"   {record.tournament_id} [{record.date}] {winner_icon} "
                      f"{record.format} - {record.final_score} "
                      f"(MVP: {record.mvp_agent or 'N/A'})")

        print("=" * 80 + "\n")

    def _print_team_record(self, stats: TeamStats):
        """Print team record line."""
        print(f"   {stats.team_name:8}: {stats.tournaments_won}W - {stats.tournaments_lost}L "
              f"({stats.win_rate():.1f}%) | "
              f"Avg Score: {stats.average_points_per_tournament():,.0f}")

    def get_standings(self) -> Dict[str, Any]:
        """
        Get current standings as dictionary.

        Returns:
            Dictionary with complete leaderboard data
        """
        return {
            "creator": {
                "rating": self.creator_stats.rating,
                "record": f"{self.creator_stats.tournaments_won}-{self.creator_stats.tournaments_lost}",
                "win_rate": self.creator_stats.win_rate(),
                "battle_record": f"{self.creator_stats.battles_won}-{self.creator_stats.battles_lost}",
                "battle_win_rate": self.creator_stats.battle_win_rate(),
                "win_streak": self.creator_stats.win_streak,
                "longest_streak": self.creator_stats.longest_win_streak
            },
            "opponent": {
                "rating": self.opponent_stats.rating,
                "record": f"{self.opponent_stats.tournaments_won}-{self.opponent_stats.tournaments_lost}",
                "win_rate": self.opponent_stats.win_rate(),
                "battle_record": f"{self.opponent_stats.battles_won}-{self.opponent_stats.battles_lost}",
                "battle_win_rate": self.opponent_stats.battle_win_rate(),
                "win_streak": self.opponent_stats.win_streak,
                "longest_streak": self.opponent_stats.longest_win_streak
            },
            "total_tournaments": self.tournament_count
        }

    def _save_data(self):
        """Save leaderboard data to file."""
        data = {
            "tournament_count": self.tournament_count,
            "creator": self._stats_to_dict(self.creator_stats),
            "opponent": self._stats_to_dict(self.opponent_stats)
        }

        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self):
        """Load leaderboard data from file."""
        if not os.path.exists(self.save_file):
            return

        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)

            self.tournament_count = data.get("tournament_count", 0)
            self.creator_stats = self._dict_to_stats(data.get("creator", {}), "Creator")
            self.opponent_stats = self._dict_to_stats(data.get("opponent", {}), "Opponent")

            print(f"📥 Loaded leaderboard data: {self.tournament_count} tournaments")
        except Exception as e:
            print(f"⚠️ Could not load leaderboard data: {e}")

    def _stats_to_dict(self, stats: TeamStats) -> Dict[str, Any]:
        """Convert TeamStats to dictionary."""
        return {
            "team_name": stats.team_name,
            "tournaments_played": stats.tournaments_played,
            "tournaments_won": stats.tournaments_won,
            "tournaments_lost": stats.tournaments_lost,
            "total_battles": stats.total_battles,
            "battles_won": stats.battles_won,
            "battles_lost": stats.battles_lost,
            "total_points_scored": stats.total_points_scored,
            "total_points_spent": stats.total_points_spent,
            "rating": stats.rating,
            "highest_rating": stats.highest_rating,
            "lowest_rating": stats.lowest_rating,
            "win_streak": stats.win_streak,
            "longest_win_streak": stats.longest_win_streak,
            "tournaments": [
                {
                    "tournament_id": t.tournament_id,
                    "date": t.date,
                    "format": t.format,
                    "winner": t.winner,
                    "final_score": t.final_score,
                    "creator_wins": t.creator_wins,
                    "opponent_wins": t.opponent_wins,
                    "total_battles": t.total_battles,
                    "average_score_per_battle": t.average_score_per_battle,
                    "total_points_spent": t.total_points_spent,
                    "mvp_agent": t.mvp_agent,
                    "mvp_contribution": t.mvp_contribution
                }
                for t in stats.tournaments
            ]
        }

    def _dict_to_stats(self, data: Dict[str, Any], team_name: str) -> TeamStats:
        """Convert dictionary to TeamStats."""
        tournaments = [
            TournamentRecord(**t) for t in data.get("tournaments", [])
        ]

        return TeamStats(
            team_name=team_name,
            tournaments_played=data.get("tournaments_played", 0),
            tournaments_won=data.get("tournaments_won", 0),
            tournaments_lost=data.get("tournaments_lost", 0),
            total_battles=data.get("total_battles", 0),
            battles_won=data.get("battles_won", 0),
            battles_lost=data.get("battles_lost", 0),
            total_points_scored=data.get("total_points_scored", 0),
            total_points_spent=data.get("total_points_spent", 0),
            rating=data.get("rating", 1500.0),
            highest_rating=data.get("highest_rating", 1500.0),
            lowest_rating=data.get("lowest_rating", 1500.0),
            win_streak=data.get("win_streak", 0),
            longest_win_streak=data.get("longest_win_streak", 0),
            tournaments=tournaments
        )


# =============================================================================
# SEASON MODE SYSTEM
# =============================================================================

@dataclass
class SeasonStanding:
    """Team standing within a season."""
    team_name: str
    emoji: str = ""
    season_points: int = 0
    tournaments_played: int = 0
    first_place: int = 0
    second_place: int = 0
    third_place: int = 0
    fourth_place: int = 0
    total_wins: int = 0
    total_losses: int = 0
    points_scored: int = 0
    points_allowed: int = 0
    clinched_playoffs: bool = False
    eliminated: bool = False
    playoff_seed: int = 0

    @property
    def point_differential(self) -> int:
        return self.points_scored - self.points_allowed

    @property
    def win_rate(self) -> float:
        total = self.total_wins + self.total_losses
        return (self.total_wins / total * 100) if total > 0 else 0.0


@dataclass
class SeasonConfig:
    """Configuration for a season."""
    total_tournaments: int = 10
    playoff_teams: int = 4
    points_first: int = 10
    points_second: int = 6
    points_third: int = 4
    points_fourth: int = 2
    season_name: str = "Season 1"


class SeasonManager:
    """
    Manages a full season of tournaments with playoffs.

    Features:
    - Track standings across multiple tournaments
    - Points-based ranking system (10/6/4/2)
    - Playoff clinch/elimination tracking
    - End-of-season championship bracket
    - Dynasty tracking (consecutive season wins)
    """

    # Dramatic banners
    SEASON_START_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏆🏆🏆  S E A S O N   {season_num}   B E G I N S !  🏆🏆🏆                  ║
║                                                                              ║
║   {num_teams} teams competing across {num_tournaments} tournaments!          ║
║   Top {playoff_teams} advance to PLAYOFFS!                                   ║
║                                                                              ║
║   Points: {pts_1}(1st) | {pts_2}(2nd) | {pts_3}(3rd) | {pts_4}(4th)          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    CLINCH_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎉🎉🎉  P L A Y O F F   B E R T H   C L I N C H E D !  🎉🎉🎉             ║
║                                                                              ║
║                    {emoji} {team}                                            ║
║                                                                              ║
║   Secured a spot in the postseason!                                          ║
║   Current Seed: #{seed}                                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    ELIMINATED_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   💔💔💔  E L I M I N A T E D   F R O M   P L A Y O F F S  💔💔💔           ║
║                                                                              ║
║                    {emoji} {team}                                            ║
║                                                                              ║
║   Can no longer qualify for postseason.                                      ║
║   Better luck next season!                                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    PLAYOFFS_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⭐⭐⭐  P L A Y O F F S   B E G I N !  ⭐⭐⭐                                ║
║                                                                              ║
║   The top {num_teams} teams battle for the championship!                     ║
║                                                                              ║
║   #1 {t1_emoji} {team1} vs #4 {t4_emoji} {team4}                             ║
║   #2 {t2_emoji} {team2} vs #3 {t3_emoji} {team3}                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    CHAMPION_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   👑👑👑  S E A S O N   {season_num}   C H A M P I O N !  👑👑👑             ║
║                                                                              ║
║                    {emoji} {champion}                                        ║
║                                                                              ║
║   Season Points: {points}  |  Record: {wins}W-{losses}L                      ║
║   Tournament Wins: {first_place}  |  Point Diff: +{diff:,}                   ║
║   {dynasty_msg}                                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, config: SeasonConfig = None,
                 teams: List[str] = None,
                 save_file: str = "data/season_data.json"):
        """
        Initialize season manager.

        Args:
            config: Season configuration
            teams: List of team names (with emojis like "🔴 Alpha")
            save_file: Path to save season data
        """
        self.config = config or SeasonConfig()
        self.save_file = save_file
        self.standings: Dict[str, SeasonStanding] = {}
        self.current_tournament = 0
        self.season_complete = False
        self.playoffs_complete = False
        self.champion: Optional[str] = None
        self.dynasty_count = 0  # Consecutive season wins
        self.season_history: List[Dict] = []

        # Initialize standings for teams
        if teams:
            for team in teams:
                # Parse emoji from team name (e.g., "🔴 Alpha" -> emoji="🔴", name="Alpha")
                parts = team.split(" ", 1)
                emoji = parts[0] if len(parts) > 1 else ""
                name = parts[1] if len(parts) > 1 else parts[0]
                self.standings[name] = SeasonStanding(team_name=name, emoji=emoji)

        self._load_data()

    def start_season(self, verbose: bool = True):
        """Start a new season."""
        self.current_tournament = 0
        self.season_complete = False
        self.playoffs_complete = False
        self.champion = None

        # Reset standings
        for standing in self.standings.values():
            standing.season_points = 0
            standing.tournaments_played = 0
            standing.first_place = 0
            standing.second_place = 0
            standing.third_place = 0
            standing.fourth_place = 0
            standing.total_wins = 0
            standing.total_losses = 0
            standing.points_scored = 0
            standing.points_allowed = 0
            standing.clinched_playoffs = False
            standing.eliminated = False
            standing.playoff_seed = 0

        if verbose:
            print(self.SEASON_START_BANNER.format(
                season_num=len(self.season_history) + 1,
                num_teams=len(self.standings),
                num_tournaments=self.config.total_tournaments,
                playoff_teams=self.config.playoff_teams,
                pts_1=self.config.points_first,
                pts_2=self.config.points_second,
                pts_3=self.config.points_third,
                pts_4=self.config.points_fourth
            ))

    def record_tournament_result(self, placements: List[str],
                                  tournament_stats: Dict[str, Dict] = None,
                                  verbose: bool = True):
        """
        Record results from a tournament.

        Args:
            placements: List of team names in order [1st, 2nd, 3rd, 4th, ...]
            tournament_stats: Optional dict with {team: {wins, losses, pts_for, pts_against}}
            verbose: Print dramatic announcements
        """
        if self.season_complete:
            print("Season is already complete!")
            return

        self.current_tournament += 1

        if verbose:
            print(f"\n   📅 Tournament {self.current_tournament}/{self.config.total_tournaments} Results:")
            print("   " + "-" * 50)

        # Award points based on placement
        point_awards = [
            self.config.points_first,
            self.config.points_second,
            self.config.points_third,
            self.config.points_fourth
        ]

        for i, team_name in enumerate(placements):
            if team_name not in self.standings:
                continue

            standing = self.standings[team_name]
            standing.tournaments_played += 1

            # Award placement points
            if i < len(point_awards):
                points = point_awards[i]
                standing.season_points += points

                if i == 0:
                    standing.first_place += 1
                    if verbose:
                        print(f"   🥇 1st: {standing.emoji} {team_name} (+{points} pts)")
                elif i == 1:
                    standing.second_place += 1
                    if verbose:
                        print(f"   🥈 2nd: {standing.emoji} {team_name} (+{points} pts)")
                elif i == 2:
                    standing.third_place += 1
                    if verbose:
                        print(f"   🥉 3rd: {standing.emoji} {team_name} (+{points} pts)")
                elif i == 3:
                    standing.fourth_place += 1
                    if verbose:
                        print(f"   4th: {standing.emoji} {team_name} (+{points} pts)")

            # Update tournament stats if provided
            if tournament_stats and team_name in tournament_stats:
                stats = tournament_stats[team_name]
                standing.total_wins += stats.get('wins', 0)
                standing.total_losses += stats.get('losses', 0)
                standing.points_scored += stats.get('pts_for', 0)
                standing.points_allowed += stats.get('pts_against', 0)

        # Check for clinch/elimination
        self._update_playoff_status(verbose)

        # Check if regular season is complete
        if self.current_tournament >= self.config.total_tournaments:
            self.season_complete = True
            if verbose:
                print("\n   🏁 REGULAR SEASON COMPLETE!")
                self.print_standings()

        self._save_data()

    def _update_playoff_status(self, verbose: bool = True):
        """Check for playoff clinch/elimination."""
        sorted_standings = self.get_sorted_standings()
        tournaments_remaining = self.config.total_tournaments - self.current_tournament
        max_possible_points = tournaments_remaining * self.config.points_first

        for i, standing in enumerate(sorted_standings):
            if standing.clinched_playoffs or standing.eliminated:
                continue

            current_rank = i + 1

            # Check clinch: if even all teams below getting max points can't catch up
            if current_rank <= self.config.playoff_teams:
                # Team at rank N is clinched if team at rank (playoff_teams + 1) can't catch them
                if len(sorted_standings) > self.config.playoff_teams:
                    bubble_team = sorted_standings[self.config.playoff_teams]
                    if standing.season_points > bubble_team.season_points + max_possible_points:
                        standing.clinched_playoffs = True
                        standing.playoff_seed = current_rank
                        if verbose:
                            print(self.CLINCH_BANNER.format(
                                emoji=standing.emoji,
                                team=standing.team_name.upper(),
                                seed=current_rank
                            ))

            # Check elimination: if max points can't reach playoff cutoff
            if current_rank > self.config.playoff_teams:
                playoff_cutoff_team = sorted_standings[self.config.playoff_teams - 1]
                if standing.season_points + max_possible_points < playoff_cutoff_team.season_points:
                    standing.eliminated = True
                    if verbose:
                        print(self.ELIMINATED_BANNER.format(
                            emoji=standing.emoji,
                            team=standing.team_name.upper()
                        ))

    def get_sorted_standings(self) -> List[SeasonStanding]:
        """Get standings sorted by points, then differential, then wins."""
        standings = list(self.standings.values())
        standings.sort(key=lambda s: (
            s.season_points,
            s.point_differential,
            s.total_wins
        ), reverse=True)
        return standings

    def get_playoff_teams(self) -> List[SeasonStanding]:
        """Get teams that qualified for playoffs."""
        sorted_standings = self.get_sorted_standings()
        return sorted_standings[:self.config.playoff_teams]

    def run_playoffs(self, verbose: bool = True) -> Optional[str]:
        """
        Run the playoff bracket.

        Returns:
            Name of the champion
        """
        if not self.season_complete:
            print("Regular season not complete!")
            return None

        playoff_teams = self.get_playoff_teams()

        if len(playoff_teams) < self.config.playoff_teams:
            print(f"Not enough teams for playoffs! Need {self.config.playoff_teams}")
            return None

        # Assign playoff seeds
        for i, team in enumerate(playoff_teams):
            team.playoff_seed = i + 1

        if verbose and len(playoff_teams) >= 4:
            print(self.PLAYOFFS_BANNER.format(
                num_teams=len(playoff_teams),
                t1_emoji=playoff_teams[0].emoji,
                team1=playoff_teams[0].team_name,
                t2_emoji=playoff_teams[1].emoji,
                team2=playoff_teams[1].team_name,
                t3_emoji=playoff_teams[2].emoji,
                team3=playoff_teams[2].team_name,
                t4_emoji=playoff_teams[3].emoji,
                team4=playoff_teams[3].team_name
            ))

        # Simple playoff simulation (1 vs 4, 2 vs 3, winners to finals)
        import random

        # Semifinals
        if verbose:
            print("\n   ═══════════ SEMIFINALS ═══════════")

        # Match 1: #1 vs #4
        t1, t4 = playoff_teams[0], playoff_teams[3]
        winner1 = self._simulate_playoff_match(t1, t4, verbose)

        # Match 2: #2 vs #3
        t2, t3 = playoff_teams[1], playoff_teams[2]
        winner2 = self._simulate_playoff_match(t2, t3, verbose)

        # Finals
        if verbose:
            print("\n   ═══════════ CHAMPIONSHIP FINALS ═══════════")

        champion_standing = self._simulate_playoff_match(winner1, winner2, verbose)
        self.champion = champion_standing.team_name
        self.playoffs_complete = True

        # Update dynasty
        if self.season_history:
            last_champ = self.season_history[-1].get('champion')
            if last_champ == self.champion:
                self.dynasty_count += 1
            else:
                self.dynasty_count = 1
        else:
            self.dynasty_count = 1

        dynasty_msg = ""
        if self.dynasty_count >= 3:
            dynasty_msg = f"🏆 DYNASTY! {self.dynasty_count} consecutive championships!"
        elif self.dynasty_count == 2:
            dynasty_msg = "🔥 Back-to-back champion!"

        if verbose:
            print(self.CHAMPION_BANNER.format(
                season_num=len(self.season_history) + 1,
                emoji=champion_standing.emoji,
                champion=self.champion.upper(),
                points=champion_standing.season_points,
                wins=champion_standing.total_wins,
                losses=champion_standing.total_losses,
                first_place=champion_standing.first_place,
                diff=champion_standing.point_differential,
                dynasty_msg=dynasty_msg
            ))

        # Record season history
        self.season_history.append({
            'season_num': len(self.season_history) + 1,
            'champion': self.champion,
            'champion_emoji': champion_standing.emoji,
            'champion_points': champion_standing.season_points,
            'standings': [
                {
                    'team': s.team_name,
                    'emoji': s.emoji,
                    'points': s.season_points,
                    'first': s.first_place
                }
                for s in self.get_sorted_standings()
            ]
        })

        self._save_data()
        return self.champion

    def _simulate_playoff_match(self, team1: SeasonStanding, team2: SeasonStanding,
                                 verbose: bool = True) -> SeasonStanding:
        """Simulate a playoff match between two teams."""
        import random

        # Higher seed has advantage based on season performance
        t1_strength = team1.season_points + team1.point_differential / 1000
        t2_strength = team2.season_points + team2.point_differential / 1000

        # Add randomness
        t1_score = max(1000, int(5000 + t1_strength * 100 + random.randint(-3000, 5000)))
        t2_score = max(1000, int(5000 + t2_strength * 100 + random.randint(-3000, 5000)))

        # No ties
        if t1_score == t2_score:
            t1_score += 100

        winner = team1 if t1_score > t2_score else team2
        loser = team2 if winner == team1 else team1

        if verbose:
            w_color = "" if winner == team1 else ""
            print(f"\n   #{team1.playoff_seed} {team1.emoji} {team1.team_name:<15} {t1_score:>6,}")
            print(f"       vs")
            print(f"   #{team2.playoff_seed} {team2.emoji} {team2.team_name:<15} {t2_score:>6,}")
            print(f"\n   ► Winner: {winner.emoji} {winner.team_name}")

        return winner

    def print_standings(self):
        """Print formatted season standings."""
        standings = self.get_sorted_standings()
        tournaments_remaining = self.config.total_tournaments - self.current_tournament

        print("\n" + "=" * 85)
        print(f"   🏆 {self.config.season_name.upper()} STANDINGS")
        print(f"   Tournament {self.current_tournament}/{self.config.total_tournaments}" +
              (f" ({tournaments_remaining} remaining)" if tournaments_remaining > 0 else " - COMPLETE"))
        print("=" * 85)

        # Header
        print(f"\n   {'Rank':<6}{'Team':<20}{'Pts':<6}{'1st':<5}{'2nd':<5}{'3rd':<5}"
              f"{'W-L':<10}{'Diff':<10}{'Status':<15}")
        print("   " + "-" * 80)

        for i, s in enumerate(standings, 1):
            # Rank indicator
            if i <= self.config.playoff_teams:
                rank = f"#{i}*" if s.clinched_playoffs else f"#{i}"
            else:
                rank = f"#{i}"

            # Status
            if s.clinched_playoffs:
                status = "✅ CLINCHED"
            elif s.eliminated:
                status = "❌ ELIMINATED"
            elif i <= self.config.playoff_teams:
                status = "🎯 Playoff spot"
            else:
                status = "⚠️ On bubble"

            # Point differential
            diff = s.point_differential
            diff_str = f"+{diff:,}" if diff > 0 else f"{diff:,}"

            print(f"   {rank:<6}{s.emoji} {s.team_name:<17}{s.season_points:<6}"
                  f"{s.first_place:<5}{s.second_place:<5}{s.third_place:<5}"
                  f"{s.total_wins}-{s.total_losses:<7}{diff_str:<10}{status:<15}")

        print("   " + "-" * 80)
        print(f"\n   * = Clinched playoff berth | Top {self.config.playoff_teams} advance to playoffs")
        print("=" * 85 + "\n")

    def print_season_history(self):
        """Print history of past seasons."""
        if not self.season_history:
            print("\n   No season history yet!")
            return

        print("\n" + "=" * 60)
        print("   📜 SEASON HISTORY")
        print("=" * 60)

        for season in self.season_history:
            dynasty = ""
            if season.get('dynasty_count', 0) >= 2:
                dynasty = f" (Dynasty x{season['dynasty_count']})"

            print(f"\n   Season {season['season_num']}: {season['champion_emoji']} {season['champion']}{dynasty}")
            print(f"      Points: {season['champion_points']}")

        print("\n" + "=" * 60)

    def _save_data(self):
        """Save season data to file."""
        import os
        os.makedirs(os.path.dirname(self.save_file), exist_ok=True)

        data = {
            'config': {
                'total_tournaments': self.config.total_tournaments,
                'playoff_teams': self.config.playoff_teams,
                'points_first': self.config.points_first,
                'points_second': self.config.points_second,
                'points_third': self.config.points_third,
                'points_fourth': self.config.points_fourth,
                'season_name': self.config.season_name
            },
            'current_tournament': self.current_tournament,
            'season_complete': self.season_complete,
            'playoffs_complete': self.playoffs_complete,
            'champion': self.champion,
            'dynasty_count': self.dynasty_count,
            'standings': {
                name: {
                    'team_name': s.team_name,
                    'emoji': s.emoji,
                    'season_points': s.season_points,
                    'tournaments_played': s.tournaments_played,
                    'first_place': s.first_place,
                    'second_place': s.second_place,
                    'third_place': s.third_place,
                    'fourth_place': s.fourth_place,
                    'total_wins': s.total_wins,
                    'total_losses': s.total_losses,
                    'points_scored': s.points_scored,
                    'points_allowed': s.points_allowed,
                    'clinched_playoffs': s.clinched_playoffs,
                    'eliminated': s.eliminated,
                    'playoff_seed': s.playoff_seed
                }
                for name, s in self.standings.items()
            },
            'season_history': self.season_history
        }

        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self):
        """Load season data from file."""
        if not os.path.exists(self.save_file):
            return

        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)

            self.current_tournament = data.get('current_tournament', 0)
            self.season_complete = data.get('season_complete', False)
            self.playoffs_complete = data.get('playoffs_complete', False)
            self.champion = data.get('champion')
            self.dynasty_count = data.get('dynasty_count', 0)
            self.season_history = data.get('season_history', [])

            # Load standings
            for name, s_data in data.get('standings', {}).items():
                self.standings[name] = SeasonStanding(
                    team_name=s_data.get('team_name', name),
                    emoji=s_data.get('emoji', ''),
                    season_points=s_data.get('season_points', 0),
                    tournaments_played=s_data.get('tournaments_played', 0),
                    first_place=s_data.get('first_place', 0),
                    second_place=s_data.get('second_place', 0),
                    third_place=s_data.get('third_place', 0),
                    fourth_place=s_data.get('fourth_place', 0),
                    total_wins=s_data.get('total_wins', 0),
                    total_losses=s_data.get('total_losses', 0),
                    points_scored=s_data.get('points_scored', 0),
                    points_allowed=s_data.get('points_allowed', 0),
                    clinched_playoffs=s_data.get('clinched_playoffs', False),
                    eliminated=s_data.get('eliminated', False),
                    playoff_seed=s_data.get('playoff_seed', 0)
                )

            print(f"📥 Loaded season data: Tournament {self.current_tournament}/{self.config.total_tournaments}")
        except Exception as e:
            print(f"⚠️ Could not load season data: {e}")
