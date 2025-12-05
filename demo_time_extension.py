#!/usr/bin/env python3
"""
Time Extension Demo - +20s Comeback Mechanic

Demonstrates the time extension bonus system:
- Earned as rewards from previous victories
- Used when behind in score
- Extends battle duration by +20 seconds
- Strategic comeback opportunities
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core import BattleEngine, EventBus
from agents.specialists.kinetik_sniper import AgentKinetik
from agents.specialists.strike_master import AgentStrikeMaster
from agents.specialists.activator import AgentActivator
from agents.specialists.sentinel import AgentSentinel


def main():
    print("\n" + "="*70)
    print("⏱️  TIME EXTENSION BONUS DEMO (+20s)")
    print("="*70)

    print("\n📋 Mechanic:")
    print("  • Earned as rewards from previous battle victories")
    print("  • Extends battle duration by +20 seconds")
    print("  • Used automatically when behind in score")
    print("  • Strategic resource for comeback attempts")

    print("\n🎯 Demo Scenario:")
    print("  • 180-second base battle")
    print("  • Team starts with 2 time extensions (+40s potential)")
    print("  • Extensions activate when losing by 1000+ points")
    print("  • Watch for ⏱️  TIME EXTENSION ACTIVATED!")

    print("\n" + "="*70 + "\n")

    # Create battle with time extensions
    event_bus = EventBus()
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.1,
        event_bus=event_bus,
        enable_multipliers=True,
        time_extensions=2  # ← 2 time extension bonuses available
    )

    # Add specialist team
    kinetik = AgentKinetik()
    kinetik.event_bus = event_bus
    engine.add_agent(kinetik)

    strike_master = AgentStrikeMaster()
    strike_master.event_bus = event_bus
    engine.add_agent(strike_master)

    activator = AgentActivator()
    activator.event_bus = event_bus
    engine.add_agent(activator)

    sentinel = AgentSentinel()
    sentinel.event_bus = event_bus
    engine.add_agent(sentinel)

    agents = [kinetik, strike_master, activator, sentinel]

    print("✅ Team assembled:")
    for agent in agents:
        print(f"   {agent.emoji} {agent.name}")

    if engine.time_extension_manager:
        status = engine.time_extension_manager.get_status()
        print(f"\n⏱️  Time Extensions Available: {status['available']}")
        print(f"   Base battle duration: 180s")
        print(f"   Maximum with extensions: {180 + (status['available'] * 20)}s")

    print("\n" + "="*70)
    print("🎬 Starting Battle with Time Extensions")
    print("="*70 + "\n")

    # Run battle
    engine.run(silent=False)

    # Results
    winner = engine.score_tracker.get_leader()
    creator_score, opponent_score = engine.score_tracker.get_scores()
    final_duration = engine.time_manager.battle_duration

    print("\n" + "="*70)
    print("📊 BATTLE RESULTS")
    print("="*70)
    print(f"\nCreator:  {creator_score:,} points")
    print(f"Opponent: {opponent_score:,} points")
    print(f"Winner:   {(winner or 'tie').upper()}")

    print(f"\n⏱️  Time Statistics:")
    print(f"   Base duration: {engine.time_manager.base_duration}s")
    print(f"   Final duration: {final_duration}s")
    print(f"   Extensions used: {engine.time_manager.extensions_used}")
    print(f"   Total time added: {final_duration - engine.time_manager.base_duration}s")

    if engine.time_extension_manager:
        ext_stats = engine.time_extension_manager.get_statistics()
        print(f"\n⏱️  Extension Details:")
        print(f"   Available: {ext_stats['extensions_available']}")
        print(f"   Used: {ext_stats['extensions_used']}")

        if ext_stats['use_times']:
            print(f"   Activated at:")
            for i, time in enumerate(ext_stats['use_times'], 1):
                trigger = ext_stats['triggered_by'][i-1] if i-1 < len(ext_stats['triggered_by']) else 'Unknown'
                print(f"      {i}. t={time}s by {trigger}")

    print(f"\n💰 Agent Performance:")
    for agent in agents:
        print(f"\n{agent.emoji} {agent.name}:")
        print(f"   Total donated: {agent.total_donated:,} points")
        print(f"   Actions taken: {agent.action_count}")

    print("\n" + "="*70)
    print("\n✨ Time Extension Demo Complete!")
    print("\n💡 Key Observations:")
    print("   • Extensions auto-activate when losing by 1000+ points")
    print("   • Each extension adds +20 seconds to battle duration")
    print("   • Strategic resource earned from previous victories")
    print("   • Enables dramatic comeback opportunities")
    print("\n💡 Strategic Tips:")
    print("   • Save extensions for desperate situations")
    print("   • Use when losing in final 30 seconds")
    print("   • Coordinate team actions during extended time")
    print("   • Multiple extensions = multiple comeback chances\n")


if __name__ == "__main__":
    main()
