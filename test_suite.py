#!/usr/bin/env python3
"""
Multi-Battle Test Suite - Run multiple battles with different configurations.

This helps you:
- Understand agent behavior patterns
- Compare different team compositions
- Identify what creates compelling narratives
- Gather data for analysis
"""

import sys
from pathlib import Path
import json
import time as time_module
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core import BattleEngine, EventBus, EventType
from agents.personas import NovaWhale, PixelPixie, GlitchMancer, ShadowPatron, Dramatron
from agents.communication import CommunicationChannel


class BattleRecorder:
    """Records battle data for later analysis."""

    def __init__(self):
        self.battles = []

    def record_battle(self, battle_id, config, results, event_bus, comm_channel):
        """Record a complete battle."""

        # Extract key events
        all_events = event_bus.get_history()
        gifts = [e for e in all_events if e.event_type == EventType.GIFT_SENT]
        messages = [e for e in all_events if e.event_type == EventType.AGENT_DIALOGUE]
        emotions = [e for e in all_events if e.event_type == EventType.EMOTION_CHANGED]

        battle_record = {
            "battle_id": battle_id,
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "results": results,
            "statistics": {
                "total_gifts": len(gifts),
                "total_messages": len(messages),
                "emotion_changes": len(emotions),
                "total_events": len(all_events),
            },
            "timeline": {
                "gifts": [
                    {
                        "time": e.timestamp,
                        "agent": e.data.get("agent"),
                        "points": e.data.get("points"),
                        "emotion": e.data.get("emotion")
                    }
                    for e in gifts
                ],
                "emotional_arc": [
                    {
                        "time": e.timestamp,
                        "agent": e.data.get("agent"),
                        "emotion": e.data.get("emotion")
                    }
                    for e in emotions
                ],
                "dialogue": comm_channel.get_dialogue_history()
            }
        }

        self.battles.append(battle_record)

    def save_to_file(self, filename="data/battles/test_results.json"):
        """Save all battle data to JSON."""
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump({
                "test_suite_run": datetime.now().isoformat(),
                "total_battles": len(self.battles),
                "battles": self.battles
            }, f, indent=2)

        print(f"\n💾 Battle data saved to: {filepath}")
        return filepath

    def get_summary_stats(self):
        """Get aggregate statistics across all battles."""
        if not self.battles:
            return {}

        total_battles = len(self.battles)
        creator_wins = sum(1 for b in self.battles if b["results"]["winner"] == "creator")

        avg_gifts = sum(b["statistics"]["total_gifts"] for b in self.battles) / total_battles
        avg_messages = sum(b["statistics"]["total_messages"] for b in self.battles) / total_battles
        avg_emotions = sum(b["statistics"]["emotion_changes"] for b in self.battles) / total_battles

        return {
            "total_battles": total_battles,
            "creator_wins": creator_wins,
            "opponent_wins": total_battles - creator_wins,
            "creator_win_rate": creator_wins / total_battles,
            "avg_gifts_per_battle": avg_gifts,
            "avg_messages_per_battle": avg_messages,
            "avg_emotion_changes": avg_emotions,
        }


def run_test_scenario(scenario_name, agents, num_battles=3, tick_speed=0.1):
    """
    Run multiple battles with the same configuration.

    Args:
        scenario_name: Name of the test scenario
        agents: List of agent instances
        num_battles: Number of battles to run
        tick_speed: Speed of simulation (lower = faster)

    Returns:
        List of battle results
    """
    print(f"\n{'='*70}")
    print(f"📋 Test Scenario: {scenario_name}")
    print(f"   Agents: {', '.join(a.name for a in agents)}")
    print(f"   Battles: {num_battles}")
    print(f"{'='*70}\n")

    recorder = BattleRecorder()

    for battle_num in range(1, num_battles + 1):
        print(f"\n🎬 Battle {battle_num}/{num_battles}")
        print("-" * 50)

        # Create fresh instances
        event_bus = EventBus(debug=False)
        comm_channel = CommunicationChannel()
        engine = BattleEngine(battle_duration=60, tick_speed=tick_speed, event_bus=event_bus)

        # Add agents (create new instances to reset state)
        for agent_class in [type(a) for a in agents]:
            agent = agent_class()
            agent.comm_channel = comm_channel
            engine.add_agent(agent)

        # Run battle silently
        start_time = time_module.time()
        engine.run(silent=True)
        duration = time_module.time() - start_time

        # Get results
        state = engine.get_state()
        creator_score, opponent_score = engine.score_tracker.get_scores()

        results = {
            "battle_number": battle_num,
            "winner": state["leader"] or "tie",
            "creator_score": creator_score,
            "opponent_score": opponent_score,
            "margin": abs(creator_score - opponent_score),
            "duration_seconds": round(duration, 2),
            "agent_contributions": {
                agent.name: agent.total_donated for agent in engine.agents
            }
        }

        # Record battle
        recorder.record_battle(
            battle_id=f"{scenario_name}_battle_{battle_num}",
            config={
                "scenario": scenario_name,
                "agents": [a.name for a in agents],
                "tick_speed": tick_speed
            },
            results=results,
            event_bus=event_bus,
            comm_channel=comm_channel
        )

        # Print quick summary
        print(f"   Winner: {results['winner'].upper()}")
        print(f"   Score: {creator_score} vs {opponent_score}")
        print(f"   Duration: {duration:.1f}s")

    return recorder


