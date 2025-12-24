"""
TikTok Live Battle Configuration - Official Parameters

Real TikTok Battle settings based on official documentation.
Sources:
- https://www.tiktok.com/live/creators/en-US/article/match-power-ups-win-with-fewer-gifts
- https://blog.push.fm/17839/need-know-tiktok-battles/
- TikTok Discover pages for battles

Last Updated: December 2025
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class BattlePhase(Enum):
    """Battle phases during a TikTok Live match."""
    COUNTDOWN = "countdown"          # Pre-battle countdown
    BATTLE = "battle"                # Main battle (5 minutes)
    FINAL_PUSH = "final_push"        # Last 30 seconds - critical moment
    VICTORY_LAP = "victory_lap"      # Post-battle celebration (3 minutes)
    ENDED = "ended"


class PowerUpType(Enum):
    """Official TikTok Battle Power-Ups."""
    BOOSTING_GLOVE = "boosting_glove"  # 30% chance of 5x points for 30 seconds
    MAGIC_MIST = "magic_mist"          # Hides opponent's points
    TIME_MAKER = "time_maker"          # Extends match time
    STUN_HAMMER = "stun_hammer"        # Used during victory lap


@dataclass
class PowerUpConfig:
    """Configuration for a power-up."""
    name: str
    emoji: str
    duration_seconds: int
    multiplier: float = 1.0
    activation_chance: float = 1.0  # Chance of effect triggering
    best_timing: str = ""  # When to use


@dataclass
class TikTokBattleConfig:
    """
    Official TikTok Live Battle Configuration.

    These are the real parameters used in TikTok Live Battles.
    """

    # === TIMING (Official) ===
    battle_duration: int = 300          # 5 minutes (300 seconds)
    victory_lap_duration: int = 150     # 2 min 30 sec - shows scores/winner (no points)
    countdown_duration: int = 3         # 3 second countdown before battle

    # === PHASES ===
    final_push_start: int = 270         # Last 30 seconds (at 270s elapsed = 30s remaining)

    # === POINTS SYSTEM (Official) ===
    coins_to_points: int = 1            # 1 coin = 1 point
    first_like_points: int = 3          # First like = 3 points
    subsequent_like_points: int = 1     # Following likes = 1 point each

    # === POWER-UPS (Official) ===
    power_ups: Dict[str, PowerUpConfig] = field(default_factory=lambda: {
        "boosting_glove": PowerUpConfig(
            name="Boosting Glove",
            emoji="🥊",
            duration_seconds=30,
            multiplier=5.0,
            activation_chance=0.30,  # 30% chance per gift
            best_timing="Beginning of match or when losing"
        ),
        "magic_mist": PowerUpConfig(
            name="Magic Mist",
            emoji="☁️",
            duration_seconds=30,  # Estimated
            multiplier=1.0,
            activation_chance=1.0,
            best_timing="Last 30 seconds of match"
        ),
        "time_maker": PowerUpConfig(
            name="Time-Maker",
            emoji="⏰",
            duration_seconds=30,  # Adds 30 seconds (estimated)
            multiplier=1.0,
            activation_chance=1.0,
            best_timing="Near end of LIVE match"
        ),
        "stun_hammer": PowerUpConfig(
            name="Stun Hammer",
            emoji="🔨",
            duration_seconds=15,  # Estimated
            multiplier=1.0,
            activation_chance=1.0,
            best_timing="Victory lap period"
        ),
    })

    # === SPEED EVENTS (Special TikTok Events) ===
    speed_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "normal": 1.0,
        "2x_event": 2.0,      # Double points event
        "3x_event": 3.0,      # Triple points event
    })

    # === REVENUE (Official) ===
    tiktok_cut_percentage: float = 70.0   # TikTok takes ~70%
    creator_cut_percentage: float = 30.0  # Creator keeps ~30%

    # === GIFT VALUE TIERS ===
    strategic_gift_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "micro": 10,          # 1-10 points (Rose, TikTok)
        "small": 100,         # 11-100 points (Ice Cream, Doughnut)
        "medium": 1000,       # 101-1000 points (Hand Heart, GG)
        "large": 10000,       # 1001-10000 points (Lion, Drama Queen)
        "whale": 100000,      # 10001+ points (Universe, TikTok Universe)
    })

    def get_phase(self, elapsed_seconds: int) -> BattlePhase:
        """Determine current battle phase based on elapsed time."""
        if elapsed_seconds < 0:
            return BattlePhase.COUNTDOWN
        elif elapsed_seconds < self.final_push_start:
            return BattlePhase.BATTLE
        elif elapsed_seconds < self.battle_duration:
            return BattlePhase.FINAL_PUSH
        elif elapsed_seconds < self.battle_duration + self.victory_lap_duration:
            return BattlePhase.VICTORY_LAP
        else:
            return BattlePhase.ENDED

    def get_time_remaining(self, elapsed_seconds: int) -> int:
        """Get remaining battle time (not including victory lap)."""
        return max(0, self.battle_duration - elapsed_seconds)

    def is_final_push(self, elapsed_seconds: int) -> bool:
        """Check if we're in the critical final 30 seconds."""
        return self.final_push_start <= elapsed_seconds < self.battle_duration

    def calculate_glove_points(self, base_points: int) -> int:
        """
        Calculate points when Boosting Glove is active.
        30% chance of 5x multiplier.
        """
        import random
        glove = self.power_ups["boosting_glove"]
        if random.random() < glove.activation_chance:
            return int(base_points * glove.multiplier)
        return base_points


