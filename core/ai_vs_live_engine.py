"""
AI vs Live Streamer Battle Engine

Pits our AI agent team against a real TikTok Live streamer.
The AI agents simulate gifting while we monitor the real stream's gifts.

Modes:
- CHALLENGE: AI team tries to beat the live stream's gift score
- TRAINING: AI learns from real gift patterns
- TOURNAMENT: Best-of-X series against live stream

Usage:
    engine = AIvsLiveEngine(
        target_streamer="@username",
        ai_team=["NovaWhale", "PixelPixie", "GlitchMancer"],
        battle_duration=120
    )
    await engine.start_battle()
"""

import asyncio
import time
from typing import Optional, Dict, List, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import random

from core.tiktok_live_connector import (
    TikTokLiveConnector,
    LiveGiftEvent,
    ConnectionStatus,
    TIKTOK_LIVE_AVAILABLE
)
from core.tiktok_gifts_catalog import TIKTOK_GIFTS_CATALOG
from core.tiktok_battle_config import (
    TIKTOK_BATTLE_CONFIG,
    TOURNAMENT_CONFIG,
    BattlePhase,
    PowerUpType,
    BATTLE_DURATION_SECONDS,
    VICTORY_LAP_SECONDS,
    BATTLE_COOLDOWN_SECONDS,
    FINAL_PUSH_SECONDS,
    GLOVE_DURATION_SECONDS,
    GLOVE_MULTIPLIER,
    GLOVE_ACTIVATION_CHANCE,
)

logger = logging.getLogger("AIvsLiveEngine")


# Counter-attack gift tiers based on burst intensity
# Gift names must match TIKTOK_GIFTS_CATALOG keys (uppercase with underscores)
COUNTER_ATTACK_GIFTS = {
    'small': [('DOUGHNUT', 30), ('PAPER_CRANE', 99)],           # <1000 pts burst
    'medium': [('CORGI', 299), ('BOXING_GLOVES', 300)],         # 1000-5000 pts
    'large': [('MONEY_GUN', 450), ('ROSES', 500)],              # 5000-20000 pts
    'whale': [('LION', 29999), ('TIKTOK_UNIVERSE', 44999)]      # >20000 pts
}

# Live Fest campaign gift names (for detection)
LIVE_FEST_GIFT_KEYWORDS = [
    'fest', 'vote', 'cheer', 'popular', 'team', 'guardian', 'banner',
    'champion', 'supporter', 'firework', 'trophy'
]

# Live Fest 2025 strategy gifts
# IMPORTANT: Fest gifts give 1.5x POINTS PER COIN!
# Source: TikTok LiveFest 2025 creator briefing
LIVE_FEST_STRATEGY_GIFTS = {
    'volume': [('FEST_POP', 1)],                                # 1 coin = 1.5 pts (high volume grind)
    'standard': [('FEST_GEAR', 99), ('FEST_POP', 1)],          # 99c = 148.5 pts, mix strategy
    'premium': [('FEST_CHEERS', 399), ('FEST_GEAR', 99)],      # 399c = 598.5 pts, premium push
    'whale': [('FEST_PARTY', 2999), ('FEST_CHEERS', 399)],     # 2999c = 4498.5 pts, whale mode
    'vault': [('VAULT_GIFT', 5000)],                           # 5000c = 7500 pts, vault gift
}


@dataclass
class BurstEvent:
    """Represents a detected gift burst from live stream."""
    username: str
    gift_count: int
    total_points: int
    duration_seconds: float
    threat_level: str  # "low", "medium", "high", "critical"
    timestamp: float = field(default_factory=time.time)


class LiveBurstDetector:
    """
    Detects rapid gift sequences from live stream.

    A burst is defined as multiple gifts from same user or rapid gifts
    that exceed a threshold within a time window.
    """

    def __init__(
        self,
        burst_threshold: int = 3000,  # Points threshold for burst
        window_seconds: float = 10.0,  # Time window for burst detection
        critical_threshold: int = 10000  # Points for critical burst
    ):
        self.burst_threshold = burst_threshold
        self.window_seconds = window_seconds
        self.critical_threshold = critical_threshold
        self.gift_history: List[Tuple[float, str, int]] = []  # (timestamp, user, points)
        self._active_burst: Optional[BurstEvent] = None
        self._last_burst_time: float = 0
        self._burst_cooldown: float = 5.0  # Seconds between bursts

    def record_gift(self, username: str, points: int, timestamp: float = None) -> Optional[BurstEvent]:
        """
        Record a gift and detect if it's part of a burst.

        Returns BurstEvent if a burst is detected, None otherwise.
        """
        if timestamp is None:
            timestamp = time.time()

        self.gift_history.append((timestamp, username, points))

        # Clean old history
        cutoff = timestamp - self.window_seconds
        self.gift_history = [(t, u, p) for t, u, p in self.gift_history if t >= cutoff]

        # Check if on cooldown from recent burst
        if timestamp - self._last_burst_time < self._burst_cooldown:
            return None

        # Analyze recent gifts
        burst = self._detect_burst(timestamp)

        if burst:
            self._last_burst_time = timestamp
            self._active_burst = burst
            logger.info(f"🚨 BURST DETECTED: {burst.total_points:,} pts from {burst.username} "
                       f"({burst.gift_count} gifts in {burst.duration_seconds:.1f}s) "
                       f"- Threat: {burst.threat_level.upper()}")

        return burst

    def _detect_burst(self, current_time: float) -> Optional[BurstEvent]:
        """Detect if recent gifts constitute a burst."""
        if len(self.gift_history) < 2:
            return None

        # Calculate total points in window
        total_points = sum(p for _, _, p in self.gift_history)

        if total_points < self.burst_threshold:
            return None

        # Find the user with most points
        user_points: Dict[str, int] = {}
        user_gifts: Dict[str, int] = {}
        for _, user, pts in self.gift_history:
            user_points[user] = user_points.get(user, 0) + pts
            user_gifts[user] = user_gifts.get(user, 0) + 1

        top_user = max(user_points.keys(), key=lambda u: user_points[u])
        top_points = user_points[top_user]

        # Determine threat level
        if total_points >= self.critical_threshold * 2:
            threat_level = "critical"
        elif total_points >= self.critical_threshold:
            threat_level = "high"
        elif total_points >= self.burst_threshold * 2:
            threat_level = "medium"
        else:
            # "low" threat - don't report yet, wait for more data
            # This prevents premature cooldown from blocking larger burst detection
            return None

        # Calculate duration
        timestamps = [t for t, _, _ in self.gift_history]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 1.0

        return BurstEvent(
            username=top_user,
            gift_count=len(self.gift_history),
            total_points=total_points,
            duration_seconds=max(duration, 0.1),
            threat_level=threat_level,
            timestamp=current_time
        )

    def get_user_velocity(self, username: str) -> float:
        """Get current gift velocity (points per second) for a user."""
        user_gifts = [(t, p) for t, u, p in self.gift_history if u == username]
        if len(user_gifts) < 2:
            return 0.0

        timestamps = [t for t, _ in user_gifts]
        total_points = sum(p for _, p in user_gifts)
        duration = max(timestamps) - min(timestamps)

        return total_points / max(duration, 0.1)

    def reset(self):
        """Reset detector for new round."""
        self.gift_history.clear()
        self._active_burst = None
        self._last_burst_time = 0


