#!/usr/bin/env python3
"""
Live Tournament Engine - Best-of-X TikTok Battle Tournaments

Supports Best-of-3, Best-of-5, and Best-of-7 tournament formats
with real TikTok Live streams.

Features:
- Multiple round battles with score tracking
- Round-by-round winner determination
- Series momentum tracking
- Break time between rounds
- Real-time score broadcasting via WebSocket
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Callable, Any
import logging

# Local imports
from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveGiftEvent,
    ConnectionStatus,
    TIKTOK_LIVE_AVAILABLE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveTournamentEngine")


class TournamentFormat(Enum):
    """Tournament format types."""
    BEST_OF_3 = 3
    BEST_OF_5 = 5
    BEST_OF_7 = 7


class TournamentState(Enum):
    """Tournament state machine."""
    WAITING = "waiting"
    CONNECTING = "connecting"
    ROUND_STARTING = "round_starting"
    ROUND_ACTIVE = "round_active"
    ROUND_ENDED = "round_ended"
    BREAK_TIME = "break_time"
    TOURNAMENT_ENDED = "tournament_ended"
    ERROR = "error"


@dataclass
class RoundResult:
    """Result of a single round."""
    round_number: int
    creator_score: int
    opponent_score: int
    winner: str  # "creator", "opponent", or "tie"
    duration_seconds: int
    start_time: datetime
    end_time: datetime
    gift_count: int
    top_gifter: Optional[str] = None
    top_gift_amount: int = 0


@dataclass
class TournamentStats:
    """Overall tournament statistics."""
    creator_username: str
    opponent_username: str
    format: TournamentFormat
    creator_rounds_won: int = 0
    opponent_rounds_won: int = 0
    total_creator_score: int = 0
    total_opponent_score: int = 0
    total_gifts: int = 0
    total_coins: int = 0
    rounds_played: int = 0
    rounds: List[RoundResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    winner: Optional[str] = None

    @property
    def wins_needed(self) -> int:
        """Number of wins needed to win the series."""
        return (self.format.value // 2) + 1

    @property
    def is_finished(self) -> bool:
        """Check if tournament is finished."""
        return (self.creator_rounds_won >= self.wins_needed or
                self.opponent_rounds_won >= self.wins_needed)

    @property
    def series_score(self) -> str:
        """Get series score string."""
        return f"{self.creator_rounds_won}-{self.opponent_rounds_won}"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'creator_username': self.creator_username,
            'opponent_username': self.opponent_username,
            'format': f"Best of {self.format.value}",
            'creator_rounds_won': self.creator_rounds_won,
            'opponent_rounds_won': self.opponent_rounds_won,
            'series_score': self.series_score,
            'total_creator_score': self.total_creator_score,
            'total_opponent_score': self.total_opponent_score,
            'total_gifts': self.total_gifts,
            'total_coins': self.total_coins,
            'rounds_played': self.rounds_played,
            'wins_needed': self.wins_needed,
            'is_finished': self.is_finished,
            'winner': self.winner,
            'rounds': [
                {
                    'round_number': r.round_number,
                    'creator_score': r.creator_score,
                    'opponent_score': r.opponent_score,
                    'winner': r.winner,
                    'duration_seconds': r.duration_seconds,
                    'gift_count': r.gift_count,
                    'top_gifter': r.top_gifter,
                    'top_gift_amount': r.top_gift_amount,
                }
                for r in self.rounds
            ],
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
        }


class LiveTournamentEngine:
    """
    Engine for running Best-of-X tournaments with real TikTok Live streams.

    Usage:
        tournament = LiveTournamentEngine(
            creator_username="@user1",
            opponent_username="@user2",
            format=TournamentFormat.BEST_OF_5,
            round_duration=180  # 3 minutes per round
        )

        tournament.on_round_start(my_round_start_handler)
        tournament.on_gift(my_gift_handler)
        tournament.on_round_end(my_round_end_handler)
        tournament.on_tournament_end(my_tournament_end_handler)

        await tournament.start()
    """

    def __init__(
        self,
        creator_username: str,
        opponent_username: str,
        format: TournamentFormat = TournamentFormat.BEST_OF_3,
        round_duration: int = 180,  # 3 minutes default
        break_duration: int = 30,   # 30 seconds between rounds
    ):
        """
        Initialize tournament engine.

        Args:
            creator_username: First TikTok username
            opponent_username: Second TikTok username
            format: Tournament format (Bo3, Bo5, Bo7)
            round_duration: Duration of each round in seconds
            break_duration: Break time between rounds in seconds
        """
        if not TIKTOK_LIVE_AVAILABLE:
            raise ImportError("TikTokLive library not installed")

        self.creator_username = creator_username.lstrip('@')
        self.opponent_username = opponent_username.lstrip('@')
        self.format = format
        self.round_duration = round_duration
        self.break_duration = break_duration

        # State
        self.state = TournamentState.WAITING
        self.current_round = 0
        self.round_start_time: Optional[datetime] = None
        self.round_creator_score = 0
        self.round_opponent_score = 0
        self.round_gifts: List[LiveGiftEvent] = []

        # Connectors
        self.creator_connector: Optional[TikTokLiveConnector] = None
        self.opponent_connector: Optional[TikTokLiveConnector] = None

        # Statistics
        self.stats = TournamentStats(
            creator_username=self.creator_username,
            opponent_username=self.opponent_username,
            format=format
        )

        # Callbacks
        self._on_round_start_callbacks: List[Callable] = []
        self._on_gift_callbacks: List[Callable] = []
        self._on_score_update_callbacks: List[Callable] = []
        self._on_round_end_callbacks: List[Callable] = []
        self._on_tournament_end_callbacks: List[Callable] = []
        self._on_break_start_callbacks: List[Callable] = []
        self._on_state_change_callbacks: List[Callable] = []

        # Gifter tracking per round
        self._round_gifters: Dict[str, int] = {}

    # === Callback Registration ===

    def on_round_start(self, callback: Callable[[int, Dict], Any]):
        """Register callback for round start. Receives (round_number, stats_dict)."""
        self._on_round_start_callbacks.append(callback)
        return self

    def on_gift(self, callback: Callable[[LiveGiftEvent, int, int, int], Any]):
        """Register callback for gifts. Receives (event, round, creator_score, opponent_score)."""
        self._on_gift_callbacks.append(callback)
        return self

    def on_score_update(self, callback: Callable[[int, int, int, int], Any]):
        """Register callback for score updates. Receives (round, creator_score, opponent_score, time_remaining)."""
        self._on_score_update_callbacks.append(callback)
        return self

    def on_round_end(self, callback: Callable[[RoundResult, Dict], Any]):
        """Register callback for round end. Receives (round_result, stats_dict)."""
        self._on_round_end_callbacks.append(callback)
        return self

    def on_tournament_end(self, callback: Callable[[str, Dict], Any]):
        """Register callback for tournament end. Receives (winner, stats_dict)."""
        self._on_tournament_end_callbacks.append(callback)
        return self

    def on_break_start(self, callback: Callable[[int, int], Any]):
        """Register callback for break time. Receives (next_round, break_seconds)."""
        self._on_break_start_callbacks.append(callback)
        return self

    def on_state_change(self, callback: Callable[[TournamentState], Any]):
        """Register callback for state changes."""
        self._on_state_change_callbacks.append(callback)
        return self

    # === State Management ===

    def _set_state(self, new_state: TournamentState):
        """Update tournament state and notify callbacks."""
        old_state = self.state
        self.state = new_state
        logger.info(f"Tournament state: {old_state.value} -> {new_state.value}")

        for callback in self._on_state_change_callbacks:
            try:
                result = callback(new_state)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.error(f"State change callback error: {e}")

    # === Gift Handling ===

    async def _handle_gift(self, event: LiveGiftEvent):
        """Handle incoming gift event."""
        if self.state != TournamentState.ROUND_ACTIVE:
            return

        # Update round scores
        if event.team == "creator":
            self.round_creator_score += event.total_points
        else:
            self.round_opponent_score += event.total_points

        # Track gifter
        if event.username not in self._round_gifters:
            self._round_gifters[event.username] = 0
        self._round_gifters[event.username] += event.total_coins

        # Store gift event
        self.round_gifts.append(event)

        # Update total stats
        self.stats.total_gifts += event.repeat_count
        self.stats.total_coins += event.total_coins

        # Emit callbacks
        for callback in self._on_gift_callbacks:
            try:
                result = callback(
                    event,
                    self.current_round,
                    self.round_creator_score,
                    self.round_opponent_score
                )
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Gift callback error: {e}")

    # === Tournament Flow ===

    async def start(self):
        """Start the tournament."""
        logger.info(f"\n{'='*60}")
        logger.info(f"🏆 LIVE TOURNAMENT STARTING")
        logger.info(f"   Format: Best of {self.format.value}")
        logger.info(f"   @{self.creator_username} vs @{self.opponent_username}")
        logger.info(f"   Round Duration: {self.round_duration}s")
        logger.info(f"{'='*60}\n")

        self.stats.start_time = datetime.now()
        self._set_state(TournamentState.CONNECTING)

        # Initialize connectors
        self.creator_connector = TikTokLiveConnector(self.creator_username, team="creator")
        self.opponent_connector = TikTokLiveConnector(self.opponent_username, team="opponent")

        # Register gift handlers
        self.creator_connector.on_gift(self._handle_gift)
        self.opponent_connector.on_gift(self._handle_gift)

        try:
            # Run tournament rounds
            while not self.stats.is_finished:
                self.current_round += 1
                await self._run_round()

                # Break between rounds (if not finished)
                if not self.stats.is_finished:
                    await self._run_break()

            # Tournament ended
            await self._finish_tournament()

        except Exception as e:
            logger.error(f"Tournament error: {e}")
            self._set_state(TournamentState.ERROR)
            raise

        return self.stats.to_dict()

    async def _run_round(self):
        """Run a single round."""
        self._set_state(TournamentState.ROUND_STARTING)

        # Reset round state
        self.round_creator_score = 0
        self.round_opponent_score = 0
        self.round_gifts = []
        self._round_gifters = {}
        self.round_start_time = datetime.now()

        logger.info(f"\n🎮 ROUND {self.current_round} STARTING")
        logger.info(f"   Series: {self.stats.series_score}")

        # Emit round start callbacks
        for callback in self._on_round_start_callbacks:
            try:
                result = callback(self.current_round, self.stats.to_dict())
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Round start callback error: {e}")

        self._set_state(TournamentState.ROUND_ACTIVE)

        # Connect to both streams and run for round duration
        connect_task = asyncio.create_task(self._connect_streams())
        timer_task = asyncio.create_task(self._round_timer())

        # Wait for timer to complete
        await timer_task

        # Stop connections
        await self._disconnect_streams()
        connect_task.cancel()

        # End round
        await self._end_round()

    async def _connect_streams(self):
        """Connect to both TikTok streams."""
        try:
            await asyncio.gather(
                self.creator_connector.connect(auto_reconnect=True, reconnect_delay=3),
                self.opponent_connector.connect(auto_reconnect=True, reconnect_delay=3),
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass

    async def _disconnect_streams(self):
        """Disconnect from both streams."""
        try:
            if self.creator_connector:
                await self.creator_connector.disconnect()
            if self.opponent_connector:
                await self.opponent_connector.disconnect()
        except Exception as e:
            logger.debug(f"Disconnect error (non-critical): {e}")

    async def _round_timer(self):
        """Timer for round duration with periodic score updates."""
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = max(0, self.round_duration - int(elapsed))

            # Emit score update
            for callback in self._on_score_update_callbacks:
                try:
                    result = callback(
                        self.current_round,
                        self.round_creator_score,
                        self.round_opponent_score,
                        remaining
                    )
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Score update callback error: {e}")

            if remaining <= 0:
                break

            await asyncio.sleep(1)

    async def _end_round(self):
        """End current round and record result."""
        self._set_state(TournamentState.ROUND_ENDED)

        end_time = datetime.now()
        duration = int((end_time - self.round_start_time).total_seconds())

        # Determine winner
        if self.round_creator_score > self.round_opponent_score:
            winner = "creator"
            self.stats.creator_rounds_won += 1
        elif self.round_opponent_score > self.round_creator_score:
            winner = "opponent"
            self.stats.opponent_rounds_won += 1
        else:
            winner = "tie"
            # In case of tie, no one wins the round - will need extra round

        # Find top gifter
        top_gifter = None
        top_amount = 0
        for gifter, amount in self._round_gifters.items():
            if amount > top_amount:
                top_gifter = gifter
                top_amount = amount

        # Create round result
        result = RoundResult(
            round_number=self.current_round,
            creator_score=self.round_creator_score,
            opponent_score=self.round_opponent_score,
            winner=winner,
            duration_seconds=duration,
            start_time=self.round_start_time,
            end_time=end_time,
            gift_count=len(self.round_gifts),
            top_gifter=top_gifter,
            top_gift_amount=top_amount
        )

        self.stats.rounds.append(result)
        self.stats.rounds_played += 1
        self.stats.total_creator_score += self.round_creator_score
        self.stats.total_opponent_score += self.round_opponent_score

        logger.info(f"\n🏁 ROUND {self.current_round} ENDED")
        logger.info(f"   Creator: {self.round_creator_score:,} | Opponent: {self.round_opponent_score:,}")
        logger.info(f"   Winner: {winner.upper()}")
        logger.info(f"   Series: {self.stats.series_score}")

        # Emit round end callbacks
        for callback in self._on_round_end_callbacks:
            try:
                result_callback = callback(result, self.stats.to_dict())
                if asyncio.iscoroutine(result_callback):
                    await result_callback
            except Exception as e:
                logger.error(f"Round end callback error: {e}")

    async def _run_break(self):
        """Run break time between rounds."""
        self._set_state(TournamentState.BREAK_TIME)

        next_round = self.current_round + 1
        logger.info(f"\n⏸️  BREAK TIME - {self.break_duration}s until Round {next_round}")

        # Emit break start callbacks
        for callback in self._on_break_start_callbacks:
            try:
                result = callback(next_round, self.break_duration)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Break start callback error: {e}")

        await asyncio.sleep(self.break_duration)

    async def _finish_tournament(self):
        """Finish the tournament."""
        self._set_state(TournamentState.TOURNAMENT_ENDED)
        self.stats.end_time = datetime.now()

        # Determine overall winner
        if self.stats.creator_rounds_won > self.stats.opponent_rounds_won:
            self.stats.winner = "creator"
            winner_name = self.creator_username
        else:
            self.stats.winner = "opponent"
            winner_name = self.opponent_username

        logger.info(f"\n{'='*60}")
        logger.info(f"🏆 TOURNAMENT ENDED")
        logger.info(f"   Winner: @{winner_name}")
        logger.info(f"   Series: {self.stats.series_score}")
        logger.info(f"   Total Points: {self.stats.total_creator_score:,} - {self.stats.total_opponent_score:,}")
        logger.info(f"   Total Gifts: {self.stats.total_gifts}")
        logger.info(f"{'='*60}\n")

        # Emit tournament end callbacks
        for callback in self._on_tournament_end_callbacks:
            try:
                result = callback(self.stats.winner, self.stats.to_dict())
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Tournament end callback error: {e}")

    def get_state(self) -> Dict:
        """Get current tournament state."""
        time_remaining = 0
        if self.state == TournamentState.ROUND_ACTIVE and self.round_start_time:
            elapsed = (datetime.now() - self.round_start_time).total_seconds()
            time_remaining = max(0, self.round_duration - int(elapsed))

        return {
            'state': self.state.value,
            'current_round': self.current_round,
            'round_creator_score': self.round_creator_score,
            'round_opponent_score': self.round_opponent_score,
            'time_remaining': time_remaining,
            'stats': self.stats.to_dict(),
        }

    async def stop(self):
        """Stop the tournament early."""
        logger.info("Tournament stopped by user")
        await self._disconnect_streams()
        self._set_state(TournamentState.TOURNAMENT_ENDED)


# === Demo / CLI ===

async def demo_tournament():
    """Demo tournament with real TikTok streams."""
    print("\n" + "=" * 60)
    print("🏆 LIVE TOURNAMENT DEMO")
    print("=" * 60)

    creator = input("Enter Creator username: ").strip().lstrip('@')
    opponent = input("Enter Opponent username: ").strip().lstrip('@')

    print("\nSelect format:")
    print("  1. Best of 3")
    print("  2. Best of 5")
    print("  3. Best of 7")
    format_choice = input("Choice (1-3): ").strip()

    format_map = {
        '1': TournamentFormat.BEST_OF_3,
        '2': TournamentFormat.BEST_OF_5,
        '3': TournamentFormat.BEST_OF_7,
    }
    tournament_format = format_map.get(format_choice, TournamentFormat.BEST_OF_3)

    round_duration = int(input("Round duration in seconds (default 120): ") or "120")

    # Create tournament
    tournament = LiveTournamentEngine(
        creator_username=creator,
        opponent_username=opponent,
        format=tournament_format,
        round_duration=round_duration,
        break_duration=15
    )

    # Register callbacks
    def on_round_start(round_num, stats):
        print(f"\n🎮 ROUND {round_num} - FIGHT!")
        print(f"   Series: {stats['series_score']}")

    def on_gift(event, round_num, creator_score, opponent_score):
        team_emoji = "🔵" if event.team == "creator" else "🔴"
        print(f"{team_emoji} {event.username}: {event.gift_name} x{event.repeat_count}")
        print(f"   Round {round_num}: Creator {creator_score:,} | Opponent {opponent_score:,}")

    def on_round_end(result, stats):
        print(f"\n🏁 ROUND {result.round_number} - Winner: {result.winner.upper()}")
        print(f"   Score: {result.creator_score:,} - {result.opponent_score:,}")
        print(f"   Series: {stats['series_score']}")

    def on_tournament_end(winner, stats):
        print(f"\n{'='*60}")
        print(f"🏆 TOURNAMENT CHAMPION: {winner.upper()}")
        print(f"   Final Series: {stats['series_score']}")
        print(f"   Total Points: {stats['total_creator_score']:,} - {stats['total_opponent_score']:,}")
        print(f"{'='*60}")

    tournament.on_round_start(on_round_start)
    tournament.on_gift(on_gift)
    tournament.on_round_end(on_round_end)
    tournament.on_tournament_end(on_tournament_end)

    try:
        result = await tournament.start()
        print(f"\nFinal result: {result}")
    except KeyboardInterrupt:
        print("\nTournament cancelled")
        await tournament.stop()


if __name__ == "__main__":
    asyncio.run(demo_tournament())
