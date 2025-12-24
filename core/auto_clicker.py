"""
Auto-Clicker Module for TikTok Live Fest Battles
=================================================

Automated gift sending system for small gifts (1-coin balloons/Fest Pop).
Designed for sessions where only small gifts count and scores are doubled.

Features:
- Configurable click speed (clicks per second)
- Pre-defined batch sizes (10, 100, 1000, 10000)
- Custom quantity input
- Subscription tiers for access control
- Real-time progress tracking
- Safety limits and cooldowns
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger("AutoClicker")


class SubscriptionTier(Enum):
    """Subscription levels for auto-clicker access."""
    FREE = "free"           # Limited: 100 clicks/day, 1 CPS
    BASIC = "basic"         # 1000 clicks/day, 5 CPS
    PREMIUM = "premium"     # 10000 clicks/day, 10 CPS
    UNLIMITED = "unlimited" # No limits, 20 CPS max


@dataclass
class SubscriptionPlan:
    """Subscription plan details."""
    tier: SubscriptionTier
    name: str
    price_monthly: float  # USD
    daily_click_limit: int
    max_clicks_per_second: float
    batch_sizes_allowed: List[int]
    features: List[str]


# Available subscription plans
SUBSCRIPTION_PLANS: Dict[SubscriptionTier, SubscriptionPlan] = {
    SubscriptionTier.FREE: SubscriptionPlan(
        tier=SubscriptionTier.FREE,
        name="Free Trial",
        price_monthly=0.0,
        daily_click_limit=100,
        max_clicks_per_second=1.0,
        batch_sizes_allowed=[10],
        features=[
            "100 clicks/day",
            "1 click/second max",
            "Batch of 10 only",
        ]
    ),
    SubscriptionTier.BASIC: SubscriptionPlan(
        tier=SubscriptionTier.BASIC,
        name="Basic",
        price_monthly=9.99,
        daily_click_limit=1000,
        max_clicks_per_second=5.0,
        batch_sizes_allowed=[10, 100],
        features=[
            "1,000 clicks/day",
            "5 clicks/second max",
            "Batches: 10, 100",
            "Progress tracking",
        ]
    ),
    SubscriptionTier.PREMIUM: SubscriptionPlan(
        tier=SubscriptionTier.PREMIUM,
        name="Premium",
        price_monthly=29.99,
        daily_click_limit=10000,
        max_clicks_per_second=10.0,
        batch_sizes_allowed=[10, 100, 1000, 5000],
        features=[
            "10,000 clicks/day",
            "10 clicks/second max",
            "Batches: 10, 100, 1K, 5K",
            "Priority support",
            "Custom quantities",
        ]
    ),
    SubscriptionTier.UNLIMITED: SubscriptionPlan(
        tier=SubscriptionTier.UNLIMITED,
        name="Unlimited Pro",
        price_monthly=99.99,
        daily_click_limit=999999,  # Effectively unlimited
        max_clicks_per_second=20.0,
        batch_sizes_allowed=[10, 100, 1000, 5000, 10000, 50000],
        features=[
            "Unlimited clicks",
            "20 clicks/second max",
            "All batch sizes",
            "Custom quantities",
            "API access",
            "Multi-session support",
            "Priority queue",
        ]
    ),
}


# Pre-defined batch packages
BATCH_PACKAGES = {
    "micro": {"quantity": 10, "coins": 10, "estimated_time": "10s"},
    "small": {"quantity": 100, "coins": 100, "estimated_time": "20s"},
    "medium": {"quantity": 1000, "coins": 1000, "estimated_time": "2min"},
    "large": {"quantity": 5000, "coins": 5000, "estimated_time": "8min"},
    "mega": {"quantity": 10000, "coins": 10000, "estimated_time": "17min"},
    "ultra": {"quantity": 50000, "coins": 50000, "estimated_time": "42min"},
}


@dataclass
class ClickerSession:
    """Tracks a single auto-clicker session."""
    session_id: str
    user_id: str
    target_username: str
    gift_type: str  # "FEST_POP", "ROSE", etc.
    total_quantity: int
    clicks_sent: int = 0
    clicks_failed: int = 0
    points_generated: int = 0
    coins_spent: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "pending"  # pending, running, paused, completed, cancelled
    error_message: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_quantity == 0:
            return 0.0
        return (self.clicks_sent / self.total_quantity) * 100

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def clicks_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return self.clicks_sent / self.elapsed_seconds

    @property
    def remaining(self) -> int:
        return self.total_quantity - self.clicks_sent

    @property
    def eta_seconds(self) -> float:
        if self.clicks_per_second == 0:
            return float('inf')
        return self.remaining / self.clicks_per_second


@dataclass
class UserQuota:
    """Tracks user's daily usage."""
    user_id: str
    subscription: SubscriptionTier
    clicks_today: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    def reset_if_needed(self):
        """Reset daily counter if it's a new day."""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.clicks_today = 0
            self.last_reset = now

    @property
    def remaining_today(self) -> int:
        plan = SUBSCRIPTION_PLANS[self.subscription]
        return max(0, plan.daily_click_limit - self.clicks_today)

    def can_click(self, amount: int = 1) -> bool:
        self.reset_if_needed()
        return self.clicks_today + amount <= SUBSCRIPTION_PLANS[self.subscription].daily_click_limit


