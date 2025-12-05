"""
Achievement System - Track and reward player accomplishments!

Features:
- Battle Achievements (per-battle accomplishments)
- Agent Achievements (cumulative progress)
- Tournament Achievements (series-wide accomplishments)
- Dramatic unlock announcements
- Diamond rewards
- Rarity tiers
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import os


class AchievementRarity(Enum):
    """Rarity tiers for achievements."""
    COMMON = ("Common", "⬜", 50)
    UNCOMMON = ("Uncommon", "🟢", 100)
    RARE = ("Rare", "🔵", 250)
    EPIC = ("Epic", "🟣", 500)
    LEGENDARY = ("Legendary", "🟡", 1000)

    def __init__(self, display_name: str, color_emoji: str, base_diamonds: int):
        self.display_name = display_name
        self.color_emoji = color_emoji
        self.base_diamonds = base_diamonds


class AchievementCategory(Enum):
    """Categories of achievements."""
    BATTLE = "⚔️ Battle"
    AGENT = "🤖 Agent"
    TOURNAMENT = "🏆 Tournament"
    SECRET = "🔒 Secret"


@dataclass
class Achievement:
    """Definition of an achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str = "🏅"
    diamonds: int = 0  # Will be set from rarity if 0
    threshold: int = 1  # For progressive achievements
    secret: bool = False  # Hidden until unlocked

    def __post_init__(self):
        if self.diamonds == 0:
            self.diamonds = self.rarity.base_diamonds


@dataclass
class AchievementProgress:
    """Track progress toward an achievement."""
    achievement_id: str
    current_value: int = 0
    is_unlocked: bool = False
    unlocked_at: Optional[str] = None
    unlocked_in_battle: Optional[str] = None


# =============================================================================
# ACHIEVEMENT DEFINITIONS
# =============================================================================

# Battle Achievements (single battle accomplishments)
BATTLE_ACHIEVEMENTS = [
    Achievement(
        id="first_blood",
        name="First Blood",
        description="Send the first gift of a battle",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.COMMON,
        icon="🩸"
    ),
    Achievement(
        id="perfect_victory",
        name="Perfect Victory",
        description="Win a battle never falling behind",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.RARE,
        icon="👑"
    ),
    Achievement(
        id="domination",
        name="Domination",
        description="Win by 2x or more points",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.UNCOMMON,
        icon="💪"
    ),
    Achievement(
        id="photo_finish",
        name="Photo Finish",
        description="Win by less than 100 points",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.RARE,
        icon="📷"
    ),
    Achievement(
        id="comeback_king",
        name="Comeback King",
        description="Win after being down by 2x deficit",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.EPIC,
        icon="👑"
    ),
    Achievement(
        id="clutch_master",
        name="Clutch Master",
        description="Score 5000+ points in final 10 seconds",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.RARE,
        icon="⏱️"
    ),
    Achievement(
        id="x5_sniper",
        name="x5 Sniper",
        description="Trigger x5 multiplier 3+ times in one battle",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.UNCOMMON,
        icon="🎯"
    ),
    Achievement(
        id="whale_drop",
        name="Whale Drop",
        description="Send a 50k+ point gift",
        category=AchievementCategory.BATTLE,
        rarity=AchievementRarity.RARE,
        icon="🐋"
    ),
]

# Agent Achievements (cumulative progress)
AGENT_ACHIEVEMENTS = [
    Achievement(
        id="mvp_elite",
        name="MVP Elite",
        description="Earn MVP 10 times",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.RARE,
        icon="⭐",
        threshold=10
    ),
    Achievement(
        id="millionaire_donor",
        name="Millionaire Donor",
        description="Donate 1,000,000 total points",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.EPIC,
        icon="💰",
        threshold=1000000
    ),
    Achievement(
        id="battle_veteran",
        name="Battle Veteran",
        description="Participate in 100 battles",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.RARE,
        icon="🎖️",
        threshold=100
    ),
    Achievement(
        id="whale_master",
        name="Whale Master",
        description="Send 50 whale gifts (10k+)",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.EPIC,
        icon="🐳",
        threshold=50
    ),
    Achievement(
        id="rose_garden",
        name="Rose Garden",
        description="Send 1000 roses",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.UNCOMMON,
        icon="🌹",
        threshold=1000
    ),
    Achievement(
        id="winning_streak",
        name="Winning Streak",
        description="Win 10 battles in a row",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.EPIC,
        icon="🔥",
        threshold=10
    ),
    Achievement(
        id="quick_learner",
        name="Quick Learner",
        description="Improve win rate by 20% after 50 battles",
        category=AchievementCategory.AGENT,
        rarity=AchievementRarity.RARE,
        icon="🧠"
    ),
]

