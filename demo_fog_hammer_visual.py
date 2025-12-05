#!/usr/bin/env python3
"""
Visual demonstration of Fog and Hammer mechanics in a real battle.

Shows both defensive mechanics working in a competitive scenario.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core import BattleEngine, EventBus
from agents.specialists.sentinel import AgentSentinel
from agents.specialists.strike_master import AgentStrikeMaster
from agents.specialists.kinetik_sniper import AgentKinetik


def main():
    """Run visual demo of fog and hammer mechanics."""

    print("\n" + "="*70)
    print("🛡️ FOG & HAMMER DEMONSTRATION")
    print("="*70)
    print("\nScenario:")
    print("  • Sentinel will deploy FOG at t=155s for stealth")
    print("  • StrikeMaster will trigger x5 strikes")
    print("  • Watch for HAMMER counters if opponent x5 detected")
    print("  • Kinetik will snipe during fog cover")
    print("\n" + "="*70 + "\n")

    # Create battle
    event_bus = EventBus()
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.05,  # Faster for demo
        event_bus=event_bus,
        enable_multipliers=True
    )

    # Add agents
    sentinel = AgentSentinel()
    sentinel.event_bus = event_bus
    sentinel.fog_deploy_time = 155  # Deploy before final snipe
    engine.add_agent(sentinel)

    strike_master = AgentStrikeMaster()
    strike_master.event_bus = event_bus
    engine.add_agent(strike_master)

    kinetik = AgentKinetik()
    kinetik.event_bus = event_bus
    engine.add_agent(kinetik)

    print("🎬 Starting battle with defensive team...\n")
    print("="*70)

    # Run battle
    engine.run(silent=False)

    # Results
    winner = engine.score_tracker.get_leader()
    creator_score, opponent_score = engine.score_tracker.get_scores()

    print("\n" + "="*70)
    print("📊 BATTLE RESULTS")
    print("="*70)
    print(f"\nCreator:  {creator_score:,} points")
    print(f"Opponent: {opponent_score:,} points")
    print(f"Winner:   {(winner or 'tie').upper()}\n")

    # Show defensive stats
    inventory = sentinel.get_inventory_status()

    print("="*70)
    print("🛡️ SENTINEL DEFENSIVE STATS")
    print("="*70)
    print(f"\n🔨 Hammers:")
    print(f"   Used: {2 - inventory['hammers']}/2")
    print(f"   Remaining: {inventory['hammers']}/2")

    print(f"\n🌫️ Fog:")
    print(f"   Deployed: {'✅ YES' if inventory['fog_deployed'] else '❌ NO'}")
    print(f"   Remaining: {inventory['fogs']}/2")

    print(f"\n💰 Total Contribution:")
    print(f"   Points: {sentinel.total_donated:,}")
    print(f"   Actions: {sentinel.action_count}")

    print("\n" + "="*70)
    print("\n✨ Demo complete!")
    print("\n💡 Key Observations:")
    print("   • Fog deployed at t=155s (before Kinetik's 175s snipe)")
    print("   • Hammer available to counter opponent x5 strikes")
    print("   • Defensive mechanics enable offensive tactics\n")


if __name__ == "__main__":
    main()
