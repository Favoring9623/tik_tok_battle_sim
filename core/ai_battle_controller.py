#!/usr/bin/env python3
"""
AI Battle Controller - Intelligent gift sending for TikTok battles

Reads live battle scores from browser, makes AI decisions,
and sends gifts strategically to win battles.

Features:
- Real-time score reading via Playwright
- Multiple AI strategies (aggressive, defensive, sniper, smart)
- Automatic gift selection based on battle state
- Budget management and efficiency optimization
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Callable, Any

from playwright.async_api import Page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIBattleController")


class BattleState(Enum):
    """Current state of the battle."""
    UNKNOWN = "unknown"
    NO_BATTLE = "no_battle"
    ACTIVE = "active"
    ENDING = "ending"      # Last 30 seconds
    FINAL = "final"        # Last 10 seconds
    FINISHED = "finished"


class AIStrategy(Enum):
    """AI decision strategies."""
    AGGRESSIVE = "aggressive"   # Always sending at max rate
    DEFENSIVE = "defensive"     # Only send when behind
    SNIPER = "sniper"           # Wait and strike at end
    SMART = "smart"             # Adaptive based on situation
    CONSERVATIVE = "conservative"  # Minimal spending, maintain lead


@dataclass
class BattleScore:
    """Current battle score data."""
    our_score: int = 0
    opponent_score: int = 0
    our_name: str = ""
    opponent_name: str = ""
    time_remaining: int = 0
    battle_active: bool = False

    @property
    def gap(self) -> int:
        """Score gap (positive = winning, negative = losing)."""
        return self.our_score - self.opponent_score

    @property
    def is_winning(self) -> bool:
        return self.gap > 0

    @property
    def is_losing(self) -> bool:
        return self.gap < 0

    @property
    def is_tied(self) -> bool:
        return self.gap == 0

    @property
    def gap_percentage(self) -> float:
        """Gap as percentage of total score."""
        total = self.our_score + self.opponent_score
        if total == 0:
            return 0.0
        return (self.gap / total) * 100


@dataclass
class AIDecision:
    """AI decision for what action to take."""
    should_send: bool = False
    gift_name: str = "Fest Pop"
    quantity: int = 0
    urgency: str = "normal"  # low, normal, high, critical
    reason: str = ""
    cps: float = 6.0


@dataclass
class AIConfig:
    """Configuration for AI behavior."""
    strategy: AIStrategy = AIStrategy.SMART
    target_streamer: str = ""
    gift_name: str = "Fest Pop"

    # Budget limits
    max_gifts_per_minute: int = 500
    max_total_gifts: int = 10000
    min_gap_to_relax: int = 1000  # Points ahead to slow down

    # Decision thresholds
    critical_gap_behind: int = -2000  # Emergency mode
    comfortable_gap_ahead: int = 500  # Can slow down
    sniper_time_threshold: int = 30   # Seconds remaining to activate sniper

    # Speed settings
    normal_cps: float = 6.0
    fast_cps: float = 10.0
    turbo_cps: float = 12.0


class BattleScoreReader:
    """Reads battle scores from TikTok page via Playwright."""

    def __init__(self, page: Page):
        self.page = page
        self._last_score = BattleScore()

    async def read_score(self) -> BattleScore:
        """Read current battle score from page."""
        try:
            # Try to find battle panel elements
            score_data = await self.page.evaluate("""
                () => {
                    const result = {
                        our_score: 0,
                        opponent_score: 0,
                        our_name: '',
                        opponent_name: '',
                        time_remaining: 0,
                        battle_active: false
                    };

                    // Method 1: Find battle bar elements by TikTok class pattern
                    // TikTok battle bar uses classes like 'ecft6fa*' for score elements
                    // Left score is around x < 500, right score is around x > 600
                    // Both are in y range 50-150px

                    const scoreElements = [];

                    // Look for elements with ecft6fa class pattern (TikTok battle bar)
                    const battleElements = document.querySelectorAll('[class*="ecft6fa"]');

                    for (const el of battleElements) {
                        const text = el.innerText?.trim() || '';
                        // Match 4-6 digit numbers (typical battle scores)
                        if (text.match(/^\\d{4,6}$/)) {
                            const rect = el.getBoundingClientRect();
                            // Battle bar is in the top area (y between 50-150px)
                            if (rect.y > 40 && rect.y < 160) {
                                scoreElements.push({
                                    value: parseInt(text),
                                    x: rect.x,
                                    y: rect.y
                                });
                            }
                        }
                    }

                    // Deduplicate scores (same value at similar position)
                    const uniqueScores = [];
                    for (const score of scoreElements) {
                        const isDupe = uniqueScores.some(s =>
                            s.value === score.value && Math.abs(s.x - score.x) < 50
                        );
                        if (!isDupe) {
                            uniqueScores.push(score);
                        }
                    }

                    // Sort by x position: left = our score, right = opponent
                    if (uniqueScores.length >= 2) {
                        uniqueScores.sort((a, b) => a.x - b.x);
                        result.our_score = uniqueScores[0].value;
                        result.opponent_score = uniqueScores[uniqueScores.length - 1].value;
                        result.battle_active = true;
                    }

                    // Method 2: Fallback - find scores by position if ecft6fa not found
                    if (!result.battle_active) {
                        const walker = document.createTreeWalker(
                            document.body, NodeFilter.SHOW_TEXT, null, false
                        );
                        const candidates = [];

                        while (walker.nextNode()) {
                            const text = walker.currentNode.textContent.trim();
                            if (text.match(/^\\d{4,6}$/)) {
                                const el = walker.currentNode.parentElement;
                                const rect = el?.getBoundingClientRect();
                                if (rect && rect.y > 40 && rect.y < 160) {
                                    candidates.push({
                                        value: parseInt(text),
                                        x: rect.x,
                                        y: rect.y
                                    });
                                }
                            }
                        }

                        // Deduplicate
                        const unique = [];
                        for (const c of candidates) {
                            const isDupe = unique.some(u =>
                                u.value === c.value && Math.abs(u.x - c.x) < 50
                            );
                            if (!isDupe) unique.push(c);
                        }

                        if (unique.length >= 2) {
                            unique.sort((a, b) => a.x - b.x);
                            result.our_score = unique[0].value;
                            result.opponent_score = unique[unique.length - 1].value;
                            result.battle_active = true;
                        }
                    }

                    // Method 3: Find timer (MM:SS format)
                    const allText = document.body.innerText;
                    const timerMatch = allText.match(/(\\d{1,2}):(\\d{2})/);
                    if (timerMatch) {
                        const mins = parseInt(timerMatch[1]);
                        const secs = parseInt(timerMatch[2]);
                        // Battle timers are usually under 10 minutes
                        if (mins < 10) {
                            result.time_remaining = mins * 60 + secs;
                        }
                    }

                    // Method 4: Detect "WIN" badge
                    if (allText.includes('WIN x') || allText.includes('WIN X')) {
                        result.battle_active = true;
                    }

                    return result;
                }
            """)

            self._last_score = BattleScore(
                our_score=score_data.get('our_score', 0),
                opponent_score=score_data.get('opponent_score', 0),
                our_name=score_data.get('our_name', ''),
                opponent_name=score_data.get('opponent_name', ''),
                time_remaining=score_data.get('time_remaining', 0),
                battle_active=score_data.get('battle_active', False)
            )

            return self._last_score

        except Exception as e:
            logger.warning(f"Error reading score: {e}")
            return self._last_score

    async def detect_battle_state(self) -> BattleState:
        """Detect current battle state."""
        score = await self.read_score()

        if not score.battle_active:
            return BattleState.NO_BATTLE

        if score.time_remaining <= 0:
            return BattleState.FINISHED
        elif score.time_remaining <= 10:
            return BattleState.FINAL
        elif score.time_remaining <= 30:
            return BattleState.ENDING
        else:
            return BattleState.ACTIVE


class BattleAI:
    """AI decision engine for battle strategy."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._gifts_sent_this_minute = 0
        self._total_gifts_sent = 0
        self._minute_start = datetime.now()
        self._last_decision_time = None

    def decide(self, score: BattleScore, state: BattleState) -> AIDecision:
        """Make a decision based on current battle state."""

        # Reset minute counter if needed
        now = datetime.now()
        if (now - self._minute_start).seconds >= 60:
            self._gifts_sent_this_minute = 0
            self._minute_start = now

        # Check budget limits
        if self._total_gifts_sent >= self.config.max_total_gifts:
            return AIDecision(
                should_send=False,
                reason="Budget limit reached"
            )

        if self._gifts_sent_this_minute >= self.config.max_gifts_per_minute:
            return AIDecision(
                should_send=False,
                reason="Per-minute limit reached"
            )

        # Battle state checks
        if state == BattleState.NO_BATTLE:
            return AIDecision(should_send=False, reason="No active battle")

        if state == BattleState.FINISHED:
            return AIDecision(should_send=False, reason="Battle finished")

        # Strategy-specific decisions
        if self.config.strategy == AIStrategy.AGGRESSIVE:
            return self._aggressive_decision(score, state)
        elif self.config.strategy == AIStrategy.DEFENSIVE:
            return self._defensive_decision(score, state)
        elif self.config.strategy == AIStrategy.SNIPER:
            return self._sniper_decision(score, state)
        elif self.config.strategy == AIStrategy.CONSERVATIVE:
            return self._conservative_decision(score, state)
        else:  # SMART
            return self._smart_decision(score, state)

    def _aggressive_decision(self, score: BattleScore, state: BattleState) -> AIDecision:
        """Aggressive: Always send at max rate."""
        urgency = "critical" if state == BattleState.FINAL else "high"

        return AIDecision(
            should_send=True,
            gift_name=self.config.gift_name,
            quantity=50,  # Bursts of 50
            urgency=urgency,
            reason="Aggressive: Max pressure",
            cps=self.config.turbo_cps
        )

    def _defensive_decision(self, score: BattleScore, state: BattleState) -> AIDecision:
        """Defensive: Only send when behind."""
        if score.is_winning and score.gap > self.config.comfortable_gap_ahead:
            return AIDecision(
                should_send=False,
                reason=f"Winning by {score.gap} - maintaining lead"
            )

        if score.is_losing:
            quantity = min(100, abs(score.gap) // 10)
            urgency = "critical" if score.gap < self.config.critical_gap_behind else "high"

            return AIDecision(
                should_send=True,
                gift_name=self.config.gift_name,
                quantity=max(20, quantity),
                urgency=urgency,
                reason=f"Behind by {abs(score.gap)} - catching up",
                cps=self.config.fast_cps if urgency == "critical" else self.config.normal_cps
            )

        # Tied or slightly ahead
        return AIDecision(
            should_send=True,
            gift_name=self.config.gift_name,
            quantity=20,
            urgency="normal",
            reason="Maintaining position",
            cps=self.config.normal_cps
        )

    def _sniper_decision(self, score: BattleScore, state: BattleState) -> AIDecision:
        """Sniper: Wait and strike at the end."""
        if state not in [BattleState.ENDING, BattleState.FINAL]:
            # Save resources, send minimally
            if score.is_losing and score.gap < -500:
                return AIDecision(
                    should_send=True,
                    gift_name=self.config.gift_name,
                    quantity=10,
                    urgency="low",
                    reason="Sniper: Minimal pressure before final",
                    cps=self.config.normal_cps
                )
            return AIDecision(
                should_send=False,
                reason="Sniper: Waiting for final moments"
            )

        # Final moments - GO ALL IN
        return AIDecision(
            should_send=True,
            gift_name=self.config.gift_name,
            quantity=200,  # Large burst
            urgency="critical",
            reason=f"SNIPER STRIKE! {score.time_remaining}s remaining",
            cps=self.config.turbo_cps
        )

    def _conservative_decision(self, score: BattleScore, state: BattleState) -> AIDecision:
        """Conservative: Minimal spending, maintain lead."""
        if score.is_winning and score.gap > self.config.min_gap_to_relax:
            return AIDecision(
                should_send=False,
                reason=f"Conservative: Comfortable lead of {score.gap}"
            )

        # Only send enough to stay ahead
        if score.is_losing or score.is_tied:
            return AIDecision(
                should_send=True,
                gift_name=self.config.gift_name,
                quantity=10,
                urgency="normal",
                reason="Conservative: Minimal push to gain lead",
                cps=self.config.normal_cps
            )

        return AIDecision(
            should_send=False,
            reason="Conservative: Maintaining lead without spending"
        )

    def _smart_decision(self, score: BattleScore, state: BattleState) -> AIDecision:
        """Smart: Adaptive strategy based on situation."""

        # Final moments - all in
        if state == BattleState.FINAL:
            return AIDecision(
                should_send=True,
                gift_name=self.config.gift_name,
                quantity=100,
                urgency="critical",
                reason="FINAL PUSH!",
                cps=self.config.turbo_cps
            )

        # Ending phase
        if state == BattleState.ENDING:
            if score.is_losing:
                return AIDecision(
                    should_send=True,
                    gift_name=self.config.gift_name,
                    quantity=50,
                    urgency="high",
                    reason=f"Ending phase: Behind by {abs(score.gap)}",
                    cps=self.config.fast_cps
                )
            else:
                return AIDecision(
                    should_send=True,
                    gift_name=self.config.gift_name,
                    quantity=30,
                    urgency="normal",
                    reason="Ending phase: Securing lead",
                    cps=self.config.normal_cps
                )

        # Active battle
        if score.gap < self.config.critical_gap_behind:
            # Emergency!
            return AIDecision(
                should_send=True,
                gift_name=self.config.gift_name,
                quantity=100,
                urgency="critical",
                reason=f"EMERGENCY: Behind by {abs(score.gap)}!",
                cps=self.config.turbo_cps
            )

        if score.is_losing:
            return AIDecision(
                should_send=True,
                gift_name=self.config.gift_name,
                quantity=30,
                urgency="high",
                reason=f"Catching up: {abs(score.gap)} behind",
                cps=self.config.fast_cps
            )

        if score.gap > self.config.min_gap_to_relax:
            return AIDecision(
                should_send=True,
                gift_name=self.config.gift_name,
                quantity=10,
                urgency="low",
                reason=f"Comfortable lead: {score.gap} ahead",
                cps=self.config.normal_cps
            )

        # Tied or small lead
        return AIDecision(
            should_send=True,
            gift_name=self.config.gift_name,
            quantity=20,
            urgency="normal",
            reason="Maintaining pressure",
            cps=self.config.normal_cps
        )

    def record_send(self, quantity: int):
        """Record that gifts were sent."""
        self._gifts_sent_this_minute += quantity
        self._total_gifts_sent += quantity


class AIBattleController:
    """
    Main controller that combines score reading, AI decisions, and gift sending.
    """

    def __init__(
        self,
        page: Page,
        config: AIConfig,
        gift_sender=None  # TikTokGiftSender instance
    ):
        self.page = page
        self.config = config
        self.gift_sender = gift_sender

        self.score_reader = BattleScoreReader(page)
        self.ai = BattleAI(config)

        self._running = False
        self._callbacks: List[Callable] = []

        # Stats
        self.stats = {
            "decisions_made": 0,
            "gifts_sent": 0,
            "gifts_failed": 0,
            "start_time": None,
            "last_score": None,
            "last_decision": None
        }

    def on_decision(self, callback: Callable[[AIDecision, BattleScore], Any]):
        """Register callback for decisions."""
        self._callbacks.append(callback)
        return self

    async def _emit_decision(self, decision: AIDecision, score: BattleScore):
        """Emit decision to callbacks."""
        for callback in self._callbacks:
            try:
                result = callback(decision, score)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def run_battle_ai(self, duration: int = 300):
        """
        Run the AI battle controller for specified duration.

        Args:
            duration: Maximum duration in seconds
        """
        logger.info(f"""
{'='*60}
AI BATTLE CONTROLLER STARTING
{'='*60}
Strategy: {self.config.strategy.value}
Target: @{self.config.target_streamer}
Gift: {self.config.gift_name}
Duration: {duration}s
{'='*60}
        """)

        self._running = True
        self.stats["start_time"] = datetime.now()

        start_time = datetime.now()

        while self._running:
            # Check duration
            elapsed = (datetime.now() - start_time).seconds
            if elapsed >= duration:
                logger.info("Duration limit reached")
                break

            try:
                # Read score
                score = await self.score_reader.read_score()
                state = await self.score_reader.detect_battle_state()

                self.stats["last_score"] = score

                # Get AI decision
                decision = self.ai.decide(score, state)
                self.stats["decisions_made"] += 1
                self.stats["last_decision"] = decision

                # Log decision
                if decision.should_send:
                    logger.info(
                        f"[{state.value.upper()}] Score: {score.our_score:,} vs {score.opponent_score:,} | "
                        f"Gap: {score.gap:+,} | Decision: {decision.reason}"
                    )

                # Emit to callbacks
                await self._emit_decision(decision, score)

                # Execute decision
                if decision.should_send and self.gift_sender:
                    try:
                        result = await self.gift_sender.send_gifts(
                            username=self.config.target_streamer,
                            gift_name=decision.gift_name,
                            quantity=decision.quantity,
                            cps=decision.cps
                        )

                        if result.success:
                            self.ai.record_send(result.sent)
                            self.stats["gifts_sent"] += result.sent
                            self.stats["gifts_failed"] += result.failed
                            logger.info(f"Sent {result.sent} {decision.gift_name}")
                        else:
                            logger.warning(f"Send failed: {result.message}")

                    except Exception as e:
                        logger.error(f"Gift sending error: {e}")

                # Wait before next decision
                wait_time = 2.0 if decision.urgency == "critical" else 5.0
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Battle loop error: {e}")
                await asyncio.sleep(5)

        self._running = False

        # Final stats
        total_time = (datetime.now() - self.stats["start_time"]).seconds
        logger.info(f"""
{'='*60}
AI BATTLE CONTROLLER FINISHED
{'='*60}
Duration: {total_time}s
Decisions: {self.stats['decisions_made']}
Gifts sent: {self.stats['gifts_sent']:,}
Gifts failed: {self.stats['gifts_failed']}
{'='*60}
        """)

        return self.stats

    def stop(self):
        """Stop the battle AI."""
        self._running = False


async def main():
    """Demo without actual gift sending."""
    from playwright.async_api import async_playwright

    print("""
╔══════════════════════════════════════════════════════════════════╗
║   AI BATTLE CONTROLLER - DEMO MODE                               ║
╠══════════════════════════════════════════════════════════════════╣
║   This demo reads scores but doesn't send gifts                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    username = input("Streamer username to watch: ").strip()
    if not username:
        username = "liznogalh"

    strategy = input("Strategy (aggressive/defensive/sniper/smart/conservative): ").strip()
    try:
        strat = AIStrategy(strategy.lower())
    except:
        strat = AIStrategy.SMART

    config = AIConfig(
        strategy=strat,
        target_streamer=username,
        gift_name="Fest Pop"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state="data/tiktok_session/state.json",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        # Navigate to stream
        print(f"\nConnecting to @{username}...")
        await page.goto(f"https://www.tiktok.com/@{username}/live")
        await asyncio.sleep(5)

        # Create controller (no gift sender = demo mode)
        controller = AIBattleController(page, config)

        # Callback to display decisions
        def on_decision(decision, score):
            print(f"""
┌─────────────────────────────────────────────────────────┐
│ Score: {score.our_score:>8,} vs {score.opponent_score:<8,} (Gap: {score.gap:+,})
│ Battle: {'ACTIVE' if score.battle_active else 'INACTIVE'} | Time: {score.time_remaining}s
├─────────────────────────────────────────────────────────┤
│ Decision: {'SEND' if decision.should_send else 'WAIT'}
│ Reason: {decision.reason}
│ Urgency: {decision.urgency} | CPS: {decision.cps}
└─────────────────────────────────────────────────────────┘
            """)

        controller.on_decision(on_decision)

        try:
            await controller.run_battle_ai(duration=120)  # 2 min demo
        except KeyboardInterrupt:
            print("\nStopping...")
            controller.stop()
        finally:
            await context.storage_state(path="data/tiktok_session/state.json")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
