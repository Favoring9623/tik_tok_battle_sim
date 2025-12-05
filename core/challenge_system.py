"""
Challenge Scenarios System

Pre-built difficult situations that test agent skills:
- Unique victory conditions
- Star ratings (1-3 stars based on performance)
- Progress tracking and rewards
- Increasing difficulty tiers

Challenge Categories:
1. SURVIVAL - Defend against specific threats
2. COMEBACK - Overcome disadvantages
3. EFFICIENCY - Win with limited resources
4. MASTERY - Perfect execution challenges
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import os


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE BANNERS
# ═══════════════════════════════════════════════════════════════════════════════

CHALLENGE_START_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎯🎯🎯  C H A L L E N G E   M O D E  🎯🎯🎯                                ║
║                                                                              ║
║   {name:<68} ║
║   {description:<68} ║
║                                                                              ║
║   Difficulty: {difficulty}  |  Category: {category:<20}              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

CHALLENGE_OBJECTIVES_BANNER = """
┌──────────────────────────────────────────────────────────────────────────────┐
│  🎯 OBJECTIVES                                                               │
│  {objectives}
│                                                                              │
│  ⭐ STAR CONDITIONS                                                          │
│  {star1}
│  {star2}
│  {star3}
└──────────────────────────────────────────────────────────────────────────────┘
"""

CHALLENGE_COMPLETE_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏆🏆🏆  C H A L L E N G E   C O M P L E T E !  🏆🏆🏆                      ║
║                                                                              ║
║   {name:<68} ║
║                                                                              ║
║   Result: {result:<59} ║
║   Stars:  {stars:<59} ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

CHALLENGE_FAILED_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ❌❌❌  C H A L L E N G E   F A I L E D  ❌❌❌                              ║
║                                                                              ║
║   {name:<68} ║
║   {reason:<68} ║
║                                                                              ║
║   Don't give up! Try again with a different strategy.                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════════
# NEW CHALLENGE CATEGORY BANNERS
# ═══════════════════════════════════════════════════════════════════════════════

TIMING_CHALLENGE_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⏱️⏱️⏱️  T I M I N G   C H A L L E N G E  ⏱️⏱️⏱️                           ║
║                                                                              ║
║   {name:<68} ║
║                                                                              ║
║   x5 Activations: {activations}/{target}  |  During Boosts: {boost_count:<15} ║
║                                                                              ║
║   PRECISION IS EVERYTHING!                                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

STREAK_CHALLENGE_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔥🔥🔥  S T R E A K   C H A L L E N G E  🔥🔥🔥                            ║
║                                                                              ║
║   {name:<68} ║
║                                                                              ║
║   Current Streak: {current}/{required}                                       ║
║   {streak_visual:<68} ║
║                                                                              ║
║   KEEP THE FIRE BURNING!                                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

UNDERDOG_CHALLENGE_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   💪💪💪  U N D E R D O G   C H A L L E N G E  💪💪💪                        ║
║                                                                              ║
║   Budget Ratio: 1:{ratio} UNDERDOG                                           ║
║                                                                              ║
║   You: {creator_budget:>10,} coins                                           ║
║   Them: {opponent_budget:>9,} coins                                          ║
║                                                                              ║
║   BELIEVE IN YOURSELF!                                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

PERFECT_X5_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⚡⚡⚡  P E R F E C T   x 5   T I M I N G  ⚡⚡⚡                            ║
║                                                                              ║
║   x5 #{count} ACTIVATED DURING {phase}!                                      ║
║                                                                              ║
║   Progress: [{bar}] {current}/3                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

STREAK_PROGRESS_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔥  W I N   S T R E A K :   {streak}  🔥                                   ║
║                                                                              ║
║   {visual}                                                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


class ChallengeDifficulty(Enum):
    """Challenge difficulty levels."""
    BEGINNER = "⭐ Beginner"
    INTERMEDIATE = "⭐⭐ Intermediate"
    ADVANCED = "⭐⭐⭐ Advanced"
    EXPERT = "⭐⭐⭐⭐ Expert"
    NIGHTMARE = "💀 Nightmare"


class ChallengeCategory(Enum):
    """Challenge categories."""
    SURVIVAL = "🛡️ Survival"
    COMEBACK = "🔄 Comeback"
    EFFICIENCY = "💰 Efficiency"
    MASTERY = "🎯 Mastery"
    TIMING = "⏱️ Timing"      # NEW: Perfect timing challenges
    STREAK = "🔥 Streak"       # NEW: Consecutive win challenges
    SPECIAL = "✨ Special"


@dataclass
class StarCondition:
    """Condition for earning a star."""
    description: str
    check: Callable[[Dict], bool]  # Function that takes battle_result and returns True/False


@dataclass
class ChallengeConfig:
    """Configuration overrides for a challenge."""
    # Budget settings
    creator_budget: Optional[int] = None
    opponent_budget: Optional[int] = None

    # Phase settings
    battle_duration: int = 300
    boost1_enabled: bool = True
    boost2_enabled: bool = True

    # Opponent settings
    opponent_strategy: Optional[str] = None  # Strategy profile name
    opponent_aggression_multiplier: float = 1.0

    # Special conditions
    start_time: int = 0  # Start battle at this time (for "Final Stand" etc.)
    creator_start_score: int = 0
    opponent_start_score: int = 0

    # Restrictions
    gloves_allowed: bool = True
    fog_allowed: bool = True
    hammer_allowed: bool = True
    whale_gifts_allowed: bool = True


@dataclass
class Challenge:
    """A challenge scenario."""
    id: str
    name: str
    description: str
    category: ChallengeCategory
    difficulty: ChallengeDifficulty

    # Configuration
    config: ChallengeConfig

    # Victory conditions
    victory_condition: Callable[[Dict], bool]
    victory_description: str

    # Star conditions (1-3 stars)
    star_conditions: List[StarCondition] = field(default_factory=list)

    # Rewards
    reward_coins: int = 0
    reward_items: Dict[str, int] = field(default_factory=dict)

    # Hints
    hints: List[str] = field(default_factory=list)

    # Unlock requirements
    requires_challenges: List[str] = field(default_factory=list)  # Challenge IDs


@dataclass
class ChallengeResult:
    """Result of a challenge attempt."""
    challenge_id: str
    completed: bool
    stars_earned: int
    score: int
    opponent_score: int
    time_taken: float
    date: str
    battle_stats: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_challenges() -> Dict[str, Challenge]:
    """Create all challenge definitions."""
    challenges = {}

    # ─────────────────────────────────────────────────────────────────────────
    # BEGINNER CHALLENGES
    # ─────────────────────────────────────────────────────────────────────────

    challenges["first_victory"] = Challenge(
        id="first_victory",
        name="First Victory",
        description="Win your first battle against a passive opponent.",
        category=ChallengeCategory.MASTERY,
        difficulty=ChallengeDifficulty.BEGINNER,
        config=ChallengeConfig(
            creator_budget=300000,
            opponent_budget=50000,
            opponent_strategy="sniper",
            opponent_aggression_multiplier=0.3,
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Win the battle",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Win by 50,000+ points", lambda r: r['creator_score'] - r['opponent_score'] >= 50000),
            StarCondition("Win by 100,000+ points", lambda r: r['creator_score'] - r['opponent_score'] >= 100000),
        ],
        hints=["Focus on sending gifts during boost phases for maximum points!"],
        reward_coins=1000,
    )

    challenges["boost_basics"] = Challenge(
        id="boost_basics",
        name="Boost Basics",
        description="Learn to dominate during Boost #1.",
        category=ChallengeCategory.MASTERY,
        difficulty=ChallengeDifficulty.BEGINNER,
        config=ChallengeConfig(
            creator_budget=200000,
            opponent_budget=100000,
            boost2_enabled=False,
        ),
        victory_condition=lambda r: r['winner'] == 'creator' and r.get('boost1_points', 0) >= 50000,
        victory_description="Win and score 50,000+ during Boost #1",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Score 50,000+ in Boost #1", lambda r: r.get('boost1_points', 0) >= 50000),
            StarCondition("Score 100,000+ in Boost #1", lambda r: r.get('boost1_points', 0) >= 100000),
        ],
        hints=["Save your whale gifts for when the boost multiplier is active!"],
        requires_challenges=["first_victory"],
        reward_coins=1500,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SURVIVAL CHALLENGES
    # ─────────────────────────────────────────────────────────────────────────

    challenges["survive_the_snipe"] = Challenge(
        id="survive_the_snipe",
        name="Survive the Snipe",
        description="Opponent saves everything for final 5 seconds. Build an unbeatable lead!",
        category=ChallengeCategory.SURVIVAL,
        difficulty=ChallengeDifficulty.INTERMEDIATE,
        config=ChallengeConfig(
            creator_budget=250000,
            opponent_budget=400000,
            opponent_strategy="sniper",
            opponent_aggression_multiplier=1.5,
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Win despite the massive snipe attack",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Lead by 200,000+ before snipe", lambda r: r.get('lead_at_175s', 0) >= 200000),
            StarCondition("Win by 50,000+ after snipe", lambda r: r['creator_score'] - r['opponent_score'] >= 50000),
        ],
        hints=[
            "Build a massive lead before the final 30 seconds",
            "Use fog to hide your lead and confuse the sniper",
        ],
        requires_challenges=["boost_basics"],
        reward_coins=3000,
        reward_items={"fog": 1},
    )

    challenges["whale_war"] = Challenge(
        id="whale_war",
        name="Whale War",
        description="Both sides have massive budgets. All-out whale gift warfare!",
        category=ChallengeCategory.SURVIVAL,
        difficulty=ChallengeDifficulty.ADVANCED,
        config=ChallengeConfig(
            creator_budget=800000,
            opponent_budget=800000,
            opponent_strategy="steady_pressure",
            opponent_aggression_multiplier=1.3,
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Win the whale war",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Send 10+ whale gifts", lambda r: r.get('whale_gifts_sent', 0) >= 10),
            StarCondition("Score 1,000,000+ total", lambda r: r['creator_score'] >= 1000000),
        ],
        hints=["Time your whale gifts with boost phases for maximum impact!"],
        requires_challenges=["survive_the_snipe"],
        reward_coins=5000,
        reward_items={"x5_glove": 1},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # COMEBACK CHALLENGES
    # ─────────────────────────────────────────────────────────────────────────

    challenges["comeback_king"] = Challenge(
        id="comeback_king",
        name="Comeback King",
        description="Start 100,000 points behind. Can you overcome the deficit?",
        category=ChallengeCategory.COMEBACK,
        difficulty=ChallengeDifficulty.INTERMEDIATE,
        config=ChallengeConfig(
            creator_budget=300000,
            opponent_budget=200000,
            opponent_start_score=100000,
            opponent_strategy="momentum_rider",
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Overcome the 100,000 point deficit and win",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Win by 25,000+", lambda r: r['creator_score'] - r['opponent_score'] >= 25000),
            StarCondition("Never let deficit exceed 150,000", lambda r: r.get('max_deficit', 999999) <= 150000),
        ],
        hints=["Focus on boost phases to quickly close the gap"],
        requires_challenges=["boost_basics"],
        reward_coins=3500,
    )

    challenges["final_stand"] = Challenge(
        id="final_stand",
        name="Final Stand",
        description="Battle starts at 270s - only 30 seconds remain! Down by 50,000.",
        category=ChallengeCategory.COMEBACK,
        difficulty=ChallengeDifficulty.ADVANCED,
        config=ChallengeConfig(
            creator_budget=150000,
            opponent_budget=100000,
            start_time=270,
            opponent_start_score=50000,
            opponent_strategy="sniper",
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Win in the final 30 seconds",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Win by 20,000+", lambda r: r['creator_score'] - r['opponent_score'] >= 20000),
            StarCondition("Activate glove x5", lambda r: r.get('glove_activated', False)),
        ],
        hints=["Every second counts - send gifts immediately!", "Glove x5 is crucial here"],
        requires_challenges=["comeback_king"],
        reward_coins=4000,
        reward_items={"x5_glove": 1},
    )

    challenges["impossible_deficit"] = Challenge(
        id="impossible_deficit",
        name="Impossible Deficit",
        description="Start 300,000 points behind with half the budget. Legendary difficulty.",
        category=ChallengeCategory.COMEBACK,
        difficulty=ChallengeDifficulty.NIGHTMARE,
        config=ChallengeConfig(
            creator_budget=200000,
            opponent_budget=400000,
            opponent_start_score=300000,
            opponent_strategy="late_dominator",
            opponent_aggression_multiplier=1.2,
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Overcome the impossible 300,000 deficit",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Win by any margin", lambda r: r['creator_score'] > r['opponent_score']),
            StarCondition("Win by 50,000+", lambda r: r['creator_score'] - r['opponent_score'] >= 50000),
        ],
        hints=["This requires perfect execution. Good luck."],
        requires_challenges=["final_stand", "whale_war"],
        reward_coins=10000,
        reward_items={"x5_glove": 2, "fog": 2, "hammer": 1},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # EFFICIENCY CHALLENGES
    # ─────────────────────────────────────────────────────────────────────────

    challenges["budget_crisis"] = Challenge(
        id="budget_crisis",
        name="Budget Crisis",
        description="Win with only 50,000 coins against 150,000. Efficiency is key!",
        category=ChallengeCategory.EFFICIENCY,
        difficulty=ChallengeDifficulty.INTERMEDIATE,
        config=ChallengeConfig(
            creator_budget=50000,
            opponent_budget=150000,
            opponent_strategy="steady_pressure",
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Win with limited budget",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Spend less than 40,000", lambda r: r.get('budget_spent', 99999) <= 40000),
            StarCondition("Win by 10,000+", lambda r: r['creator_score'] - r['opponent_score'] >= 10000),
        ],
        hints=[
            "Small gifts during boosts can be very efficient",
            "Don't waste budget outside of multiplier phases",
        ],
        requires_challenges=["boost_basics"],
        reward_coins=4000,
    )

    challenges["rose_army"] = Challenge(
        id="rose_army",
        name="Rose Army",
        description="Win using ONLY Rose gifts (1 coin each). Quantity over quality!",
        category=ChallengeCategory.EFFICIENCY,
        difficulty=ChallengeDifficulty.ADVANCED,
        config=ChallengeConfig(
            creator_budget=100000,
            opponent_budget=100000,
            whale_gifts_allowed=False,  # Only roses allowed (enforced in battle)
        ),
        victory_condition=lambda r: r['winner'] == 'creator' and r.get('only_roses', False),
        victory_description="Win using only Rose gifts",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Send 500+ roses", lambda r: r.get('roses_sent', 0) >= 500),
            StarCondition("Win by 20,000+", lambda r: r['creator_score'] - r['opponent_score'] >= 20000),
        ],
        hints=["Roses during x5 glove = 5 points each!", "Volume is everything"],
        requires_challenges=["budget_crisis"],
        reward_coins=5000,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # MASTERY CHALLENGES
    # ─────────────────────────────────────────────────────────────────────────

    challenges["threshold_master"] = Challenge(
        id="threshold_master",
        name="Threshold Master",
        description="Qualify for Boost #2 while spending minimum coins.",
        category=ChallengeCategory.MASTERY,
        difficulty=ChallengeDifficulty.INTERMEDIATE,
        config=ChallengeConfig(
            creator_budget=200000,
            opponent_budget=150000,
        ),
        victory_condition=lambda r: r['winner'] == 'creator' and r.get('boost2_qualified', False),
        victory_description="Win and qualify for Boost #2",
        star_conditions=[
            StarCondition("Qualify for Boost #2", lambda r: r.get('boost2_qualified', False)),
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Qualify with exact threshold (+10)", lambda r: r.get('threshold_efficiency', 999) <= 10),
        ],
        hints=["Watch the threshold reveal and calculate exactly what you need"],
        requires_challenges=["boost_basics"],
        reward_coins=3500,
    )

    challenges["glove_gambit"] = Challenge(
        id="glove_gambit",
        name="Glove Gambit",
        description="Win by activating glove x5 at least 3 times.",
        category=ChallengeCategory.MASTERY,
        difficulty=ChallengeDifficulty.ADVANCED,
        config=ChallengeConfig(
            creator_budget=400000,
            opponent_budget=300000,
            opponent_strategy="boost2_specialist",
        ),
        victory_condition=lambda r: r['winner'] == 'creator' and r.get('gloves_activated', 0) >= 3,
        victory_description="Win with 3+ glove x5 activations",
        star_conditions=[
            StarCondition("Activate glove x5 3+ times", lambda r: r.get('gloves_activated', 0) >= 3),
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Score 500,000+ during x5", lambda r: r.get('x5_points', 0) >= 500000),
        ],
        hints=["Send gloves during boost phases for better activation odds"],
        requires_challenges=["survive_the_snipe"],
        reward_coins=5000,
        reward_items={"x5_glove": 2},
    )

    challenges["perfect_game"] = Challenge(
        id="perfect_game",
        name="Perfect Game",
        description="Win while keeping opponent under 50,000 points.",
        category=ChallengeCategory.MASTERY,
        difficulty=ChallengeDifficulty.EXPERT,
        config=ChallengeConfig(
            creator_budget=400000,
            opponent_budget=200000,
            opponent_strategy="chaotic",
        ),
        victory_condition=lambda r: r['winner'] == 'creator' and r['opponent_score'] < 50000,
        victory_description="Win with opponent scoring under 50,000",
        star_conditions=[
            StarCondition("Opponent scores < 50,000", lambda r: r['opponent_score'] < 50000),
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Opponent scores < 25,000", lambda r: r['opponent_score'] < 25000),
        ],
        hints=["Use hammer to neutralize opponent's x5", "Fog hides your dominance"],
        requires_challenges=["glove_gambit", "whale_war"],
        reward_coins=7500,
        reward_items={"hammer": 2},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # TIMING CHALLENGES (NEW CATEGORY)
    # ─────────────────────────────────────────────────────────────────────────

    challenges["perfect_x5"] = Challenge(
        id="perfect_x5",
        name="Perfect x5 Timing",
        description="Activate x5 multiplier exactly 3 times, ALL during boost phases.",
        category=ChallengeCategory.TIMING,
        difficulty=ChallengeDifficulty.ADVANCED,
        config=ChallengeConfig(
            creator_budget=350000,
            opponent_budget=250000,
            gloves_allowed=True,
        ),
        victory_condition=lambda r: (
            r['winner'] == 'creator' and
            r.get('gloves_activated', 0) >= 3 and
            r.get('x5_during_boost', 0) >= 3
        ),
        victory_description="Activate x5 exactly 3 times, all during boosts",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Activate x5 during Boost #1", lambda r: r.get('x5_boost1', 0) >= 1),
            StarCondition("All 3 x5 during boosts", lambda r: r.get('x5_during_boost', 0) >= 3),
        ],
        hints=[
            "Timing is everything!",
            "Save gloves for multiplier phases",
            "Boost #2 has higher activation rates",
        ],
        requires_challenges=["glove_gambit"],
        reward_coins=6000,
        reward_items={"x5_glove": 2},
    )

    challenges["snipe_the_sniper"] = Challenge(
        id="snipe_the_sniper",
        name="Snipe the Sniper",
        description="Opponent saves EVERYTHING for final 3 seconds. Out-snipe them!",
        category=ChallengeCategory.TIMING,
        difficulty=ChallengeDifficulty.EXPERT,
        config=ChallengeConfig(
            creator_budget=300000,
            opponent_budget=400000,
            opponent_strategy="ultimate_sniper",
            opponent_aggression_multiplier=0.1,  # Saves everything
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Beat the ultimate sniper",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Score 200k+ in final 10s", lambda r: r.get('final_10s_score', 0) >= 200000),
            StarCondition("Win by 50k+", lambda r: r['creator_score'] - r['opponent_score'] >= 50000),
        ],
        hints=[
            "They're saving EVERYTHING",
            "You need to out-snipe a sniper",
            "Consider split timing - early pressure AND final burst",
        ],
        requires_challenges=["survive_the_snipe"],
        reward_coins=8000,
        reward_items={"x5_glove": 1, "fog": 2},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # EFFICIENCY CHALLENGES (NEW)
    # ─────────────────────────────────────────────────────────────────────────

    challenges["no_whales_victory"] = Challenge(
        id="no_whales_victory",
        name="No Whales Allowed",
        description="Win without sending any gift worth 10,000+ coins.",
        category=ChallengeCategory.EFFICIENCY,
        difficulty=ChallengeDifficulty.ADVANCED,
        config=ChallengeConfig(
            creator_budget=200000,
            opponent_budget=200000,
            whale_gifts_allowed=False,
        ),
        victory_condition=lambda r: (
            r['winner'] == 'creator' and
            r.get('max_gift_value', 999999) < 10000
        ),
        victory_description="Win using only gifts under 10,000 coins",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Max gift under 5,000", lambda r: r.get('max_gift_value', 999999) < 5000),
            StarCondition("Max gift under 1,000", lambda r: r.get('max_gift_value', 999999) < 1000),
        ],
        hints=[
            "Volume over value!",
            "Timing small gifts with multipliers is key",
            "x5 makes roses worth 5!",
        ],
        requires_challenges=["budget_crisis"],
        reward_coins=5500,
    )

    challenges["underdog_miracle"] = Challenge(
        id="underdog_miracle",
        name="Underdog Miracle",
        description="Win with 1/4 the opponent's budget. True skill test!",
        category=ChallengeCategory.EFFICIENCY,
        difficulty=ChallengeDifficulty.NIGHTMARE,
        config=ChallengeConfig(
            creator_budget=75000,
            opponent_budget=300000,
            opponent_strategy="balanced",
            opponent_aggression_multiplier=1.2,
        ),
        victory_condition=lambda r: r['winner'] == 'creator',
        victory_description="Win with 1/4 the budget",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Spend under 60k", lambda r: r.get('budget_spent', 999999) <= 60000),
            StarCondition("Win by 5k+", lambda r: r['creator_score'] - r['opponent_score'] >= 5000),
        ],
        hints=[
            "Every coin must count!",
            "Perfect timing is essential",
            "This is VERY hard - good luck!",
        ],
        requires_challenges=["rose_army", "budget_crisis"],
        reward_coins=15000,
        reward_items={"x5_glove": 3, "fog": 2, "hammer": 2},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # COMEBACK CHALLENGES (NEW)
    # ─────────────────────────────────────────────────────────────────────────

    challenges["down_30_comeback"] = Challenge(
        id="down_30_comeback",
        name="Down 30% Comeback",
        description="Win after being behind by 30% or more at any point.",
        category=ChallengeCategory.COMEBACK,
        difficulty=ChallengeDifficulty.EXPERT,
        config=ChallengeConfig(
            creator_budget=300000,
            opponent_budget=350000,
            opponent_start_score=50000,
            opponent_strategy="early_aggressor",
            opponent_aggression_multiplier=1.4,
        ),
        victory_condition=lambda r: (
            r['winner'] == 'creator' and
            r.get('max_deficit_percent', 0) >= 30
        ),
        victory_description="Come back from 30%+ deficit to win",
        star_conditions=[
            StarCondition("Win the battle", lambda r: r['winner'] == 'creator'),
            StarCondition("Come back from 30%+ deficit", lambda r: r.get('max_deficit_percent', 0) >= 30),
            StarCondition("Win by 10%+ margin", lambda r: r.get('final_margin_percent', 0) >= 10),
        ],
        hints=[
            "Don't panic when behind!",
            "Save resources for your comeback window",
            "Boost phases are your friend",
        ],
        requires_challenges=["comeback_king"],
        reward_coins=7000,
        reward_items={"fog": 2, "hammer": 1},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # STREAK CHALLENGES (NEW CATEGORY)
    # ─────────────────────────────────────────────────────────────────────────

    challenges["three_in_a_row"] = Challenge(
        id="three_in_a_row",
        name="Three in a Row",
        description="Win 3 battles consecutively with the same team.",
        category=ChallengeCategory.STREAK,
        difficulty=ChallengeDifficulty.INTERMEDIATE,
        config=ChallengeConfig(
            creator_budget=250000,
            opponent_budget=200000,
        ),
        victory_condition=lambda r: r.get('streak_wins', 0) >= 3,
        victory_description="Win 3 battles in a row",
        star_conditions=[
            StarCondition("Win 3 in a row", lambda r: r.get('streak_wins', 0) >= 3),
            StarCondition("Win 5 in a row", lambda r: r.get('streak_wins', 0) >= 5),
            StarCondition("Win 7 in a row (perfect)", lambda r: r.get('streak_wins', 0) >= 7),
        ],
        hints=[
            "Consistency is key!",
            "Adapt your strategy between battles",
            "Learn from each win",
        ],
        requires_challenges=["first_victory"],
        reward_coins=4500,
    )

    challenges["flawless_tournament"] = Challenge(
        id="flawless_tournament",
        name="Flawless Tournament",
        description="Win a Best of 5 tournament without losing a single battle.",
        category=ChallengeCategory.STREAK,
        difficulty=ChallengeDifficulty.EXPERT,
        config=ChallengeConfig(
            creator_budget=400000,
            opponent_budget=300000,
        ),
        victory_condition=lambda r: (
            r.get('tournament_win', False) and
            r.get('tournament_losses', 1) == 0
        ),
        victory_description="Win Best of 5 going 3-0",
        star_conditions=[
            StarCondition("Win tournament 3-0", lambda r: r.get('tournament_record') == '3-0'),
            StarCondition("Total margin 100k+", lambda r: r.get('total_margin', 0) >= 100000),
            StarCondition("MVP in all 3 battles", lambda r: r.get('mvp_count', 0) >= 3),
        ],
        hints=[
            "Perfection requires preparation",
            "Dominate every battle",
            "No room for error",
        ],
        requires_challenges=["three_in_a_row"],
        reward_coins=12000,
        reward_items={"x5_glove": 2, "fog": 2, "hammer": 1, "time_ext": 1},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SPECIAL CHALLENGES
    # ─────────────────────────────────────────────────────────────────────────

    challenges["the_gauntlet"] = Challenge(
        id="the_gauntlet",
        name="The Gauntlet",
        description="Face 5 opponents in a row. Budget carries over. Can you survive?",
        category=ChallengeCategory.SPECIAL,
        difficulty=ChallengeDifficulty.NIGHTMARE,
        config=ChallengeConfig(
            creator_budget=500000,
            opponent_budget=100000,  # Per opponent
            # Special: This is a multi-battle challenge
        ),
        victory_condition=lambda r: r.get('gauntlet_wins', 0) >= 5,
        victory_description="Defeat 5 opponents in a row",
        star_conditions=[
            StarCondition("Beat 5 opponents", lambda r: r.get('gauntlet_wins', 0) >= 5),
            StarCondition("Finish with 100,000+ budget", lambda r: r.get('remaining_budget', 0) >= 100000),
            StarCondition("No losses", lambda r: r.get('gauntlet_losses', 0) == 0),
        ],
        hints=["Manage your budget carefully - it has to last!", "Each opponent is harder than the last"],
        requires_challenges=["perfect_game", "impossible_deficit"],
        reward_coins=20000,
        reward_items={"x5_glove": 3, "fog": 3, "hammer": 2, "time_ext": 2},
    )

    return challenges


# ═══════════════════════════════════════════════════════════════════════════════
# CHALLENGE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ChallengeManager:
    """
    Manages challenge scenarios, progress, and rewards.
    """

    def __init__(self, save_file: str = "challenge_progress.json"):
        self.save_file = save_file
        self.challenges = create_challenges()

        # Progress tracking
        self.completed_challenges: Dict[str, ChallengeResult] = {}
        self.best_stars: Dict[str, int] = {}
        self.total_stars: int = 0
        self.coins_earned: int = 0
        self.items_earned: Dict[str, int] = {}

        self._load_progress()

    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Get a challenge by ID."""
        return self.challenges.get(challenge_id)

    def is_unlocked(self, challenge_id: str) -> bool:
        """Check if a challenge is unlocked."""
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return False

        # Check requirements
        for req_id in challenge.requires_challenges:
            if req_id not in self.completed_challenges:
                return False

        return True

    def get_available_challenges(self) -> List[Challenge]:
        """Get list of challenges available to play."""
        available = []
        for challenge in self.challenges.values():
            if self.is_unlocked(challenge.id):
                available.append(challenge)
        return available

    def get_challenges_by_category(self, category: ChallengeCategory) -> List[Challenge]:
        """Get challenges filtered by category."""
        return [c for c in self.challenges.values() if c.category == category]

    def get_challenges_by_difficulty(self, difficulty: ChallengeDifficulty) -> List[Challenge]:
        """Get challenges filtered by difficulty."""
        return [c for c in self.challenges.values() if c.difficulty == difficulty]

    def start_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Start a challenge and display intro."""
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            print(f"❌ Challenge '{challenge_id}' not found!")
            return None

        if not self.is_unlocked(challenge_id):
            print(f"🔒 Challenge '{challenge.name}' is locked!")
            print(f"   Complete these first: {', '.join(challenge.requires_challenges)}")
            return None

        # Display challenge intro
        print(CHALLENGE_START_BANNER.format(
            name=challenge.name,
            description=challenge.description,
            difficulty=challenge.difficulty.value,
            category=challenge.category.value,
        ))

        # Display objectives
        objectives = f"  • {challenge.victory_description:<64} │"
        star1 = f"  ⭐ {challenge.star_conditions[0].description:<62} │" if len(challenge.star_conditions) > 0 else ""
        star2 = f"  ⭐⭐ {challenge.star_conditions[1].description:<60} │" if len(challenge.star_conditions) > 1 else ""
        star3 = f"  ⭐⭐⭐ {challenge.star_conditions[2].description:<58} │" if len(challenge.star_conditions) > 2 else ""

        print(CHALLENGE_OBJECTIVES_BANNER.format(
            objectives=objectives,
            star1=star1,
            star2=star2,
            star3=star3,
        ))

        # Display hints
        if challenge.hints:
            print("💡 HINTS:")
            for hint in challenge.hints:
                print(f"   • {hint}")
            print()

        return challenge

    def evaluate_result(self, challenge_id: str, battle_result: Dict) -> ChallengeResult:
        """Evaluate a battle result against challenge conditions."""
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            raise ValueError(f"Challenge '{challenge_id}' not found")

        # Check victory condition
        completed = challenge.victory_condition(battle_result)

        # Count stars
        stars_earned = 0
        for i, star_cond in enumerate(challenge.star_conditions):
            if star_cond.check(battle_result):
                stars_earned = i + 1
            else:
                break  # Stars must be earned in order

        # Create result
        result = ChallengeResult(
            challenge_id=challenge_id,
            completed=completed,
            stars_earned=stars_earned,
            score=battle_result.get('creator_score', 0),
            opponent_score=battle_result.get('opponent_score', 0),
            time_taken=battle_result.get('time_taken', 0),
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            battle_stats=battle_result,
        )

        # Display result
        if completed:
            stars_display = "⭐" * stars_earned + "☆" * (3 - stars_earned)
            print(CHALLENGE_COMPLETE_BANNER.format(
                name=challenge.name,
                result="VICTORY!",
                stars=stars_display,
            ))

            # Award rewards if this is a new completion or better stars
            if challenge_id not in self.completed_challenges or stars_earned > self.best_stars.get(challenge_id, 0):
                self._award_rewards(challenge, stars_earned)
        else:
            reason = "Victory condition not met"
            print(CHALLENGE_FAILED_BANNER.format(
                name=challenge.name,
                reason=reason,
            ))

        # Update progress
        self._update_progress(result)

        return result

    def _award_rewards(self, challenge: Challenge, stars: int):
        """Award rewards for completing a challenge."""
        print("\n🎁 REWARDS EARNED:")

        # Base reward
        coins = challenge.reward_coins
        if stars >= 2:
            coins = int(coins * 1.5)
        if stars >= 3:
            coins = int(coins * 2)

        print(f"   💰 {coins:,} coins")
        self.coins_earned += coins

        # Item rewards (only for 3 stars or first completion)
        if challenge.reward_items:
            for item, count in challenge.reward_items.items():
                print(f"   🎁 {count}x {item}")
                self.items_earned[item] = self.items_earned.get(item, 0) + count

        print()

    def _update_progress(self, result: ChallengeResult):
        """Update progress tracking."""
        if result.completed:
            # Track completion
            self.completed_challenges[result.challenge_id] = result

            # Update best stars
            current_best = self.best_stars.get(result.challenge_id, 0)
            if result.stars_earned > current_best:
                self.best_stars[result.challenge_id] = result.stars_earned
                self.total_stars += (result.stars_earned - current_best)

        self._save_progress()

    def print_progress(self):
        """Print challenge progress summary."""
        print("\n" + "=" * 70)
        print("🎯 CHALLENGE PROGRESS")
        print("=" * 70)

        total_challenges = len(self.challenges)
        completed = len(self.completed_challenges)
        max_stars = total_challenges * 3

        print(f"\n📊 Overall Progress:")
        print(f"   Challenges: {completed}/{total_challenges} ({100*completed//total_challenges}%)")
        print(f"   Stars: {self.total_stars}/{max_stars}")
        print(f"   Coins Earned: {self.coins_earned:,}")

        # Progress by category
        print(f"\n📁 By Category:")
        for category in ChallengeCategory:
            cat_challenges = self.get_challenges_by_category(category)
            cat_completed = sum(1 for c in cat_challenges if c.id in self.completed_challenges)
            cat_stars = sum(self.best_stars.get(c.id, 0) for c in cat_challenges)
            print(f"   {category.value}: {cat_completed}/{len(cat_challenges)} | ⭐ {cat_stars}/{len(cat_challenges)*3}")

        # Recent completions
        if self.completed_challenges:
            print(f"\n🏆 Recent Completions:")
            recent = sorted(self.completed_challenges.values(), key=lambda r: r.date, reverse=True)[:5]
            for r in recent:
                challenge = self.challenges.get(r.challenge_id)
                stars = "⭐" * r.stars_earned
                print(f"   {challenge.name}: {stars} ({r.date})")

        print("=" * 70 + "\n")

    def print_challenge_list(self):
        """Print list of all challenges with status."""
        print("\n" + "=" * 80)
        print("🎯 CHALLENGE LIST")
        print("=" * 80)

        for category in ChallengeCategory:
            challenges = self.get_challenges_by_category(category)
            if not challenges:
                continue

            print(f"\n{category.value}")
            print("-" * 40)

            for c in sorted(challenges, key=lambda x: list(ChallengeDifficulty).index(x.difficulty)):
                # Status
                if c.id in self.completed_challenges:
                    stars = self.best_stars.get(c.id, 0)
                    status = "⭐" * stars + "☆" * (3 - stars)
                elif self.is_unlocked(c.id):
                    status = "🔓 Available"
                else:
                    status = "🔒 Locked"

                print(f"   {c.name:<25} {c.difficulty.value:<20} {status}")

        print("\n" + "=" * 80)

    def _save_progress(self):
        """Save progress to file."""
        data = {
            "completed": {k: {
                "challenge_id": v.challenge_id,
                "completed": v.completed,
                "stars_earned": v.stars_earned,
                "score": v.score,
                "opponent_score": v.opponent_score,
                "date": v.date,
            } for k, v in self.completed_challenges.items()},
            "best_stars": self.best_stars,
            "total_stars": self.total_stars,
            "coins_earned": self.coins_earned,
            "items_earned": self.items_earned,
        }

        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_progress(self):
        """Load progress from file."""
        if not os.path.exists(self.save_file):
            return

        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)

            # Load completed challenges
            for k, v in data.get("completed", {}).items():
                self.completed_challenges[k] = ChallengeResult(
                    challenge_id=v["challenge_id"],
                    completed=v["completed"],
                    stars_earned=v["stars_earned"],
                    score=v["score"],
                    opponent_score=v["opponent_score"],
                    time_taken=0,
                    date=v["date"],
                )

            self.best_stars = data.get("best_stars", {})
            self.total_stars = data.get("total_stars", 0)
            self.coins_earned = data.get("coins_earned", 0)
            self.items_earned = data.get("items_earned", {})

            print(f"📥 Loaded challenge progress: {len(self.completed_challenges)} completed, {self.total_stars} stars")
        except Exception as e:
            print(f"⚠️ Could not load challenge progress: {e}")