@dataclass
class LiveFestStatus:
    """Status of Live Fest campaign detection."""
    is_active: bool = False
    confidence: float = 0.0  # 0-1, how confident we are
    fest_gifts_count: int = 0
    total_gifts_count: int = 0
    fest_gift_ratio: float = 0.0
    detected_fest_gifts: List[str] = field(default_factory=list)
    detection_time: float = 0.0


class LiveFestDetector:
    """
    Detects when opponent is participating in a TikTok Live Fest campaign.

    Live Fest campaigns have specific gifts (Fest Pop, Popular Vote, etc.)
    that are sent in high volumes. When detected, AI should adjust strategy
    to maintain constant pressure rather than waiting for bursts.
    """

    def __init__(
        self,
        detection_threshold: float = 0.15,  # 15% Live Fest gifts triggers detection
        min_gifts_for_detection: int = 20,   # Need at least 20 gifts to detect
    ):
        self.detection_threshold = detection_threshold
        self.min_gifts_for_detection = min_gifts_for_detection
        self.gift_history: List[Tuple[str, bool]] = []  # (gift_name, is_fest_gift)
        self._status = LiveFestStatus()

    def record_gift(self, gift_name: str) -> LiveFestStatus:
        """
        Record a gift and update Live Fest detection status.

        Returns updated LiveFestStatus.
        """
        # Check if this is a Live Fest gift
        is_fest = self._is_live_fest_gift(gift_name)
        self.gift_history.append((gift_name, is_fest))

        # Update status
        self._update_status()

        return self._status

    def _is_live_fest_gift(self, gift_name: str) -> bool:
        """Check if gift name matches Live Fest patterns."""
        gift_lower = gift_name.lower()
        return any(keyword in gift_lower for keyword in LIVE_FEST_GIFT_KEYWORDS)

    def _update_status(self):
        """Update detection status based on gift history."""
        total = len(self.gift_history)
        fest_count = sum(1 for _, is_fest in self.gift_history if is_fest)

        self._status.total_gifts_count = total
        self._status.fest_gifts_count = fest_count

        if total >= self.min_gifts_for_detection:
            ratio = fest_count / total
            self._status.fest_gift_ratio = ratio

            # Calculate confidence based on ratio and sample size
            # Higher ratio and more samples = higher confidence
            base_confidence = min(ratio / self.detection_threshold, 1.0)
            sample_factor = min(total / 100, 1.0)  # Max confidence at 100 gifts
            self._status.confidence = base_confidence * sample_factor

            # Detect if ratio exceeds threshold
            was_active = self._status.is_active
            self._status.is_active = ratio >= self.detection_threshold

            if self._status.is_active and not was_active:
                self._status.detection_time = time.time()
                # Collect unique fest gift names
                self._status.detected_fest_gifts = list(set(
                    name for name, is_fest in self.gift_history if is_fest
                ))
                logger.info(f"🎪 LIVE FEST DETECTED! Ratio: {ratio:.1%}, "
                           f"Gifts: {self._status.detected_fest_gifts}")

    def get_status(self) -> LiveFestStatus:
        """Get current Live Fest detection status."""
        return self._status

    def reset(self):
        """Reset detector for new round."""
        self.gift_history.clear()
        self._status = LiveFestStatus()


class AIBattleMode(Enum):
    """Battle modes for AI vs Live."""
    CHALLENGE = "challenge"      # AI tries to win
    TRAINING = "training"        # AI learns patterns
    TOURNAMENT = "tournament"    # Best-of-X series
    SIMULATION = "simulation"    # Simulate live stream (for testing when rate limited)


class TournamentFormat(Enum):
    """Tournament formats."""
    BEST_OF_1 = 1
    BEST_OF_3 = 3
    BEST_OF_5 = 5
    BEST_OF_7 = 7


