"""
TikTok Live Connector - Real-Time Gift Integration

Connects to TikTok Live streams using the TikTokLive library
and integrates gift events with the battle simulation engine.

Features:
- Connect to any TikTok Live stream by username
- Receive real-time gift events
- Map TikTok gifts to our catalog
- Track gift streaks and repeat counts
- Battle mode: Two streams competing in real-time

Sources:
- TikTokLive Library: https://github.com/isaackogan/TikTokLive
- PyPI: https://pypi.org/project/TikTokLive/
"""

import asyncio
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

# TikTokLive imports
try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import (
        ConnectEvent,
        DisconnectEvent,
        GiftEvent,
        CommentEvent,
        LikeEvent,
        ShareEvent,
        FollowEvent,
        JoinEvent,
    )
    from TikTokLive.client.web.web_settings import WebDefaults
    TIKTOK_LIVE_AVAILABLE = True

    # Configure EulerStream API key to bypass rate limits
    try:
        from config.eulerstream import EULERSTREAM_API_KEY
        if EULERSTREAM_API_KEY:
            WebDefaults.tiktok_sign_api_key = EULERSTREAM_API_KEY
    except ImportError:
        pass  # No API key configured

except ImportError:
    TIKTOK_LIVE_AVAILABLE = False
    print("WARNING: TikTokLive not installed. Run: pip install TikTokLive")

    # Define dummy classes for type hints when TikTokLive is not installed
    class GiftEvent: pass
    class ConnectEvent: pass
    class DisconnectEvent: pass
    class CommentEvent: pass
    class LikeEvent: pass
    class ShareEvent: pass
    class FollowEvent: pass
    class JoinEvent: pass
    TikTokLiveClient = None

# Local imports
from core.tiktok_gifts_catalog import TIKTOK_GIFTS_CATALOG, TikTokGift, GiftTier


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TikTokLiveConnector")