def print_test_summary(recorder):
    """Print summary of test results."""
    stats = recorder.get_summary_stats()

    print(f"\n{'='*70}")
    print("📊 TEST SUITE SUMMARY")
    print(f"{'='*70}\n")

    print(f"Total Battles Run:     {stats['total_battles']}")
    print(f"Creator Wins:          {stats['creator_wins']} ({stats['creator_win_rate']:.1%})")
    print(f"Opponent Wins:         {stats['opponent_wins']}")
    print(f"\nAverage per battle:")
    print(f"  Gifts sent:          {stats['avg_gifts_per_battle']:.1f}")
    print(f"  Messages:            {stats['avg_messages_per_battle']:.1f}")
    print(f"  Emotion changes:     {stats['avg_emotion_changes']:.1f}")

    # Agent performance across all battles
    print(f"\n🤖 Agent Performance Across All Battles:")

    agent_totals = {}
    for battle in recorder.battles:
        for agent_name, contribution in battle["results"]["agent_contributions"].items():
            if agent_name not in agent_totals:
                agent_totals[agent_name] = []
            agent_totals[agent_name].append(contribution)

    for agent_name, contributions in sorted(agent_totals.items(),
                                           key=lambda x: sum(x[1]), reverse=True):
        total = sum(contributions)
        avg = total / len(contributions)
        print(f"   {agent_name:15} - Total: {total:,} pts, Avg: {avg:,.0f} pts/battle")

    print(f"\n{'='*70}")


def main():
    """Run comprehensive test suite."""

    print("=" * 70)
    print("🧪 TikTok Battle Simulator - Comprehensive Test Suite")
    print("=" * 70)
    print("\nThis will run multiple test scenarios to explore agent behavior.\n")

    # Define test scenarios
    scenarios = [
        {
            "name": "Full Squad (All 5 Agents)",
            "agents": [NovaWhale(), PixelPixie(), GlitchMancer(), ShadowPatron(), Dramatron()],
            "battles": 5
        },
        {
            "name": "Budget Team (PixelPixie Only)",
            "agents": [PixelPixie(), PixelPixie()],  # Two cheerleaders
            "battles": 3
        },
        {
            "name": "Whale Team (NovaWhale + ShadowPatron)",
            "agents": [NovaWhale(), ShadowPatron()],
            "battles": 3
        },
        {
            "name": "Chaos Squad (GlitchMancer + Dramatron)",
            "agents": [GlitchMancer(), Dramatron()],
            "battles": 3
        },
        {
            "name": "Strategic Team (NovaWhale + PixelPixie + ShadowPatron)",
            "agents": [NovaWhale(), PixelPixie(), ShadowPatron()],
            "battles": 3
        }
    ]

    # Master recorder
    all_recorders = []

    # Run each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n\n{'#'*70}")
        print(f"# Scenario {i}/{len(scenarios)}: {scenario['name']}")
        print(f"{'#'*70}")

        recorder = run_test_scenario(
            scenario_name=scenario['name'],
            agents=scenario['agents'],
            num_battles=scenario['battles'],
            tick_speed=0.05  # Fast simulation
        )

        all_recorders.append(recorder)

        # Scenario summary
        stats = recorder.get_summary_stats()
        print(f"\n   📈 Scenario Results:")
        print(f"      Win Rate: {stats['creator_win_rate']:.1%}")
        print(f"      Avg Gifts: {stats['avg_gifts_per_battle']:.1f}")
        print(f"      Avg Drama: {stats['avg_messages_per_battle']:.1f} messages")

    # Combine all data
    master_recorder = BattleRecorder()
    for recorder in all_recorders:
        master_recorder.battles.extend(recorder.battles)

    # Print overall summary
    print("\n\n" + "=" * 70)
    print("🏆 OVERALL TEST SUITE RESULTS")
    print("=" * 70)
    print_test_summary(master_recorder)

    # Save data
    filepath = master_recorder.save_to_file()

    print(f"\n✨ Test suite complete!")
    print(f"\n📂 Data saved to: {filepath}")
    print(f"\n💡 Next steps:")
    print(f"   - Analyze battle data in {filepath}")
    print(f"   - Look for interesting patterns")
    print(f"   - Identify most compelling agent combinations")
    print(f"   - Refine agent strategies based on findings\n")


if __name__ == "__main__":
    main()
