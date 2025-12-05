"""
Strategic AI Agents for Advanced Battle System

Specialized agents for 180s battles with phase system:
- Kinetik: Final sniper (last 5 seconds)
- StrikeMaster: Glove expert with reinforcement learning
- PhaseTracker: Phase monitor and trigger specialist
- LoadoutMaster: Power-up inventory manager
"""

import random
from typing import Optional, Dict, List
from agents.base_agent import BaseAgent
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType


class Kinetik(BaseAgent):
    """
    🔫 Kinetik - The Final Sniper

    Specialty: Last-second interventions

    Strategy:
    - Silent observer until final 5 seconds
    - Analyzes score deficit
    - Deploys massive gifts (Universe, Lion)
    - Can trigger time bonus if losing
    - Calculates comeback probability
    """

    def __init__(self):
        super().__init__(name="Kinetik", emoji="🔫")
        self.has_acted = False
        self.snipe_window = 5  # Last 5 seconds
        self.phase_manager: Optional[AdvancedPhaseManager] = None

    def set_phase_manager(self, manager: AdvancedPhaseManager):
        """Link to phase manager."""
        self.phase_manager = manager

    def decide_action(self, battle):
        """Snipe strategy - wait until final seconds."""
        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score

        # Only act in final window
        if time_remaining > self.snipe_window:
            return

        # Already acted
        if self.has_acted:
            return

        # Calculate if intervention needed
        deficit = opponent_score - creator_score

        if deficit > 0:
            # We're losing - TIME TO SNIPE
            print(f"\n🔫 Kinetik activating! Deficit: {deficit:,} points")

            # Determine snipe power needed (real TikTok coin values)
            if deficit > 30000:
                # Massive deficit - try Universe
                print(f"   🌌 Deploying TikTok Universe for comeback!")
                self.send_gift(battle, "TikTok Universe", 44999)

            elif deficit > 15000:
                # Large deficit - Lion
                print(f"   🦁 Deploying Lion!")
                self.send_gift(battle, "Lion", 29999)

            else:
                # Medium deficit - Dragon Flame
                print(f"   🐉🔥 Deploying Dragon Flame!")
                self.send_gift(battle, "Dragon Flame", 10000)

            self.has_acted = True

            # Check if time bonus needed
            if self.phase_manager:
                # If still losing after snipe, try time bonus
                if opponent_score > creator_score + 10000:
                    print(f"   ⏱️ Requesting TIME BONUS for extra comeback chance!")
                    self.phase_manager.use_power_up(PowerUpType.TIME_BONUS, "creator", current_time)

    def get_personality_prompt(self) -> str:
        return """You are Kinetik, a calculated sniper who strikes at the perfect moment.
        You observe the entire battle in silence, analyzing patterns and deficits.
        When the final seconds arrive, you deploy massive firepower with surgical precision.
        You never waste resources - every strike counts."""


