#!/usr/bin/env python3
"""
TikTok Battle Platform - Unified Integration Module

Combines all battle components into a cohesive platform:
- AI Battle Controller (intelligent decision making)
- Gift Sender (automated gift delivery)
- Score Reader (real-time battle monitoring)
- Strategy Engine (multiple AI strategies)

This module is designed for TikTok Live Fest integration.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Callable, Any

from playwright.async_api import async_playwright, Page, BrowserContext

# Import platform components
from core.ai_battle_controller import (
    AIBattleController,
    AIConfig,
    AIStrategy,
    BattleScoreReader,
    BattleAI,
    BattleScore,
    BattleState,
    AIDecision
)
from core.gift_sender import TikTokGiftSender, GiftSendResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BattlePlatform")


class PlatformMode(Enum):
    """Platform operation modes."""
    OBSERVER = "observer"      # Watch and analyze only
    SUPPORTER = "supporter"    # AI-controlled gift sending
    MANUAL = "manual"          # Manual gift control via API
    HYBRID = "hybrid"          # AI + Manual override


@dataclass
class PlatformConfig:
    """Platform configuration."""
    mode: PlatformMode = PlatformMode.SUPPORTER
    target_streamer: str = ""

    # AI settings
    ai_strategy: AIStrategy = AIStrategy.SMART
    ai_enabled: bool = True

    # Gift settings
    default_gift: str = "Fest Pop"
    max_gifts_per_minute: int = 500
    max_total_budget: int = 10000  # Total gifts allowed

    # Speed settings
    normal_cps: float = 6.0
    fast_cps: float = 10.0
    turbo_cps: float = 12.0

    # Session
    session_path: str = "data/tiktok_session/state.json"
    headless: bool = False


@dataclass
class PlatformStats:
    """Platform statistics."""
    start_time: Optional[datetime] = None
    battles_monitored: int = 0
    gifts_sent: int = 0
    gifts_failed: int = 0
    decisions_made: int = 0
    total_points_contributed: int = 0
    wins: int = 0
    losses: int = 0

    # Current session
    current_streamer: Optional[str] = None
    current_score: Optional[BattleScore] = None
    current_state: BattleState = BattleState.UNKNOWN
    last_decision: Optional[AIDecision] = None

    def to_dict(self) -> Dict:
        """Convert stats to dictionary."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "battles_monitored": self.battles_monitored,
            "gifts_sent": self.gifts_sent,
            "gifts_failed": self.gifts_failed,
            "decisions_made": self.decisions_made,
            "total_points_contributed": self.total_points_contributed,
            "wins": self.wins,
            "losses": self.losses,
            "current_streamer": self.current_streamer,
            "current_score": {
                "our_score": self.current_score.our_score if self.current_score else 0,
                "opponent_score": self.current_score.opponent_score if self.current_score else 0,
                "gap": self.current_score.gap if self.current_score else 0,
                "time_remaining": self.current_score.time_remaining if self.current_score else 0,
            } if self.current_score else None,
            "current_state": self.current_state.value,
            "last_decision": {
                "should_send": self.last_decision.should_send,
                "gift_name": self.last_decision.gift_name,
                "quantity": self.last_decision.quantity,
                "urgency": self.last_decision.urgency,
                "reason": self.last_decision.reason,
            } if self.last_decision else None,
        }