# Tournament Achievements
TOURNAMENT_ACHIEVEMENTS = [
    Achievement(
        id="undefeated_champion",
        name="Undefeated Champion",
        description="Win tournament without losing a battle",
        category=AchievementCategory.TOURNAMENT,
        rarity=AchievementRarity.LEGENDARY,
        icon="👑",
        diamonds=2000
    ),
    Achievement(
        id="bracket_buster",
        name="Bracket Buster",
        description="Beat a higher-seeded team",
        category=AchievementCategory.TOURNAMENT,
        rarity=AchievementRarity.UNCOMMON,
        icon="🔥"
    ),
    Achievement(
        id="dynasty",
        name="Dynasty",
        description="Win 3 tournaments in a row",
        category=AchievementCategory.TOURNAMENT,
        rarity=AchievementRarity.LEGENDARY,
        icon="🏛️",
        threshold=3,
        diamonds=3000
    ),
    Achievement(
        id="comeback_series",
        name="Comeback Series",
        description="Win from 0-2 in Best of 5",
        category=AchievementCategory.TOURNAMENT,
        rarity=AchievementRarity.EPIC,
        icon="🔄",
        diamonds=1000
    ),
    Achievement(
        id="sweep",
        name="Clean Sweep",
        description="Win tournament 3-0 or 4-0",
        category=AchievementCategory.TOURNAMENT,
        rarity=AchievementRarity.RARE,
        icon="🧹"
    ),
    Achievement(
        id="grand_slam",
        name="Grand Slam",
        description="Win all tournament formats (BO3, BO5, BO7)",
        category=AchievementCategory.TOURNAMENT,
        rarity=AchievementRarity.LEGENDARY,
        icon="🎾",
        diamonds=2500
    ),
]

# Secret Achievements
SECRET_ACHIEVEMENTS = [
    Achievement(
        id="lucky_777",
        name="Lucky 777",
        description="Win a battle with exactly 77,777 points",
        category=AchievementCategory.SECRET,
        rarity=AchievementRarity.LEGENDARY,
        icon="🎰",
        secret=True
    ),
    Achievement(
        id="underdog_miracle",
        name="Underdog Miracle",
        description="Win with 1/4 of opponent's budget",
        category=AchievementCategory.SECRET,
        rarity=AchievementRarity.LEGENDARY,
        icon="🐕",
        secret=True
    ),
]

# Combine all achievements
ALL_ACHIEVEMENTS = (
    BATTLE_ACHIEVEMENTS +
    AGENT_ACHIEVEMENTS +
    TOURNAMENT_ACHIEVEMENTS +
    SECRET_ACHIEVEMENTS
)


# =============================================================================
# DRAMATIC BANNERS
# =============================================================================

ACHIEVEMENT_UNLOCKED_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏆🏆🏆  A C H I E V E M E N T   U N L O C K E D !  🏆🏆🏆                  ║
║                                                                              ║
║   {icon} {name}                                                              ║
║   {description}                                                              ║
║                                                                              ║
║   {rarity_emoji} {rarity} | 💎 +{diamonds} Diamonds                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

SECRET_UNLOCKED_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔓🔓🔓  S E C R E T   A C H I E V E M E N T !  🔓🔓🔓                      ║
║                                                                              ║
║   {icon} {name}                                                              ║
║   {description}                                                              ║
║                                                                              ║
║   🟡 LEGENDARY | 💎 +{diamonds} Diamonds                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

MILESTONE_BANNER = """
┌──────────────────────────────────────────────────────────────────────────────┐
│   📊 MILESTONE: {name} - {progress}/{threshold} ({percent}%)                 │
└──────────────────────────────────────────────────────────────────────────────┘
"""


# =============================================================================
# ACHIEVEMENT MANAGER
# =============================================================================

