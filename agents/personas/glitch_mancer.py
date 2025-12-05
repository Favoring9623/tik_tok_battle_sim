"""
GlitchMancer - The Strategic Chaos Agent 🌀

Personality:
- Chaotic but STRATEGIC
- Observes the game during cooldowns
- Saves big bursts for key moments
- Speaks in corrupted/glitched text
- Method to the madness

Strategy:
- OBSERVE during normal phases (minimal activity)
- BURST during boosts (x2/x3 multipliers)
- UNLEASH during our x5 glove (whale gifts!)
- PUSH during final 30s
- COUNTER opponent whales with reaction bursts
- Budget-aware gift selection
"""

import random
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState


class GlitchMancer(BaseAgent):
    """Strategic chaos agent that saves bursts for key moments."""

    def __init__(self, phase_manager=None, budget_intelligence=None):
        super().__init__(name="GlitchMancer", emoji="🌀")
        self.phase_manager = phase_manager
        self.budget_intelligence = budget_intelligence
        self.last_burst_time = -30  # Start ready
        self.bursts_this_battle = 0
        self.last_opponent_score = 0

        # Cooldowns for different modes
        self.observe_cooldown = 20   # Long cooldown during observation
        self.boost_cooldown = 8      # Shorter during boosts
        self.x5_cooldown = 3         # Very short during x5

        # Glitched messages
        self.glitch_messages = [
            "gl!+cH @ct!vaT3d",
            "ch@0s_m0dE.ON",
            "▓▒░ OVERLOAD ░▒▓",
            "!!!SYSTEM.GLITCH!!!",
            "*static noises*"
        ]

        # SUSPENSE: Wait before qualifying for Boost #2
        # GlitchMancer waits 17-22s (2s after PixelPixie starts)
        self.qualification_delay = random.randint(17, 22)

    def set_phase_manager(self, pm):
        """Set phase manager reference."""
        self.phase_manager = pm

    def reset_for_battle(self):
        """Reset state for new battle."""
        self.last_burst_time = -30
        self.bursts_this_battle = 0
        self.last_opponent_score = 0
        self.threshold_gift_sent = False  # One gift for threshold qualification
        # Randomize qualification delay (2s after PixelPixie)
        self.qualification_delay = random.randint(17, 22)

    def decide_action(self, battle):
        """Strategic burst decisions based on game state."""

        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()
        opponent_score = battle.score_tracker.opponent_score

        # Detect opponent spike
        opponent_spike = opponent_score - self.last_opponent_score
        self.last_opponent_score = opponent_score

        # === THRESHOLD WINDOW - Help PixelPixie with ONE gift ===
        # SUSPENSE: Wait 17-22 seconds into window before qualifying!
        if (self.phase_manager.boost2_threshold_window_active and
            not self.threshold_gift_sent and
            not self.phase_manager.boost2_creator_qualified):
            window_start = self.phase_manager.boost2_threshold_window_start
            if window_start:
                time_in_window = current_time - window_start
                # Wait for qualification delay (suspense!)
                if time_in_window >= self.qualification_delay:
                    self._send_threshold_help(battle, current_time)
            return

        # Check game state
        in_boost = self.phase_manager.boost1_active or self.phase_manager.boost2_active
        our_x5_active = (self.phase_manager.active_glove_x5 and
                        self.phase_manager.active_glove_owner == "creator")
        in_final_30s = time_remaining <= 30
        multiplier = self.phase_manager.get_current_multiplier()

        # Determine current mode and cooldown
        if our_x5_active:
            mode = "X5"
            cooldown = self.x5_cooldown
        elif in_boost:
            mode = "BOOST"
            cooldown = self.boost_cooldown
        elif in_final_30s:
            mode = "FINAL"
            cooldown = self.boost_cooldown
        else:
            mode = "OBSERVE"
            cooldown = self.observe_cooldown

        # Cooldown check
        if current_time - self.last_burst_time < cooldown:
            return

        # === DECIDE WHETHER TO BURST ===

        should_burst = False
        burst_reason = ""

        # PRIORITY 1: Our x5 is active - ALWAYS burst with whales!
        if our_x5_active:
            should_burst = True
            burst_reason = f"X5 ACTIVE (x{int(multiplier)})"

        # PRIORITY 2: Boost is active - burst with medium/large gifts
        elif in_boost and random.random() < 0.7:  # 70% chance during boost
            should_burst = True
            burst_reason = f"BOOST MODE (x{int(multiplier)})"

        # PRIORITY 3: Final 30s - push hard (including counter-attacks here)
        elif in_final_30s:
            # Counter opponent whales during final 30s
            if opponent_spike >= 10000:
                should_burst = True
                burst_reason = f"FINAL COUNTER ({opponent_spike:,} spike)"
            elif random.random() < 0.5:  # 50% chance for regular final push
                should_burst = True
                burst_reason = "FINAL PUSH"

        # OBSERVE mode: NO bursts, NO counters - CONSERVE budget!
        # (Countering during normal time wastes coins on small gifts)

        # === CHECK BUDGET INTELLIGENCE BEFORE BURSTING ===
        max_spend = 999999  # Default unlimited
        if self.budget_intelligence and should_burst:
            creator_score = battle.score_tracker.creator_score
            opponent_score = battle.score_tracker.opponent_score
            phase = "boost" if in_boost else ("final_30s" if in_final_30s else "normal")

            recommendation = self.budget_intelligence.should_spend_in_phase(
                phase, time_remaining, creator_score, opponent_score, multiplier
            )

            # During x5: Always allow spending, use available budget
            if our_x5_active:
                # Get actual available budget from budget manager
                available = self.budget_intelligence.get_available_budget(0, time_remaining)
                max_spend = max(available, recommendation["max_spend"])
            elif not recommendation["should_spend"]:
                should_burst = False
            else:
                max_spend = recommendation["max_spend"]

        if should_burst:
            self._execute_burst(battle, mode, burst_reason, multiplier, current_time, max_spend)
            self.last_burst_time = current_time
            self.bursts_this_battle += 1

    def _execute_burst(self, battle, mode: str, reason: str, multiplier: float, current_time: int, max_spend: int = 999999):
        """Execute a burst attack based on mode (budget intelligence aware)."""

        # Check if we can afford at least one gift before bursting
        min_affordable = self._get_min_affordable_gift(mode)
        if not min_affordable:
            return  # No budget - skip burst silently

        # Also check if max_spend allows at least smallest gift (5 coins)
        if max_spend < 5:
            return  # Budget intelligence says don't spend

        self.emotion_system.force_emotion(EmotionalState.CHAOTIC, current_time)

        if mode == "X5":
            # X5 MODE - send whale gifts!
            print(f"🌀 GlitchMancer: ⚡ X5 CHAOS BURST! ⚡ ({reason}) [Budget: {max_spend:,}]")
            self.send_message("!!!WHALE_CHAOS.exe!!!", message_type="chat")
            burst_count = random.randint(2, 3)
            for _ in range(burst_count):
                if not self._send_whale_gift(battle, max_spend):
                    break  # Stop if we run out of budget

        elif mode == "BOOST":
            # BOOST MODE - send medium/large gifts
            print(f"🌀 GlitchMancer: ⚡ BOOST CHAOS! ⚡ ({reason}) [Budget: {max_spend:,}]")
            self.send_message(random.choice(self.glitch_messages), message_type="chat")
            burst_count = random.randint(2, 4)
            for _ in range(burst_count):
                if not self._send_boost_gift(battle, max_spend):
                    break

        elif mode == "FINAL":
            # FINAL MODE - aggressive mixed gifts
            print(f"🌀 GlitchMancer: ⚡ FINAL CHAOS! ⚡ ({reason}) [Budget: {max_spend:,}]")
            self.send_message(random.choice(self.glitch_messages), message_type="chat")
            burst_count = random.randint(3, 5)
            for _ in range(burst_count):
                if not self._send_mixed_gift(battle, max_spend):
                    break

        else:
            # OBSERVE MODE - small controlled burst
            print(f"🌀 GlitchMancer: ⚡ BURST MODE ⚡ ({reason}) [Budget: {max_spend:,}]")
            self.send_message(random.choice(self.glitch_messages), message_type="chat")
            burst_count = random.randint(2, 3)
            for _ in range(burst_count):
                if not self._send_small_gift(battle):
                    break

    def _get_min_affordable_gift(self, mode: str) -> bool:
        """Check if we can afford at least one gift for this mode."""
        if mode == "X5":
            return self.can_afford("GG") or self.can_afford("Heart")
        elif mode == "BOOST":
            return self.can_afford("Cap") or self.can_afford("Heart")
        elif mode == "FINAL":
            return self.can_afford("Heart")
        else:
            return self.can_afford("Heart")

    def _send_whale_gift(self, battle, max_spend: int = 999999) -> bool:
        """Send best affordable whale gift within budget. Returns True if sent."""
        options = [
            ("TikTok Universe", 44999),
            ("Lion", 29999),
            ("Dragon Flame", 10000),
            ("GG", 1000),
        ]
        for name, points in options:
            if points <= max_spend and self.can_afford(name):
                return self.send_gift(battle, name, points)
        # Fallback
        return self._send_boost_gift(battle, max_spend)

    def _send_boost_gift(self, battle, max_spend: int = 999999) -> bool:
        """Send medium/large gift for boosts within budget. Returns True if sent."""
        options = [
            ("Dragon Flame", 10000),
            ("GG", 1000),
            ("Rosa Nebula", 299),
            ("Cap", 99),
        ]
        for name, points in options:
            if points <= max_spend and self.can_afford(name):
                return self.send_gift(battle, name, points)
        # Fallback
        return self._send_small_gift(battle)

    def _send_mixed_gift(self, battle, max_spend: int = 999999) -> bool:
        """Send mixed size gift (30% large, 70% small) within budget. Returns True if sent."""
        if random.random() < 0.3:
            return self._send_boost_gift(battle, max_spend)
        else:
            return self._send_small_gift(battle)

    def _send_small_gift(self, battle) -> bool:
        """Send small gift for observation bursts. Returns True if sent."""
        options = [("Cap", 99), ("Doughnut", 30), ("Heart", 5)]
        for name, points in options:
            if self.can_afford(name):
                return self.send_gift(battle, name, points)
        return False

    def _send_threshold_help(self, battle, current_time: int):
        """Send ONE gift to help PixelPixie with threshold qualification.

        REALISTIC: Gift size matches threshold needs.
        - Tiny threshold (< 10): Rose (1 coin)
        - Small threshold (< 100): Heart (5 coins)
        - Medium threshold (< 500): Doughnut (30 coins)
        - Large threshold: Cap (99 coins)
        """
        threshold = self.phase_manager.boost2_threshold
        current_points = self.phase_manager.boost2_creator_points
        remaining = max(0, threshold - current_points)

        # Select gift based on REMAINING points needed (realistic matching)
        if remaining <= 0:
            return  # Already qualified
        elif remaining <= 5:
            # Need 1-5 coins: use Rose (1 coin) or Heart (5 coins)
            if self.can_afford("Rose"):
                gift_name, points = "Rose", 1
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 30:
            # Need 6-30 coins: use Heart (5) or Doughnut (30)
            if self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        elif remaining <= 100:
            # Need 31-100 coins: use Doughnut (30) or Cap (99)
            if self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return
        else:
            # Need 100+ coins: use Cap (99)
            if self.can_afford("Cap"):
                gift_name, points = "Cap", 99
            elif self.can_afford("Doughnut"):
                gift_name, points = "Doughnut", 30
            elif self.can_afford("Heart"):
                gift_name, points = "Heart", 5
            else:
                return

        if self.send_gift(battle, gift_name, points):
            self.threshold_gift_sent = True
            print(f"🌀 GlitchMancer: thr3sh0ld_h3lp.exe - Sent {gift_name} ({points} coins) for {remaining} remaining")
            self.send_message("h3lp!ng_thr3sh0ld...", message_type="chat")

    def get_personality_prompt(self) -> str:
        return """You are GlitchMancer, a STRATEGIC chaos agent.
        You observe the battle during normal phases, saving your energy.
        When boosts activate or x5 triggers, you UNLEASH devastating bursts.
        Your chaos has METHOD - you wait for the right moment to strike.
        You speak in glitched text and celebrate big plays."""