class TikTokBattlePlatform:
    """
    Unified TikTok Battle Platform.

    Provides a complete solution for:
    - Real-time battle monitoring
    - AI-powered gift sending decisions
    - Manual gift control
    - Statistics and analytics
    """

    def __init__(self, config: PlatformConfig = None):
        self.config = config or PlatformConfig()
        self.stats = PlatformStats()

        # Browser components
        self._playwright = None
        self._browser = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Platform components
        self._gift_sender: Optional[TikTokGiftSender] = None
        self._score_reader: Optional[BattleScoreReader] = None
        self._ai: Optional[BattleAI] = None
        self._controller: Optional[AIBattleController] = None

        # State
        self._connected = False
        self._running = False
        self._paused = False

        # Callbacks
        self._on_score_update: List[Callable] = []
        self._on_decision: List[Callable] = []
        self._on_gift_sent: List[Callable] = []
        self._on_battle_end: List[Callable] = []

    # === Event Registration ===

    def on_score_update(self, callback: Callable[[BattleScore], Any]):
        """Register callback for score updates."""
        self._on_score_update.append(callback)
        return self

    def on_decision(self, callback: Callable[[AIDecision, BattleScore], Any]):
        """Register callback for AI decisions."""
        self._on_decision.append(callback)
        return self

    def on_gift_sent(self, callback: Callable[[GiftSendResult], Any]):
        """Register callback for gift sends."""
        self._on_gift_sent.append(callback)
        return self

    def on_battle_end(self, callback: Callable[[Dict], Any]):
        """Register callback for battle end."""
        self._on_battle_end.append(callback)
        return self

    # === Connection Management ===

    async def connect(self) -> bool:
        """Initialize browser and connect to TikTok."""
        if self._connected:
            return True

        try:
            logger.info("Initializing Battle Platform...")

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.headless,
                slow_mo=0
            )
            self._context = await self._browser.new_context(
                storage_state=self.config.session_path,
                viewport={"width": 1280, "height": 800}
            )
            self._page = await self._context.new_page()

            # Initialize components
            self._score_reader = BattleScoreReader(self._page)

            ai_config = AIConfig(
                strategy=self.config.ai_strategy,
                target_streamer=self.config.target_streamer,
                gift_name=self.config.default_gift,
                max_gifts_per_minute=self.config.max_gifts_per_minute,
                max_total_gifts=self.config.max_total_budget,
                normal_cps=self.config.normal_cps,
                fast_cps=self.config.fast_cps,
                turbo_cps=self.config.turbo_cps
            )
            self._ai = BattleAI(ai_config)

            # Create gift sender with shared browser
            self._gift_sender = TikTokGiftSender(self.config.session_path)
            self._gift_sender._playwright = self._playwright
            self._gift_sender._browser = self._browser
            self._gift_sender._context = self._context
            self._gift_sender._page = self._page
            self._gift_sender._is_connected = True

            self._connected = True
            self.stats.start_time = datetime.now()

            logger.info("Battle Platform connected!")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Close browser and save session."""
        if not self._connected:
            return

        self._running = False

        try:
            await self._context.storage_state(path=self.config.session_path)
            await self._browser.close()
            await self._playwright.stop()
        except Exception as e:
            logger.warning(f"Disconnect warning: {e}")

        self._connected = False
        logger.info("Battle Platform disconnected")

    async def go_to_stream(self, username: str) -> bool:
        """Navigate to a streamer's live."""
        if not self._connected:
            return False

        username = username.lstrip("@")
        self.config.target_streamer = username

        try:
            logger.info(f"Connecting to @{username}...")
            await self._page.goto(
                f"https://www.tiktok.com/@{username}/live",
                wait_until="domcontentloaded",
                timeout=30000
            )
            await asyncio.sleep(5)

            self.stats.current_streamer = username
            self._gift_sender._current_streamer = username

            logger.info(f"Connected to @{username}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to @{username}: {e}")
            return False

    # === Battle Operations ===

    async def read_score(self) -> BattleScore:
        """Read current battle score."""
        if not self._score_reader:
            return BattleScore()

        score = await self._score_reader.read_score()
        self.stats.current_score = score
        self.stats.current_state = await self._score_reader.detect_battle_state()

        # Emit callbacks
        for cb in self._on_score_update:
            try:
                result = cb(score)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Score callback error: {e}")

        return score

    async def get_ai_decision(self, score: BattleScore = None) -> AIDecision:
        """Get AI decision for current state."""
        if not self._ai:
            return AIDecision(should_send=False, reason="AI not initialized")

        if score is None:
            score = await self.read_score()

        state = await self._score_reader.detect_battle_state()
        decision = self._ai.decide(score, state)

        self.stats.decisions_made += 1
        self.stats.last_decision = decision

        # Emit callbacks
        for cb in self._on_decision:
            try:
                result = cb(decision, score)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Decision callback error: {e}")

        return decision

    async def send_gifts(
        self,
        gift_name: str = None,
        quantity: int = 10,
        cps: float = None
    ) -> GiftSendResult:
        """Send gifts to current streamer."""
        if not self._gift_sender or not self.stats.current_streamer:
            return GiftSendResult(
                success=False, sent=0, failed=0,
                gift_name=gift_name or self.config.default_gift,
                streamer="", cps=0,
                message="Not connected to stream"
            )

        gift_name = gift_name or self.config.default_gift
        cps = cps or self.config.normal_cps

        result = await self._gift_sender.send_gifts(
            username=self.stats.current_streamer,
            gift_name=gift_name,
            quantity=quantity,
            cps=cps
        )

        # Update stats
        self.stats.gifts_sent += result.sent
        self.stats.gifts_failed += result.failed
        if result.success:
            self._ai.record_send(result.sent)

        # Emit callbacks
        for cb in self._on_gift_sent:
            try:
                cb_result = cb(result)
                if asyncio.iscoroutine(cb_result):
                    await cb_result
            except Exception as e:
                logger.error(f"Gift callback error: {e}")

        return result

    async def run_observer(self, duration: int = 300) -> Dict:
        """
        Run in observer mode - monitor battles and show AI analysis without sending gifts.

        Args:
            duration: Maximum duration in seconds

        Returns:
            Battle statistics
        """
        if not self._connected:
            raise RuntimeError("Platform not connected")

        logger.info(f"""
{'='*60}
BATTLE PLATFORM - OBSERVER MODE
{'='*60}
Streamer: @{self.stats.current_streamer}
Strategy: {self.config.ai_strategy.value} (Analysis only)
Mode: OBSERVER (No gifts will be sent)
Duration: {duration}s
{'='*60}
        """)

        self._running = True
        self._paused = False
        start_time = datetime.now()
        last_battle_active = False

        while self._running:
            elapsed = (datetime.now() - start_time).seconds
            if elapsed >= duration:
                logger.info("Duration limit reached")
                break

            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                # Read score
                score = await self.read_score()
                state = self.stats.current_state

                # Track battle state changes
                if score.battle_active and not last_battle_active:
                    self.stats.battles_monitored += 1
                    logger.info("Battle detected!")
                elif not score.battle_active and last_battle_active:
                    # Battle ended
                    if score.is_winning:
                        self.stats.wins += 1
                    else:
                        self.stats.losses += 1

                    # Emit battle end
                    for cb in self._on_battle_end:
                        try:
                            cb({"winner": "us" if score.is_winning else "them", "score": score})
                        except:
                            pass

                last_battle_active = score.battle_active

                # Get AI decision (for analysis only - no sending)
                decision = await self.get_ai_decision(score)

                # Log what the AI WOULD do
                action = "WOULD SEND" if decision.should_send else "WAIT"
                logger.info(
                    f"[{state.value}] Score: {score.our_score:,} vs {score.opponent_score:,} | "
                    f"Gap: {score.gap:+,} | AI: {action} - {decision.reason}"
                )

                # Emit callbacks
                for cb in self._on_decision:
                    try:
                        result = cb(decision, score)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"Decision callback error: {e}")

                # Wait interval
                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Observer loop error: {e}")
                await asyncio.sleep(5)

        self._running = False

        # Final stats
        total_time = (datetime.now() - start_time).seconds
        logger.info(f"""
{'='*60}
OBSERVER MODE ENDED
{'='*60}
Duration: {total_time}s
Battles observed: {self.stats.battles_monitored}
Decisions analyzed: {self.stats.decisions_made}
(No gifts were sent - Observer mode)
{'='*60}
        """)

        return self.stats.to_dict()

    async def run_ai_battle(self, duration: int = 300) -> Dict:
        """
        Run AI-controlled battle support.

        Args:
            duration: Maximum duration in seconds

        Returns:
            Battle result statistics
        """
        if not self._connected:
            raise RuntimeError("Platform not connected")

        # If in observer mode, run observer instead
        if self.config.mode == PlatformMode.OBSERVER:
            return await self.run_observer(duration)

        logger.info(f"""
{'='*60}
BATTLE PLATFORM - AI SUPPORT ACTIVE
{'='*60}
Streamer: @{self.stats.current_streamer}
Strategy: {self.config.ai_strategy.value}
Mode: {self.config.mode.value}
Duration: {duration}s
{'='*60}
        """)

        self._running = True
        self._paused = False
        start_time = datetime.now()
        last_battle_active = False

        while self._running:
            elapsed = (datetime.now() - start_time).seconds
            if elapsed >= duration:
                logger.info("Duration limit reached")
                break

            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                # Read score
                score = await self.read_score()
                state = self.stats.current_state

                # Track battle state changes
                if score.battle_active and not last_battle_active:
                    self.stats.battles_monitored += 1
                    logger.info("Battle started!")
                elif not score.battle_active and last_battle_active:
                    # Battle ended
                    if score.is_winning:
                        self.stats.wins += 1
                    else:
                        self.stats.losses += 1

                    # Emit battle end
                    for cb in self._on_battle_end:
                        try:
                            cb({"winner": "us" if score.is_winning else "them", "score": score})
                        except:
                            pass

                last_battle_active = score.battle_active

                # AI decision
                if self.config.ai_enabled and self.config.mode in [PlatformMode.SUPPORTER, PlatformMode.HYBRID]:
                    decision = await self.get_ai_decision(score)

                    if decision.should_send:
                        logger.info(f"[{state.value}] Gap: {score.gap:+,} | {decision.reason}")

                        result = await self.send_gifts(
                            gift_name=decision.gift_name,
                            quantity=decision.quantity,
                            cps=decision.cps
                        )

                        if result.success:
                            logger.info(f"Sent {result.sent} {decision.gift_name}")

                # Wait interval based on urgency
                wait_time = 2.0 if self.stats.last_decision and self.stats.last_decision.urgency == "critical" else 5.0
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Battle loop error: {e}")
                await asyncio.sleep(5)

        self._running = False

        # Final stats
        total_time = (datetime.now() - start_time).seconds
        logger.info(f"""
{'='*60}
BATTLE SUPPORT ENDED
{'='*60}
Duration: {total_time}s
Gifts sent: {self.stats.gifts_sent:,}
Decisions: {self.stats.decisions_made}
Battles: {self.stats.battles_monitored}
{'='*60}
        """)

        return self.stats.to_dict()

    # === Control Methods ===

    def pause(self):
        """Pause AI operations."""
        self._paused = True
        logger.info("Platform paused")

    def resume(self):
        """Resume AI operations."""
        self._paused = False
        logger.info("Platform resumed")

    def stop(self):
        """Stop platform operations."""
        self._running = False
        logger.info("Platform stopping...")

    def set_strategy(self, strategy: AIStrategy):
        """Change AI strategy."""
        self.config.ai_strategy = strategy
        if self._ai:
            self._ai.config.strategy = strategy
        logger.info(f"Strategy changed to: {strategy.value}")

    def set_gift(self, gift_name: str):
        """Change default gift."""
        self.config.default_gift = gift_name
        if self._ai:
            self._ai.config.gift_name = gift_name
        logger.info(f"Default gift changed to: {gift_name}")

    def get_stats(self) -> Dict:
        """Get current statistics."""
        return self.stats.to_dict()

    def is_running(self) -> bool:
        """Check if platform is running."""
        return self._running

    def is_connected(self) -> bool:
        """Check if platform is connected."""
        return self._connected


