"""
TikTok Gifts Catalog - Real Data

Official TikTok gift catalog with authentic coin prices.
Data sourced from streamtoearn.io (Last update: November 2025)

This module provides the complete, up-to-date list of TikTok gifts
for use in realistic battle simulations.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class GiftTier(Enum):
    """Gift price tiers."""
    BASIC = "basic"           # 1 coin
    LOW = "low"              # 2-30 coins
    STANDARD = "standard"    # 31-99 coins
    PREMIUM = "premium"      # 100-499 coins
    HIGH = "high"           # 500-5,999 coins
    LUXURY = "luxury"       # 6,000-24,999 coins
    ULTRA = "ultra"         # 25,000-44,999 coins
    LIVE_FEST = "live_fest"  # Special event gifts (campaigns)


@dataclass
class TikTokGift:
    """Represents a TikTok gift."""
    name: str
    coins: int
    tier: GiftTier
    emoji: str = "🎁"
    description: str = ""

    @property
    def points(self) -> int:
        """Battle points equal coin value (TikTok official: 1 coin = 1 diamond = 1 point)."""
        return self.coins

    @property
    def live_fest_points(self) -> float:
        """
        Live Fest ranking points.

        During LiveFest 2025:
        - Fest gifts (FEST_POP, FEST_GEAR, FEST_CHEERS, FEST_PARTY) = 1.5x points
        - Vault gifts = 1.5x points
        - Regular gifts = 1x points
        - Votes = 1 point (free)
        """
        if self.tier == GiftTier.LIVE_FEST:
            return self.coins * 1.5  # 1.5x multiplier for Fest/Vault gifts
        return float(self.coins)

    def usd_cost(self, coin_rate: float = 0.0133) -> float:
        """Calculate USD cost (default rate: $0.0133/coin)."""
        return self.coins * coin_rate


# Complete TikTok Gifts Catalog (Official Data)
TIKTOK_GIFTS_CATALOG: Dict[str, TikTokGift] = {

    # ===== BASIC TIER (1 coin) =====
    "ROSE": TikTokGift(
        name="Rose",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="🌹",
        description="The most popular basic gift"
    ),
    "TIKTOK": TikTokGift(
        name="TikTok",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="⚡",
        description="TikTok's signature gift"
    ),
    "YOURE_AWESOME": TikTokGift(
        name="You're awesome",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="✨",
        description="Encouragement gift"
    ),
    "CAKE_SLICE": TikTokGift(
        name="Cake Slice",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="🍰",
        description="Sweet treat"
    ),
    "LOVE_YOU_SO_MUCH": TikTokGift(
        name="Love you so much",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="💕",
        description="Affection expression"
    ),
    "ICE_CREAM_CONE": TikTokGift(
        name="Ice Cream Cone",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="🍦",
        description="Cool refreshment"
    ),
    "GG": TikTokGift(
        name="GG",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="🎮",
        description="Good game - gaming culture"
    ),
    "HEART_ME": TikTokGift(
        name="Heart Me",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="❤️",
        description="Simple love"
    ),
    "THUMBS_UP": TikTokGift(
        name="Thumbs Up",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="👍",
        description="Approval"
    ),
    "HEART": TikTokGift(
        name="Heart",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="💗",
        description="Classic heart"
    ),
    "LIGHTNING_BOLT": TikTokGift(
        name="Lightning Bolt",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="⚡",
        description="Energy boost"
    ),
    "LOVE_YOU": TikTokGift(
        name="Love you",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="💘",
        description="Simple I love you"
    ),
    "BLOW_A_KISS": TikTokGift(
        name="Blow a kiss",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="😘",
        description="Romantic gesture"
    ),
    "FAIRY_WINGS": TikTokGift(
        name="Fairy wings",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="🧚",
        description="Magical"
    ),
    "FLAME_HEART": TikTokGift(
        name="Flame heart",
        coins=1,
        tier=GiftTier.BASIC,
        emoji="❤️‍🔥",
        description="Passionate love"
    ),

    # ===== LOW TIER (2-30 coins) =====
    "FINGER_HEART": TikTokGift(
        name="Finger Heart",
        coins=5,
        tier=GiftTier.LOW,
        emoji="💗",
        description="Korean finger heart gesture"
    ),
    "ICE_CREAM": TikTokGift(
        name="Ice cream",
        coins=5,
        tier=GiftTier.LOW,
        emoji="🍨",
        description="Delicious dessert"
    ),
    "APPLAUSE": TikTokGift(
        name="Applause",
        coins=9,
        tier=GiftTier.LOW,
        emoji="👏",
        description="Appreciation"
    ),
    "ROSA": TikTokGift(
        name="Rosa",
        coins=10,
        tier=GiftTier.LOW,
        emoji="🌹",
        description="Premium rose variant"
    ),
    "PERFUME": TikTokGift(
        name="Perfume",
        coins=20,
        tier=GiftTier.LOW,
        emoji="💐",
        description="Elegant scent"
    ),
    "DOUGHNUT": TikTokGift(
        name="Doughnut",
        coins=30,
        tier=GiftTier.LOW,
        emoji="🍩",
        description="Sweet snack"
    ),

    # ===== STANDARD TIER (31-99 coins) =====
    "BUTTERFLY": TikTokGift(
        name="Butterfly",
        coins=88,
        tier=GiftTier.STANDARD,
        emoji="🦋",
        description="Transformation symbol"
    ),
    "FAMILY": TikTokGift(
        name="Family",
        coins=90,
        tier=GiftTier.STANDARD,
        emoji="👨‍👩‍👧‍👦",
        description="Family love"
    ),
    "GUITAR": TikTokGift(
        name="Guitar",
        coins=99,
        tier=GiftTier.STANDARD,
        emoji="🎸",
        description="Musical talent"
    ),
    "PAPER_CRANE": TikTokGift(
        name="Paper Crane",
        coins=99,
        tier=GiftTier.STANDARD,
        emoji="🕊️",
        description="Peace and wishes"
    ),
    "CONFETTI": TikTokGift(
        name="Confetti",
        coins=100,
        tier=GiftTier.STANDARD,
        emoji="🎊",
        description="Celebration"
    ),

    # ===== PREMIUM TIER (100-499 coins) =====
    "LITTLE_CROWN": TikTokGift(
        name="Little Crown",
        coins=100,
        tier=GiftTier.PREMIUM,
        emoji="👑",
        description="Royalty lite"
    ),
    "CAP": TikTokGift(
        name="Cap",
        coins=100,
        tier=GiftTier.PREMIUM,
        emoji="🧢",
        description="Casual style"
    ),
    "GAME_CONTROLLER": TikTokGift(
        name="Game Controller",
        coins=100,
        tier=GiftTier.PREMIUM,
        emoji="🎮",
        description="Gamer culture"
    ),
    "HEART_RAIN": TikTokGift(
        name="Heart Rain",
        coins=149,
        tier=GiftTier.PREMIUM,
        emoji="💕",
        description="Hearts falling"
    ),
    "BOWKNOT": TikTokGift(
        name="Bowknot",
        coins=199,
        tier=GiftTier.PREMIUM,
        emoji="🎀",
        description="Gift wrapping"
    ),
    "MASQUERADE": TikTokGift(
        name="Masquerade",
        coins=200,
        tier=GiftTier.PREMIUM,
        emoji="🎭",
        description="Mystery and elegance"
    ),
    "PINCH_CHEEK": TikTokGift(
        name="Pinch Cheek",
        coins=250,
        tier=GiftTier.PREMIUM,
        emoji="😊",
        description="Cute affection"
    ),
    "CORGI": TikTokGift(
        name="Corgi",
        coins=299,
        tier=GiftTier.PREMIUM,
        emoji="🐕",
        description="Adorable dog"
    ),
    "BOXING_GLOVES": TikTokGift(
        name="Boxing Gloves",
        coins=300,
        tier=GiftTier.PREMIUM,
        emoji="🥊",
        description="Fighter spirit"
    ),
    "BACKING_MONKEY": TikTokGift(
        name="Backing Monkey",
        coins=349,
        tier=GiftTier.PREMIUM,
        emoji="🐵",
        description="Support"
    ),
    "BECOME_KITTEN": TikTokGift(
        name="Become Kitten",
        coins=400,
        tier=GiftTier.PREMIUM,
        emoji="🐱",
        description="Cute transformation"
    ),
    "MARKED_WITH_LOVE": TikTokGift(
        name="Marked with Love",
        coins=450,
        tier=GiftTier.PREMIUM,
        emoji="💋",
        description="Love mark"
    ),
    "MONEY_GUN": TikTokGift(
        name="Money Gun",
        coins=450,
        tier=GiftTier.PREMIUM,
        emoji="💵",
        description="Flex wealth"
    ),
    "DRAGON_CROWN": TikTokGift(
        name="Dragon Crown",
        coins=499,
        tier=GiftTier.PREMIUM,
        emoji="👑",
        description="Mythical royalty"
    ),
    "RACING_HELMET": TikTokGift(
        name="Racing Helmet",
        coins=499,
        tier=GiftTier.PREMIUM,
        emoji="🏎️",
        description="Speed demon"
    ),

    # ===== HIGH TIER (500-5,999 coins) =====
    "ROSES": TikTokGift(
        name="Roses",
        coins=500,
        tier=GiftTier.HIGH,
        emoji="🌹",
        description="Bouquet of roses"
    ),
    "SWAN": TikTokGift(
        name="Swan",
        coins=699,
        tier=GiftTier.HIGH,
        emoji="🦢",
        description="Grace and beauty"
    ),
    "THE_VAN_CAT": TikTokGift(
        name="The Van Cat",
        coins=799,
        tier=GiftTier.HIGH,
        emoji="🐱",
        description="Turkish van cat"
    ),
    "TRAIN": TikTokGift(
        name="Train",
        coins=899,
        tier=GiftTier.HIGH,
        emoji="🚂",
        description="Journey together"
    ),
    "SUPERSTAR": TikTokGift(
        name="Superstar",
        coins=900,
        tier=GiftTier.HIGH,
        emoji="⭐",
        description="Celebrity status"
    ),
    "DIAMOND_TREE": TikTokGift(
        name="Diamond Tree",
        coins=1088,
        tier=GiftTier.HIGH,
        emoji="💎",
        description="Prosperity"
    ),
    "GAMING_CHAIR": TikTokGift(
        name="Gaming Chair",
        coins=1200,
        tier=GiftTier.HIGH,
        emoji="🎮",
        description="Pro gamer setup"
    ),
    "WOLF": TikTokGift(
        name="Wolf",
        coins=5500,
        tier=GiftTier.HIGH,
        emoji="🐺",
        description="Wild and free"
    ),

    # ===== LUXURY TIER (6,000-24,999 coins) =====
    "DEVOTED_HEART": TikTokGift(
        name="Devoted Heart",
        coins=5999,
        tier=GiftTier.LUXURY,
        emoji="💝",
        description="Ultimate devotion"
    ),
    "FUTURE_CITY": TikTokGift(
        name="Future City",
        coins=6000,
        tier=GiftTier.LUXURY,
        emoji="🏙️",
        description="Futuristic vision"
    ),
    "CELEBRATION_TIME": TikTokGift(
        name="Celebration Time",
        coins=6999,
        tier=GiftTier.LUXURY,
        emoji="🎉",
        description="Party time"
    ),
    "SPORTS_CAR": TikTokGift(
        name="Sports Car",
        coins=7000,
        tier=GiftTier.LUXURY,
        emoji="🏎️",
        description="Luxury vehicle"
    ),
    "BIG_BEN": TikTokGift(
        name="Big Ben",
        coins=15000,
        tier=GiftTier.LUXURY,
        emoji="🕰️",
        description="Iconic landmark"
    ),

    # ===== ULTRA TIER (25,000+ coins) =====
    "PHOENIX": TikTokGift(
        name="Phoenix",
        coins=25999,
        tier=GiftTier.ULTRA,
        emoji="🔥🐦",
        description="Rise from ashes"
    ),
    "LION": TikTokGift(
        name="Lion",
        coins=29999,
        tier=GiftTier.ULTRA,
        emoji="🦁",
        description="King of the jungle"
    ),
    "TIKTOK_UNIVERSE": TikTokGift(
        name="TikTok Universe",
        coins=44999,
        tier=GiftTier.ULTRA,
        emoji="🌌",
        description="The ultimate TikTok gift"
    ),

    # ===== LIVE FEST 2025 BONUS GIFTS =====
    # These 4 gifts give 1.5x POINTS PER COIN (official TikTok LiveFest 2025)
    # Source: TikTok LiveFest 2025 creator briefing
    "FEST_POP": TikTokGift(
        name="Fest Pop",
        coins=1,
        tier=GiftTier.LIVE_FEST,
        emoji="🎪",
        description="1.5x points! Basic Live Fest gift (1 coin = 1.5 pts)"
    ),
    "FEST_GEAR": TikTokGift(
        name="Fest Gear",
        coins=99,
        tier=GiftTier.LIVE_FEST,
        emoji="😎",
        description="1.5x points! Cool sunglasses (99 coins = 148.5 pts)"
    ),
    "FEST_CHEERS": TikTokGift(
        name="Fest Cheers",
        coins=399,  # Corrected from 299!
        tier=GiftTier.LIVE_FEST,
        emoji="🎉",
        description="1.5x points! Premium fest gift (399 coins = 598.5 pts)"
    ),
    "FEST_PARTY": TikTokGift(
        name="Fest Party",
        coins=2999,
        tier=GiftTier.LIVE_FEST,
        emoji="🥳",
        description="1.5x points! Whale fest gift (2999 coins = 4498.5 pts)"
    ),

    # ===== VAULT GIFTS (Live Fest exclusive) =====
    # Also give 1.5x points per coin!
    # Only available during LiveFest - require unlocking
    "VAULT_GIFT": TikTokGift(
        name="Vault Gift",
        coins=5000,
        tier=GiftTier.LIVE_FEST,
        emoji="🔐",
        description="1.5x points! Exclusive LiveFest vault gift"
    ),

    # ===== VOTES (Free support) =====
    # Votes earned through challenges, calendar check-ins, etc.
    # Each vote = 1 point (no money required)
    "LIVE_FEST_VOTE": TikTokGift(
        name="Live Fest Vote",
        coins=0,  # FREE - earned through challenges
        tier=GiftTier.LIVE_FEST,
        emoji="🗳️",
        description="FREE vote = 1 point (earned via challenges/calendar)"
    ),
}


def get_gift(gift_key: str) -> TikTokGift:
    """Get a gift by key."""
    return TIKTOK_GIFTS_CATALOG.get(gift_key)


def get_gifts_by_tier(tier: GiftTier) -> List[TikTokGift]:
    """Get all gifts in a specific tier."""
    return [gift for gift in TIKTOK_GIFTS_CATALOG.values() if gift.tier == tier]


def get_affordable_gifts(max_coins: int) -> List[TikTokGift]:
    """Get all gifts affordable with given coins."""
    return [gift for gift in TIKTOK_GIFTS_CATALOG.values() if gift.coins <= max_coins]


def calculate_total_cost(gifts: Dict[str, int], coin_rate: float = 0.0133) -> Dict[str, float]:
    """
    Calculate total cost for a dictionary of gifts.

    Args:
        gifts: Dict mapping gift keys to quantities
        coin_rate: USD per coin rate

    Returns:
        Dict with 'coins', 'usd', and 'points' totals
    """
    total_coins = 0
    total_points = 0

    for gift_key, quantity in gifts.items():
        gift = get_gift(gift_key)
        if gift:
            total_coins += gift.coins * quantity
            total_points += gift.points * quantity

    return {
        'coins': total_coins,
        'usd': total_coins * coin_rate,
        'points': total_points
    }


# Coin packages (official TikTok pricing)
COIN_PACKAGES = {
    '65_coins': {'coins': 65, 'usd': 0.99, 'rate': 0.0152},
    '330_coins': {'coins': 330, 'usd': 4.99, 'rate': 0.0151},
    '660_coins': {'coins': 660, 'usd': 9.99, 'rate': 0.0151},
    '1320_coins': {'coins': 1320, 'usd': 19.99, 'rate': 0.0151},
    '3300_coins': {'coins': 3300, 'usd': 49.99, 'rate': 0.0151},
    '6600_coins': {'coins': 6600, 'usd': 99.99, 'rate': 0.0151},
    '16500_coins': {'coins': 16500, 'usd': 249.99, 'rate': 0.0151},
}


# Average coin rate for calculations
AVG_COIN_RATE = 0.0151  # ~$0.015 per coin


if __name__ == '__main__':
    # Demo usage
    print("TikTok Gifts Catalog")
    print("=" * 70)

    # Show basic gifts
    print("\nBASIC TIER (1 coin):")
    basic_gifts = get_gifts_by_tier(GiftTier.BASIC)
    for gift in basic_gifts[:5]:
        print(f"  {gift.emoji} {gift.name}: {gift.coins} coins = {gift.points} points")

    # Show ultra gifts
    print("\nULTRA TIER (25,000+ coins):")
    ultra_gifts = get_gifts_by_tier(GiftTier.ULTRA)
    for gift in ultra_gifts:
        print(f"  {gift.emoji} {gift.name}: {gift.coins:,} coins = {gift.points:,} points (${gift.usd_cost(AVG_COIN_RATE):.2f})")

    # Example calculation
    print("\nExample Battle Spending:")
    gifts_sent = {
        'ROSE': 50,
        'CORGI': 5,
        'LION': 1
    }
    cost = calculate_total_cost(gifts_sent, AVG_COIN_RATE)
    print(f"  50x Rose + 5x Corgi + 1x Lion")
    print(f"  Total: {cost['coins']:,} coins = ${cost['usd']:.2f} = {cost['points']:,} points")
