#!/usr/bin/env python3
"""
Specialist Agents Demo - Showcasing the 4 new tactical agents.

Features:
- Real TikTok gift catalog (42 gifts from StreamToEarn)
- 4 specialized agents with unique roles:
  🔫 Kinetik - Final seconds sniper
  🥊 StrikeMaster - x5 glove specialist
  📊 Activator - Bonus session trigger
  🛡️ Sentinel - Defense and stealth
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
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    load_env_file()

from core import BattleEngine, EventBus, EventType
from agents.specialists.kinetik_sniper import AgentKinetik
from agents.specialists.strike_master import AgentStrikeMaster
from agents.specialists.activator import AgentActivator
from agents.specialists.sentinel import AgentSentinel
from agents.communication import CommunicationChannel
from core.gift_catalog import get_gift_catalog


def print_header():
    """Print demo header."""
    print("=" * 70)
    print("🎯 SPECIALIST AGENTS DEMO")
    print("=" * 70)
    print("\nFeaturing 4 tactical specialists with real TikTok gifts:\n")
    print("  🔫 Kinetik       - Final seconds sniper (Universe bombs)")
    print("  🥊 StrikeMaster  - x5 glove strike master (Lion combos)")
    print("  📊 Activator     - Bonus session trigger (Rose spam)")
    print("  🛡️ Sentinel      - Defense & stealth (Hammer/Fog)")
    print("\n" + "=" * 70 + "\n")


def show_gift_catalog():
    """Display available gifts."""
    catalog = get_gift_catalog()

    print("\n📦 REAL TIKTOK GIFT CATALOG")
    print("=" * 70)

    print("\n💰 Budget Gifts (1-99 coins):")
    for gift in catalog.get_budget_gifts()[:5]:
        print(f"   {gift}")

    print("\n💎 Premium Gifts (1,000-9,999 coins):")
    for gift in catalog.get_premium_gifts()[:5]:
        print(f"   {gift}")

    print("\n🐋 Whale Gifts (10,000+ coins):")
    for gift in catalog.get_whale_gifts():
        print(f"   {gift}")

    print(f"\n   Total: {len(catalog.gifts)} gifts available")
    print("=" * 70 + "\n")


def show_specialist_loadouts():
    """Show each specialist's signature gifts and inventory."""
    catalog = get_gift_catalog()

    print("\n⚔️ SPECIALIST LOADOUTS")
    print("=" * 70)

    specialists = [
        ("Kinetik", "🔫", "TikTok Universe", "44,999 coins", "1x Universe snipe"),
        ("StrikeMaster", "🥊", "Lion", "29,999 coins", "3 Gloves + Lion"),
        ("Activator", "📊", "Rose", "1 coin", "5,000 Roses available"),
        ("Sentinel", "🛡️", "Galaxy", "1,000 coins", "2 Hammers, 2 Fogs"),
    ]

    for name, emoji, gift_name, cost, inventory in specialists:
        gift = catalog.get_gift(gift_name)
        print(f"\n{emoji} {name}:")
        print(f"   Signature: {gift}")
        print(f"   Inventory: {inventory}")

    print("\n" + "=" * 70 + "\n")


def run_battle():
    """Run a battle with the specialist team."""

    print("🎬 Initializing battle with specialist team...\n")

    # Create specialists
    kinetik = AgentKinetik()
    strike_master = AgentStrikeMaster()
    activator = AgentActivator()
    sentinel = AgentSentinel()

    agents = [kinetik, strike_master, activator, sentinel]

    print("✅ Agents ready:")
    for agent in agents:
        print(f"   {agent.emoji} {agent.name}")

    # Create battle engine
    event_bus = EventBus()
    comm_channel = CommunicationChannel()

    engine = BattleEngine(
        battle_duration=180,  # Full 3-minute battle!
        tick_speed=0.1,  # Faster ticks for demo (0.1s real-time per battle second)
        event_bus=event_bus
    )

    # Add and connect agents
    for agent in agents:
        agent.event_bus = event_bus
        agent.comm_channel = comm_channel
        engine.add_agent(agent)

    print("\n" + "=" * 70)
    print("🎬 Starting Battle...")
    print("=" * 70 + "\n")

    # Run battle
    engine.run(silent=False)

    # Get results
    winner = engine.score_tracker.get_leader()
    creator_score, opponent_score = engine.score_tracker.get_scores()

    # Show results
    print("\n" + "=" * 70)
    print("🏆 BATTLE RESULTS")
    print("=" * 70)

    print(f"\nCreator:  {creator_score:,} points")
    print(f"Opponent: {opponent_score:,} points")
    print(f"Winner:   {(winner or 'tie').upper()}\n")

    # Show specialist stats
    print("=" * 70)
    print("📊 SPECIALIST PERFORMANCE")
    print("=" * 70)

    for agent in agents:
        print(f"\n{agent.emoji} {agent.name}:")
        print(f"   Total Donated: {agent.total_donated:,} points")
        print(f"   Actions Taken: {agent.action_count}")

        # Specialist-specific stats
        if isinstance(agent, AgentStrikeMaster):
            print(f"   Gloves Used: {agent.gloves_used}/{agent.gloves_available}")
            print(f"   x5 Success Rate: {agent.x5_success_rate:.1%}")
        elif isinstance(agent, AgentActivator):
            stats = agent.get_activation_stats()
            print(f"   Bonus Triggered: {'✅ YES' if stats['bonus_triggered'] else '❌ NO'}")
            print(f"   Roses Sent: {stats['roses_sent']}")
        elif isinstance(agent, AgentSentinel):
            inv = agent.get_inventory_status()
            print(f"   Hammers Remaining: {inv['hammers']}/2")
            print(f"   Fogs Remaining: {inv['fogs']}/2")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main demo function."""

    print_header()
    show_gift_catalog()
    show_specialist_loadouts()

    run_battle()

    print("✨ Demo complete!\n")
    print("💡 Features Active:")
    print("   ✅ 180-second battle timeline")
    print("   ✅ x2/x3/x5 multiplier system")
    print("   ✅ 4 specialist agents with unique roles")
    print("   ✅ Real TikTok gift catalog (42 gifts)")
    print("\n💡 Next steps:")
    print("   - Add GPT-powered versions of specialists")
    print("   - Test Fog deployment and Hammer counters")
    print("   - Optimize agent coordination\n")


if __name__ == "__main__":
    main()