# === Convenience Functions ===

async def quick_support(
    username: str,
    strategy: str = "smart",
    duration: int = 300,
    gift: str = "Fest Pop"
) -> Dict:
    """
    Quick start battle support.

    Args:
        username: Target streamer
        strategy: AI strategy (smart, aggressive, defensive, sniper, conservative)
        duration: Support duration in seconds
        gift: Gift to send

    Returns:
        Battle statistics
    """
    try:
        strat = AIStrategy(strategy.lower())
    except:
        strat = AIStrategy.SMART

    config = PlatformConfig(
        mode=PlatformMode.SUPPORTER,
        target_streamer=username,
        ai_strategy=strat,
        default_gift=gift
    )

    platform = TikTokBattlePlatform(config)

    try:
        await platform.connect()
        await platform.go_to_stream(username)
        return await platform.run_ai_battle(duration)
    finally:
        await platform.disconnect()


async def quick_observe(
    username: str,
    strategy: str = "smart",
    duration: int = 300
) -> Dict:
    """
    Quick start battle observation with AI analysis (no gift sending).

    Args:
        username: Target streamer
        strategy: AI strategy to use for analysis
        duration: Observation duration in seconds

    Returns:
        Battle statistics
    """
    try:
        strat = AIStrategy(strategy.lower())
    except:
        strat = AIStrategy.SMART

    config = PlatformConfig(
        mode=PlatformMode.OBSERVER,
        target_streamer=username,
        ai_strategy=strat,
        ai_enabled=True  # Enable AI for analysis
    )

    platform = TikTokBattlePlatform(config)

    try:
        await platform.connect()
        await platform.go_to_stream(username)
        return await platform.run_observer(duration)
    finally:
        await platform.disconnect()


