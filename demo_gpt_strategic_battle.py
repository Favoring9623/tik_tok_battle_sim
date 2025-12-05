"""
GPT-Powered Strategic Battle Demo

Demonstrates strategic battles enhanced with GPT-4:
- Pre-battle strategic analysis
- Real-time commentary on key moments
- Agent action analysis
- Post-battle summary with insights
"""

import sys
import os

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, will use system env vars

from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.reward_system import RewardDistributor, create_contributor_stats_from_analytics
from agents.gpt_strategic_agents import create_gpt_strategic_team, OPENAI_AVAILABLE
from agents.personas import NovaWhale


def run_gpt_strategic_battle(api_key: str = None):
    """Run a GPT-enhanced strategic battle."""

    print("\n" + "🤖"*35)
    print("GPT-POWERED STRATEGIC BATTLE")
    print("🤖"*35 + "\n")

    # Check prerequisites
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI package not installed!")
        print("   Install with: pip install openai")
        return

    api_key = api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found!")
        print("   Set with: export OPENAI_API_KEY='your-key-here'")
        print("\n💡 Running in DEMO MODE without GPT features...")
        api_key = None

    print("🔧 Battle Configuration:")
    print("   Duration: 180 seconds")
    print("   AI Commentary: GPT-4")
    print("   Strategic Agents: 4 specialized + GPT narrator")
    print("   Features: Real-time analysis, strategic insights, battle summary")
    print("\n" + "="*70 + "\n")

    # Create advanced phase manager
    print("⚙️  Initializing Advanced Phase Manager...")
    phase_manager = AdvancedPhaseManager(battle_duration=180)

    # Add power-ups
    print("🧰 Loading power-ups inventory...")
    phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
    phase_manager.add_power_up(PowerUpType.FOG, "creator")
    phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")
    print("   ✅ Hammer, Fog, Time Bonus loaded\n")

    # Create GPT-enhanced strategic team
    print("🤖 Creating GPT-Enhanced Strategic Team...")
    strategic_agents, narrator = create_gpt_strategic_team(phase_manager, api_key=api_key)

    print("\n   GPT-Enhanced Roster:")
    for agent in strategic_agents:
        print(f"      {agent.emoji} {agent.name} (GPT-powered)")

    # Add control agent
    whale = NovaWhale()
    strategic_agents.append(whale)
    print(f"      {whale.emoji} {whale.name} (control)")

    # Generate pre-battle analysis
    if narrator.enabled:
        print("\n" + "="*70)
        print("🎙️  GPT PRE-BATTLE ANALYSIS")
        print("="*70 + "\n")

        analysis = narrator.generate_pre_battle_analysis(strategic_agents[:-1], 180)
        print(f"💬 {analysis}")

        print("\n" + "="*70)

    print("\n" + "="*70)
    print("🚀 BATTLE START - GPT Commentary Enabled")
    print("="*70 + "\n")

    # Create battle engine
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.1,  # Fast for testing
        enable_multipliers=False,
        enable_analytics=True
    )

    # Add agents
    for agent in strategic_agents:
        engine.add_agent(agent)

    # Track phase transitions for commentary
    last_phase_name = None
    phase_transition_count = 0

    # Wrap battle tick to integrate phase manager and GPT commentary
    original_tick = engine._tick

    def wrapped_tick(silent):
        nonlocal last_phase_name, phase_transition_count

        # Call original tick
        original_tick(silent)

        # Update phase manager
        current_time = engine.time_manager.current_time
        phase_manager.update(current_time)

        # Check for phase transitions
        phase_info = phase_manager.get_phase_info()
        current_phase = phase_info.get('name', '')

        if current_phase != last_phase_name and current_phase:
            last_phase_name = current_phase

            # Display phase info
            if current_time % 10 == 0 or phase_transition_count < 3:
                print(f"\n⏱️  t={current_time}s | Phase: {current_phase} | "
                      f"Multiplier: x{phase_info.get('multiplier', 1.0)}")
                print(f"   Creator: {engine.score_tracker.creator_score:,} | "
                      f"Opponent: {engine.score_tracker.opponent_score:,}")

                # GPT commentary on phase transitions (first 3 only to avoid spam)
                if narrator.enabled and phase_transition_count < 3:
                    score_diff = abs(
                        engine.score_tracker.creator_score -
                        engine.score_tracker.opponent_score
                    )

                    commentary = narrator.comment_on_phase_transition(
                        current_phase,
                        phase_info.get('multiplier', 1.0),
                        current_time,
                        score_diff
                    )

                    if commentary:
                        print(f"\n💬 GPT Commentary: {commentary}")

                phase_transition_count += 1

    engine._tick = wrapped_tick

    # Run battle
    try:
        engine.run(silent=False)
    except KeyError:
        pass  # Ignore analytics errors

    # Battle complete
    print("\n" + "="*70)
    print("🏁 BATTLE COMPLETE - GPT Analysis")
    print("="*70)

    # Final scores
    print(f"\n🏆 Final Result:")
    print(f"   Winner: {engine.analytics.winner.upper()}")
    print(f"   Creator: {engine.analytics.final_scores['creator']:,} points")
    print(f"   Opponent: {engine.analytics.final_scores['opponent']:,} points")
    print(f"   Duration: {engine.time_manager.current_time}s")

    # GPT Battle Summary
    if narrator.enabled:
        print("\n" + "="*70)
        print("🎙️  GPT BATTLE SUMMARY")
        print("="*70 + "\n")

        analytics = phase_manager.get_analytics()
        summary = narrator.generate_battle_summary(
            winner=engine.analytics.winner,
            final_scores=engine.analytics.final_scores,
            analytics=analytics
        )

        print(f"💬 {summary}")

        print("\n" + "="*70)

    # Phase analytics
    print(f"\n📊 Phase System Analytics:")
    analytics = phase_manager.get_analytics()
    print(f"   Total phases: {analytics['total_phases']}")
    print(f"   Boost #2 triggered: {'✅ YES' if analytics['boost2_triggered'] else '❌ NO'}")
    print(f"   Gloves sent: {analytics['gloves_sent']}")
    print(f"   Gloves activated (x5): {analytics['gloves_activated']} "
          f"({analytics['gloves_activated']/max(analytics['gloves_sent'], 1)*100:.0f}%)")
    print(f"   Power-ups used: {analytics['power_ups_used']}")

    # Agent performance
    print(f"\n👥 Strategic Agent Performance:")
    agent_perf = engine.analytics.get_agent_performance()
    for agent_name, perf in sorted(agent_perf.items(),
                                   key=lambda x: x[1]['total_donated'],
                                   reverse=True)[:4]:  # Top 4
        print(f"\n   {agent_name}:")
        print(f"      Points donated: {perf['total_donated']:,}")
        print(f"      Gifts sent: {perf['gifts_sent']}")

    # Distribute rewards
    print(f"\n{'='*70}")
    print("💎 DISTRIBUTING REWARDS...")
    print(f"{'='*70}")

    contributors = create_contributor_stats_from_analytics(
        agent_perf,
        engine.time_manager.battle_duration
    )

    battle_history = {
        'comeback_victory': engine.analytics.final_scores['creator'] > engine.analytics.final_scores['opponent'],
        'perfect_victory': False,
        'max_deficit_ratio': 1.0,
        'boost2_triggered': analytics.get('boost2_triggered', False),
        'gloves_activated_by_team': analytics.get('gloves_activated', 0),
        'power_ups_used': analytics.get('power_ups_used', 0)
    }

    distributor = RewardDistributor()
    rewards = distributor.distribute_rewards(
        contributors,
        winner=engine.analytics.winner,
        battle_history=battle_history
    )

    distributor.print_rewards(rewards)

    print("\n" + "="*70)
    print("✅ GPT-Powered Strategic Battle Complete!")
    print("="*70 + "\n")

    if narrator.enabled:
        print("🤖 GPT-4 provided real-time strategic commentary throughout the battle!")
    else:
        print("💡 Set OPENAI_API_KEY to enable GPT-4 commentary")

    return engine, phase_manager, narrator


def main():
    """Main entry point."""

    # Check for API key argument
    import sys
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]

    run_gpt_strategic_battle(api_key=api_key)

    print("\n💡 Usage:")
    print("   With GPT: export OPENAI_API_KEY='your-key' && python3 demo_gpt_strategic_battle.py")
    print("   Without GPT: python3 demo_gpt_strategic_battle.py")
    print("\n📖 See agents/gpt_strategic_agents.py for GPT integration details\n")


if __name__ == '__main__':
    main()