class AutoClicker:
    """
    Auto-clicker for sending small gifts in TikTok Live Fest battles.

    Usage:
        clicker = AutoClicker(user_id="donor123", subscription=SubscriptionTier.PREMIUM)

        # Using pre-defined batch
        session = await clicker.send_batch("medium", target="@streamer")

        # Using custom quantity
        session = await clicker.send_custom(quantity=2500, target="@streamer")
    """

    def __init__(
        self,
        user_id: str,
        subscription: SubscriptionTier = SubscriptionTier.FREE,
        gift_type: str = "FEST_POP",
        on_click: Optional[Callable[[int, int], None]] = None,
        on_progress: Optional[Callable[[ClickerSession], None]] = None,
    ):
        self.user_id = user_id
        self.subscription = subscription
        self.gift_type = gift_type
        self.quota = UserQuota(user_id=user_id, subscription=subscription)
        self.current_session: Optional[ClickerSession] = None
        self.session_history: List[ClickerSession] = []

        # Callbacks
        self._on_click = on_click
        self._on_progress = on_progress

        # Control flags
        self._running = False
        self._paused = False

        # Get plan limits
        self.plan = SUBSCRIPTION_PLANS[subscription]

    @property
    def clicks_per_second(self) -> float:
        """Get configured CPS based on subscription."""
        return self.plan.max_clicks_per_second

    def get_available_batches(self) -> Dict[str, dict]:
        """Get batch sizes available for current subscription."""
        available = {}
        for name, batch in BATCH_PACKAGES.items():
            if batch["quantity"] in self.plan.batch_sizes_allowed:
                available[name] = batch
        return available

    def validate_quantity(self, quantity: int) -> tuple[bool, str]:
        """Validate if quantity is allowed for current subscription."""
        # Check daily quota
        if not self.quota.can_click(quantity):
            remaining = self.quota.remaining_today
            return False, f"Daily limit exceeded. Remaining: {remaining:,} clicks"

        # Check if custom quantities are allowed
        if quantity not in [b["quantity"] for b in BATCH_PACKAGES.values()]:
            if self.subscription in [SubscriptionTier.FREE, SubscriptionTier.BASIC]:
                return False, "Custom quantities require Premium or Unlimited subscription"

        # Check max batch size
        max_allowed = max(self.plan.batch_sizes_allowed)
        if quantity > max_allowed:
            return False, f"Max batch size for {self.plan.name}: {max_allowed:,}"

        return True, "OK"

    async def send_batch(
        self,
        batch_name: str,
        target_username: str,
        multiplier: float = 1.0,
    ) -> ClickerSession:
        """Send a pre-defined batch of gifts."""
        if batch_name not in BATCH_PACKAGES:
            raise ValueError(f"Unknown batch: {batch_name}. Available: {list(BATCH_PACKAGES.keys())}")

        batch = BATCH_PACKAGES[batch_name]
        quantity = batch["quantity"]

        # Validate
        valid, msg = self.validate_quantity(quantity)
        if not valid:
            raise PermissionError(msg)

        return await self._execute_clicks(quantity, target_username, multiplier)

    async def send_custom(
        self,
        quantity: int,
        target_username: str,
        multiplier: float = 1.0,
    ) -> ClickerSession:
        """Send a custom quantity of gifts."""
        # Validate
        valid, msg = self.validate_quantity(quantity)
        if not valid:
            raise PermissionError(msg)

        return await self._execute_clicks(quantity, target_username, multiplier)

    async def _execute_clicks(
        self,
        quantity: int,
        target_username: str,
        multiplier: float,
    ) -> ClickerSession:
        """Execute the click sequence."""
        import uuid

        # Create session
        session = ClickerSession(
            session_id=str(uuid.uuid4())[:8],
            user_id=self.user_id,
            target_username=target_username,
            gift_type=self.gift_type,
            total_quantity=quantity,
            status="running",
        )
        self.current_session = session
        self._running = True
        self._paused = False

        # Calculate timing
        delay = 1.0 / self.clicks_per_second
        points_per_click = 1.5 * multiplier  # Fest Pop = 1 coin = 1.5 pts base

        logger.info(f"🖱️ AutoClicker started: {quantity:,} {self.gift_type} @ {self.clicks_per_second} CPS")

        try:
            for i in range(quantity):
                # Check controls
                if not self._running:
                    session.status = "cancelled"
                    break

                while self._paused:
                    await asyncio.sleep(0.1)
                    if not self._running:
                        break

                # Simulate click
                success = await self._simulate_click()

                if success:
                    session.clicks_sent += 1
                    session.coins_spent += 1
                    session.points_generated += int(points_per_click)
                    self.quota.clicks_today += 1
                else:
                    session.clicks_failed += 1

                # Callbacks
                if self._on_click:
                    self._on_click(session.clicks_sent, quantity)

                if self._on_progress and session.clicks_sent % 100 == 0:
                    self._on_progress(session)

                # Rate limiting
                await asyncio.sleep(delay)

            if session.status == "running":
                session.status = "completed"

        except Exception as e:
            session.status = "error"
            session.error_message = str(e)
            logger.error(f"AutoClicker error: {e}")

        finally:
            session.end_time = time.time()
            self._running = False
            self.session_history.append(session)
            self.current_session = None

        logger.info(f"🖱️ AutoClicker finished: {session.clicks_sent:,}/{quantity:,} sent, {session.points_generated:,} pts")
        return session

    async def _simulate_click(self) -> bool:
        """Simulate a gift click. Override for real implementation."""
        # In real implementation, this would call TikTok API
        # For simulation, 99.5% success rate
        import random
        return random.random() < 0.995

    def pause(self):
        """Pause the current session."""
        self._paused = True
        if self.current_session:
            self.current_session.status = "paused"
        logger.info("⏸️ AutoClicker paused")

    def resume(self):
        """Resume the current session."""
        self._paused = False
        if self.current_session:
            self.current_session.status = "running"
        logger.info("▶️ AutoClicker resumed")

    def stop(self):
        """Stop the current session."""
        self._running = False
        logger.info("⏹️ AutoClicker stopped")

    def get_status(self) -> dict:
        """Get current status."""
        session = self.current_session
        return {
            "running": self._running,
            "paused": self._paused,
            "subscription": self.plan.name,
            "daily_remaining": self.quota.remaining_today,
            "current_session": {
                "progress": f"{session.progress_percent:.1f}%",
                "sent": session.clicks_sent,
                "total": session.total_quantity,
                "cps": f"{session.clicks_per_second:.1f}",
                "eta": f"{session.eta_seconds:.0f}s",
            } if session else None,
        }


