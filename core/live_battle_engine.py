"""
Live Battle Engine - Real TikTok Integration

Extends the BattleEngine to support real TikTok Live streams.
Receives actual gift events and updates scores in real-time.

Features:
- Connect to two TikTok Live streams
- Real-time score updates from actual gifts
- Phase system integration (Boosts, Power-ups)
- Dashboard streaming support
- Hybrid mode: Real gifts + AI simulation

Usage:
    engine = LiveBattleEngine(
        creator_username="@creator1",
        opponent_username="@creator2",
        battle_duration=300
    )
    await engine.start_live_battle()
"""

import asyncio
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveBattleConnector,
    LiveGiftEvent,
    ConnectionStatus,
    TIKTOK_LIVE_AVAILABLE
)
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.event_bus import EventBus, EventType
from core.tiktok_gifts_catalog import TIKTOK_GIFTS_CATALOG

# Import leaderboard (optional - won't fail if not available)
try:
    from core.database import LeaderboardRepository
    LEADERBOARD_AVAILABLE = True
except ImportError:
    LEADERBOARD_AVAILABLE = False

logger = logging.getLogger("LiveBattleEngine")


class BattleMode(Enum):
    """Battle operation modes."""
    SIMULATION = "simulation"  # Pure AI simulation
    LIVE = "live"              # Pure TikTok Live
    HYBRID = "hybrid"          # Live + AI backup


@dataclass
class LiveBattleState:
    """Current state of a live battle."""
    mode: BattleMode
    creator_username: str
    opponent_username: str
    creator_score: int = 0
    opponent_score: int = 0
    creator_connected: bool = False
    opponent_connected: bool = False
    battle_started: bool = False
    battle_start_time: Optional[datetime] = None
    current_time: int = 0
    time_remaining: int = 0
    current_phase: str = "normal"
    current_multiplier: float = 1.0

    # Gift tracking
    creator_gifts: List[LiveGiftEvent] = field(default_factory=list)
    opponent_gifts: List[LiveGiftEvent] = field(default_factory=list)

    # Top gifters
    top_creator_gifters: Dict[str, int] = field(default_factory=dict)
    top_opponent_gifters: Dict[str, int] = field(default_factory=dict)

    # Gift counts per user (for leaderboard)
    gifter_gift_counts: Dict[str, int] = field(default_factory=dict)
    gifter_favorite_gifts: Dict[str, Dict[str, int]] = field(default_factory=dict)  # username -> {gift_name: count}