class AchievementManager:
    """
    Manages achievement tracking, progress, and unlocks.

    Features:
    - Track progress toward achievements
    - Check conditions and unlock achievements
    - Emit dramatic announcements
    - Persist to JSON/Database
    """

    def __init__(self, save_file: str = "data/achievements.json"):
        """Initialize achievement manager."""
        self.save_file = save_file
        self.achievements: Dict[str, Achievement] = {a.id: a for a in ALL_ACHIEVEMENTS}
        self.progress: Dict[str, Dict[str, AchievementProgress]] = {}  # agent -> achievement_id -> progress
        self.total_diamonds: Dict[str, int] = {}  # agent -> total diamonds

        self._load_data()

    def get_or_create_progress(self, agent_name: str, achievement_id: str) -> AchievementProgress:
        """Get or create progress tracker for an agent's achievement."""
        if agent_name not in self.progress:
            self.progress[agent_name] = {}

        if achievement_id not in self.progress[agent_name]:
            self.progress[agent_name][achievement_id] = AchievementProgress(
                achievement_id=achievement_id
            )

        return self.progress[agent_name][achievement_id]

    def update_progress(self, agent_name: str, achievement_id: str,
                        value: int = 1, battle_id: str = None,
                        verbose: bool = True) -> bool:
        """
        Update progress toward an achievement.

        Args:
            agent_name: Name of agent
            achievement_id: Achievement ID
            value: Value to add (or set for non-cumulative)
            battle_id: Current battle ID
            verbose: Print announcements

        Returns:
            True if achievement was just unlocked
        """
        if achievement_id not in self.achievements:
            return False

        achievement = self.achievements[achievement_id]
        progress = self.get_or_create_progress(agent_name, achievement_id)

        if progress.is_unlocked:
            return False  # Already unlocked

        # Update progress
        progress.current_value += value

        # Check for milestone (25%, 50%, 75%)
        if verbose and achievement.threshold > 1:
            percent = (progress.current_value / achievement.threshold) * 100
            if percent in [25, 50, 75]:
                print(MILESTONE_BANNER.format(
                    name=achievement.name,
                    progress=progress.current_value,
                    threshold=achievement.threshold,
                    percent=int(percent)
                ))

        # Check if unlocked
        if progress.current_value >= achievement.threshold:
            return self._unlock(agent_name, achievement_id, battle_id, verbose)

        return False

    def check_and_unlock(self, agent_name: str, achievement_id: str,
                         condition: bool, battle_id: str = None,
                         verbose: bool = True) -> bool:
        """
        Check condition and unlock achievement if met.

        Args:
            agent_name: Name of agent
            achievement_id: Achievement ID
            condition: Boolean condition for unlock
            battle_id: Current battle ID
            verbose: Print announcements

        Returns:
            True if achievement was just unlocked
        """
        if not condition:
            return False

        if achievement_id not in self.achievements:
            return False

        progress = self.get_or_create_progress(agent_name, achievement_id)
        if progress.is_unlocked:
            return False

        return self._unlock(agent_name, achievement_id, battle_id, verbose)

    def _unlock(self, agent_name: str, achievement_id: str,
                battle_id: str = None, verbose: bool = True) -> bool:
        """Actually unlock an achievement."""
        achievement = self.achievements[achievement_id]
        progress = self.progress[agent_name][achievement_id]

        progress.is_unlocked = True
        progress.unlocked_at = datetime.now().isoformat()
        progress.unlocked_in_battle = battle_id

        # Award diamonds
        if agent_name not in self.total_diamonds:
            self.total_diamonds[agent_name] = 0
        self.total_diamonds[agent_name] += achievement.diamonds

        # Announcement
        if verbose:
            if achievement.secret:
                print(SECRET_UNLOCKED_BANNER.format(
                    icon=achievement.icon,
                    name=achievement.name.upper(),
                    description=achievement.description,
                    diamonds=achievement.diamonds
                ))
            else:
                print(ACHIEVEMENT_UNLOCKED_BANNER.format(
                    icon=achievement.icon,
                    name=achievement.name.upper(),
                    description=achievement.description,
                    rarity_emoji=achievement.rarity.color_emoji,
                    rarity=achievement.rarity.display_name.upper(),
                    diamonds=achievement.diamonds
                ))

        self._save_data()
        return True

    # =========================================================================
    # BATTLE ACHIEVEMENT CHECKS
    # =========================================================================

    def check_battle_achievements(self, agent_name: str, battle_id: str,
                                   winner: str, creator_score: int,
                                   opponent_score: int, analytics: Dict = None,
                                   verbose: bool = True):
        """
        Check all battle achievements after a battle.

        Args:
            agent_name: Name of agent to check
            battle_id: Battle identifier
            winner: "creator" or "opponent"
            creator_score: Final creator score
            opponent_score: Final opponent score
            analytics: Battle analytics data
        """
        won = (winner == "creator")

        # First Blood - check analytics for first gift
        if analytics and analytics.get('first_gifter') == agent_name:
            self.check_and_unlock(agent_name, "first_blood", True, battle_id, verbose)

        if won:
            # Perfect Victory - never behind
            if analytics and analytics.get('never_behind', False):
                self.check_and_unlock(agent_name, "perfect_victory", True, battle_id, verbose)

            # Domination - 2x score
            if creator_score >= opponent_score * 2 and opponent_score > 0:
                self.check_and_unlock(agent_name, "domination", True, battle_id, verbose)

            # Photo Finish - < 100 point difference
            diff = abs(creator_score - opponent_score)
            if diff < 100:
                self.check_and_unlock(agent_name, "photo_finish", True, battle_id, verbose)

            # Comeback King - was down 2x
            if analytics and analytics.get('max_deficit_ratio', 0) >= 2.0:
                self.check_and_unlock(agent_name, "comeback_king", True, battle_id, verbose)

        # Clutch Master - 5k+ in final 10s
        if analytics and analytics.get('final_10s_points', 0) >= 5000:
            self.check_and_unlock(agent_name, "clutch_master", True, battle_id, verbose)

        # x5 Sniper - 3+ x5 triggers
        if analytics and analytics.get('x5_triggers', 0) >= 3:
            self.check_and_unlock(agent_name, "x5_sniper", True, battle_id, verbose)

        # Whale Drop - 50k+ single gift
        if analytics and analytics.get('max_single_gift', 0) >= 50000:
            self.check_and_unlock(agent_name, "whale_drop", True, battle_id, verbose)

        # Secret: Lucky 777
        if creator_score == 77777:
            self.check_and_unlock(agent_name, "lucky_777", True, battle_id, verbose)

    # =========================================================================
    # AGENT ACHIEVEMENT UPDATES
    # =========================================================================

    def update_agent_achievements(self, agent_name: str, battle_id: str,
                                   points_donated: int, was_mvp: bool,
                                   won: bool, whale_gifts: int = 0,
                                   roses_sent: int = 0,
                                   verbose: bool = True):
        """
        Update cumulative agent achievements.

        Args:
            agent_name: Agent name
            battle_id: Battle ID
            points_donated: Points donated this battle
            was_mvp: Was this agent MVP
            won: Did team win
            whale_gifts: Number of 10k+ gifts
            roses_sent: Number of roses sent
        """
        # MVP Elite
        if was_mvp:
            self.update_progress(agent_name, "mvp_elite", 1, battle_id, verbose)

        # Millionaire Donor
        self.update_progress(agent_name, "millionaire_donor", points_donated, battle_id, verbose)

        # Battle Veteran
        self.update_progress(agent_name, "battle_veteran", 1, battle_id, verbose)

        # Whale Master
        if whale_gifts > 0:
            self.update_progress(agent_name, "whale_master", whale_gifts, battle_id, verbose)

        # Rose Garden
        if roses_sent > 0:
            self.update_progress(agent_name, "rose_garden", roses_sent, battle_id, verbose)

        # Winning Streak (handled separately with streak tracking)

    # =========================================================================
    # TOURNAMENT ACHIEVEMENT CHECKS
    # =========================================================================

    def check_tournament_achievements(self, agent_name: str, tournament_id: str,
                                        tournament_stats: Dict,
                                        verbose: bool = True):
        """
        Check tournament achievements after tournament ends.

        Args:
            agent_name: Agent/team name
            tournament_id: Tournament ID
            tournament_stats: Stats from TournamentManager
        """
        winner = tournament_stats.get('tournament_winner')
        if winner != "creator":
            return  # Only check if won

        creator_wins = tournament_stats.get('creator_wins', 0)
        opponent_wins = tournament_stats.get('opponent_wins', 0)
        format_name = tournament_stats.get('format', '')

        # Undefeated Champion
        if opponent_wins == 0:
            self.check_and_unlock(agent_name, "undefeated_champion", True, tournament_id, verbose)

        # Clean Sweep (3-0 or 4-0)
        if opponent_wins == 0 and creator_wins >= 3:
            self.check_and_unlock(agent_name, "sweep", True, tournament_id, verbose)

        # Comeback Series (down 0-2, win 3-2)
        # This would need battle-by-battle tracking, simplified here
        battles = tournament_stats.get('battles', [])
        if len(battles) >= 5:
            early_losses = sum(1 for b in battles[:2] if b.get('winner') == 'opponent')
            if early_losses == 2 and creator_wins == 3:
                self.check_and_unlock(agent_name, "comeback_series", True, tournament_id, verbose)

    # =========================================================================
    # DISPLAY METHODS
    # =========================================================================

    def get_agent_achievements(self, agent_name: str) -> List[Dict]:
        """Get all achievements for an agent."""
        results = []

        for ach_id, achievement in self.achievements.items():
            progress = self.get_or_create_progress(agent_name, ach_id)

            results.append({
                'id': ach_id,
                'name': achievement.name,
                'description': achievement.description if not achievement.secret or progress.is_unlocked else "???",
                'icon': achievement.icon if not achievement.secret or progress.is_unlocked else "🔒",
                'category': achievement.category.value,
                'rarity': achievement.rarity.display_name,
                'rarity_emoji': achievement.rarity.color_emoji,
                'diamonds': achievement.diamonds,
                'threshold': achievement.threshold,
                'current': progress.current_value,
                'unlocked': progress.is_unlocked,
                'unlocked_at': progress.unlocked_at,
                'percent': min(100, int((progress.current_value / achievement.threshold) * 100)),
                'secret': achievement.secret
            })

        return results

    def print_achievements(self, agent_name: str):
        """Print formatted achievement list for an agent."""
        achievements = self.get_agent_achievements(agent_name)
        unlocked = [a for a in achievements if a['unlocked']]
        locked = [a for a in achievements if not a['unlocked'] and not a['secret']]
        secrets = [a for a in achievements if a['secret'] and a['unlocked']]

        total_diamonds = self.total_diamonds.get(agent_name, 0)

        print("\n" + "=" * 70)
        print(f"   🏆 ACHIEVEMENTS: {agent_name}")
        print(f"   💎 Total Diamonds: {total_diamonds:,}")
        print("=" * 70)

        # Unlocked
        if unlocked:
            print(f"\n   ✅ UNLOCKED ({len(unlocked)})")
            print("   " + "-" * 65)
            for a in unlocked:
                print(f"   {a['icon']} {a['name']:<25} {a['rarity_emoji']} {a['rarity']:<12} 💎 {a['diamonds']}")

        # Secret unlocked
        if secrets:
            print(f"\n   🔓 SECRET ACHIEVEMENTS ({len(secrets)})")
            print("   " + "-" * 65)
            for a in secrets:
                print(f"   {a['icon']} {a['name']:<25} 🟡 Legendary     💎 {a['diamonds']}")

        # In progress
        in_progress = [a for a in locked if a['current'] > 0]
        if in_progress:
            print(f"\n   🔄 IN PROGRESS ({len(in_progress)})")
            print("   " + "-" * 65)
            for a in in_progress:
                bar = self._progress_bar(a['percent'])
                print(f"   🔒 {a['name']:<25} {bar} {a['current']}/{a['threshold']}")

        print("\n" + "=" * 70)

    def _progress_bar(self, percent: int, width: int = 10) -> str:
        """Create ASCII progress bar."""
        filled = int(width * percent / 100)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}] {percent}%"

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _save_data(self):
        """Save achievement data to file."""
        os.makedirs(os.path.dirname(self.save_file) or '.', exist_ok=True)

        data = {
            'progress': {
                agent: {
                    ach_id: {
                        'achievement_id': p.achievement_id,
                        'current_value': p.current_value,
                        'is_unlocked': p.is_unlocked,
                        'unlocked_at': p.unlocked_at,
                        'unlocked_in_battle': p.unlocked_in_battle
                    }
                    for ach_id, p in agent_progress.items()
                }
                for agent, agent_progress in self.progress.items()
            },
            'total_diamonds': self.total_diamonds
        }

        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self):
        """Load achievement data from file."""
        if not os.path.exists(self.save_file):
            return

        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)

            # Load progress
            for agent, agent_data in data.get('progress', {}).items():
                self.progress[agent] = {}
                for ach_id, p_data in agent_data.items():
                    self.progress[agent][ach_id] = AchievementProgress(
                        achievement_id=p_data['achievement_id'],
                        current_value=p_data['current_value'],
                        is_unlocked=p_data['is_unlocked'],
                        unlocked_at=p_data.get('unlocked_at'),
                        unlocked_in_battle=p_data.get('unlocked_in_battle')
                    )

            self.total_diamonds = data.get('total_diamonds', {})

            total_unlocked = sum(
                sum(1 for p in ap.values() if p.is_unlocked)
                for ap in self.progress.values()
            )
            print(f"📥 Loaded achievements: {total_unlocked} unlocked")

        except Exception as e:
            print(f"⚠️ Could not load achievements: {e}")