class AutoClickerUI:
    """Terminal UI for auto-clicker."""

    @staticmethod
    def display_subscription_plans():
        """Display available subscription plans."""
        print("\n" + "=" * 70)
        print("🖱️ AUTO-CLICKER SUBSCRIPTION PLANS")
        print("=" * 70)

        for tier, plan in SUBSCRIPTION_PLANS.items():
            print(f"\n┌{'─' * 68}┐")
            print(f"│ {'⭐ ' if tier == SubscriptionTier.PREMIUM else ''}{plan.name.upper():<64} │")
            print(f"├{'─' * 68}┤")
            print(f"│ {'Price:':<15} {'FREE' if plan.price_monthly == 0 else f'${plan.price_monthly:.2f}/month':<51} │")
            print(f"│ {'Daily Limit:':<15} {plan.daily_click_limit:,} clicks{' ' * (44 - len(f'{plan.daily_click_limit:,}'))} │")
            print(f"│ {'Speed:':<15} {plan.max_clicks_per_second:.0f} clicks/second{' ' * (42 - len(f'{plan.max_clicks_per_second:.0f}'))} │")
            print(f"│ {'Batches:':<15} {', '.join(f'{b:,}' for b in plan.batch_sizes_allowed):<51} │")
            print(f"├{'─' * 68}┤")
            for feature in plan.features:
                print(f"│   ✓ {feature:<62} │")
            print(f"└{'─' * 68}┘")

    @staticmethod
    def display_batch_packages(available_only: List[int] = None):
        """Display available batch packages."""
        print("\n" + "=" * 70)
        print("📦 BATCH PACKAGES")
        print("=" * 70)
        print(f"\n{'Package':<10} │ {'Quantity':>10} │ {'Coins':>10} │ {'Est. Time':>12} │ {'Available':>10}")
        print("-" * 70)

        for name, batch in BATCH_PACKAGES.items():
            available = "✓" if available_only is None or batch["quantity"] in available_only else "🔒"
            print(f"{name:<10} │ {batch['quantity']:>10,} │ {batch['coins']:>10,} │ {batch['estimated_time']:>12} │ {available:>10}")

    @staticmethod
    def display_session_progress(session: ClickerSession):
        """Display session progress bar."""
        width = 40
        filled = int(width * session.progress_percent / 100)
        bar = "█" * filled + "░" * (width - filled)

        print(f"\r  [{bar}] {session.progress_percent:>5.1f}% | "
              f"{session.clicks_sent:,}/{session.total_quantity:,} | "
              f"{session.clicks_per_second:.1f} CPS | "
              f"ETA: {session.eta_seconds:.0f}s", end="", flush=True)