# Default configuration instance
TIKTOK_BATTLE_CONFIG = TikTokBattleConfig()


@dataclass
class TournamentConfig:
    """
    Configuration for Best-of-X tournaments.
    """

    # === TOURNAMENT FORMATS ===
    formats: Dict[str, int] = field(default_factory=lambda: {
        "bo1": 1,   # Single match
        "bo3": 3,   # Best of 3 (first to 2 wins)
        "bo5": 5,   # Best of 5 (first to 3 wins)
        "bo7": 7,   # Best of 7 (first to 4 wins)
    })

    # === TIMING (Official TikTok) ===
    # Victory Lap = break between rounds (shows scores, no points)
    break_between_rounds: int = 150     # 2 min 30 sec (victory lap)
    pre_tournament_countdown: int = 10  # 10 seconds before tournament starts

    # === USING REAL BATTLE CONFIG ===
    battle_config: TikTokBattleConfig = field(default_factory=TikTokBattleConfig)

    def wins_needed(self, format: str) -> int:
        """Calculate wins needed to win the tournament."""
        total_rounds = self.formats.get(format, 1)
        return (total_rounds // 2) + 1

    def max_rounds(self, format: str) -> int:
        """Maximum possible rounds in the tournament."""
        return self.formats.get(format, 1)


# Default tournament configuration
TOURNAMENT_CONFIG = TournamentConfig()


# === CONVENIENCE CONSTANTS ===

# Official battle duration
BATTLE_DURATION_SECONDS = 300  # 5 minutes

# Victory lap = cooldown (shows scores/winner, no points count)
VICTORY_LAP_SECONDS = 150  # 2 min 30 sec
BATTLE_COOLDOWN_SECONDS = VICTORY_LAP_SECONDS  # Same thing

# Final push timing (last 30 seconds)
FINAL_PUSH_SECONDS = 30

# Boosting Glove effect
GLOVE_DURATION_SECONDS = 30
GLOVE_MULTIPLIER = 5.0
GLOVE_ACTIVATION_CHANCE = 0.30  # 30%

# Point conversion
COINS_TO_POINTS = 1  # 1:1 ratio
FIRST_LIKE_POINTS = 3
LIKE_POINTS = 1


def print_config_summary():
    """Print a summary of the battle configuration."""
    config = TIKTOK_BATTLE_CONFIG

    print("\n" + "="*60)
    print("TIKTOK LIVE BATTLE - OFFICIAL CONFIGURATION")
    print("="*60)

    print("\n📊 TIMING:")
    print(f"   Battle Duration:     {config.battle_duration}s (5 minutes)")
    print(f"   Victory Lap:         {config.victory_lap_duration}s (2 min 30 sec) - scores only, no points")
    print(f"   Final Push:          Last {config.battle_duration - config.final_push_start}s")

    print("\n💰 POINTS:")
    print(f"   1 Coin = {config.coins_to_points} Point")
    print(f"   First Like = {config.first_like_points} Points")
    print(f"   Subsequent Likes = {config.subsequent_like_points} Point each")

    print("\n⚡ POWER-UPS:")
    for name, powerup in config.power_ups.items():
        print(f"   {powerup.emoji} {powerup.name}:")
        print(f"      Duration: {powerup.duration_seconds}s")
        if powerup.multiplier > 1:
            print(f"      Multiplier: {powerup.multiplier}x ({int(powerup.activation_chance*100)}% chance)")
        print(f"      Best Use: {powerup.best_timing}")

    print("\n🎮 SPEED EVENTS:")
    for event, mult in config.speed_multipliers.items():
        print(f"   {event}: {mult}x points")

    print("\n💵 REVENUE SPLIT:")
    print(f"   TikTok: {config.tiktok_cut_percentage}%")
    print(f"   Creator: {config.creator_cut_percentage}%")

    print("\n" + "="*60)


if __name__ == "__main__":
    print_config_summary()