@dataclass
class AIAgent:
    """Simplified AI agent for live battles."""
    name: str
    emoji: str
    style: str  # "whale", "budget", "chaotic", "strategic"
    aggression: float = 0.5  # 0-1, how often they gift
    budget_coins: int = 10000  # Virtual coins
    spent_coins: int = 0
    gifts_sent: int = 0
    points_generated: int = 0

    # Gift preferences by style (names must match TIKTOK_GIFTS_CATALOG keys)
    STYLE_GIFTS = {
        "whale": ["TIKTOK_UNIVERSE", "LION", "PHOENIX", "BIG_BEN"],
        "budget": ["ROSE", "ICE_CREAM_CONE", "DOUGHNUT", "PAPER_CRANE"],
        "chaotic": ["ROSE", "GG", "LION", "TIKTOK_UNIVERSE"],  # Mix of all
        "strategic": ["DOUGHNUT", "CORGI", "BOXING_GLOVES", "LION"],
    }

    def select_gift(self, battle_context: dict) -> Optional[tuple]:
        """Select a gift based on agent style and battle context."""
        time_remaining = battle_context.get('time_remaining', 60)
        score_diff = battle_context.get('ai_score', 0) - battle_context.get('live_score', 0)
        is_boost = battle_context.get('is_boost_phase', False)
        multiplier = battle_context.get('multiplier', 1.0)
        burst_detected = battle_context.get('burst_detected', False)
        burst_info = battle_context.get('burst_info')

        # ============================================
        # COUNTER-ATTACK MODE: Respond to live bursts
        # ============================================
        if burst_detected and burst_info:
            counter_gift = self._get_counter_attack_gift(burst_info, score_diff)
            if counter_gift:
                return counter_gift

        # ============================================
        # X5 MULTIPLIER: Use whale gifts
        # ============================================
        if multiplier >= 5.0 and self.style in ["whale", "strategic", "chaotic"]:
            whale_gift = self._get_whale_gift()
            if whale_gift:
                return whale_gift

        # ============================================
        # LIVE FEST MODE: High volume pressure strategy
        # ============================================
        live_fest_active = battle_context.get('live_fest_active', False)
        if live_fest_active:
            fest_gift = self._get_live_fest_gift(score_diff)
            if fest_gift:
                return fest_gift

        # Check if agent wants to act this tick
        action_chance = self.aggression

        # Live Fest increases aggression for all agents
        if live_fest_active:
            action_chance *= 1.5

        # Increase action in final seconds
        if time_remaining <= 30:
            action_chance *= 1.5
        if time_remaining <= 10:
            action_chance *= 2

        # Boost phase increases action
        if is_boost:
            action_chance *= 1.3

        # If losing badly, increase aggression
        if score_diff < -5000:
            action_chance *= 1.5

        # Random check
        if random.random() > action_chance:
            return None

        # Select gift based on style
        preferred_gifts = self.STYLE_GIFTS.get(self.style, self.STYLE_GIFTS["budget"])

        # Whales go big in final moments or when losing
        if self.style == "whale" and (time_remaining <= 20 or score_diff < -10000):
            preferred_gifts = ["TIKTOK_UNIVERSE", "LION", "PHOENIX", "BIG_BEN"]

        # Budget players stick to cheap gifts
        if self.style == "budget" and self.spent_coins > self.budget_coins * 0.7:
            preferred_gifts = ["ROSE", "ICE_CREAM_CONE"]

        # Chaotic players are unpredictable
        if self.style == "chaotic" and random.random() < 0.2:
            preferred_gifts = list(TIKTOK_GIFTS_CATALOG.keys())[:20]

        # Find affordable gift
        for gift_name in preferred_gifts:
            gift_obj = TIKTOK_GIFTS_CATALOG.get(gift_name)
            if gift_obj:
                if self.spent_coins + gift_obj.coins <= self.budget_coins:
                    return (gift_name, {'coins': gift_obj.coins, 'points': gift_obj.points})

        # Fallback to cheapest gift (ROSE = 1 coin)
        if self.spent_coins + 1 <= self.budget_coins:
            rose = TIKTOK_GIFTS_CATALOG.get("ROSE")
            if rose:
                return ("ROSE", {'coins': rose.coins, 'points': rose.points})
            return ("ROSE", {"coins": 1, "points": 10})

        return None

    def _get_counter_attack_gift(self, burst_info: 'BurstEvent', score_diff: int) -> Optional[tuple]:
        """Select a counter-attack gift based on burst intensity."""
        burst_points = burst_info.total_points
        threat = burst_info.threat_level

        # Determine tier based on burst intensity
        if threat == "critical" or burst_points >= 20000:
            tier = 'whale'
        elif threat == "high" or burst_points >= 5000:
            tier = 'large'
        elif threat == "medium" or burst_points >= 1000:
            tier = 'medium'
        else:
            tier = 'small'

        # Only whale/strategic agents do big counter-attacks
        if tier in ['whale', 'large'] and self.style not in ['whale', 'strategic', 'chaotic']:
            tier = 'medium'

        # Get gifts for tier
        tier_gifts = COUNTER_ATTACK_GIFTS.get(tier, COUNTER_ATTACK_GIFTS['small'])

        # Find affordable gift from tier
        for gift_name, coins in tier_gifts:
            if self.spent_coins + coins <= self.budget_coins:
                gift_obj = TIKTOK_GIFTS_CATALOG.get(gift_name)
                if gift_obj:
                    return (gift_name, {'coins': gift_obj.coins, 'points': gift_obj.points})
                else:
                    # Fallback: 1 coin = 1 point (TikTok official)
                    return (gift_name, {'coins': coins, 'points': coins})

        return None

    def _get_whale_gift(self) -> Optional[tuple]:
        """Select a whale gift for x5 moments."""
        whale_gifts = [
            ("TIKTOK_UNIVERSE", 44999),
            ("LION", 29999),
            ("PHOENIX", 25999),
            ("BIG_BEN", 15000),
            ("SPORTS_CAR", 7000),
            ("MONEY_GUN", 450),
        ]

        for gift_name, coins in whale_gifts:
            if self.spent_coins + coins <= self.budget_coins:
                gift_obj = TIKTOK_GIFTS_CATALOG.get(gift_name)
                if gift_obj:
                    return (gift_name, {'coins': gift_obj.coins, 'points': gift_obj.points})
                else:
                    # Fallback: 1 coin = 1 point (TikTok official)
                    return (gift_name, {'coins': coins, 'points': coins})

        return None

    def _get_live_fest_gift(self, score_diff: int) -> Optional[tuple]:
        """
        Select gift for Live Fest ranking strategy.

        IMPORTANT: Only FEST-branded gifts count for Live Fest ranking!
        Strategy focuses on sending Fest Pop, Fest Gear, Fest Cheers, Fest Party.
        """
        # Determine strategy based on agent style and score
        if self.style == "whale":
            # Whales use premium/whale fest gifts for big ranking pushes
            if score_diff < -1000:
                strategy = 'whale'  # Behind badly: FEST_PARTY
            else:
                strategy = 'premium' if random.random() < 0.4 else 'standard'
        elif self.style == "strategic":
            # Strategic agents balance cost/ranking efficiency
            strategy = 'premium' if score_diff < -500 else 'standard'
        elif self.style == "budget":
            # Budget agents spam FEST_POP for volume
            strategy = 'volume'
        else:
            # Default: standard mix
            strategy = 'standard' if random.random() < 0.7 else 'volume'

        # Get gifts for chosen strategy
        strategy_gifts = LIVE_FEST_STRATEGY_GIFTS.get(strategy, LIVE_FEST_STRATEGY_GIFTS['volume'])

        for gift_name, coins in strategy_gifts:
            if self.spent_coins + coins <= self.budget_coins:
                gift_obj = TIKTOK_GIFTS_CATALOG.get(gift_name)
                if gift_obj:
                    return (gift_name, {'coins': gift_obj.coins, 'points': gift_obj.points})
                else:
                    return (gift_name, {'coins': coins, 'points': coins})

        # Fallback to FEST_POP (always available, counts for ranking)
        if self.spent_coins + 1 <= self.budget_coins:
            fest_pop = TIKTOK_GIFTS_CATALOG.get("FEST_POP")
            if fest_pop:
                return ("FEST_POP", {'coins': fest_pop.coins, 'points': fest_pop.points})

        return None