class LiveBattleEngine:
    """
    Battle engine with TikTok Live integration.

    Connects to actual TikTok Live streams and processes
    real gift events while managing phases and power-ups.
    """

    def __init__(
        self,
        creator_username: str,
        opponent_username: str,
        battle_duration: int = 300,
        mode: BattleMode = BattleMode.LIVE
    ):
        """
        Initialize live battle engine.

        Args:
            creator_username: TikTok username for creator team
            opponent_username: TikTok username for opponent team
            battle_duration: Battle duration in seconds
            mode: Battle mode (LIVE, SIMULATION, HYBRID)
        """
        self.creator_username = creator_username.lstrip("@")
        self.opponent_username = opponent_username.lstrip("@")
        self.battle_duration = battle_duration
        self.mode = mode

        # State
        self.state = LiveBattleState(
            mode=mode,
            creator_username=self.creator_username,
            opponent_username=self.opponent_username,
            time_remaining=battle_duration
        )

        # TikTok connectors
        self.creator_connector: Optional[TikTokLiveConnector] = None
        self.opponent_connector: Optional[TikTokLiveConnector] = None

        # Phase manager
        self.phase_manager = AdvancedPhaseManager(battle_duration=battle_duration)

        # Event bus for dashboard integration
        self.event_bus = EventBus()

        # Callbacks
        self._gift_callbacks: List[Callable] = []
        self._phase_callbacks: List[Callable] = []
        self._score_callbacks: List[Callable] = []
        self._end_callbacks: List[Callable] = []

        # Battle loop task
        self._battle_task: Optional[asyncio.Task] = None
        self._running = False

    def on_gift(self, callback: Callable[[LiveGiftEvent, int, int], Any]):
        """Register gift event callback."""
        self._gift_callbacks.append(callback)
        return self

    def on_phase_change(self, callback: Callable[[str, float], Any]):
        """Register phase change callback."""
        self._phase_callbacks.append(callback)
        return self

    def on_score_update(self, callback: Callable[[int, int], Any]):
        """Register score update callback."""
        self._score_callbacks.append(callback)
        return self

    def on_battle_end(self, callback: Callable[[str, Dict], Any]):
        """Register battle end callback."""
        self._end_callbacks.append(callback)
        return self

    async def _setup_connectors(self):
        """Setup TikTok Live connectors."""
        if not TIKTOK_LIVE_AVAILABLE:
            raise ImportError("TikTokLive not installed")

        self.creator_connector = TikTokLiveConnector(
            self.creator_username,
            team="creator"
        )
        self.opponent_connector = TikTokLiveConnector(
            self.opponent_username,
            team="opponent"
        )

        # Setup event handlers
        self.creator_connector.on_gift(self._on_creator_gift)
        self.creator_connector.on_connect(lambda uid: self._on_connect("creator", uid))
        self.creator_connector.on_disconnect(lambda uid: self._on_disconnect("creator", uid))

        self.opponent_connector.on_gift(self._on_opponent_gift)
        self.opponent_connector.on_connect(lambda uid: self._on_connect("opponent", uid))
        self.opponent_connector.on_disconnect(lambda uid: self._on_disconnect("opponent", uid))

    async def _on_creator_gift(self, gift_event: LiveGiftEvent):
        """Handle gift to creator."""
        # Apply current multiplier
        base_points = gift_event.total_points
        multiplier = self.state.current_multiplier
        effective_points = int(base_points * multiplier)

        # Update score
        self.state.creator_score += effective_points
        self.state.creator_gifts.append(gift_event)

        # Track top gifter
        username = gift_event.username
        if username not in self.state.top_creator_gifters:
            self.state.top_creator_gifters[username] = 0
        self.state.top_creator_gifters[username] += gift_event.total_coins

        # Track for leaderboard
        if username not in self.state.gifter_gift_counts:
            self.state.gifter_gift_counts[username] = 0
            self.state.gifter_favorite_gifts[username] = {}
        self.state.gifter_gift_counts[username] += gift_event.repeat_count
        gift_name = gift_event.gift_name
        if gift_name not in self.state.gifter_favorite_gifts[username]:
            self.state.gifter_favorite_gifts[username][gift_name] = 0
        self.state.gifter_favorite_gifts[username][gift_name] += gift_event.repeat_count

        # Log
        logger.info(
            f"[CREATOR] {gift_event.username}: {gift_event.gift_name} x{gift_event.repeat_count} "
            f"= {effective_points:,} pts (x{multiplier})"
        )

        # Emit callbacks
        await self._emit_gift(gift_event, effective_points)
        await self._emit_score_update()

        # Publish to event bus
        self.event_bus.publish(
            EventType.GIFT_SENT,
            {
                "team": "creator",
                "username": gift_event.username,
                "gift": gift_event.gift_name,
                "coins": gift_event.total_coins,
                "points": effective_points,
                "multiplier": multiplier
            }
        )

    async def _on_opponent_gift(self, gift_event: LiveGiftEvent):
        """Handle gift to opponent."""
        base_points = gift_event.total_points
        multiplier = self.state.current_multiplier
        effective_points = int(base_points * multiplier)

        self.state.opponent_score += effective_points
        self.state.opponent_gifts.append(gift_event)

        username = gift_event.username
        if username not in self.state.top_opponent_gifters:
            self.state.top_opponent_gifters[username] = 0
        self.state.top_opponent_gifters[username] += gift_event.total_coins

        # Track for leaderboard
        if username not in self.state.gifter_gift_counts:
            self.state.gifter_gift_counts[username] = 0
            self.state.gifter_favorite_gifts[username] = {}
        self.state.gifter_gift_counts[username] += gift_event.repeat_count
        gift_name = gift_event.gift_name
        if gift_name not in self.state.gifter_favorite_gifts[username]:
            self.state.gifter_favorite_gifts[username][gift_name] = 0
        self.state.gifter_favorite_gifts[username][gift_name] += gift_event.repeat_count

        logger.info(
            f"[OPPONENT] {gift_event.username}: {gift_event.gift_name} x{gift_event.repeat_count} "
            f"= {effective_points:,} pts (x{multiplier})"
        )

        await self._emit_gift(gift_event, effective_points)
        await self._emit_score_update()

        self.event_bus.publish(
            EventType.GIFT_SENT,
            {
                "team": "opponent",
                "username": gift_event.username,
                "gift": gift_event.gift_name,
                "coins": gift_event.total_coins,
                "points": effective_points,
                "multiplier": multiplier
            }
        )

    def _on_connect(self, team: str, unique_id: str):
        """Handle connection event."""
        if team == "creator":
            self.state.creator_connected = True
        else:
            self.state.opponent_connected = True

        logger.info(f"{team.upper()} connected: @{unique_id}")

        self.event_bus.publish(
            EventType.BATTLE_START,
            {"team": team, "username": unique_id, "status": "connected"}
        )

    def _on_disconnect(self, team: str, unique_id: str):
        """Handle disconnection event."""
        if team == "creator":
            self.state.creator_connected = False
        else:
            self.state.opponent_connected = False

        logger.warning(f"{team.upper()} disconnected: @{unique_id}")

    async def _emit_gift(self, gift_event: LiveGiftEvent, effective_points: int):
        """Emit gift event to callbacks."""
        for callback in self._gift_callbacks:
            try:
                result = callback(
                    gift_event,
                    self.state.creator_score,
                    self.state.opponent_score
                )
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Gift callback error: {e}")

    async def _emit_score_update(self):
        """Emit score update to callbacks."""
        for callback in self._score_callbacks:
            try:
                result = callback(
                    self.state.creator_score,
                    self.state.opponent_score
                )
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Score callback error: {e}")

    async def _emit_phase_change(self, phase: str, multiplier: float):
        """Emit phase change to callbacks."""
        for callback in self._phase_callbacks:
            try:
                result = callback(phase, multiplier)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Phase callback error: {e}")

    async def _battle_loop(self):
        """Main battle loop - updates time and phases."""
        self._running = True
        start_time = datetime.now()

        while self._running and self.state.time_remaining > 0:
            # Update current time
            elapsed = (datetime.now() - start_time).seconds
            self.state.current_time = elapsed
            self.state.time_remaining = max(0, self.battle_duration - elapsed)

            # Update phase manager
            self.phase_manager.update(elapsed)

            # Check for phase changes
            new_multiplier = self.phase_manager.get_current_multiplier()
            if new_multiplier != self.state.current_multiplier:
                old_multiplier = self.state.current_multiplier
                self.state.current_multiplier = new_multiplier

                # Determine phase name
                if self.phase_manager.boost1_active:
                    phase = "boost1"
                elif self.phase_manager.boost2_active:
                    phase = "boost2"
                elif self.phase_manager.active_glove_x5:
                    phase = "x5"
                elif self.state.time_remaining <= 30:
                    phase = "final_30s"
                elif self.state.time_remaining <= 5:
                    phase = "final_5s"
                else:
                    phase = "normal"

                self.state.current_phase = phase
                logger.info(f"Phase change: {phase} (x{new_multiplier})")

                await self._emit_phase_change(phase, new_multiplier)

                self.event_bus.publish(
                    EventType.PHASE_CHANGE,
                    {"phase": phase, "multiplier": new_multiplier}
                )

            # Wait 1 second
            await asyncio.sleep(1)

        # Battle ended
        self._running = False
        await self._end_battle()

    async def _end_battle(self):
        """End the battle and determine winner."""
        # Determine winner
        if self.state.creator_score > self.state.opponent_score:
            winner = "creator"
        elif self.state.opponent_score > self.state.creator_score:
            winner = "opponent"
        else:
            winner = "tie"

        # Build result
        result = {
            "winner": winner,
            "creator_score": self.state.creator_score,
            "opponent_score": self.state.opponent_score,
            "creator_username": self.creator_username,
            "opponent_username": self.opponent_username,
            "duration": self.battle_duration,
            "creator_gifts": len(self.state.creator_gifts),
            "opponent_gifts": len(self.state.opponent_gifts),
            "top_creator_gifters": dict(sorted(
                self.state.top_creator_gifters.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "top_opponent_gifters": dict(sorted(
                self.state.top_opponent_gifters.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
        }

        logger.info(f"\n{'='*60}")
        logger.info("BATTLE ENDED!")
        logger.info(f"Winner: {winner.upper()}")
        logger.info(f"@{self.creator_username}: {self.state.creator_score:,}")
        logger.info(f"@{self.opponent_username}: {self.state.opponent_score:,}")
        logger.info(f"{'='*60}\n")

        # Emit callbacks
        for callback in self._end_callbacks:
            try:
                cb_result = callback(winner, result)
                if asyncio.iscoroutine(cb_result):
                    await cb_result
            except Exception as e:
                logger.error(f"End callback error: {e}")

        # Publish event
        self.event_bus.publish(EventType.BATTLE_END, result)

        # Update gifter leaderboard
        if LEADERBOARD_AVAILABLE:
            try:
                # Combine creator and opponent gifters
                all_gifters = {}
                for username, coins in self.state.top_creator_gifters.items():
                    all_gifters[username] = coins
                for username, coins in self.state.top_opponent_gifters.items():
                    if username in all_gifters:
                        all_gifters[username] += coins
                    else:
                        all_gifters[username] = coins

                # Update each gifter in leaderboard
                for username, total_coins in all_gifters.items():
                    # Find favorite gift
                    favorite_gift = None
                    if username in self.state.gifter_favorite_gifts:
                        gifts = self.state.gifter_favorite_gifts[username]
                        if gifts:
                            favorite_gift = max(gifts.items(), key=lambda x: x[1])[0]

                    LeaderboardRepository.update_gifter_stats(
                        username=username,
                        gift_name=favorite_gift or "Gift",
                        coins=total_coins
                    )

                logger.info(f"Updated leaderboard for {len(all_gifters)} gifters")
            except Exception as e:
                logger.error(f"Failed to update gifter leaderboard: {e}")

        return result

    async def start_live_battle(self):
        """Start the live battle."""
        logger.info(f"\n{'='*60}")
        logger.info("LIVE BATTLE STARTING")
        logger.info(f"@{self.creator_username} vs @{self.opponent_username}")
        logger.info(f"Duration: {self.battle_duration}s")
        logger.info(f"{'='*60}\n")

        self.state.battle_started = True
        self.state.battle_start_time = datetime.now()

        # Setup connectors
        await self._setup_connectors()

        # Connect to both streams
        connect_tasks = []
        if self.creator_connector:
            connect_tasks.append(self.creator_connector.connect())
        if self.opponent_connector:
            connect_tasks.append(self.opponent_connector.connect())

        # Start battle loop
        self._battle_task = asyncio.create_task(self._battle_loop())

        # Wait for connections (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*connect_tasks, return_exceptions=True),
                timeout=30
            )
        except asyncio.TimeoutError:
            logger.warning("Connection timeout - some streams may not be live")

        # Wait for battle to complete
        if self._battle_task:
            await self._battle_task

    async def stop_battle(self):
        """Stop the battle early."""
        self._running = False

        if self.creator_connector:
            await self.creator_connector.disconnect()
        if self.opponent_connector:
            await self.opponent_connector.disconnect()

    def get_state(self) -> Dict:
        """Get current battle state as dict."""
        return {
            "mode": self.state.mode.value,
            "creator_username": self.state.creator_username,
            "opponent_username": self.state.opponent_username,
            "creator_score": self.state.creator_score,
            "opponent_score": self.state.opponent_score,
            "creator_connected": self.state.creator_connected,
            "opponent_connected": self.state.opponent_connected,
            "battle_started": self.state.battle_started,
            "current_time": self.state.current_time,
            "time_remaining": self.state.time_remaining,
            "current_phase": self.state.current_phase,
            "current_multiplier": self.state.current_multiplier,
            "leader": "creator" if self.state.creator_score > self.state.opponent_score else (
                "opponent" if self.state.opponent_score > self.state.creator_score else "tie"
            ),
            "gap": abs(self.state.creator_score - self.state.opponent_score),
        }


# Demo
if __name__ == "__main__":
    async def demo():
        print("=" * 60)
        print("LIVE BATTLE ENGINE DEMO")
        print("=" * 60)

        creator = input("Creator username: ").strip() or "test_creator"
        opponent = input("Opponent username: ").strip() or "test_opponent"
        duration = int(input("Duration (seconds, default 60): ") or "60")

        engine = LiveBattleEngine(
            creator_username=creator,
            opponent_username=opponent,
            battle_duration=duration
        )

        # Register callbacks
        def on_gift(event, creator_score, opponent_score):
            team = "" if event.team == "creator" else ""
            print(f"{team} {event.username}: {event.gift_name} x{event.repeat_count}")
            print(f"   Score: {creator_score:,} vs {opponent_score:,}")

        def on_phase(phase, multiplier):
            print(f"\n PHASE: {phase.upper()} (x{multiplier})\n")

        def on_end(winner, result):
            print(f"\n WINNER: {winner.upper()}")
            print(f"   Creator: {result['creator_score']:,}")
            print(f"   Opponent: {result['opponent_score']:,}")

        engine.on_gift(on_gift)
        engine.on_phase_change(on_phase)
        engine.on_battle_end(on_end)

        try:
            await engine.start_live_battle()
        except KeyboardInterrupt:
            print("\nStopping battle...")
            await engine.stop_battle()

    asyncio.run(demo())