class StrikeMaster(BaseAgent):
    """
    🥊 StrikeMaster - The Glove Strategist

    Specialty: Maximizing Glove x5 activations

    Strategy:
    - Learns optimal Glove timing through experience
    - Tracks x2/x3 phases for maximum chance
    - Uses reinforcement learning (success rate tracking)
    - Adapts strategy based on past results
    """

    def __init__(self):
        super().__init__(name="StrikeMaster", emoji="🥊")
        self.phase_manager: Optional[AdvancedPhaseManager] = None

        # Learning system
        self.glove_attempts = []  # (time, during_boost, last_30s, activated)
        self.success_rate = 0.0
        self.gloves_sent = 0
        self.gloves_activated = 0

        # Strategy params (learned over time)
        self.prefer_boost_phase = True
        self.prefer_last_30s = False
        self.cooldown = 20  # seconds between attempts
        self.last_glove_time = -999

    def set_phase_manager(self, manager: AdvancedPhaseManager):
        """Link to phase manager."""
        self.phase_manager = manager

    def decide_action(self, battle):
        """Glove strategy with learning."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        time_remaining = battle.time_manager.time_remaining()

        # Cooldown check
        if current_time - self.last_glove_time < self.cooldown:
            return

        # Analyze current conditions
        phase_info = self.phase_manager.get_phase_info()
        in_boost = phase_info.get('multiplier', 1.0) > 1.0
        in_last_30s = time_remaining <= 30

        # Decide if conditions are good
        should_send = False

        if self.prefer_boost_phase and in_boost:
            should_send = True
        elif self.prefer_last_30s and in_last_30s:
            should_send = True
        elif in_boost or in_last_30s:
            # Either condition is good
            should_send = random.random() < 0.5

        if should_send:
            print(f"\n🥊 StrikeMaster sending GLOVE!")
            print(f"   Conditions: Boost={in_boost}, Last30s={in_last_30s}")
            print(f"   Success rate: {self.success_rate*100:.1f}% ({self.gloves_activated}/{self.gloves_sent})")

            self.send_gift(battle, "GLOVE", 100)  # Glove gift
            self.last_glove_time = current_time
            self.gloves_sent += 1

            # Track for learning
            # (will be updated post-battle with actual activation status)
            self.glove_attempts.append({
                'time': current_time,
                'in_boost': in_boost,
                'in_last_30s': in_last_30s,
                'activated': None  # Updated later
            })

    def learn_from_result(self, glove_index: int, activated: bool):
        """Update learning based on glove result."""
        if glove_index < len(self.glove_attempts):
            self.glove_attempts[glove_index]['activated'] = activated

            if activated:
                self.gloves_activated += 1

            # Update success rate
            if self.gloves_sent > 0:
                self.success_rate = self.gloves_activated / self.gloves_sent

            # Adapt strategy
            self._adapt_strategy()

    def _adapt_strategy(self):
        """Adapt strategy based on learning."""
        if len(self.glove_attempts) < 3:
            return  # Not enough data

        # Analyze successes
        boost_successes = sum(1 for g in self.glove_attempts
                             if g['activated'] and g['in_boost'])
        last30_successes = sum(1 for g in self.glove_attempts
                              if g['activated'] and g['in_last_30s'])

        boost_attempts = sum(1 for g in self.glove_attempts if g['in_boost'])
        last30_attempts = sum(1 for g in self.glove_attempts if g['in_last_30s'])

        # Calculate rates
        boost_rate = boost_successes / boost_attempts if boost_attempts > 0 else 0
        last30_rate = last30_successes / last30_attempts if last30_attempts > 0 else 0

        # Adapt preferences
        if boost_rate > last30_rate:
            self.prefer_boost_phase = True
            self.prefer_last_30s = False
        else:
            self.prefer_boost_phase = False
            self.prefer_last_30s = True

        print(f"\n📊 StrikeMaster learned: Prefer {'Boost' if self.prefer_boost_phase else 'Last30s'}")

    def get_personality_prompt(self) -> str:
        return """You are StrikeMaster, a martial artist who masters the art of the glove.
        You learn from every battle, adapting your timing to maximize x5 activations.
        You are patient, strategic, and data-driven."""


class PhaseTracker(BaseAgent):
    """
    ⏱️ PhaseTracker - The Phase Monitor

    Specialty: Triggering conditional phases

    Strategy:
    - Monitors phase conditions closely
    - Sends strategic roses to trigger Boost #2
    - Tracks points threshold
    - Ensures maximum phase coverage
    """

    def __init__(self):
        super().__init__(name="PhaseTracker", emoji="⏱️")
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.roses_sent_for_trigger = 0
        self.trigger_attempted = False

    def set_phase_manager(self, manager: AdvancedPhaseManager):
        """Link to phase manager."""
        self.phase_manager = manager

    def decide_action(self, battle):
        """Monitor and trigger phases."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time

        # Check if we're in the trigger window (post Boost #1, pre Boost #2)
        if 60 <= current_time < 90 and not self.trigger_attempted:
            # Check boost2 status
            if not self.phase_manager.boost2.condition_met:
                # Need to trigger it!
                if self.roses_sent_for_trigger < 5:
                    print(f"⏱️ PhaseTracker: Sending strategic Rose #{self.roses_sent_for_trigger + 1}/5 to trigger Boost #2")
                    self.send_gift(battle, "Rose", 1)
                    self.roses_sent_for_trigger += 1
                else:
                    self.trigger_attempted = True

    def get_personality_prompt(self) -> str:
        return """You are PhaseTracker, a temporal specialist who ensures optimal phase sequences.
        You monitor the battle timeline closely, ensuring conditions are met for maximum multiplier coverage.
        You are methodical and precise."""


