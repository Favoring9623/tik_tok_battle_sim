#!/usr/bin/env python3
"""
Demo Battle Simulation - Showcase of the new architecture.

This demonstrates:
- Event-driven battle engine
- Emotion modeling
- Inter-agent communication
- Multiple unique agent personalities
- Analytics and insights
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import BattleEngine, EventBus, EventType
from agents.personas import NovaWhale, PixelPixie, GlitchMancer, ShadowPatron, Dramatron
from agents.communication import CommunicationChannel


def print_header():
    """Print demo header."""
    print("=" * 70)
    print("🎬 TikTok AI Battle Simulator v2.0 - Demo Battle")
    print("=" * 70)
    print("\nFeaturing 5 AI Agents with Unique Personalities:\n")
    print("  🐋 NovaWhale      - Strategic whale (waits for critical moments)")
    print("  🧚‍♀️ PixelPixie     - Budget cheerleader (frequent small gifts)")
    print("  🌀 GlitchMancer   - Chaotic burst mode (unpredictable spikes)")
    print("  👤 ShadowPatron   - Silent observer (crisis intervention)")
    print("  🎭 Dramatron      - Theatrical narrator (dramatic performance)")
    print("\n" + "=" * 70 + "\n")


def setup_analytics(event_bus):
    """Set up event listeners for analytics."""

    analytics = {
        "gifts_sent": 0,
        "total_points": 0,
        "messages_sent": 0,
        "emotion_changes": 0,
        "momentum_shifts": 0,
    }

    def track_gift(event):
        analytics["gifts_sent"] += 1
        analytics["total_points"] += event.data.get("points", 0)

    def track_message(event):
        analytics["messages_sent"] += 1

    def track_emotion(event):
        analytics["emotion_changes"] += 1

    def track_momentum(event):
        analytics["momentum_shifts"] += 1
        print(f"\n⚡ MOMENTUM SHIFT! New leader: {event.data['new_leader']} ⚡\n")

    event_bus.subscribe(EventType.GIFT_SENT, track_gift)
    event_bus.subscribe(EventType.AGENT_DIALOGUE, track_message)
    event_bus.subscribe(EventType.EMOTION_CHANGED, track_emotion)
    event_bus.subscribe(EventType.MOMENTUM_SHIFT, track_momentum)

    return analytics


def print_battle_summary(engine, analytics, comm_channel):
    """Print detailed battle summary."""

    print("\n" + "=" * 70)
    print("📊 BATTLE SUMMARY")
    print("=" * 70)

    # Final scores
    creator, opponent = engine.score_tracker.get_scores()
    winner = engine.score_tracker.get_leader()

    print(f"\n🏆 Final Score:")
    print(f"   Creator:  {creator:,} points")
    print(f"   Opponent: {opponent:,} points")
    print(f"   Winner:   {winner.upper() if winner else 'TIE'}")
    print(f"   Margin:   {engine.score_tracker.get_score_diff():,} points")

    # Agent contributions
    print(f"\n🤖 Agent Contributions:")
    for agent in engine.agents:
        stats = agent.get_stats()
        print(f"   {agent.emoji} {agent.name:15} - {stats['total_donated']:,} points "
              f"({stats['action_count']} gifts) - {stats['current_emotion']}")

    # Battle dynamics
    print(f"\n📈 Battle Dynamics:")
    print(f"   Gifts Sent:       {analytics['gifts_sent']}")
    print(f"   Total Donated:    {analytics['total_points']:,} points")
    print(f"   Messages Sent:    {analytics['messages_sent']}")
    print(f"   Emotion Changes:  {analytics['emotion_changes']}")
    print(f"   Momentum Shifts:  {analytics['momentum_shifts']}")

    # Event statistics
    print(f"\n🎯 Event Statistics:")
    event_stats = engine.event_bus.get_stats()
    for event_name, count in sorted(event_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {event_name:20} {count} times")

    # Communication highlights
    print(f"\n💬 Communication Highlights:")
    dialogue = comm_channel.get_dialogue_history()
    if dialogue:
        # Show first 3 and last 3 messages
        highlights = dialogue[:3] + ["   ..."] + dialogue[-3:] if len(dialogue) > 6 else dialogue
        for msg in highlights:
            print(f"   {msg}")
    else:
        print("   (No messages)")

    print("\n" + "=" * 70)


def main():
    """Run the demo battle."""

    print_header()

    # Create event bus and communication channel
    event_bus = EventBus(debug=False)
    comm_channel = CommunicationChannel()

    # Create battle engine
    engine = BattleEngine(
        battle_duration=60,
        tick_speed=0.25,  # 0.25s per tick = 15s real time for 60s battle
        event_bus=event_bus
    )

    # Add all agents
    agents = [
        NovaWhale(),
        PixelPixie(),
        GlitchMancer(),
        ShadowPatron(),
        Dramatron(),
    ]

    for agent in agents:
        agent.comm_channel = comm_channel  # Give them communication access
        engine.add_agent(agent)

    # Set up analytics tracking
    analytics = setup_analytics(event_bus)

    # Run the battle!
    print("🎬 Battle Starting in 3... 2... 1...\n")

    try:
        engine.run(silent=False)
    except KeyboardInterrupt:
        print("\n\n⚠️ Battle interrupted by user!")
        engine.stop()

    # Print summary
    print_battle_summary(engine, analytics, comm_channel)

    print("\n✨ Demo complete! The new architecture is working beautifully.\n")


if __name__ == "__main__":
    main()
