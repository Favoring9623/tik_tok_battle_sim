#!/usr/bin/env python3
"""
Coordination Optimization Demo

Demonstrates improved agent coordination:
- Action sequencing (Fog → Snipe)
- Conflict prevention (no duplicate gloves)
- Team strategy adaptation
- Resource sharing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core import BattleEngine, EventBus
from core.team_coordinator import TeamCoordinator, CoordinationPattern
from agents.specialists.kinetik_sniper import AgentKinetik
from agents.specialists.strike_master import AgentStrikeMaster
from agents.specialists.activator import AgentActivator
from agents.specialists.sentinel import AgentSentinel


def main():
    print("\n" + "="*70)
    print("🤝 AGENT COORDINATION OPTIMIZATION DEMO")
    print("="*70)

    print("\n📋 Features:")
    print("  ✓ Action sequencing (dependencies)")
    print("  ✓ Conflict prevention (no wasted gloves)")
    print("  ✓ Team strategy adaptation")
    print("  ✓ Resource coordination")
    print("\n" + "="*70 + "\n")

    # Create team coordinator
    coordinator = TeamCoordinator()

    # Create battle
    event_bus = EventBus()
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.1,
        event_bus=event_bus,
        enable_multipliers=True
    )

    # Create specialist team
    print("🎯 Assembling coordinated team...\n")

    kinetik = AgentKinetik()
    kinetik.event_bus = event_bus
    if hasattr(kinetik, 'set_coordinator'):
        kinetik.set_coordinator(coordinator)
    engine.add_agent(kinetik)

    strike_master = AgentStrikeMaster()
    strike_master.event_bus = event_bus
    strike_master.set_coordinator(coordinator)  # Has coordination
    engine.add_agent(strike_master)

    activator = AgentActivator()
    activator.event_bus = event_bus
    if hasattr(activator, 'set_coordinator'):
        activator.set_coordinator(coordinator)
    engine.add_agent(activator)

    sentinel = AgentSentinel()
    sentinel.event_bus = event_bus
    if hasattr(sentinel, 'set_coordinator'):
        sentinel.set_coordinator(coordinator)
    engine.add_agent(sentinel)

    agents = [kinetik, strike_master, activator, sentinel]

    print("✅ Team assembled:")
    for agent in agents:
        coord_status = "✓" if hasattr(agent, 'coordinator') and agent.coordinator else "✗"
        print(f"   [{coord_status}] {agent.emoji} {agent.name}")

    # Set up coordination patterns
    print("\n📊 Setting up coordination patterns...\n")

    # Pattern 1: Stealth Snipe (Fog → Snipe)
    print("   Pattern 1: Stealth Snipe")
    print("   └─ Sentinel deploys fog at 160s")
    print("   └─ Kinetik snipes at 175s (depends on fog)")
    CoordinationPattern.stealth_snipe_pattern(coordinator, fog_time=160, snipe_time=175)

    # Pattern 2: Bonus Session Strike
    print("\n   Pattern 2: Session Strike")
    print("   └─ Activator triggers session at 95s")
    print("   └─ StrikeMaster strikes at 105s (during session)")
    CoordinationPattern.bonus_session_pattern(coordinator, activation_time=95, strike_time=105)

    print("\n" + "="*70)
    print("🎬 Starting Coordinated Battle")
    print("="*70 + "\n")

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

    # Coordination statistics
    print("="*70)
    print("🤝 COORDINATION STATISTICS")
    print("="*70)

    coord_summary = coordinator.get_coordination_summary()
    team_state = coordinator.get_team_state()

    print(f"\n📋 Actions Coordinated:")
    print(f"   Total planned: {coord_summary['total_actions_coordinated']}")
    print(f"   Completed: {coord_summary['completed_actions']}")
    print(f"   Conflicts prevented: {coord_summary['conflicts_prevented']}")

    print(f"\n🎯 Team State:")
    print(f"   Final phase: {coord_summary['final_phase']}")
    print(f"   Strategy: {coord_summary['final_strategy']}")
    print(f"   Fog deployed: {team_state['fog_deployed']}")
    print(f"   Bonus triggered: {team_state['bonus_triggered']}")

    print(f"\n💰 Agent Performance:")
    for agent in agents:
        print(f"\n{agent.emoji} {agent.name}:")
        print(f"   Total donated: {agent.total_donated:,} points")
        print(f"   Actions taken: {agent.action_count}")

        # Specialist-specific stats
        if isinstance(agent, AgentStrikeMaster):
            print(f"   Gloves used: {agent.gloves_used}/{agent.gloves_available}")
            print(f"   x5 success rate: {agent.x5_success_rate:.1%}")
            print(f"   Coordination enabled: {agent.coordination_enabled}")

    print("\n" + "="*70)
    print("\n✨ Coordination Demo Complete!")
    print("\n💡 Coordination Benefits:")
    print("   ✓ No wasted gloves (conflict prevention)")
    print("   ✓ Fog deployed before snipe (dependencies)")
    print("   ✓ Team strategy adapts to battle state")
    print("   ✓ Actions sequenced for maximum efficiency\n")


if __name__ == "__main__":
    main()