class LoadoutMaster(BaseAgent):
    """
    🧰 LoadoutMaster - The Inventory Manager

    Specialty: Strategic power-up deployment

    Strategy:
    - Manages team's power-up inventory
    - Deploys Hammer to neutralize opponent x5
    - Uses Fog strategically to hide score
    - Activates Time Bonus when needed
    - Makes tactical decisions based on battle state
    """

    def __init__(self):
        super().__init__(name="LoadoutMaster", emoji="🧰")
        self.phase_manager: Optional[AdvancedPhaseManager] = None
        self.hammer_used = False
        self.fog_used = False

    def set_phase_manager(self, manager: AdvancedPhaseManager):
        """Link to phase manager."""
        self.phase_manager = manager

    def decide_action(self, battle):
        """Strategic power-up deployment."""
        if not self.phase_manager:
            return

        current_time = battle.time_manager.current_time
        creator_score = battle.score_tracker.creator_score
        opponent_score = battle.score_tracker.opponent_score

        # Check for opponent x5 to neutralize
        if not self.hammer_used and self.phase_manager.active_glove_x5:
            # Opponent has x5 active!
            print(f"\n🧰 LoadoutMaster: Opponent x5 detected!")

            # Use hammer if we have it and are losing
            if opponent_score > creator_score:
                print(f"   🔨 Deploying HAMMER to neutralize!")
                success = self.phase_manager.use_power_up(PowerUpType.HAMMER, "creator", current_time)
                if success:
                    self.hammer_used = True

        # Use fog if we're ahead and want to hide score
        if not self.fog_used and creator_score > opponent_score + 50000:
            if current_time > 120:  # Late game
                print(f"\n🧰 LoadoutMaster: We're ahead, deploying FOG!")
                success = self.phase_manager.use_power_up(PowerUpType.FOG, "creator", current_time)
                if success:
                    self.fog_used = True

        # Time bonus handled by Kinetik usually, but LoadoutMaster can also deploy
        # if critical situation detected

    def get_personality_prompt(self) -> str:
        return """You are LoadoutMaster, a tactical specialist who manages your team's arsenal.
        You deploy power-ups at the perfect moment to counter opponents or secure victory.
        You are strategic, reactive, and always prepared."""


# Helper function to setup strategic team
def create_strategic_team(phase_manager: AdvancedPhaseManager) -> List[BaseAgent]:
    """
    Create a team of strategic agents linked to phase manager.

    Returns list of specialized agents ready for 180s advanced battles.
    """
    kinetik = Kinetik()
    strike_master = StrikeMaster()
    phase_tracker = PhaseTracker()
    loadout_master = LoadoutMaster()

    # Link all to phase manager
    kinetik.set_phase_manager(phase_manager)
    strike_master.set_phase_manager(phase_manager)
    phase_tracker.set_phase_manager(phase_manager)
    loadout_master.set_phase_manager(phase_manager)

    return [kinetik, strike_master, phase_tracker, loadout_master]


if __name__ == '__main__':
    # Demo
    print("Strategic Agents Demo")
    print("="*70)

    from core.advanced_phase_system import AdvancedPhaseManager

    # Create phase manager
    phase_mgr = AdvancedPhaseManager(battle_duration=180)

    # Create strategic team
    team = create_strategic_team(phase_mgr)

    print("\n🎯 Strategic Team Created:")
    for agent in team:
        print(f"   {agent.emoji} {agent.name}")

    print("\n✅ All agents linked to Advanced Phase Manager")
    print("\n📋 Agent Capabilities:")
    print("   🔫 Kinetik: Final sniper (last 5s)")
    print("   🥊 StrikeMaster: Glove expert with learning")
    print("   ⏱️ PhaseTracker: Phase trigger specialist")
    print("   🧰 LoadoutMaster: Power-up manager")
