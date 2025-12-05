"""
Real TikTok Gift Catalog - Based on StreamToEarn data.

Provides gift selection, pricing, and tier management.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Gift:
    """Represents a TikTok gift."""
    name: str
    coins: int
    emoji: str
    tier: str = "budget"

    @property
    def points(self) -> int:
        """Gift value in battle points (1 coin = 1 point for simplicity)."""
        return self.coins

    def __repr__(self):
        return f"{self.emoji} {self.name} ({self.coins} coins)"


class GiftCatalog:
    """
    Manages the real TikTok gift catalog.

    Provides gift selection by budget, tier, and strategic needs.
    """

    def __init__(self, catalog_path: Optional[str] = None):
        """Initialize gift catalog from JSON file."""
        if catalog_path is None:
            catalog_path = Path(__file__).parent.parent / "data" / "tiktok_gifts.json"

        self.catalog_path = catalog_path
        self.gifts: List[Gift] = []
        self.gifts_by_tier: Dict[str, List[Gift]] = {}
        self.gifts_by_name: Dict[str, Gift] = {}

        self._load_catalog()

    def _load_catalog(self):
        """Load gifts from JSON file."""
        with open(self.catalog_path) as f:
            data = json.load(f)

        catalog = data["gift_catalog"]

        # Load all tiers
        for tier_name, tier_data in catalog.items():
            if tier_name == "special_objects":
                continue  # Handle separately

            tier_gifts = []
            for gift_data in tier_data["gifts"]:
                gift = Gift(
                    name=gift_data["name"],
                    coins=gift_data["coins"],
                    emoji=gift_data["emoji"],
                    tier=tier_name
                )
                tier_gifts.append(gift)
                self.gifts.append(gift)
                self.gifts_by_name[gift.name] = gift

            self.gifts_by_tier[tier_name] = tier_gifts

        # Sort gifts by cost
        self.gifts.sort(key=lambda g: g.coins)

    def get_gift(self, name: str) -> Optional[Gift]:
        """Get a specific gift by name."""
        return self.gifts_by_name.get(name)

    def get_gifts_by_tier(self, tier: str) -> List[Gift]:
        """Get all gifts in a specific tier."""
        return self.gifts_by_tier.get(tier, [])

    def get_gifts_in_budget(self, max_coins: int, min_coins: int = 0) -> List[Gift]:
        """Get all gifts within a budget range."""
        return [g for g in self.gifts if min_coins <= g.coins <= max_coins]

    def get_budget_gifts(self) -> List[Gift]:
        """Get budget tier gifts (1-99 coins)."""
        return self.get_gifts_by_tier("budget_tier")

    def get_premium_gifts(self) -> List[Gift]:
        """Get premium gifts (1000-9999 coins)."""
        return self.get_gifts_by_tier("premium_tier")

    def get_whale_gifts(self) -> List[Gift]:
        """Get ultra-premium whale gifts (10,000+ coins)."""
        return self.get_gifts_by_tier("ultra_premium_tier")

    def select_gift_for_budget(self, available_coins: int, strategy: str = "max") -> Optional[Gift]:
        """
        Select appropriate gift based on budget and strategy.

        Args:
            available_coins: Maximum coins available
            strategy: "max" (biggest possible), "min" (smallest), "mid" (middle range)

        Returns:
            Selected gift or None if no affordable gift
        """
        affordable = self.get_gifts_in_budget(available_coins)

        if not affordable:
            return None

        if strategy == "max":
            return max(affordable, key=lambda g: g.coins)
        elif strategy == "min":
            return min(affordable, key=lambda g: g.coins)
        elif strategy == "mid":
            # Get middle range gift
            mid_idx = len(affordable) // 2
            return affordable[mid_idx]
        else:
            return affordable[0]

    def get_signature_gift(self, agent_type: str) -> Optional[Gift]:
        """
        Get signature gift for specific agent types.

        Maps agent personalities to appropriate gifts.
        """
        signature_map = {
            # Existing agents
            "NovaWhale": "TikTok Universe",  # 44,999 coins
            "PixelPixie": "Rose",  # 1 coin
            "GlitchMancer": "Fireworks",  # 1,088 coins
            "ShadowPatron": "Galaxy",  # 1,000 coins
            "Dramatron": "Star of Red Carpet",  # 1,999 coins

            # New specialist agents
            "Kinetik": "TikTok Universe",  # Sniper uses biggest
            "StrikeMaster": "Lion",  # 29,999 coins for x5 combos
            "Activator": "Rose",  # Spam roses for threshold
            "Sentinel": "Galaxy",  # Solid defensive gift
        }

        gift_name = signature_map.get(agent_type)
        return self.get_gift(gift_name) if gift_name else None

    def list_all_gifts(self) -> str:
        """Get formatted list of all gifts."""
        output = []
        output.append("=" * 60)
        output.append("🎁 TIKTOK GIFT CATALOG")
        output.append("=" * 60)

        for tier_name, gifts in self.gifts_by_tier.items():
            tier_display = tier_name.replace("_", " ").title()
            output.append(f"\n{tier_display}:")
            output.append("-" * 60)

            for gift in sorted(gifts, key=lambda g: g.coins):
                output.append(f"  {gift}")

        output.append("\n" + "=" * 60)
        output.append(f"Total Gifts: {len(self.gifts)}")
        output.append(f"Price Range: {self.gifts[0].coins} - {self.gifts[-1].coins} coins")
        output.append("=" * 60)

        return "\n".join(output)


# Singleton instance for easy access
_catalog_instance = None

def get_gift_catalog() -> GiftCatalog:
    """Get singleton gift catalog instance."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = GiftCatalog()
    return _catalog_instance


if __name__ == "__main__":
    # Demo the catalog
    catalog = GiftCatalog()
    print(catalog.list_all_gifts())

    print("\n\n🔍 Testing Gift Selection:")
    print("-" * 60)

    # Test budget selection
    print("\n1. Budget of 100 coins (max strategy):")
    gift = catalog.select_gift_for_budget(100, "max")
    print(f"   Selected: {gift}")

    print("\n2. Budget of 2000 coins (max strategy):")
    gift = catalog.select_gift_for_budget(2000, "max")
    print(f"   Selected: {gift}")

    print("\n3. Signature gifts:")
    for agent in ["NovaWhale", "PixelPixie", "Kinetik", "StrikeMaster"]:
        gift = catalog.get_signature_gift(agent)
        print(f"   {agent}: {gift}")

    print("\n4. Whale gifts (10,000+ coins):")
    whale_gifts = catalog.get_whale_gifts()
    for gift in whale_gifts:
        print(f"   {gift}")