# ============================================================
# DEMO / TEST
# ============================================================

async def demo_auto_clicker():
    """Demonstrate auto-clicker functionality."""
    print("\n" + "=" * 70)
    print("🖱️ AUTO-CLICKER DEMO")
    print("=" * 70)

    # Show subscription plans
    AutoClickerUI.display_subscription_plans()

    # Create clicker with Premium subscription
    clicker = AutoClicker(
        user_id="demo_user",
        subscription=SubscriptionTier.PREMIUM,
        gift_type="FEST_POP",
        on_progress=lambda s: AutoClickerUI.display_session_progress(s),
    )

    # Show available batches
    print("\n")
    AutoClickerUI.display_batch_packages(clicker.plan.batch_sizes_allowed)

    # Run a small demo batch
    print("\n\n🚀 Starting demo batch (100 clicks)...")
    print("-" * 70)

    session = await clicker.send_batch("small", target_username="@demo_streamer", multiplier=6.0)

    print(f"\n\n{'─' * 70}")
    print("📊 SESSION COMPLETE")
    print(f"{'─' * 70}")
    print(f"   Session ID: {session.session_id}")
    print(f"   Target: {session.target_username}")
    print(f"   Clicks: {session.clicks_sent:,} sent, {session.clicks_failed:,} failed")
    print(f"   Coins spent: {session.coins_spent:,}")
    print(f"   Points generated: {session.points_generated:,}")
    print(f"   Duration: {session.elapsed_seconds:.1f}s")
    print(f"   Average CPS: {session.clicks_per_second:.2f}")
    print(f"   Status: {session.status}")

    # Show remaining quota
    print(f"\n📈 Daily quota remaining: {clicker.quota.remaining_today:,} clicks")


if __name__ == "__main__":
    asyncio.run(demo_auto_clicker())