@dataclass
class RoundResult:
    """Result of a single round."""
    round_number: int
    winner: str  # "ai" or "live"
    ai_score: int
    live_score: int
    ai_gifts: int
    live_gifts: int
    duration: int
    top_ai_agent: str = ""
    top_live_gifter: str = ""


@dataclass
class AIvsLiveState:
    """Current state of AI vs Live battle."""
    mode: AIBattleMode
    target_streamer: str
    connected: bool = False
    battle_active: bool = False

    # Scores
    ai_score: int = 0
    live_score: int = 0

    # Round tracking (for tournament)
    current_round: int = 1
    ai_wins: int = 0
    live_wins: int = 0
    rounds: List[RoundResult] = field(default_factory=list)

    # Time
    round_duration: int = 120
    time_remaining: int = 120
    round_start_time: Optional[datetime] = None

    # Gifts
    ai_gifts: List[Dict] = field(default_factory=list)
    live_gifts: List[LiveGiftEvent] = field(default_factory=list)

    # Stats
    live_gifters: Dict[str, int] = field(default_factory=dict)
    ai_agent_stats: Dict[str, Dict] = field(default_factory=dict)

    # Phase tracking
    current_phase: str = "normal"
    current_multiplier: float = 1.0

    # Burst tracking (for counter-attacks)
    burst_active: bool = False
    burst_info: Optional[BurstEvent] = None
    last_burst_time: float = 0
    counter_attacks: int = 0

    # Budget reserves
    counter_reserve: int = 0  # Reserved for counter-attacks

    # Live Fest campaign tracking
    live_fest_active: bool = False
    live_fest_confidence: float = 0.0
    live_fest_gifts_detected: List[str] = field(default_factory=list)


