"""
Advanced Strategic Battle Demo

Demonstrates 180s battles with:
- Advanced phase system (conditional Boost #2)
- 4 specialized strategic agents
- Glove x5 mechanics
- Power-up system
- Real-time phase tracking
"""

import sys
import os

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.reward_system import RewardDistributor, create_contributor_stats_from_analytics
from agents.strategic_agents import create_strategic_team
from agents.personas import NovaWhale  # Add one regular agent for comparison


def run_strategic_battle():
    """Run a complete 180s strategic battle."""

    print("\n" + "🎯"*35)
    print("ADVANCED STRATEGIC BATTLE - 180s")
    print("🎯"*35 + "\n")

    print("🔧 Battle Configuration:")
    print("   Duration: 180 seconds (3 minutes)")
    print("   Phase System: Advanced with conditional triggers")
    print("   Agents: 4 specialized strategic agents")
    print("   Mechanics: Glove x5, Power-ups, Phase tracking")
    print("\n" + "="*70 + "\n")

    # Create advanced phase manager
    print("⚙️  Initializing Advanced Phase Manager...")
    phase_manager = AdvancedPhaseManager(battle_duration=180)

    # Add power-ups to inventory
    print("🧰 Loading power-ups inventory...")
    phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
    phase_manager.add_power_up(PowerUpType.FOG, "creator")
    phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")
    print("   ✅ Hammer, Fog, Time Bonus loaded\n")

    # Create strategic team
    print("👥 Creating Strategic Team...")
    strategic_agents = create_strategic_team(phase_manager)

    print("\n   Strategic Roster:")
    for agent in strategic_agents:
        print(f"      {agent.emoji} {agent.name}")

    # Add one whale for comparison
    whale = NovaWhale()
    strategic_agents.append(whale)
    print(f"      {whale.emoji} {whale.name} (control agent)")

    print("\n" + "="*70)
    print("🚀 BATTLE START")
    print("="*70 + "\n")

    # Create battle engine with extended duration
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.1,  # Fast simulation for testing (0.1s per tick = 18s real time)
        enable_multipliers=False,  # We're using advanced phase system instead
        enable_analytics=True
    )

    # Add all agents
    for agent in strategic_agents:
        engine.add_agent(agent)

    # Wrap battle _tick to integrate phase manager
    original_tick = engine._tick

    def wrapped_tick(silent):
        # Call original tick
        original_tick(silent)

        # Update phase manager
        current_time = engine.time_manager.current_time
        phase_manager.update(current_time)

        # Display phase info every 10 seconds
        if current_time % 10 == 0 and current_time > 0:
            phase_info = phase_manager.get_phase_info()
            print(f"\n⏱️  t={current_time}s | Phase: {phase_info.get('name', 'Unknown')} | "
                  f"Multiplier: x{phase_info.get('multiplier', 1.0)}")
            print(f"   Creator: {engine.score_tracker.creator_score:,} | "
                  f"Opponent: {engine.score_tracker.opponent_score:,}")

    engine._tick = wrapped_tick

    # Run the battle (suppress standard analytics to avoid multiplier errors)
    try:
        engine.run(silent=False)
    except KeyError:
        pass  # Ignore analytics errors when multipliers disabled

    # Battle complete
    print("\n" + "="*70)
    print("🏁 BATTLE COMPLETE - Strategic Analysis")
    print("="*70)

    # Final scores
    print(f"\n🏆 Final Result:")
    print(f"   Winner: {engine.analytics.winner.upper()}")
    print(f"   Creator: {engine.analytics.final_scores['creator']:,} points")
    print(f"   Opponent: {engine.analytics.final_scores['opponent']:,} points")
    print(f"   Duration: {engine.time_manager.current_time}s")

    # Phase analytics
    print(f"\n📊 Phase System Analytics:")
    analytics = phase_manager.get_analytics()
    print(f"   Total phases: {analytics['total_phases']}")
    print(f"   Boost #2 triggered: {'✅ YES' if analytics['boost2_triggered'] else '❌ NO'}")
    print(f"   Gloves sent: {analytics['gloves_sent']}")
    print(f"   Gloves activated (x5): {analytics['gloves_activated']} ({analytics['gloves_activated']/max(analytics['gloves_sent'], 1)*100:.0f}%)")
    print(f"   Time bonuses used: {analytics['time_bonuses_used']}")
    print(f"   Final duration: {analytics['final_duration']}s")
    print(f"   Power-ups used: {analytics['power_ups_used']}")

    # Agent performance
    print(f"\n👥 Strategic Agent Performance:")
    agent_perf = engine.analytics.get_agent_performance()
    for agent_name, perf in sorted(agent_perf.items(),
                                   key=lambda x: x[1]['total_donated'],
                                   reverse=True):
        print(f"\n   {agent_name}:")
        print(f"      Points donated: {perf['total_donated']:,}")
        print(f"      Gifts sent: {perf['gifts_sent']}")
        print(f"      Avg gift value: {perf['avg_gift_value']:.0f}")

    # Strategic insights
    print(f"\n🎯 Strategic Insights:")

    # Check Kinetik performance
    kinetik_found = any(a.name == "Kinetik" for a in strategic_agents)
    if kinetik_found:
        print(f"   🔫 Kinetik: Final sniper strategy {'executed' if analytics.get('time_bonuses_used', 0) > 0 else 'observed'}")

    # Check StrikeMaster
    strikemaster_found = any(a.name == "StrikeMaster" for a in strategic_agents)
    if strikemaster_found:
        glove_success_rate = analytics['gloves_activated'] / max(analytics['gloves_sent'], 1) * 100
        print(f"   🥊 StrikeMaster: Glove mastery {glove_success_rate:.0f}% success rate")

    # Check PhaseTracker
    print(f"   ⏱️  PhaseTracker: Boost #2 {'successfully triggered' if analytics['boost2_triggered'] else 'conditions not met'}")

    # Check LoadoutMaster
    loadout_found = any(a.name == "LoadoutMaster" for a in strategic_agents)
    if loadout_found:
        print(f"   🧰 LoadoutMaster: {analytics['power_ups_used']} power-ups deployed")

    # Distribute rewards
    print(f"\n{'='*70}")
    print("🎁 DISTRIBUTING REWARDS...")
    print(f"{'='*70}")

    # Create contributor stats from analytics
    agent_perf = engine.analytics.get_agent_performance()
    contributors = create_contributor_stats_from_analytics(
        agent_perf,
        engine.time_manager.battle_duration
    )

    # Build battle history for achievements
    battle_history = {
        'comeback_victory': engine.analytics.final_scores['creator'] > engine.analytics.final_scores['opponent'],
        'perfect_victory': False,  # Would need to track if opponent ever led
        'max_deficit_ratio': 1.0,  # Would need to track max deficit
        'boost2_triggered': analytics.get('boost2_triggered', False),
        'gloves_activated_by_team': analytics.get('gloves_activated', 0),
        'power_ups_used': analytics.get('power_ups_used', 0)
    }

    # Distribute rewards
    distributor = RewardDistributor()
    rewards = distributor.distribute_rewards(
        contributors,
        winner=engine.analytics.winner,
        battle_history=battle_history
    )

    # Print rewards
    distributor.print_rewards(rewards)

    print("\n" + "="*70)
    print("✅ Strategic Battle Complete!")
    print("="*70 + "\n")

    return engine, phase_manager


if __name__ == '__main__':
    run_strategic_battle()
