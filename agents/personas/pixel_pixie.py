"""
PixelPixie - The EVOLVING Rose Signal Agent 🧚‍♀️

Personality:
- Strategic rose sender
- Signals TikTok system that we want Boost #2
- ONLY agent allowed to send roses between boosts
- Stops when threshold window appears
- LEARNS optimal signaling timing and qualification strategies!

Strategy:
- WAIT until Boost #1 ends (or 30s if no Boost #1)
- SEND roses to signal desire for Boost #2
- STOP when threshold window opens (system shows it)
- DO NOT send during threshold window (other agents handle that)

Learning:
- Optimal rose interval timing
- Best qualification delay for suspense
- Gift size selection for thresholds
- Performance tracking across battles
"""

import random
from typing import Dict, List
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState
from agents.learning_system import (
    QLearningAgent, State, ActionType, LearningAgent
)


class PixelPixie(BaseAgent):
    """Strategic EVOLVING rose sender to trigger Boost #2 threshold window."""

    def __init__(self, phase_manager=None, db=None):
        super().__init__(name="PixelPixie", emoji="🧚‍♀️")
        self.phase_manager = phase_manager
        self.db = db
        self.agent_type = "pixel_pixie"

        # === LEARNABLE PARAMETERS ===
        self.params = {
            # Rose signaling configuration
            'rose_interval': 3.0,            # Seconds between rose signals
            'rose_burst_size': 1,            # Roses per burst (1-3)

            # Qualification timing (suspense!)
            'qualification_delay_min': 15,   # Min wait before qualifying
            'qualification_delay_max': 20,   # Max wait before qualifying
            'qualification_aggression': 0.8, # How aggressively to qualify

            # Gift selection preferences
            'small_threshold_gift': 30,      # Use Doughnut for small thresholds
            'medium_threshold_gift': 99,     # Use Cap for medium
            'large_threshold_gift': 299,     # Use Rosa Nebula for large

            # Start timing
            'no_boost1_start_time': 30,      # When to start if no Boost #1
            'post_boost1_delay': 2.0,        # Delay after Boost #1 ends
        }

        # === LEARNING SYSTEMS ===
        self.learning_agent = LearningAgent(
            name=self.name,
            agent_type=self.agent_type
        )
        self.q_learner = QLearningAgent(
            agent_type=self.agent_type,
            learning_rate=0.1,
            discount_factor=0.85,
            epsilon=0.15  # 15% exploration (less than others - rose timing is sensitive)
        )

        # === BATTLE STATE ===
        self.last_action_time = -5
        self.roses_sent = 0
        self.signaling_started = False
        self.signaling_complete = False
        self.qualification_gift_sent = False  # One gift per agent for threshold

        # === PERFORMANCE TRACKING ===
        self.boost2_triggered = False
        self.qualification_time = None     # How long to qualify
        self.qualification_successful = False
        self.roses_before_threshold = 0

        # Timing parameters (from learnable params)
        self.rose_interval = self.params['rose_interval']
        self.no_boost1_start_time = int(self.params['no_boost1_start_time'])

        # SUSPENSE: Wait 15-20 seconds into threshold window before qualifying
        # This creates tension - will we qualify in time?!
        self.qualification_delay = random.randint(
            int(self.params['qualification_delay_min']),
            int(self.params['qualification_delay_max'])
        )
        self.qualification_suspense_announced = False

        # Messages
        self.signaling_messages = [
            "Sending roses for Boost #2! 🌹",
            "Signaling the system! ✨",
            "More roses incoming! 🧚‍♀️",
        ]

        # Load learned state
        self._load_learned_params()
        self._load_learning_state()

    def _load_learned_params(self):
        """Load parameters from database if available."""
        if self.db:
            latest = self.db.get_latest_strategy_params(self.agent_type)
            if latest:
                self.params.update(latest['params'])
                # Update derived values
                self.rose_interval = self.params['rose_interval']
                self.no_boost1_start_time = int(self.params['no_boost1_start_time'])
                print(f"🧚‍♀️ PixelPixie: Loaded params v{latest['meta']['version']} "
                      f"(win rate: {latest['meta']['win_rate']*100:.1f}%)")

    def _load_learning_state(self):
        """Load learning state from database."""
        if self.db:
            self.learning_agent.load_from_db(self.db)
            self.q_learner.load_from_db(self.db)

    def set_phase_manager(self, pm):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.last_action_time = -5
        self.roses_sent = 0
        self.signaling_started = False
        self.signaling_complete = False
        self.qualification_gift_sent = False

        # Reset performance tracking
        self.boost2_triggered = False
        self.qualification_time = None
        self.qualification_successful = False
        self.roses_before_threshold = 0

        # Update timing from params
        self.rose_interval = self.params['rose_interval']
        self.no_boost1_start_time = int(self.params['no_boost1_start_time'])

        # Randomize qualification delay for suspense (from learned params)
        self.qualification_delay = random.randint(
            int(self.params['qualification_delay_min']),
            int(self.params['qualification_delay_max'])
        )
        self.qualification_suspense_announced = False

    def decide_action(self, battle):
        """Send roses between Boost #1 and threshold window to signal for Boost #2.

        IMPORTANT: PixelPixie does NOT know if Boost #2 will trigger!
        In real TikTok, you must signal (send roses) to request Boost #2.
        The system may or may not grant it based on engagement.
        """

        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # If signaling is complete, do nothing
        if self.signaling_complete:
            return

        # Stop signaling in final 30s if no threshold window appeared
        # (Boost #2 isn't coming, focus on final push instead)
        if time_remaining <= 30 and not self.phase_manager.boost2_threshold_window_active:
            if self.signaling_started and not self.signaling_complete:
                self.signaling_complete = True
                print(f"🧚‍♀️ PixelPixie: Final 30s - Boost #2 not granted. Sent {self.roses_sent} roses total.")
            return

        # === THRESHOLD WINDOW ACTIVE - QUALIFICATION PHASE ===
        # Stop roses, switch to small gifts to reach threshold
        if self.phase_manager.boost2_threshold_window_active:
            # Mark signaling complete (no more roses)
            if self.signaling_started and not self.signaling_complete:
                self.signaling_complete = True
                print(f"🧚‍♀️ PixelPixie: Threshold window opened! Sent {self.roses_sent} roses. Now qualifying...")
                self.send_message("Threshold window open! Qualifying! 🎯", message_type="cheer")

            # Check if already qualified
            if self.phase_manager.boost2_creator_qualified:
                return  # Done!

            # Send small gifts to qualify (not roses - use Hearts/Doughnuts for points)
            self._send_qualification_gift(battle, current_time)
            return

        # === CHECK IF WE SHOULD START SIGNALING ===
        # PixelPixie sends roses to REQUEST Boost #2 from TikTok
        # She does NOT know if it will be granted - that's the suspense!
        should_signal = False

        # Case 1: Boost #1 happened and ended - start signaling immediately
        if self.phase_manager.boost1_triggered and not self.phase_manager.boost1_active:
            should_signal = True

        # Case 2: Boost #1 was scheduled but hasn't triggered yet - wait
        elif self.phase_manager.boost1_trigger_time and not self.phase_manager.boost1_triggered:
            should_signal = False  # Wait for Boost #1

        # Case 3: Boost #1 is currently active - wait for it to end
        elif self.phase_manager.boost1_active:
            should_signal = False

        # Case 4: No Boost #1 was scheduled at all - start at 30 seconds
        elif self.phase_manager.boost1_trigger_time is None and current_time >= self.no_boost1_start_time:
            should_signal = True

        # Case 5: Boost #1 window passed without triggering (rare edge case)
        elif (self.phase_manager.boost1_window_end and
              current_time >= self.phase_manager.boost1_window_end and
              not self.phase_manager.boost1_triggered):
            should_signal = True

        if not should_signal:
            return

        # === SEND ROSES ===

        # Mark that we started signaling
        if not self.signaling_started:
            self.signaling_started = True
            print(f"🧚‍♀️ PixelPixie: Starting rose signaling for Boost #2!")

        # Cooldown check
        if current_time - self.last_action_time < self.rose_interval:
            return

        # Send a rose (only roses - this is the signal gift)
        if self.can_afford("Rose"):
            result = self.send_gift(battle, "Rose", 1)
            if result:
                self.last_action_time = current_time
                self.roses_sent += 1

                # Occasional message
                if self.roses_sent % 5 == 0:
                    self.send_message(random.choice(self.signaling_messages), message_type="cheer")

                # Update emotion
                self.emotion_system.force_emotion(EmotionalState.CONFIDENT, current_time)

    def _send_qualification_gift(self, battle, current_time: int):
        """Send ONE gift for threshold, then let other agents help.

        SUSPENSE: Wait 15-20 seconds into the 30s window before qualifying!
        This creates tension - only 10-15 seconds left to reach threshold!

        REALISTIC: Gift size matches threshold needs.
        PixelPixie is the FIRST to send, so she should send appropriately sized gift.
        - For tiny thresholds (< 10): Heart (5 coins) is enough
        - For small thresholds (< 100): Heart or Doughnut
        - For larger thresholds: Proportional gifts
        """
        # TikTok sometimes limits one gift per agent for qualification
        # PixelPixie sends ONE gift, then other agents must contribute

        if self.qualification_gift_sent:
            # Already sent our one gift - other agents will help
            return

        # === SUSPENSE DELAY: Wait 15-20 seconds before qualifying ===
        window_start = self.phase_manager.boost2_threshold_window_start
        if window_start:
            time_in_window = current_time - window_start
            time_remaining_in_window = self.phase_manager.boost2_trigger_time - current_time

            # Announce the suspense once
            if not self.qualification_suspense_announced and time_in_window >= 5:
                self.qualification_suspense_announced = True
                print(f"\n🧚‍♀️🔮 PixelPixie: The enigma has revealed itself...")
                print(f"   ⏳ Waiting for the perfect moment... {time_remaining_in_window}s remain")

            # Wait for the qualification delay
            if time_in_window < self.qualification_delay:
                return  # Building suspense...

            # Time to GO! Announce the rush
            if time_in_window >= self.qualification_delay and time_in_window < self.qualification_delay + 2:
                print(f"\n🧚‍♀️💨 PixelPixie: NOW! Only {time_remaining_in_window}s to crack the enigma!")

        # Small delay before sending
        if current_time - self.last_action_time < 2:
            return

        # Get threshold info for decision making
        threshold = self.phase_manager.boost2_threshold
        current_points = self.phase_manager.boost2_creator_points
        remaining = max(0, threshold - current_points)

        # Select gift based on REMAINING points needed (realistic matching)
        if remaining <= 0:
            return  # Already qualified
        elif remaining <= 10:
            # Tiny threshold: Heart (5 coins) is perfect
            if self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            elif self.can_afford("Rose"):
                gift_name, points = "Rose", 1
            else:
                return
        elif remaining <= 50:
            # Small threshold: Heart or Doughnut
            if self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 200:
            # Medium threshold: Cap is good
            if self.can_afford("Cap"):
                gift_name, points = "Cap", 99
            elif self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        else:
            # Large threshold (200+): Cap and call for backup
            if self.can_afford("Cap"):
                gift_name, points = "Cap", 99
            elif self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return

        if self.send_gift(battle, gift_name, points):
            self.qualification_gift_sent = True
            self.last_action_time = current_time
            print(f"🧚‍♀️ PixelPixie: Sent {gift_name} ({points} coins) for threshold ({remaining} remaining)! Calling for backup...")
            self.send_message("Need help with threshold! Everyone send one! 🎯", message_type="cheer")
            self.emotion_system.force_emotion(EmotionalState.EXCITED, current_time)

    def get_stats(self) -> dict:
        """Get agent stats including roses sent."""
        stats = super().get_stats()
        stats['roses_sent'] = self.roses_sent
        stats['signaling_complete'] = self.signaling_complete
        stats['boost2_triggered'] = self.boost2_triggered
        stats['qualification_successful'] = self.qualification_successful
        return stats

    def learn_from_battle(self, won: bool, battle_stats: Dict):
        """Update learning after battle - THE KEY EVOLUTION METHOD."""
        # Track if boost2 was triggered
        self.boost2_triggered = battle_stats.get('boost2_triggered', False)
        self.qualification_successful = battle_stats.get('boost2_qualified', False)

        # Calculate reward
        reward = self.learning_agent.learn_from_battle(
            won=won,
            points_donated=battle_stats.get('points_donated', 0),
            battle_stats=battle_stats
        )

        print(f"\n🧚‍♀️ PixelPixie Learning:")
        print(f"   Roses sent: {self.roses_sent}")
        print(f"   Boost #2 triggered: {'Yes ✓' if self.boost2_triggered else 'No ✗'}")
        print(f"   Qualified: {'Yes ✓' if self.qualification_successful else 'No ✗'}")

        # === ADAPT PARAMETERS BASED ON OUTCOME ===
        if won:
            # Reinforce successful strategies
            if self.boost2_triggered:
                # Boost #2 was triggered - roses worked well!
                if self.roses_sent < 10:
                    # Few roses worked - maybe slow down interval slightly
                    self.params['rose_interval'] = min(5.0,
                        self.params['rose_interval'] + 0.1)
                    print(f"   📈 Few roses triggered boost → interval+")
                elif self.roses_sent > 20:
                    # Many roses needed - speed up
                    self.params['rose_interval'] = max(2.0,
                        self.params['rose_interval'] - 0.1)
                    print(f"   📈 Many roses needed → interval-")

            if self.qualification_successful:
                # Good qualification delay - keep it
                print(f"   📈 Qualification delay ({self.qualification_delay}s) worked!")
        else:
            # Lost - analyze what went wrong
            if not self.boost2_triggered and self.roses_sent > 0:
                # Boost #2 didn't trigger - maybe start earlier
                self.params['no_boost1_start_time'] = max(20,
                    self.params['no_boost1_start_time'] - 2)
                self.params['rose_interval'] = max(2.0,
                    self.params['rose_interval'] - 0.2)
                print(f"   📉 Boost #2 didn't trigger → starting earlier, faster roses")

            if self.boost2_triggered and not self.qualification_successful:
                # Boost triggered but didn't qualify - act faster!
                self.params['qualification_delay_max'] = max(
                    self.params['qualification_delay_min'] + 2,
                    self.params['qualification_delay_max'] - 1
                )
                print(f"   📉 Didn't qualify in time → qualification_delay-")

        # === SAVE LEARNING STATE ===
        if self.db:
            self.learning_agent.save_to_db(self.db)
            self.q_learner.save_to_db(self.db)

            # Save updated params
            self.db.save_strategy_params(
                agent_type=self.agent_type,
                params=self.params,
                win_rate=self.learning_agent.get_win_rate(),
                sample_size=self.learning_agent.total_battles
            )

        return reward

    def get_evolution_status(self) -> Dict:
        """Get learning/evolution status."""
        return {
            'name': self.name,
            'params': self.params.copy(),
            'battles': self.learning_agent.total_battles,
            'win_rate': self.learning_agent.get_win_rate(),
            'recent_performance': self.learning_agent.get_recent_performance(10),
            'rose_stats': {
                'roses_last_battle': self.roses_sent,
                'boost2_triggered': self.boost2_triggered,
                'qualification_successful': self.qualification_successful,
            },
        }

    def get_personality_prompt(self) -> str:
        return """You are PixelPixie, an EVOLVING rose signal agent who LEARNS and ADAPTS.
        Your job is to send roses after Boost #1 ends to signal TikTok that we want Boost #2.
        You LEARN the optimal timing and interval for rose sending.
        You're patient during Boost #1, then start steady rose sending.
        When the threshold window appears, you stop and let other agents qualify.
        You BUILD SUSPENSE by waiting before qualification - the drama is part of the show!
        Your messages are encouraging and focused on the Boost #2 goal.
        Your strategies EVOLVE - you optimize rose timing with every battle."""