# === Main Entry Point ===

if __name__ == "__main__":
    import sys
    import argparse

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║   TIKTOK BATTLE PLATFORM                                             ║
║   Unified AI-Powered Battle Support System                           ║
╠══════════════════════════════════════════════════════════════════════╣
║   Features:                                                          ║
║   - Real-time score monitoring                                       ║
║   - AI-powered decision making                                       ║
║   - Automated gift sending                                           ║
║   - Multiple strategies (smart, aggressive, defensive, sniper)       ║
║   - Observer mode (analysis without sending)                         ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    parser = argparse.ArgumentParser(description="TikTok Battle Platform")
    parser.add_argument("username", help="Target streamer username")
    parser.add_argument("strategy", nargs="?", default="smart",
                       choices=["aggressive", "defensive", "sniper", "smart", "conservative"],
                       help="AI strategy (default: smart)")
    parser.add_argument("-d", "--duration", type=int, default=300,
                       help="Duration in seconds (default: 300)")
    parser.add_argument("-o", "--observer", action="store_true",
                       help="Observer mode - analyze without sending gifts")
    parser.add_argument("-g", "--gift", default="Fest Pop",
                       help="Gift to send (default: Fest Pop)")

    args = parser.parse_args()

    if args.observer:
        print(f"\n>>> OBSERVER MODE - No gifts will be sent <<<\n")
        asyncio.run(quick_observe(args.username, args.strategy, args.duration))
    else:
        asyncio.run(quick_support(args.username, args.strategy, args.duration, args.gift))
