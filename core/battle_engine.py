"""
Battle Engine - Core simulation orchestrator.

Coordinates time, scores, agents, and events for a complete battle.
"""

import random
import time as time_module
from typing import List, Optional

from .event_bus import EventBus, EventType
from .time_manager import TimeManager, BattlePhase
from .score_tracker import ScoreTracker
from .multiplier_system import MultiplierManager
from .time_extension_system import TimeExtensionManager
from .battle_analytics import BattleAnalytics
from .visual_utils import (
    Colors, BattleProgressBar, DramaticAnnouncements,
    ASCIIFrames, BattleVisualizer, print_separator
)


class BattleEngine:
    """
    Main battle simulation engine.

    Orchestrates all battle components using event-driven architecture.
    Agents, UI, analytics all listen to events rather than polling.

    Example:
        engine = BattleEngine()
        engine.add_agent(NovaWhale())
        engine.add_agent(PixelPixie())

        # Subscribe to events
        def on_battle_end(event):
            winner = event.data['winner']
            print(f"Winner: {winner}")

        engine.event_bus.subscribe(EventType.BATTLE_ENDED, on_battle_end)
        engine.run()
    """

    def __init__(self,
                 battle_duration: int = 60,
                 tick_speed: float = 0.25,
                 event_bus: Optional[EventBus] = None,
                 enable_multipliers: bool = True,
                 time_extensions: int = 0,
                 enable_analytics: bool = True):
        """
        Initialize battle engine.

        Args:
            battle_duration: Battle length in seconds (default 60)
            tick_speed: Real-time delay between ticks in seconds (default 0.25)
            event_bus: Optional shared event bus (creates new one if not provided)
            enable_multipliers: Enable x2/x3/x5 multiplier system (default True)
            time_extensions: Number of +20s extensions available (default 0)
            enable_analytics: Enable comprehensive battle analytics (default True)
        """
        self.event_bus = event_bus or EventBus()
        self.time_manager = TimeManager(battle_duration)
        self.score_tracker = ScoreTracker()
        self.analytics = BattleAnalytics() if enable_analytics else None
        self.multiplier_manager = MultiplierManager(battle_duration, analytics=self.analytics) if enable_multipliers else None
        self.time_extension_manager = TimeExtensionManager(time_extensions) if time_extensions > 0 else None

        self.agents = []
        self.tick_speed = tick_speed
        self._is_running = False

        # Visual components
        self.progress_bar = BattleProgressBar(width=40)
        self.visualizer = BattleVisualizer(width=70)
        self._last_display_time = -1

        # Subscribe to our own events for internal logic
        self.event_bus.subscribe(EventType.GIFT_SENT, self._handle_gift)

    def add_agent(self, agent):
        """
        Add an AI agent to the battle.

        Args:
            agent: Agent instance (must have .act(engine) method)
        """
        self.agents.append(agent)

        # Give agent access to event bus
        if hasattr(agent, 'event_bus'):
            agent.event_bus = self.event_bus

        self.event_bus.publish(
            EventType.AGENT_JOINED,
            {"agent_name": agent.name},
            source=agent.name
        )

    def run(self, silent: bool = False):
        """
        Run the complete battle simulation.

        Args:
            silent: If True, suppress console output
        """
        self._is_running = True
        self._start_battle(silent)

        # Main battle loop
        while not self.time_manager.is_battle_over() and self._is_running:
            self._tick(silent)
            time_module.sleep(self.tick_speed)

        self._end_battle(silent)

    def _start_battle(self, silent: bool):
        """Initialize and announce battle start."""
        self.time_manager.reset()
        self.score_tracker.reset()
        self.event_bus.clear_history()

        # Initialize multiplier system
        if self.multiplier_manager:
            self.multiplier_manager.initialize_auto_session()

        # Initialize analytics
        if self.analytics:
            self.analytics.record_battle_start(
                duration=self.time_manager.battle_duration,
                agent_count=len(self.agents)
            )

        if not silent:
            # Dramatic battle start announcement
            print(DramaticAnnouncements.battle_start(
                duration=self.time_manager.battle_duration,
                team_size=len(self.agents)
            ))
            print()

            # Show team lineup
            if self.agents:
                print(f"   {Colors.BOLD}TEAM LINEUP{Colors.RESET}")
                print("   " + "─" * 40)
                for agent in self.agents:
                    emoji = getattr(agent, 'emoji', '🤖')
                    name = getattr(agent, 'name', 'Agent')
                    print(f"   {emoji} {name}")
                print("   " + "─" * 40)
                print()

        self.event_bus.publish(
            EventType.BATTLE_STARTED,
            {
                "duration": self.time_manager.battle_duration,
                "agent_count": len(self.agents)
            }
        )

    def _tick(self, silent: bool):
        """Process one second of battle time."""
        current_time = self.time_manager.tick()

        # Update multiplier system
        if self.multiplier_manager:
            self.multiplier_manager.update(current_time)

        # Publish tick event
        self.event_bus.publish(
            EventType.BATTLE_TICK,
            {
                "time": current_time,
                "phase": self.time_manager.get_phase().name,
                "time_remaining": self.time_manager.time_remaining()
            },
            timestamp=current_time
        )

        # Simulate opponent behavior
        self._simulate_opponent_behavior(current_time)

        # Record score snapshot for analytics
        if self.analytics:
            creator_score, opponent_score = self.score_tracker.get_scores()
            self.analytics.record_score_snapshot(
                time=current_time,
                creator_score=creator_score,
                opponent_score=opponent_score,
                phase=self.time_manager.get_phase().name
            )

        # Let all agents act
        for agent in self.agents:
            try:
                agent.act(self)
            except Exception as e:
                self.event_bus.publish(
                    EventType.ERROR_OCCURRED,
                    {"agent": agent.name, "error": str(e)},
                    source=agent.name
                )

        # Check for time extension (if losing)
        self._check_time_extension(current_time)

        # Check for special moments
        self._check_special_moments(current_time)

        # Display current state
        if not silent:
            self._display_state(current_time)

    def _simulate_opponent_behavior(self, current_time: int):
        """
        Simulate opponent gifts (improved strategy).

        Scales based on battle duration:
        - 60s: Spikes at [15, 30, 45, 55]
        - 180s: Spikes at [45, 90, 135, 165]
        """
        duration = self.time_manager.battle_duration

        # Scale spike times based on duration
        if duration >= 180:
            spike_times = [45, 90, 135, 165]  # 180s timeline
            drip_interval = 10  # Every 10s for longer battles
            drip_amount = (100, 300)  # Higher drip for 180s
        else:
            spike_times = [15, 30, 45, 55]  # 60s timeline
            drip_interval = 5
            drip_amount = (50, 150)

        # Major spikes at strategic times (70% chance)
        if current_time in spike_times and random.random() > 0.3:
            # Spike size increases over time (proportional to duration)
            progress = current_time / duration

            if progress <= 0.33:  # Early
                spike = random.randint(400, 800)
            elif progress <= 0.67:  # Mid
                spike = random.randint(600, 1200)
            else:  # Late
                spike = random.randint(800, 1600)

            # Scale spike for longer battles
            if duration >= 180:
                spike = int(spike * 1.5)

            self.score_tracker.add_opponent_points(spike, current_time)

            self.event_bus.publish(
                EventType.SCORE_CHANGED,
                {
                    "side": "opponent",
                    "points": spike,
                    "reason": "spike"
                },
                source="opponent",
                timestamp=current_time
            )

            print(f"[OPPONENT SPIKE] Opponent gains {spike} points ⚡")

        # Gradual drip: small amounts periodically (simulates steady supporters)
        if current_time % drip_interval == 0 and current_time > 0:
            drip = random.randint(*drip_amount)
            self.score_tracker.add_opponent_points(drip, current_time)

    def _handle_gift(self, event):
        """Handle GIFT_SENT events by updating score."""
        base_points = event.data.get("points", 0)
        gift_name = event.data.get("gift", event.data.get("gift_name", "Gift"))
        agent_name = event.source or "Unknown"
        current_time = int(event.timestamp)

        # Apply multiplier if system is active
        final_multiplier = 1.0
        if self.multiplier_manager:
            # Record gift for threshold tracking
            self.multiplier_manager.record_gift(current_time, gift_name, base_points)

            # Apply current multiplier (returns dict with breakdown)
            result = self.multiplier_manager.apply_multiplier(base_points, current_time)
            final_points = result["total_points"]
            final_multiplier = final_points / base_points if base_points > 0 else 1.0

            # Show multiplier effect if active
            if final_points != base_points:
                breakdown = result["breakdown"]

                if result["has_x5"]:
                    # x5 strike active - show full breakdown
                    print(f"   [⚡ MULTIPLIER: {breakdown} = {final_points} points]")
                else:
                    # Regular session multiplier
                    session_mult = result["session_multiplier"]
                    print(f"   [x{session_mult} ACTIVE: {base_points} → {final_points} points]")
        else:
            final_points = base_points

        self.score_tracker.add_creator_points(final_points, current_time)

        # Record action in analytics
        if self.analytics:
            self.analytics.record_action(
                time=current_time,
                agent=agent_name,
                action_type="gift",
                gift_name=gift_name,
                points=final_points,
                multiplier=final_multiplier,
                coordinated=False  # TODO: Hook into coordination system
            )

    def _check_time_extension(self, current_time: int):
        """Check if time extension should be used."""
        if not self.time_extension_manager:
            return

        # Get battle state
        score_diff = self.score_tracker.opponent_score - self.score_tracker.creator_score
        time_remaining = self.time_manager.time_remaining()

        # Evaluate if extension should be used
        should_use = self.time_extension_manager.should_use_extension(
            score_diff=score_diff,
            time_remaining=time_remaining,
            current_time=current_time,
            battle_duration=self.time_manager.base_duration
        )

        if should_use:
            # Use extension
            additional_time = self.time_extension_manager.use_extension(
                current_time=current_time,
                agent_name="TeamStrategy"
            )

            if additional_time:
                # Extend battle duration
                new_duration = self.time_manager.extend_duration(additional_time)

                # Publish event
                self.event_bus.publish(
                    EventType.CRITICAL_MOMENT,  # Reuse for now
                    {
                        "type": "time_extension",
                        "time_added": additional_time,
                        "new_duration": new_duration,
                        "reason": f"Behind by {score_diff} points"
                    },
                    timestamp=current_time
                )

    def _check_special_moments(self, current_time: int):
        """Detect and announce special battle moments."""

        # Check for momentum shift
        if self.score_tracker.check_momentum_shift():
            self.event_bus.publish(
                EventType.MOMENTUM_SHIFT,
                {
                    "new_leader": self.score_tracker.get_leader(),
                    "score_diff": self.score_tracker.get_score_diff()
                },
                timestamp=current_time
            )

        # Check for critical moments (final 10 seconds + close score)
        if self.time_manager.is_critical_moment() and self.score_tracker.is_close_battle():
            self.event_bus.publish(
                EventType.CRITICAL_MOMENT,
                {
                    "time_remaining": self.time_manager.time_remaining(),
                    "score_diff": self.score_tracker.get_score_diff()
                },
                timestamp=current_time
            )

    def _display_state(self, current_time: int):
        """Print current battle state with rich visuals."""
        # Only display every 5 seconds for cleaner output
        if current_time == self._last_display_time:
            return
        if current_time % 5 != 0 and current_time != self.time_manager.battle_duration - 1:
            return
        self._last_display_time = current_time

        creator, opponent = self.score_tracker.get_scores()
        duration = self.time_manager.battle_duration
        remaining = duration - current_time

        # Score bar
        print(f"\n   {self.progress_bar.render_score_bar(creator, opponent)}")

        # Time bar with urgency coloring
        print(f"   {self.progress_bar.render_time_bar(current_time, duration)}")

        # Leader status
        if creator > opponent:
            diff = creator - opponent
            status = f"   {Colors.GREEN}📈 Creator leads by {diff:,}{Colors.RESET}"
        elif opponent > creator:
            diff = opponent - creator
            status = f"   {Colors.RED}📉 Opponent leads by {diff:,}{Colors.RESET}"
        else:
            status = f"   {Colors.YELLOW}⚖️  TIE GAME{Colors.RESET}"
        print(status)

        # Critical moment warning
        if remaining <= 10:
            print(f"   {Colors.RED}{Colors.BOLD}⚠️  FINAL {remaining} SECONDS!{Colors.RESET}")

    def _end_battle(self, silent: bool):
        """Determine winner and publish results."""
        winner = self.score_tracker.get_leader()
        creator, opponent = self.score_tracker.get_scores()
        score_diff = abs(creator - opponent)

        # Record battle end in analytics
        if self.analytics:
            self.analytics.record_battle_end(
                winner=winner or "tie",
                creator_score=creator,
                opponent_score=opponent
            )

        if not silent:
            print("\n")
            if winner == "creator":
                print(DramaticAnnouncements.victory("Creator", score_diff))
            elif winner == "opponent":
                print(DramaticAnnouncements.defeat("Opponent", score_diff))
            else:
                # Tie game
                lines = [
                    "",
                    "🤝🤝🤝  T I E   G A M E  🤝🤝🤝",
                    "",
                    "   An incredible draw!   ",
                    f"   Both sides: {creator:,} points   ",
                    "",
                ]
                print(ASCIIFrames.frame(lines, width=60, box_style="double",
                                        color=Colors.YELLOW))

            # Final score summary
            print()
            print(f"   {Colors.BOLD}FINAL SCORE{Colors.RESET}")
            print(f"   {self.progress_bar.render_score_bar(creator, opponent)}")

        self.event_bus.publish(
            EventType.BATTLE_ENDED,
            {
                "winner": winner or "tie",
                "creator_score": creator,
                "opponent_score": opponent,
                "score_diff": self.score_tracker.get_score_diff(),
                "total_events": len(self.event_bus.get_history())
            }
        )

        # Print analytics summary
        if self.analytics and not silent:
            self.analytics.print_summary()

        self._is_running = False

    def stop(self):
        """Stop the battle early."""
        self._is_running = False

    def get_state(self):
        """Get current battle state snapshot."""
        return {
            "time": self.time_manager.current_time,
            "phase": self.time_manager.get_phase().name,
            "scores": self.score_tracker.get_scores(),
            "leader": self.score_tracker.get_leader(),
            "win_probability": self.score_tracker.get_win_probability(),
            "agent_count": len(self.agents),
            "is_running": self._is_running
        }
