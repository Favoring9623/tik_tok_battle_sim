"""
Post-Battle Reward Distribution System

Implements TikTok-style reward distribution after battles:
- Top contributor rewards
- Participation rewards
- Bonus multipliers for special achievements
- Gift box system (diamond rewards)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class RewardTier(Enum):
    """Reward tiers based on contribution."""
    LEGEND = "legend"      # Top 1% - 1000+ diamonds
    MVP = "mvp"           # Top 5% - 500-1000 diamonds
    STAR = "star"         # Top 10% - 200-500 diamonds
    HERO = "hero"         # Top 25% - 100-200 diamonds
    SUPPORTER = "supporter"  # Top 50% - 50-100 diamonds
    PARTICIPANT = "participant"  # Everyone else - 10-50 diamonds


class AchievementType(Enum):
    """Special achievements for bonus rewards."""
    CLUTCH_WINNER = "clutch_winner"      # Won from behind in last 30s
    PERFECT_VICTORY = "perfect_victory"  # Won without opponent lead
    COMEBACK_KING = "comeback_king"      # Overcame 2x deficit
    SNIPER_ELITE = "sniper_elite"        # Contributed 50%+ in final phase
    PHASE_MASTER = "phase_master"        # Triggered Boost #2
    GLOVE_LEGEND = "glove_legend"        # Activated 3+ x5 gloves
    WHALE_SUPPORTER = "whale_supporter"  # Single gift worth 100k+ points
    CONSISTENCY_KING = "consistency_king"  # 20+ gifts sent
    STRATEGIC_GENIUS = "strategic_genius"  # Used 3+ power-ups successfully


@dataclass
class Reward:
    """Represents a reward package."""
    diamonds: int
    tier: RewardTier
    achievements: List[AchievementType] = field(default_factory=list)
    bonus_multiplier: float = 1.0

    @property
    def total_diamonds(self) -> int:
        """Calculate total diamonds with bonuses."""
        return int(self.diamonds * self.bonus_multiplier)

    def add_achievement(self, achievement: AchievementType, bonus: int = 100):
        """Add an achievement and bonus diamonds."""
        self.achievements.append(achievement)
        self.diamonds += bonus


@dataclass
class ContributorStats:
    """Stats for a contributor."""
    name: str
    total_donated: int
    gifts_sent: int
    avg_gift_value: float
    best_gift_value: int
    final_phase_contribution: int
    early_phase_contribution: int
    mid_phase_contribution: int
    late_phase_contribution: int


class RewardDistributor:
    """
    Distributes rewards after battle completion.

    Features:
    - Tiered rewards based on contribution
    - Achievement bonuses
    - Special rewards for winners
    - Fair distribution algorithm
    """

    def __init__(self):
        self.base_reward_map = {
            RewardTier.LEGEND: 1000,
            RewardTier.MVP: 500,
            RewardTier.STAR: 200,
            RewardTier.HERO: 100,
            RewardTier.SUPPORTER: 50,
            RewardTier.PARTICIPANT: 10
        }

        self.achievement_bonuses = {
            AchievementType.CLUTCH_WINNER: 200,
            AchievementType.PERFECT_VICTORY: 150,
            AchievementType.COMEBACK_KING: 300,
            AchievementType.SNIPER_ELITE: 250,
            AchievementType.PHASE_MASTER: 100,
            AchievementType.GLOVE_LEGEND: 200,
            AchievementType.WHALE_SUPPORTER: 400,
            AchievementType.CONSISTENCY_KING: 150,
            AchievementType.STRATEGIC_GENIUS: 300
        }

    def distribute_rewards(
        self,
        contributors: List[ContributorStats],
        winner: str,
        battle_history: Dict
    ) -> Dict[str, Reward]:
        """
        Distribute rewards to all contributors.

        Args:
            contributors: List of contributor stats
            winner: "creator" or "opponent"
            battle_history: Dict with battle timeline data

        Returns:
            Dict mapping contributor name to Reward
        """
        rewards = {}

        # Sort contributors by total donated
        sorted_contributors = sorted(
            contributors,
            key=lambda c: c.total_donated,
            reverse=True
        )

        total_contributors = len(sorted_contributors)

        for rank, contributor in enumerate(sorted_contributors, 1):
            # Determine tier based on rank percentile
            percentile = rank / total_contributors

            if percentile <= 0.01:
                tier = RewardTier.LEGEND
            elif percentile <= 0.05:
                tier = RewardTier.MVP
            elif percentile <= 0.10:
                tier = RewardTier.STAR
            elif percentile <= 0.25:
                tier = RewardTier.HERO
            elif percentile <= 0.50:
                tier = RewardTier.SUPPORTER
            else:
                tier = RewardTier.PARTICIPANT

            # Base reward
            base_diamonds = self.base_reward_map[tier]

            # Winner bonus (2x for winning team)
            bonus_multiplier = 2.0 if winner == "creator" else 1.0

            reward = Reward(
                diamonds=base_diamonds,
                tier=tier,
                bonus_multiplier=bonus_multiplier
            )

            # Check for achievements
            achievements = self._check_achievements(
                contributor,
                battle_history,
                winner,
                rank
            )

            for achievement in achievements:
                reward.add_achievement(
                    achievement,
                    self.achievement_bonuses[achievement]
                )

            rewards[contributor.name] = reward

        return rewards

    def _check_achievements(
        self,
        contributor: ContributorStats,
        battle_history: Dict,
        winner: str,
        rank: int
    ) -> List[AchievementType]:
        """Check which achievements the contributor earned."""
        achievements = []

        # Sniper Elite: 50%+ contribution in final phase
        if contributor.final_phase_contribution > 0:
            final_percent = (
                contributor.final_phase_contribution /
                max(contributor.total_donated, 1)
            )
            if final_percent >= 0.5:
                achievements.append(AchievementType.SNIPER_ELITE)

        # Whale Supporter: Single gift worth 100k+ points
        if contributor.best_gift_value >= 100000:
            achievements.append(AchievementType.WHALE_SUPPORTER)

        # Consistency King: 20+ gifts sent
        if contributor.gifts_sent >= 20:
            achievements.append(AchievementType.CONSISTENCY_KING)

        # Clutch Winner: Won from behind in last 30s
        if winner == "creator" and rank == 1:
            if battle_history.get('comeback_victory', False):
                achievements.append(AchievementType.CLUTCH_WINNER)

        # Perfect Victory: Won without opponent lead
        if winner == "creator" and rank == 1:
            if battle_history.get('perfect_victory', False):
                achievements.append(AchievementType.PERFECT_VICTORY)

        # Comeback King: Overcame 2x deficit
        if winner == "creator" and rank == 1:
            if battle_history.get('max_deficit_ratio', 0) >= 2.0:
                achievements.append(AchievementType.COMEBACK_KING)

        # Phase Master: Triggered Boost #2
        if battle_history.get('boost2_triggered', False):
            # Award to top contributor
            if rank == 1:
                achievements.append(AchievementType.PHASE_MASTER)

        # Glove Legend: Activated 3+ x5 gloves
        gloves_activated = battle_history.get('gloves_activated_by_team', 0)
        if gloves_activated >= 3 and rank == 1:
            achievements.append(AchievementType.GLOVE_LEGEND)

        # Strategic Genius: Used 3+ power-ups
        power_ups_used = battle_history.get('power_ups_used', 0)
        if power_ups_used >= 3 and rank == 1:
            achievements.append(AchievementType.STRATEGIC_GENIUS)

        return achievements

    def print_rewards(self, rewards: Dict[str, Reward]):
        """Print rewards in a nice format."""
        print("\n" + "="*70)
        print("💎 BATTLE REWARDS DISTRIBUTION")
        print("="*70)

        # Sort by total diamonds
        sorted_rewards = sorted(
            rewards.items(),
            key=lambda x: x[1].total_diamonds,
            reverse=True
        )

        for rank, (name, reward) in enumerate(sorted_rewards, 1):
            print(f"\n#{rank} {name}:")
            print(f"   Tier: {reward.tier.value.upper()}")
            print(f"   Base Diamonds: {reward.diamonds}")
            print(f"   Bonus Multiplier: x{reward.bonus_multiplier}")
            print(f"   Total Diamonds: 💎 {reward.total_diamonds}")

            if reward.achievements:
                print(f"   Achievements:")
                for achievement in reward.achievements:
                    bonus = self.achievement_bonuses.get(achievement, 0)
                    print(f"      🏆 {achievement.value.replace('_', ' ').title()} (+{bonus} diamonds)")

        print("\n" + "="*70)
        total_diamonds = sum(r.total_diamonds for r in rewards.values())
        print(f"💰 Total Diamonds Distributed: {total_diamonds:,}")
        print("="*70 + "\n")


def create_contributor_stats_from_analytics(
    agent_performance: Dict,
    battle_duration: int
) -> List[ContributorStats]:
    """
    Convert battle analytics to contributor stats.

    Args:
        agent_performance: Dict from battle_analytics.get_agent_performance()
        battle_duration: Total battle duration in seconds

    Returns:
        List of ContributorStats objects
    """
    contributors = []

    for name, perf in agent_performance.items():
        # Calculate phase contributions (rough estimation based on timing)
        timing = perf.get('gift_timing', {})

        stats = ContributorStats(
            name=name,
            total_donated=perf['total_donated'],
            gifts_sent=perf['gifts_sent'],
            avg_gift_value=perf['avg_gift_value'],
            best_gift_value=perf.get('best_gift', {}).get('points', 0),
            final_phase_contribution=timing.get('final', 0) * perf['avg_gift_value'],
            early_phase_contribution=timing.get('early', 0) * perf['avg_gift_value'],
            mid_phase_contribution=timing.get('mid', 0) * perf['avg_gift_value'],
            late_phase_contribution=timing.get('late', 0) * perf['avg_gift_value']
        )

        contributors.append(stats)

    return contributors


if __name__ == '__main__':
    # Demo
    print("Reward System Demo")
    print("="*70)

    # Create sample contributors
    contributors = [
        ContributorStats(
            name="Kinetik",
            total_donated=259990,
            gifts_sent=1,
            avg_gift_value=259990,
            best_gift_value=259990,
            final_phase_contribution=259990,
            early_phase_contribution=0,
            mid_phase_contribution=0,
            late_phase_contribution=0
        ),
        ContributorStats(
            name="NovaWhale",
            total_donated=1800,
            gifts_sent=1,
            avg_gift_value=1800,
            best_gift_value=1800,
            final_phase_contribution=0,
            early_phase_contribution=1800,
            mid_phase_contribution=0,
            late_phase_contribution=0
        ),
        ContributorStats(
            name="StrikeMaster",
            total_donated=400,
            gifts_sent=4,
            avg_gift_value=100,
            best_gift_value=100,
            final_phase_contribution=0,
            early_phase_contribution=0,
            mid_phase_contribution=200,
            late_phase_contribution=200
        ),
        ContributorStats(
            name="PhaseTracker",
            total_donated=50,
            gifts_sent=5,
            avg_gift_value=10,
            best_gift_value=10,
            final_phase_contribution=0,
            early_phase_contribution=0,
            mid_phase_contribution=50,
            late_phase_contribution=0
        )
    ]

    # Battle history
    battle_history = {
        'comeback_victory': True,
        'perfect_victory': False,
        'max_deficit_ratio': 3.5,
        'boost2_triggered': True,
        'gloves_activated_by_team': 0,
        'power_ups_used': 1
    }

    # Distribute rewards
    distributor = RewardDistributor()
    rewards = distributor.distribute_rewards(
        contributors,
        winner="creator",
        battle_history=battle_history
    )

    # Print results
    distributor.print_rewards(rewards)