class AIvsLiveEngine:
    """
    Battle engine for AI team vs real TikTok Live stream.

    Our AI agents generate simulated gifts while we track
    real gifts from the target stream.
    """

    def __init__(
        self,
        target_streamer: str,
        ai_team: List[str] = None,
        mode: AIBattleMode = AIBattleMode.CHALLENGE,
        round_duration: int = BATTLE_DURATION_SECONDS,  # 5 minutes (300s) official
        tournament_format: TournamentFormat = TournamentFormat.BEST_OF_3,
        ai_budget_per_round: int = 50000  # Total virtual coins for AI team
    ):
        self.target_streamer = target_streamer.lstrip('@')
        self.mode = mode
        self.round_duration = round_duration
        self.tournament_format = tournament_format
        self.ai_budget_per_round = ai_budget_per_round

        # Initialize AI team
        self.ai_agents = self._create_ai_team(ai_team)

        # State
        self.state = AIvsLiveState(
            mode=mode,
            target_streamer=self.target_streamer,
            round_duration=round_duration,
            time_remaining=round_duration
        )

        # TikTok connector
        self.connector: Optional[TikTokLiveConnector] = None

        # Control
        self._running = False
        self._battle_task: Optional[asyncio.Task] = None

        # Callbacks
        self._on_ai_gift_callbacks: List[Callable] = []
        self._on_live_gift_callbacks: List[Callable] = []
        self._on_score_update_callbacks: List[Callable] = []
        self._on_round_end_callbacks: List[Callable] = []
        self._on_battle_end_callbacks: List[Callable] = []
        self._on_connection_callbacks: List[Callable] = []
        self._on_counter_attack_callbacks: List[Callable] = []

        # Burst detection system (thresholds in real TikTok points: 1 coin = 1 pt)
        self.burst_detector = LiveBurstDetector(
            burst_threshold=300,     # 300 pts (~$4) triggers burst detection
            window_seconds=10.0,     # 10 second window
            critical_threshold=1000  # 1000 pts (~$13) is critical
        )

        # Live Fest campaign detection
        self.live_fest_detector = LiveFestDetector(
            detection_threshold=0.15,   # 15% Live Fest gifts triggers detection
            min_gifts_for_detection=20  # Need 20+ gifts to detect
        )
        self._on_live_fest_callbacks: List[Callable] = []

    def _create_ai_team(self, team_names: List[str] = None) -> List[AIAgent]:
        """Create AI team from names or defaults."""
        default_team = [
            AIAgent("NovaWhale", "🐋", "whale", aggression=0.3, budget_coins=30000),
            AIAgent("PixelPixie", "🧚", "budget", aggression=0.8, budget_coins=5000),
            AIAgent("GlitchMancer", "🌀", "chaotic", aggression=0.5, budget_coins=8000),
            AIAgent("ShadowPatron", "👤", "strategic", aggression=0.4, budget_coins=7000),
        ]

        if not team_names:
            return default_team

        # Match names to default agents or create basic ones
        agents = []
        for name in team_names:
            found = next((a for a in default_team if a.name == name), None)
            if found:
                agents.append(found)
            else:
                # Create basic agent
                agents.append(AIAgent(name, "🤖", "strategic", aggression=0.5))

        return agents if agents else default_team

    def reset_round(self):
        """Reset state for a new round."""
        self.state.ai_score = 0
        self.state.live_score = 0
        self.state.time_remaining = self.round_duration
        self.state.ai_gifts = []
        self.state.live_gifts = []
        self.state.live_gifters = {}
        self.state.current_phase = "normal"
        self.state.current_multiplier = 1.0

        # Reset burst tracking
        self.state.burst_active = False
        self.state.burst_info = None
        self.state.last_burst_time = 0
        self.state.counter_attacks = 0
        self.burst_detector.reset()

        # Reset Live Fest tracking
        self.state.live_fest_active = False
        self.state.live_fest_confidence = 0.0
        self.state.live_fest_gifts_detected = []
        self.live_fest_detector.reset()

        # Reset AI agents
        budget_per_agent = self.ai_budget_per_round // len(self.ai_agents)
        for agent in self.ai_agents:
            agent.spent_coins = 0
            agent.gifts_sent = 0
            agent.points_generated = 0
            agent.budget_coins = budget_per_agent

    def _handle_live_gift(self, event: LiveGiftEvent):
        """Handle gift from live stream with burst detection."""
        if not self.state.battle_active:
            # Log but don't count gifts outside of active battle
            logger.debug(f"🔴 [PRE-BATTLE] Gift from {event.username}: {event.gift_name} x{event.repeat_count}")
            return

        # Apply multiplier
        points = int(event.total_points * self.state.current_multiplier)

        # Update score
        self.state.live_score += points
        self.state.live_gifts.append(event)

        # Track gifter
        if event.username not in self.state.live_gifters:
            self.state.live_gifters[event.username] = 0
        self.state.live_gifters[event.username] += event.total_coins

        # Mark as connected if we're receiving gifts
        self.state.connected = True

        multiplier_str = f" (x{self.state.current_multiplier})" if self.state.current_multiplier > 1 else ""
        logger.info(f"🔴 LIVE: {event.username} sent {event.gift_name} x{event.repeat_count} "
                   f"(+{points:,} pts{multiplier_str}) | Live: {self.state.live_score:,}")

        # ============================================
        # BURST DETECTION: Detect rapid gift sequences
        # ============================================
        burst = self.burst_detector.record_gift(
            username=event.username,
            points=points,
            timestamp=time.time()
        )

        if burst and burst.threat_level in ['medium', 'high', 'critical']:
            self._trigger_counter_attack(burst)

        # ============================================
        # LIVE FEST DETECTION: Detect campaign gifts
        # ============================================
        fest_status = self.live_fest_detector.record_gift(event.gift_name)

        # Update state if Live Fest detected
        if fest_status.is_active and not self.state.live_fest_active:
            self.state.live_fest_active = True
            self.state.live_fest_confidence = fest_status.confidence
            self.state.live_fest_gifts_detected = fest_status.detected_fest_gifts
            # Trigger Live Fest callbacks
            for cb in self._on_live_fest_callbacks:
                try:
                    cb(fest_status)
                except Exception as e:
                    logger.error(f"Live Fest callback error: {e}")

        # Callbacks
        for cb in self._on_live_gift_callbacks:
            try:
                cb(event, self.state.live_score, self.state.ai_score)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        # Score update
        self._emit_score_update()

    def _trigger_counter_attack(self, burst: BurstEvent):
        """Trigger AI counter-attack when burst detected."""
        logger.info(f"⚔️  COUNTER-ATTACK TRIGGERED!")
        logger.info(f"   Burst: {burst.total_points:,} pts from {burst.username}")
        logger.info(f"   Threat: {burst.threat_level.upper()}")

        # Update state to signal agents
        self.state.burst_active = True
        self.state.burst_info = burst
        self.state.last_burst_time = time.time()
        self.state.counter_attacks += 1

        # Force immediate AI response - whale agents respond first
        counter_context = {
            'time_remaining': self.state.time_remaining,
            'ai_score': self.state.ai_score,
            'live_score': self.state.live_score,
            'is_boost_phase': True,  # Treat as boost for urgency
            'multiplier': self.state.current_multiplier,
            'burst_detected': True,
            'burst_info': burst,
        }

        # Prioritize whale and strategic agents for counter-attack
        priority_agents = sorted(
            self.ai_agents,
            key=lambda a: 0 if a.style == 'whale' else (1 if a.style == 'strategic' else 2)
        )

        gifts_sent = 0
        for agent in priority_agents[:2]:  # Top 2 priority agents respond
            gift_result = agent.select_gift(counter_context)
            if gift_result:
                gift_name, gift_data = gift_result
                self._process_ai_gift(agent, gift_name, gift_data)
                gifts_sent += 1
                logger.info(f"   ⚔️  {agent.emoji} {agent.name} counter with {gift_name}!")

        if gifts_sent > 0:
            logger.info(f"   Counter-attack: {gifts_sent} gifts sent")

        # Callbacks
        for cb in self._on_counter_attack_callbacks:
            try:
                cb(burst, self.state.ai_score, self.state.live_score)
            except Exception as e:
                logger.error(f"Counter-attack callback error: {e}")

    def _ai_tick(self):
        """Process one tick of AI agent decisions."""
        if not self.state.battle_active:
            return

        context = {
            'time_remaining': self.state.time_remaining,
            'ai_score': self.state.ai_score,
            'live_score': self.state.live_score,
            'is_boost_phase': self.state.current_phase != "normal",
            'multiplier': self.state.current_multiplier,
            # Burst context for counter-attacks
            'burst_detected': self.state.burst_active,
            'burst_info': self.state.burst_info,
            # Live Fest context
            'live_fest_active': self.state.live_fest_active,
        }

        for agent in self.ai_agents:
            gift_result = agent.select_gift(context)
            if gift_result:
                gift_name, gift_data = gift_result
                self._process_ai_gift(agent, gift_name, gift_data)

        # Clear burst flag after one tick (counter-attack already triggered)
        if self.state.burst_active:
            self.state.burst_active = False

    def _process_ai_gift(self, agent: AIAgent, gift_name: str, gift_data: dict):
        """Process an AI agent's gift."""
        coins = gift_data.get('coins', 1)
        base_points = gift_data.get('points', coins)

        # Apply multiplier
        points = int(base_points * self.state.current_multiplier)

        # Update agent stats
        agent.spent_coins += coins
        agent.gifts_sent += 1
        agent.points_generated += points

        # Update state
        self.state.ai_score += points

        gift_event = {
            'agent': agent.name,
            'emoji': agent.emoji,
            'gift_name': gift_name,
            'coins': coins,
            'points': points,
            'multiplier': self.state.current_multiplier,
            'timestamp': datetime.now().isoformat()
        }
        self.state.ai_gifts.append(gift_event)

        # Update agent stats in state
        if agent.name not in self.state.ai_agent_stats:
            self.state.ai_agent_stats[agent.name] = {
                'emoji': agent.emoji,
                'gifts': 0,
                'coins': 0,
                'points': 0
            }
        stats = self.state.ai_agent_stats[agent.name]
        stats['gifts'] += 1
        stats['coins'] += coins
        stats['points'] += points

        logger.info(f"🔵 AI: {agent.emoji} {agent.name} sent {gift_name} "
                   f"(+{points:,} pts) | AI: {self.state.ai_score:,}")

        # Callbacks
        for cb in self._on_ai_gift_callbacks:
            try:
                cb(gift_event, self.state.ai_score, self.state.live_score)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        self._emit_score_update()

    def _emit_score_update(self):
        """Emit score update callbacks."""
        for cb in self._on_score_update_callbacks:
            try:
                cb(
                    self.state.ai_score,
                    self.state.live_score,
                    self.state.time_remaining,
                    self.state.current_round
                )
            except Exception as e:
                logger.error(f"Score update callback error: {e}")

    def _update_phase(self):
        """
        Update battle phase based on time.
        Uses official TikTok Battle timing:
        - Battle: 5 minutes (300s)
        - Final Push: Last 30 seconds (critical moment for Mist power-up)
        - Victory Lap: 3 minutes after battle (for Hammer power-up)

        Note: TikTok doesn't have "boost phases" - multipliers come from:
        - Boosting Glove: 30% chance of 5x for 30 seconds (viewer activated)
        - Speed Events: 2x or 3x during special TikTok events
        """
        elapsed = self.round_duration - self.state.time_remaining

        # Get phase from official config
        phase = TIKTOK_BATTLE_CONFIG.get_phase(elapsed)

        # Final Push phase (last 30 seconds) - critical moment
        # This is when Magic Mist should be used
        final_push_start = self.round_duration - FINAL_PUSH_SECONDS

        if phase == BattlePhase.FINAL_PUSH or elapsed >= final_push_start:
            self.state.current_phase = "final_push"
            # No automatic multiplier in real TikTok - but we simulate increased intensity
            self.state.current_multiplier = 1.0

            # Simulate random Boosting Glove activation during final push
            # (In real TikTok, viewers activate this)
            if random.random() < 0.05:  # 5% chance per second of glove being active
                self.state.current_phase = "glove_active"
                self.state.current_multiplier = GLOVE_MULTIPLIER  # 5x

        elif phase == BattlePhase.VICTORY_LAP:
            self.state.current_phase = "victory_lap"
            self.state.current_multiplier = 1.0  # Points still count in victory lap

        elif phase == BattlePhase.BATTLE:
            self.state.current_phase = "battle"
            self.state.current_multiplier = 1.0

            # Random glove activation during normal battle
            if random.random() < 0.02:  # 2% chance per second
                self.state.current_phase = "glove_active"
                self.state.current_multiplier = GLOVE_MULTIPLIER
        else:
            self.state.current_phase = "normal"
            self.state.current_multiplier = 1.0

    async def _run_round(self) -> RoundResult:
        """Run a single battle round."""
        self.reset_round()
        self.state.battle_active = True
        self.state.round_start_time = datetime.now()

        logger.info(f"\n{'='*60}")
        logger.info(f"🎮 ROUND {self.state.current_round} START")
        logger.info(f"   AI Team vs @{self.target_streamer}")
        logger.info(f"   Duration: {self.round_duration}s")
        logger.info(f"{'='*60}\n")

        # Check if in simulation mode
        is_simulation = self.mode == AIBattleMode.SIMULATION

        # Track connection status for live mode
        last_connection_status = None

        # Battle loop
        while self.state.time_remaining > 0 and self._running:
            # Update phase
            self._update_phase()

            # AI agents act
            self._ai_tick()

            # Simulate live gifts if in simulation mode
            if is_simulation:
                self._simulate_live_gift()
            else:
                # Update connection status if changed
                if self.connector:
                    current_status = self.connector.status.value
                    if current_status != last_connection_status:
                        if current_status == "connected":
                            logger.info(f"🟢 Connected to @{self.target_streamer}")
                            self.state.connected = True
                        elif current_status == "reconnecting":
                            logger.info(f"🟡 Reconnecting to @{self.target_streamer}...")
                        elif current_status == "error":
                            logger.warning(f"🔴 Connection error - waiting for reconnect...")
                        last_connection_status = current_status

            # Wait 1 second
            await asyncio.sleep(1)
            self.state.time_remaining -= 1

            # Progress log every 10 seconds
            if self.state.time_remaining % 10 == 0 and self.state.time_remaining > 0:
                status_icon = "🟢" if self.state.connected else "🟡"
                live_gifts_count = len(self.state.live_gifts)
                logger.info(f"⏱️  {self.state.time_remaining}s | "
                           f"AI: {self.state.ai_score:,} vs Live: {self.state.live_score:,} "
                           f"| {status_icon} Live gifts: {live_gifts_count}")

        self.state.battle_active = False

        # Determine winner
        winner = "ai" if self.state.ai_score > self.state.live_score else "live"
        if self.state.ai_score == self.state.live_score:
            winner = "tie"

        # Find top performers
        top_ai = max(self.ai_agents, key=lambda a: a.points_generated)
        top_live = max(self.state.live_gifters.items(), key=lambda x: x[1], default=("None", 0))

        result = RoundResult(
            round_number=self.state.current_round,
            winner=winner,
            ai_score=self.state.ai_score,
            live_score=self.state.live_score,
            ai_gifts=len(self.state.ai_gifts),
            live_gifts=len(self.state.live_gifts),
            duration=self.round_duration,
            top_ai_agent=f"{top_ai.emoji} {top_ai.name}",
            top_live_gifter=top_live[0]
        )

        self.state.rounds.append(result)

        # Update wins
        if winner == "ai":
            self.state.ai_wins += 1
        elif winner == "live":
            self.state.live_wins += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 ROUND {self.state.current_round} COMPLETE")
        logger.info(f"   Winner: {'🔵 AI TEAM' if winner == 'ai' else '🔴 LIVE STREAM' if winner == 'live' else '🟡 TIE'}")
        logger.info(f"   Score: AI {self.state.ai_score:,} - {self.state.live_score:,} Live")
        logger.info(f"   Series: AI {self.state.ai_wins} - {self.state.live_wins} Live")
        logger.info(f"{'='*60}\n")

        # Callbacks
        for cb in self._on_round_end_callbacks:
            try:
                cb(result, self.get_stats())
            except Exception as e:
                logger.error(f"Round end callback error: {e}")

        return result

    def _simulate_live_gift(self):
        """Simulate a gift from the 'live' stream (for simulation mode)."""
        if not self.state.battle_active:
            return

        # Random chance of gift each tick
        if random.random() > 0.15:  # ~15% chance per second
            return

        # Simulated gifters
        gifters = ["SimUser123", "GiftFan99", "TikTokLover", "StreamSupporter", "RoseQueen",
                   "DiamondKing", "SuperFan2025", "LoyalViewer", "GiftMaster"]

        # Gift selection weighted by probability
        gift_choices = [
            ("Rose", 0.5),
            ("Ice Cream Cone", 0.2),
            ("Doughnut", 0.15),
            ("GG", 0.08),
            ("Hat and Mustache", 0.04),
            ("Lion", 0.02),
            ("Universe", 0.01),
        ]

        # Weighted random selection
        r = random.random()
        cumulative = 0
        selected_gift = "Rose"
        for gift, prob in gift_choices:
            cumulative += prob
            if r <= cumulative:
                selected_gift = gift
                break

        gift_obj = TIKTOK_GIFTS_CATALOG.get(selected_gift)
        if gift_obj:
            coins = gift_obj.coins
            gift_id = hash(selected_gift) % 10000
        else:
            coins = 1
            gift_id = 0
        repeat_count = random.choices([1, 2, 3, 5, 10], weights=[0.6, 0.2, 0.1, 0.07, 0.03])[0]

        event = LiveGiftEvent(
            timestamp=datetime.now(),
            username=random.choice(gifters),
            user_id=str(random.randint(10000000, 99999999)),
            gift_name=selected_gift,
            gift_id=gift_id,
            coin_value=coins,
            repeat_count=repeat_count,
            repeat_end=True,
            streak_id=f"sim_{random.randint(1000, 9999)}",
            team="opponent"
        )

        self._handle_live_gift(event)

    async def start_battle(self) -> dict:
        """Start the AI vs Live battle."""
        self._running = True
        simulation_mode = self.mode == AIBattleMode.SIMULATION

        if not simulation_mode:
            if not TIKTOK_LIVE_AVAILABLE:
                raise RuntimeError("TikTokLive library not available")

            # Connect to live stream using background connection
            logger.info(f"🔌 Connecting to @{self.target_streamer}...")

            self.connector = TikTokLiveConnector(self.target_streamer)
            # Register gift callback BEFORE connecting so we catch all gifts
            self.connector.on_gift(self._handle_live_gift)

            # Start background connection - waits up to 15s for first connect
            # but battle will start even if connection isn't established yet
            connected = await self.connector.connect_background(timeout=15.0)

            if connected:
                self.state.connected = True
                logger.info(f"✅ Connected to @{self.target_streamer}")
                # Notify connection
                for cb in self._on_connection_callbacks:
                    try:
                        cb(True, self.target_streamer)
                    except:
                        pass
            else:
                # Connection still trying in background - start battle anyway
                logger.warning(f"⚠️ Still connecting to @{self.target_streamer}...")
                logger.info("🎮 Starting battle - gifts will be tracked when connected")
                self.state.connected = False

                # Notify partial connection
                for cb in self._on_connection_callbacks:
                    try:
                        cb(True, f"{self.target_streamer} (CONNECTING...)")
                    except:
                        pass

        else:
            logger.info(f"🎮 SIMULATION MODE - Simulating @{self.target_streamer}")
            self.state.connected = True
            for cb in self._on_connection_callbacks:
                try:
                    cb(True, f"{self.target_streamer} (SIMULATED)")
                except:
                    pass

        # Determine number of rounds
        # Support tournaments in both TOURNAMENT and SIMULATION modes
        if self.mode == AIBattleMode.TOURNAMENT or (self.mode == AIBattleMode.SIMULATION and self.tournament_format.value > 1):
            wins_needed = (self.tournament_format.value // 2) + 1
            max_rounds = self.tournament_format.value
        else:
            wins_needed = 1
            max_rounds = 1

        # Run rounds
        while self._running:
            # Check if tournament is decided
            if self.state.ai_wins >= wins_needed or self.state.live_wins >= wins_needed:
                break
            if self.state.current_round > max_rounds:
                break

            # Run round
            await self._run_round()

            # Break between rounds (if more rounds)
            if self._running and self.state.current_round < max_rounds:
                if self.state.ai_wins < wins_needed and self.state.live_wins < wins_needed:
                    cooldown = BATTLE_COOLDOWN_SECONDS  # 2 min 30 sec official
                    logger.info(f"⏸️  {cooldown}s cooldown (2 min 30 sec)...")
                    await asyncio.sleep(cooldown)
                    self.state.current_round += 1

        # Disconnect
        await self.stop()

        # Final result
        final_winner = "ai" if self.state.ai_wins > self.state.live_wins else "live"

        stats = self.get_stats()
        stats['final_winner'] = final_winner

        logger.info(f"\n{'='*60}")
        logger.info(f"🏆 BATTLE COMPLETE")
        logger.info(f"   Champion: {'🔵 AI TEAM' if final_winner == 'ai' else '🔴 LIVE STREAM'}")
        logger.info(f"   Series: AI {self.state.ai_wins} - {self.state.live_wins} Live")
        logger.info(f"{'='*60}\n")

        # Callbacks
        for cb in self._on_battle_end_callbacks:
            try:
                cb(final_winner, stats)
            except Exception as e:
                logger.error(f"Battle end callback error: {e}")

        return stats

    async def stop(self):
        """Stop the battle."""
        self._running = False
        self.state.battle_active = False

        if self.connector:
            await self.connector.disconnect()
            self.state.connected = False

    def get_stats(self) -> dict:
        """Get current battle statistics."""
        total_ai_score = sum(r.ai_score for r in self.state.rounds)
        total_live_score = sum(r.live_score for r in self.state.rounds)
        total_ai_gifts = sum(r.ai_gifts for r in self.state.rounds)
        total_live_gifts = sum(r.live_gifts for r in self.state.rounds)

        return {
            'mode': self.mode.value,
            'target_streamer': self.target_streamer,
            'series_score': f"AI {self.state.ai_wins} - {self.state.live_wins} Live",
            'ai_wins': self.state.ai_wins,
            'live_wins': self.state.live_wins,
            'rounds_played': len(self.state.rounds),
            'total_ai_score': total_ai_score,
            'total_live_score': total_live_score,
            'total_ai_gifts': total_ai_gifts,
            'total_live_gifts': total_live_gifts,
            'ai_team': [
                {
                    'name': a.name,
                    'emoji': a.emoji,
                    'gifts': a.gifts_sent,
                    'points': a.points_generated,
                    'coins_spent': a.spent_coins
                }
                for a in self.ai_agents
            ],
            'rounds': [
                {
                    'round': r.round_number,
                    'winner': r.winner,
                    'ai_score': r.ai_score,
                    'live_score': r.live_score,
                    'top_ai': r.top_ai_agent,
                    'top_live': r.top_live_gifter
                }
                for r in self.state.rounds
            ]
        }

    # Callback registration
    def on_ai_gift(self, callback: Callable):
        self._on_ai_gift_callbacks.append(callback)

    def on_live_gift(self, callback: Callable):
        self._on_live_gift_callbacks.append(callback)

    def on_score_update(self, callback: Callable):
        self._on_score_update_callbacks.append(callback)

    def on_round_end(self, callback: Callable):
        self._on_round_end_callbacks.append(callback)

    def on_battle_end(self, callback: Callable):
        self._on_battle_end_callbacks.append(callback)

    def on_connection(self, callback: Callable):
        self._on_connection_callbacks.append(callback)

    def on_counter_attack(self, callback: Callable):
        """Register callback for counter-attack events."""
        self._on_counter_attack_callbacks.append(callback)

    def on_live_fest_detected(self, callback: Callable):
        """Register callback for Live Fest campaign detection."""
        self._on_live_fest_callbacks.append(callback)
