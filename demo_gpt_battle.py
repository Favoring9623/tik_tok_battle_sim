#!/usr/bin/env python3
"""
GPT-Powered Battle Demo - Intelligent agents using GPT-4.

Shows how AI agents use GPT to make strategic decisions and generate
contextual messages based on battle state.

SETUP:
1. Install OpenAI: pip install openai
2. Set API key: export OPENAI_API_KEY='your-key-here'
   OR create a .env file with: OPENAI_API_KEY=your-key-here
3. Run: python3 demo_gpt_battle.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load .env file if present
def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

try:
    from dotenv import load_dotenv
    load_dotenv()  # Use python-dotenv if available
except ImportError:
    load_env_file()  # Manual fallback if python-dotenv not installed

from core import BattleEngine, EventBus, EventType
from agents.gpt_agent import GPTNovaWhale, GPTPixelPixie, GPTShadowPatron
from agents.communication import CommunicationChannel
from extensions.gpt_intelligence import GPTDecisionEngine, GPTLoreGenerator


def check_gpt_setup():
    """Check if GPT is properly configured."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("=" * 70)
        print("⚠️  OPENAI_API_KEY not found!")
        print("=" * 70)
        print("\nTo use GPT-powered agents, you need to:")
        print("\n1. Get an API key from https://platform.openai.com/api-keys")
        print("\n2. Set it as an environment variable:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("\n3. Install the OpenAI package:")
        print("   pip install openai")
        print("\n" + "=" * 70)
        print("\nRunning demo in FALLBACK mode (agents will use basic logic)\n")
        return False

    try:
        import openai
        print("✅ OpenAI package installed")
        print(f"✅ API key configured (ending in ...{api_key[-4:]})")
        return True
    except ImportError:
        print("⚠️  OpenAI package not installed. Run: pip install openai")
        print("\nRunning in FALLBACK mode\n")
        return False


def print_header(gpt_available):
    """Print demo header."""
    print("=" * 70)
    print("🧠 GPT-Powered TikTok Battle Simulator")
    print("=" * 70)
    print()

    if gpt_available:
        print("🎉 GPT-4 Intelligence: ACTIVE")
        print("\nAgents will use GPT-4 to:")
        print("  • Analyze battle state in real-time")
        print("  • Make strategic timing decisions")
        print("  • Generate contextual messages")
        print("  • Adapt to changing situations")
    else:
        print("⚠️  GPT-4 Intelligence: UNAVAILABLE")
        print("\nAgents will use fallback logic (basic random decisions)")

    print("\n" + "=" * 70 + "\n")


def setup_battle_lore_tracking(event_bus, gpt_lore):
    """Track key moments for lore generation."""

    key_moments = []

    def track_key_moments(event):
        time = int(event.timestamp) if hasattr(event, 'timestamp') else 0

        if event.event_type == EventType.GIFT_SENT:
            points = event.data.get('points', 0)
            agent = event.data.get('agent', 'Unknown')

            if points >= 1000:
                key_moments.append(f"[{time}s] {agent} delivers massive {points}-point gift!")
            elif points >= 500:
                key_moments.append(f"[{time}s] {agent} sends substantial gift ({points} pts)")

        elif event.event_type == EventType.MOMENTUM_SHIFT:
            new_leader = event.data.get('new_leader', 'unknown')
            key_moments.append(f"[{time}s] MOMENTUM SHIFT! {new_leader.upper()} takes the lead!")

        elif event.event_type == EventType.AGENT_DIALOGUE:
            agent = event.data.get('from', 'Unknown')
            message = event.data.get('message', '')

            # Track dramatic messages
            if any(word in message.lower() for word in ['enough', 'shadows', 'tide', 'depths']):
                key_moments.append(f"[{time}s] {agent}: \"{message}\"")

    event_bus.subscribe(EventType.GIFT_SENT, track_key_moments)
    event_bus.subscribe(EventType.MOMENTUM_SHIFT, track_key_moments)
    event_bus.subscribe(EventType.AGENT_DIALOGUE, track_key_moments)

    return key_moments


def generate_battle_lore(engine, key_moments, gpt_lore):
    """Generate epic battle narrative."""

    if not gpt_lore.is_available():
        print("\n📖 Battle Lore: (GPT unavailable, skipping lore generation)")
        return

    print("\n" + "=" * 70)
    print("📖 EPIC BATTLE LORE")
    print("=" * 70 + "\n")

    print("🔮 Channeling the ancient storytellers... (GPT-4 generating narrative)\n")

    battle_data = {
        "winner": engine.score_tracker.get_leader() or "tie",
        "creator_score": engine.score_tracker.creator_score,
        "opponent_score": engine.score_tracker.opponent_score,
        "agents": [agent.name for agent in engine.agents],
        "key_moments": key_moments
    }

    lore = gpt_lore.generate_battle_summary(battle_data, style="epic")

    print(lore)
    print("\n" + "=" * 70)


def print_gpt_stats(agents):
    """Print GPT usage statistics."""

    print("\n" + "=" * 70)
    print("🤖 GPT INTELLIGENCE STATS")
    print("=" * 70 + "\n")

    for agent in agents:
        if hasattr(agent, 'get_gpt_stats'):
            stats = agent.get_gpt_stats()
            print(f"{agent.emoji} {agent.name}:")
            print(f"   GPT Decisions:      {stats['gpt_decisions']}")
            print(f"   Fallback Decisions: {stats['fallback_decisions']}")
            print(f"   GPT Usage:          {stats['gpt_percentage']:.1f}%\n")


def main():
    """Run GPT-powered battle demo."""

    # Check GPT setup
    gpt_available = check_gpt_setup()
    print_header(gpt_available)

    # Create shared GPT engines
    gpt_engine = GPTDecisionEngine(model="gpt-4")
    gpt_lore = GPTLoreGenerator(model="gpt-4")

    # Create event bus and communication
    event_bus = EventBus(debug=False)
    comm_channel = CommunicationChannel()

    # Track key moments for lore
    key_moments = setup_battle_lore_tracking(event_bus, gpt_lore)

    # Create battle engine
    engine = BattleEngine(
        battle_duration=60,
        tick_speed=0.3,  # Slightly slower to appreciate GPT decisions
        event_bus=event_bus
    )

    # Create GPT-powered agents
    print("🤖 Initializing GPT-powered agents...\n")

    agents = [
        GPTNovaWhale(gpt_engine=gpt_engine),
        GPTPixelPixie(gpt_engine=gpt_engine),
        GPTShadowPatron(gpt_engine=gpt_engine),
    ]

    for agent in agents:
        agent.comm_channel = comm_channel
        engine.add_agent(agent)
        print(f"   {agent.emoji} {agent.name} - Ready")

    print("\n🎬 Battle Starting...\n")
    print("=" * 70 + "\n")

    # Run the battle
    try:
        engine.run(silent=False)
    except KeyboardInterrupt:
        print("\n\n⚠️ Battle interrupted!")
        engine.stop()

    # Print GPT stats
    print_gpt_stats(agents)

    # Generate battle lore
    generate_battle_lore(engine, key_moments, gpt_lore)

    # Final summary
    creator, opponent = engine.score_tracker.get_scores()
    winner = engine.score_tracker.get_leader()

    print("\n" + "=" * 70)
    print("🏆 FINAL RESULTS")
    print("=" * 70)
    print(f"\nCreator:  {creator:,} points")
    print(f"Opponent: {opponent:,} points")
    print(f"Winner:   {winner.upper() if winner else 'TIE'}")
    print("\n" + "=" * 70 + "\n")

    if gpt_available:
        print("✨ GPT-powered battle complete!")
        print("\nNotice how agents:")
        print("  • Made contextual decisions based on battle state")
        print("  • Timed their actions strategically")
        print("  • Generated unique, in-character messages")
        print("  • Adapted to the flow of battle")
    else:
        print("✨ Demo complete (ran in fallback mode)")
        print("\n💡 To see GPT intelligence in action:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("   python3 demo_gpt_battle.py")

    print()


if __name__ == "__main__":
    main()