class ConnectionStatus(Enum):
    """Connection status states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class LiveGiftEvent:
    """Processed gift event from TikTok Live."""
    timestamp: datetime
    username: str
    user_id: str
    gift_name: str
    gift_id: int
    coin_value: int
    repeat_count: int
    repeat_end: bool
    streak_id: str
    team: str  # "creator" or "opponent" in battle mode

    @property
    def total_coins(self) -> int:
        """Total coins for this gift (including repeat count)."""
        return self.coin_value * self.repeat_count

    @property
    def total_points(self) -> int:
        """Battle points equal total coins (TikTok official: 1 coin = 1 point)."""
        return self.total_coins


@dataclass
class StreamStats:
    """Statistics for a connected stream."""
    unique_id: str
    connected_at: Optional[datetime] = None
    total_gifts: int = 0
    total_coins: int = 0
    total_points: int = 0
    unique_gifters: set = field(default_factory=set)
    gift_breakdown: Dict[str, int] = field(default_factory=dict)
    viewer_count: int = 0
    likes_count: int = 0
    shares_count: int = 0

    def add_gift(self, gift_event: LiveGiftEvent):
        """Record a gift event."""
        self.total_gifts += gift_event.repeat_count
        self.total_coins += gift_event.total_coins
        self.total_points += gift_event.total_points
        self.unique_gifters.add(gift_event.username)

        gift_name = gift_event.gift_name
        if gift_name not in self.gift_breakdown:
            self.gift_breakdown[gift_name] = 0
        self.gift_breakdown[gift_name] += gift_event.repeat_count


class TikTokLiveConnector:
    """
    Connects to TikTok Live streams and receives real-time events.

    Usage:
        connector = TikTokLiveConnector("@username")
        connector.on_gift(my_gift_handler)
        await connector.connect()
    """

    def __init__(self, unique_id: str, team: str = "creator"):
        """
        Initialize connector for a TikTok user.

        Args:
            unique_id: TikTok username (with or without @)
            team: Team identifier for battle mode ("creator" or "opponent")
        """
        if not TIKTOK_LIVE_AVAILABLE:
            raise ImportError("TikTokLive library not installed. Run: pip install TikTokLive")

        # Normalize username
        self.unique_id = unique_id.lstrip("@")
        self.team = team

        # Client
        self.client: Optional[TikTokLiveClient] = None
        self.status = ConnectionStatus.DISCONNECTED

        # Statistics
        self.stats = StreamStats(unique_id=self.unique_id)

        # Event callbacks
        self._gift_callbacks: List[Callable[[LiveGiftEvent], Any]] = []
        self._connect_callbacks: List[Callable[[str], Any]] = []
        self._disconnect_callbacks: List[Callable[[str], Any]] = []
        self._comment_callbacks: List[Callable[[str, str], Any]] = []

        # Gift streak tracking
        self._active_streaks: Dict[str, LiveGiftEvent] = {}

        # Gift name mapping (TikTok internal names to our catalog)
        self._gift_name_map = self._build_gift_name_map()

        # Background connection management
        self._connection_task: Optional[asyncio.Task] = None
        self._should_reconnect = True
        self._first_connect_event = asyncio.Event()
        self._ever_connected = False

    def _build_gift_name_map(self) -> Dict[str, str]:
        """Build mapping from TikTok gift names to our catalog keys."""
        mapping = {}
        for key, gift in TIKTOK_GIFTS_CATALOG.items():
            # Map various name formats
            mapping[gift.name.lower()] = key
            mapping[gift.name.lower().replace(" ", "_")] = key
            mapping[gift.name.lower().replace(" ", "")] = key
            mapping[key.lower()] = key
        return mapping

    def _normalize_gift_name(self, tiktok_name: str) -> str:
        """Convert TikTok gift name to our catalog key."""
        normalized = tiktok_name.lower().strip()

        # Direct match
        if normalized in self._gift_name_map:
            return self._gift_name_map[normalized]

        # Try without spaces
        no_spaces = normalized.replace(" ", "")
        if no_spaces in self._gift_name_map:
            return self._gift_name_map[no_spaces]

        # Try with underscores
        with_underscores = normalized.replace(" ", "_")
        if with_underscores in self._gift_name_map:
            return self._gift_name_map[with_underscores]

        # Return original if no match (will use raw coin value)
        return tiktok_name.upper().replace(" ", "_")

    def on_gift(self, callback: Callable[[LiveGiftEvent], Any]):
        """Register a callback for gift events."""
        self._gift_callbacks.append(callback)
        return self

    def on_connect(self, callback: Callable[[str], Any]):
        """Register a callback for connect events."""
        self._connect_callbacks.append(callback)
        return self

    def on_disconnect(self, callback: Callable[[str], Any]):
        """Register a callback for disconnect events."""
        self._disconnect_callbacks.append(callback)
        return self

    def on_comment(self, callback: Callable[[str, str], Any]):
        """Register a callback for comment events (username, comment)."""
        self._comment_callbacks.append(callback)
        return self

    async def connect(self, auto_reconnect: bool = True, reconnect_delay: int = 5, max_retries: int = 3):
        """
        Connect to the TikTok Live stream (blocking).

        Args:
            auto_reconnect: Automatically reconnect if disconnected
            reconnect_delay: Seconds to wait before reconnecting
            max_retries: Maximum connection attempts before giving up
        """
        if self.status == ConnectionStatus.CONNECTED:
            logger.warning(f"Already connected to @{self.unique_id}")
            return

        self.status = ConnectionStatus.CONNECTING
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay
        self._should_reconnect = auto_reconnect

        retry_count = 0
        current_delay = reconnect_delay

        while retry_count < max_retries and self._should_reconnect:
            try:
                logger.info(f"Connecting to @{self.unique_id}... (attempt {retry_count + 1}/{max_retries})")
                self.client = TikTokLiveClient(unique_id=self.unique_id)
                self._setup_event_handlers()

                # Run the client (blocks until disconnected)
                await self.client.start()

                # If we get here normally, connection succeeded then disconnected
                retry_count = 0  # Reset on successful connection
                current_delay = reconnect_delay

                if not self._should_reconnect:
                    break

                logger.info(f"Stream ended. Reconnecting in {current_delay}s...")
                self.status = ConnectionStatus.RECONNECTING
                await asyncio.sleep(current_delay)

            except Exception as e:
                self.status = ConnectionStatus.ERROR
                error_msg = str(e)
                retry_count += 1

                # Handle rate limiting specifically
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning(f"Rate limited. Waiting {current_delay * 2}s before retry...")
                    current_delay = min(current_delay * 2, 60)  # Exponential backoff, max 60s
                    await asyncio.sleep(current_delay)
                    continue

                # Handle offline stream
                elif "not live" in error_msg.lower() or "offline" in error_msg.lower():
                    logger.warning(f"@{self.unique_id} is not live.")
                    if not self._should_reconnect:
                        raise RuntimeError(f"@{self.unique_id} is not currently live")
                    logger.info(f"Waiting {current_delay}s before retry...")
                    await asyncio.sleep(current_delay)
                    continue

                else:
                    logger.error(f"Connection error: {e}")

                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) reached. Giving up.")
                    raise RuntimeError(f"Failed to connect after {max_retries} attempts: {e}")

                if not self._should_reconnect:
                    raise

                await asyncio.sleep(current_delay)

        if retry_count >= max_retries:
            raise RuntimeError(f"Failed to connect to @{self.unique_id} after {max_retries} attempts")

    async def connect_background(self, timeout: float = 15.0) -> bool:
        """
        Start connection in background and wait for first successful connect.

        This method starts the connection loop in a background task, allowing
        the caller to continue with other operations while staying connected.

        Args:
            timeout: Max seconds to wait for initial connection

        Returns:
            True if connected within timeout, False otherwise
        """
        if self._connection_task and not self._connection_task.done():
            logger.warning(f"Connection already running for @{self.unique_id}")
            return self._ever_connected

        # Reset state
        self._first_connect_event.clear()
        self._should_reconnect = True
        self._ever_connected = False

        # Start connection in background
        self._connection_task = asyncio.create_task(
            self._connection_loop()
        )

        # Wait for first connection with timeout
        try:
            await asyncio.wait_for(
                self._first_connect_event.wait(),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Connection to @{self.unique_id} timed out after {timeout}s")
            # Keep trying in background - battle can start anyway
            return False

    async def _connection_loop(self):
        """Background connection loop with auto-reconnect."""
        reconnect_delay = 3
        consecutive_failures = 0
        max_consecutive_failures = 10

        while self._should_reconnect:
            try:
                logger.info(f"🔌 Connecting to @{self.unique_id}...")
                self.status = ConnectionStatus.CONNECTING

                self.client = TikTokLiveClient(unique_id=self.unique_id)
                self._setup_event_handlers()

                # Run client - blocks until disconnected
                await self.client.start()

                # Connection ended normally (stream ended)
                consecutive_failures = 0
                reconnect_delay = 3

                if not self._should_reconnect:
                    break

                # Brief delay before reconnecting
                self.status = ConnectionStatus.RECONNECTING
                logger.info(f"🔄 Stream paused. Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)

            except asyncio.CancelledError:
                logger.info(f"Connection cancelled for @{self.unique_id}")
                break

            except Exception as e:
                consecutive_failures += 1
                error_msg = str(e).lower()
                self.status = ConnectionStatus.ERROR

                # Handle specific errors
                if "rate_limit" in error_msg or "429" in error_msg:
                    wait_time = min(reconnect_delay * 2, 30)
                    logger.warning(f"⚠️ Rate limited. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    reconnect_delay = wait_time

                elif "not live" in error_msg or "offline" in error_msg:
                    logger.warning(f"⚠️ @{self.unique_id} is not live")
                    if not self._should_reconnect:
                        break
                    await asyncio.sleep(reconnect_delay)

                else:
                    logger.error(f"❌ Connection error: {e}")
                    await asyncio.sleep(reconnect_delay)

                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"❌ Too many failures. Stopping reconnection.")
                    break

        self.status = ConnectionStatus.DISCONNECTED
        logger.info(f"🔌 Connection loop ended for @{self.unique_id}")

    def _setup_event_handlers(self):
        """Setup TikTokLive event handlers."""

        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.status = ConnectionStatus.CONNECTED
            self.stats.connected_at = datetime.now()
            logger.info(f"✅ Connected to @{self.unique_id} (Room ID: {event.room_id})")

            # Signal first connection for background mode
            if not self._ever_connected:
                self._ever_connected = True
                self._first_connect_event.set()

            for callback in self._connect_callbacks:
                try:
                    result = callback(self.unique_id)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Connect callback error: {e}")

        @self.client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            self.status = ConnectionStatus.DISCONNECTED
            logger.info(f"Disconnected from @{self.unique_id}")

            for callback in self._disconnect_callbacks:
                try:
                    result = callback(self.unique_id)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Disconnect callback error: {e}")

        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            await self._handle_gift_event(event)

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            username = event.user.nickname if event.user else "Unknown"
            comment = event.comment

            for callback in self._comment_callbacks:
                try:
                    result = callback(username, comment)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Comment callback error: {e}")

        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            self.stats.likes_count += event.count if hasattr(event, 'count') else 1

        @self.client.on(ShareEvent)
        async def on_share(event: ShareEvent):
            self.stats.shares_count += 1

    async def _handle_gift_event(self, event: GiftEvent):
        """Process a gift event from TikTok."""
        try:
            # Extract gift info
            gift = event.gift
            user = event.user

            # Get user ID - handle different TikTokLive versions
            user_id = "0"
            if user:
                if hasattr(user, 'user_id'):
                    user_id = str(user.user_id)
                elif hasattr(user, 'id'):
                    user_id = str(user.id)
                elif hasattr(user, 'unique_id'):
                    user_id = str(user.unique_id)

            # Get gift coin value - handle different attribute names
            coin_value = 0
            if gift:
                if hasattr(gift, 'diamond_count'):
                    coin_value = gift.diamond_count
                elif hasattr(gift, 'diamonds'):
                    coin_value = gift.diamonds
                elif hasattr(gift, 'coin_count'):
                    coin_value = gift.coin_count

            # Create our gift event
            gift_event = LiveGiftEvent(
                timestamp=datetime.now(),
                username=user.nickname if user else "Anonymous",
                user_id=user_id,
                gift_name=gift.name if gift else "Unknown",
                gift_id=gift.id if gift else 0,
                coin_value=coin_value,
                repeat_count=event.repeat_count if hasattr(event, 'repeat_count') else 1,
                repeat_end=event.repeat_end if hasattr(event, 'repeat_end') else True,
                streak_id=f"{user_id}_{gift.id}" if gift else "",
                team=self.team
            )

            # Handle gift streaks
            if not gift_event.repeat_end:
                # Streak in progress - update tracking
                self._active_streaks[gift_event.streak_id] = gift_event
                return  # Don't emit until streak ends
            else:
                # Streak ended or single gift
                if gift_event.streak_id in self._active_streaks:
                    del self._active_streaks[gift_event.streak_id]

            # Update stats
            self.stats.add_gift(gift_event)

            # Log the gift
            catalog_key = self._normalize_gift_name(gift_event.gift_name)
            logger.info(
                f"GIFT from {gift_event.username}: "
                f"{gift_event.gift_name} x{gift_event.repeat_count} "
                f"({gift_event.total_coins} coins, {gift_event.total_points} pts)"
            )

            # Call registered callbacks
            for callback in self._gift_callbacks:
                try:
                    result = callback(gift_event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Gift callback error: {e}")

        except Exception as e:
            logger.error(f"Error handling gift event: {e}")

    async def disconnect(self):
        """Disconnect from the stream."""
        # Stop reconnection loop
        self._should_reconnect = False

        # Cancel background connection task
        if self._connection_task and not self._connection_task.done():
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass

        if self.client:
            try:
                # Try different disconnect methods for different TikTokLive versions
                if hasattr(self.client, 'stop'):
                    await self.client.stop()
                elif hasattr(self.client, 'disconnect'):
                    await self.client.disconnect()
                elif hasattr(self.client, 'close'):
                    await self.client.close()
            except Exception as e:
                logger.debug(f"Disconnect method error (non-critical): {e}")

        self.status = ConnectionStatus.DISCONNECTED
        logger.info(f"🔌 Disconnected from @{self.unique_id}")

    def get_stats(self) -> Dict:
        """Get current stream statistics."""
        return {
            'unique_id': self.stats.unique_id,
            'status': self.status.value,
            'connected_at': self.stats.connected_at.isoformat() if self.stats.connected_at else None,
            'total_gifts': self.stats.total_gifts,
            'total_coins': self.stats.total_coins,
            'total_points': self.stats.total_points,
            'unique_gifters': len(self.stats.unique_gifters),
            'top_gifts': dict(sorted(
                self.stats.gift_breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            'likes': self.stats.likes_count,
            'shares': self.stats.shares_count,
        }


class LiveBattleConnector:
    """
    Connects to TWO TikTok Live streams for a real battle.

    Tracks gifts from both streams and determines winner
    based on total points received.

    Usage:
        battle = LiveBattleConnector("@creator1", "@creator2")
        battle.on_gift(my_handler)
        await battle.start_battle()
    """

    def __init__(
        self,
        creator_username: str,
        opponent_username: str,
        battle_duration: int = 300  # 5 minutes default
    ):
        """
        Initialize a live battle between two creators.

        Args:
            creator_username: First creator's TikTok username
            opponent_username: Second creator's TikTok username
            battle_duration: Battle duration in seconds
        """
        self.creator_connector = TikTokLiveConnector(creator_username, team="creator")
        self.opponent_connector = TikTokLiveConnector(opponent_username, team="opponent")

        self.battle_duration = battle_duration
        self.battle_started = False
        self.battle_start_time: Optional[datetime] = None

        # Scores
        self.creator_score = 0
        self.opponent_score = 0

        # Event callbacks
        self._gift_callbacks: List[Callable[[LiveGiftEvent, int, int], Any]] = []
        self._battle_end_callbacks: List[Callable[[str, int, int], Any]] = []

        # Setup internal gift handlers
        self.creator_connector.on_gift(self._on_creator_gift)
        self.opponent_connector.on_gift(self._on_opponent_gift)

    def on_gift(self, callback: Callable[[LiveGiftEvent, int, int], Any]):
        """
        Register callback for gift events.

        Callback receives: (gift_event, creator_score, opponent_score)
        """
        self._gift_callbacks.append(callback)
        return self

    def on_battle_end(self, callback: Callable[[str, int, int], Any]):
        """
        Register callback for battle end.

        Callback receives: (winner, creator_score, opponent_score)
        """
        self._battle_end_callbacks.append(callback)
        return self

    async def _on_creator_gift(self, gift_event: LiveGiftEvent):
        """Handle gift to creator."""
        self.creator_score += gift_event.total_points
        await self._emit_gift(gift_event)

    async def _on_opponent_gift(self, gift_event: LiveGiftEvent):
        """Handle gift to opponent."""
        self.opponent_score += gift_event.total_points
        await self._emit_gift(gift_event)

    async def _emit_gift(self, gift_event: LiveGiftEvent):
        """Emit gift event to registered callbacks."""
        for callback in self._gift_callbacks:
            try:
                result = callback(gift_event, self.creator_score, self.opponent_score)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Gift callback error: {e}")

    async def start_battle(self):
        """Start the live battle."""
        logger.info(f"Starting live battle: @{self.creator_connector.unique_id} vs @{self.opponent_connector.unique_id}")

        self.battle_started = True
        self.battle_start_time = datetime.now()
        self.creator_score = 0
        self.opponent_score = 0

        # Connect to both streams concurrently
        await asyncio.gather(
            self.creator_connector.connect(),
            self.opponent_connector.connect()
        )

        # Wait for battle duration
        await asyncio.sleep(self.battle_duration)

        # End battle
        await self.end_battle()

    async def end_battle(self):
        """End the battle and determine winner."""
        self.battle_started = False

        # Disconnect from streams
        await asyncio.gather(
            self.creator_connector.disconnect(),
            self.opponent_connector.disconnect()
        )

        # Determine winner
        if self.creator_score > self.opponent_score:
            winner = "creator"
        elif self.opponent_score > self.creator_score:
            winner = "opponent"
        else:
            winner = "tie"

        logger.info(f"Battle ended! Winner: {winner}")
        logger.info(f"Final scores - Creator: {self.creator_score:,} | Opponent: {self.opponent_score:,}")

        # Emit battle end
        for callback in self._battle_end_callbacks:
            try:
                result = callback(winner, self.creator_score, self.opponent_score)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Battle end callback error: {e}")

        return {
            'winner': winner,
            'creator_score': self.creator_score,
            'opponent_score': self.opponent_score,
            'creator_stats': self.creator_connector.get_stats(),
            'opponent_stats': self.opponent_connector.get_stats(),
        }

    def get_current_scores(self) -> Dict:
        """Get current battle scores."""
        return {
            'creator': self.creator_score,
            'opponent': self.opponent_score,
            'leader': 'creator' if self.creator_score > self.opponent_score else (
                'opponent' if self.opponent_score > self.creator_score else 'tie'
            ),
            'gap': abs(self.creator_score - self.opponent_score),
            'battle_started': self.battle_started,
            'time_elapsed': (datetime.now() - self.battle_start_time).seconds if self.battle_start_time else 0,
        }


# Demo usage
if __name__ == "__main__":
    async def demo_single_stream():
        """Demo: Connect to a single TikTok Live stream."""
        print("=" * 60)
        print("TikTok Live Connector Demo - Single Stream")
        print("=" * 60)

        # Replace with an actual live username
        username = input("Enter TikTok username (without @): ").strip()

        if not username:
            print("No username provided. Exiting.")
            return

        connector = TikTokLiveConnector(username)

        # Register callbacks
        def on_gift(gift_event: LiveGiftEvent):
            print(f"\n{'='*50}")
            print(f"GIFT RECEIVED!")
            print(f"  From: {gift_event.username}")
            print(f"  Gift: {gift_event.gift_name} x{gift_event.repeat_count}")
            print(f"  Value: {gift_event.total_coins:,} coins")
            print(f"  Points: {gift_event.total_points:,}")
            print(f"{'='*50}\n")

        def on_connect(unique_id: str):
            print(f"\n Connected to @{unique_id}!")
            print("Waiting for gifts...\n")

        def on_comment(username: str, comment: str):
            print(f"[{username}]: {comment}")

        connector.on_gift(on_gift)
        connector.on_connect(on_connect)
        connector.on_comment(on_comment)

        try:
            await connector.connect()
        except KeyboardInterrupt:
            print("\nDisconnecting...")
            await connector.disconnect()
            print("\nFinal Stats:")
            print(connector.get_stats())

    async def demo_battle():
        """Demo: Two-stream battle."""
        print("=" * 60)
        print("TikTok Live Connector Demo - Battle Mode")
        print("=" * 60)

        creator = input("Enter Creator username: ").strip()
        opponent = input("Enter Opponent username: ").strip()
        duration = int(input("Battle duration (seconds, default 60): ") or "60")

        battle = LiveBattleConnector(creator, opponent, duration)

        def on_gift(event: LiveGiftEvent, creator_score: int, opponent_score: int):
            team_emoji = "" if event.team == "creator" else ""
            print(f"{team_emoji} {event.username}: {event.gift_name} x{event.repeat_count}")
            print(f"   Scores: Creator {creator_score:,} | Opponent {opponent_score:,}")

        def on_battle_end(winner: str, creator_score: int, opponent_score: int):
            print(f"\n{'='*60}")
            print(f"BATTLE ENDED!")
            print(f"Winner: {winner.upper()}")
            print(f"Creator: {creator_score:,} | Opponent: {opponent_score:,}")
            print(f"{'='*60}\n")

        battle.on_gift(on_gift)
        battle.on_battle_end(on_battle_end)

        result = await battle.start_battle()
        print(f"\nBattle Result: {result}")

    # Run demo
    print("\nSelect demo mode:")
    print("1. Single stream")
    print("2. Battle mode")
    mode = input("Choice (1/2): ").strip()

    if mode == "2":
        asyncio.run(demo_battle())
    else:
        asyncio.run(demo_single_stream())
