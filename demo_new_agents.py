"""
Demo: New Agent Types Showcase

Demonstrates the 4 new specialist agents in action:
- DefenseMaster (counter-focused)
- BudgetOptimizer (efficiency specialist)
- ChaoticTrickster (psychological warfare)
- SynergyCoordinator (team combos)

Watch them work together against a tough opponent!
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.team_coordinator import TeamCoordinator
from agents.specialists import (
    DefenseMaster,
    BudgetOptimizer,
    ChaoticTrickster,
    SynergyCoordinator,
    AgentKinetik,
    AgentStrikeMaster
)


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    print(f"\n{char * 70}")
    print(f"  {text}")
    print(f"{char * 70}\n")


def print_agent_intro(agent, description: str):
    """Print agent introduction."""
    print(f"   {agent.emoji} {agent.name}")
    print(f"      {description}")
    caps = agent.get_capabilities() if hasattr(agent, 'get_capabilities') else []
    if caps:
        print(f"      Capabilities: {', '.join(caps[:4])}")
    print()


def create_new_agent_team(phase_manager):
    """Create a team featuring the 4 new agents."""

    print_header("ASSEMBLING THE NEW AGENT TEAM", "~")

    # Create coordinator for team synergy
    coordinator = TeamCoordinator()

    # Create the 4 new agents
    defense = DefenseMaster(phase_manager=phase_manager)
    budget = BudgetOptimizer(phase_manager=phase_manager)
    trickster = ChaoticTrickster(phase_manager=phase_manager)
    synergy = SynergyCoordinator(phase_manager=phase_manager)

    # Add classic agents for comparison
    kinetik = AgentKinetik()
    strike = AgentStrikeMaster()

    # Build team
    team = [defense, budget, trickster, synergy, kinetik, strike]

    # IMPORTANT: Set budget_manager to None so can_afford always returns True
    # This allows agents to send larger gifts in the demo
    for agent in team:
        agent.budget_manager = None  # No budget restrictions for demo
        if hasattr(agent, 'coordinator'):
            agent.coordinator = coordinator

    # Boost BudgetOptimizer spend rates for demo visibility
    budget.spend_rate_normal = 0.35  # 35% vs default 10%
    budget.spend_rate_boost = 0.6    # 60% vs default 40%
    budget.spend_rate_final = 0.5    # 50% vs default 30%
    budget.efficiency_threshold = 0.5  # Lower threshold for more spending

    # Boost ChaoticTrickster activity
    trickster.chaos_level = 0.6

    # Register team with synergy coordinator
    synergy.register_team(team)

    # Print introductions
    print_agent_intro(defense, "Counter-strategy specialist - neutralizes opponent threats")
    print_agent_intro(budget, "Efficiency master - maximizes points per coin spent")
    print_agent_intro(trickster, "Chaos agent - bluffs, decoys, and mind games")
    print_agent_intro(synergy, "Team orchestrator - coordinates powerful combos")
    print_agent_intro(kinetik, "Classic sniper - final seconds specialist")
    print_agent_intro(strike, "Glove master - x5 multiplier expert")

    return team


def run_showcase_battle():
    """Run a battle showcasing the new agents."""

    print("\n" + "=" * 70)
    print("   NEW AGENT TYPES SHOWCASE")
    print("   Featuring: DefenseMaster, BudgetOptimizer, ChaoticTrickster, SynergyCoordinator")
    print("=" * 70)

    # Create phase manager with power-ups
    print("\n   Initializing battle systems...")
    phase_manager = AdvancedPhaseManager(battle_duration=180)

    # Add power-ups
    for _ in range(2):
        phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
        phase_manager.add_power_up(PowerUpType.FOG, "creator")
    phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")

    print("   Power-ups loaded: 2x Hammer, 2x Fog, 1x Time Bonus")

    # Create team
    team = create_new_agent_team(phase_manager)

    print_header("BATTLE START", "=")
    print("   Duration: 180 seconds")
    print("   Team Size: 6 agents (4 new + 2 classic)")
    print("   Objective: Demonstrate new agent capabilities\n")

    # Create battle engine
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.08,  # Fast but visible
        enable_multipliers=True,
        enable_analytics=True
    )

    # Add agents
    for agent in team:
        engine.add_agent(agent)

    # Track phase manager updates
    original_tick = engine._tick

    def wrapped_tick(silent):
        original_tick(silent)
        current_time = engine.time_manager.current_time
        phase_manager.update(current_time)

        # Display updates at key moments
        if current_time % 30 == 0 and current_time > 0:
            print(f"\n{'─' * 50}")
            print(f"   t={current_time}s | Creator: {engine.score_tracker.creator_score:,} | Opponent: {engine.score_tracker.opponent_score:,}")
            print(f"{'─' * 50}\n")

    engine._tick = wrapped_tick

    # Run battle
    engine.run(silent=False)

    # Results
    print_header("BATTLE COMPLETE", "=")

    winner = "CREATOR" if engine.score_tracker.creator_score > engine.score_tracker.opponent_score else "OPPONENT"
    print(f"   Winner: {winner}")
    print(f"   Creator: {engine.score_tracker.creator_score:,}")
    print(f"   Opponent: {engine.score_tracker.opponent_score:,}")

    # Agent performance
    print_header("NEW AGENT PERFORMANCE", "-")

    for agent in team[:4]:  # Just the 4 new agents
        print(f"\n   {agent.emoji} {agent.name}:")
        print(f"      Points Donated: {agent.total_donated:,}")
        print(f"      Actions Taken: {agent.action_count}")

        # Agent-specific stats
        if hasattr(agent, 'get_efficiency_report'):
            report = agent.get_efficiency_report()
            print(f"      Efficiency: {report.get('overall_efficiency', 0):.2f}x")

        if hasattr(agent, 'get_chaos_report'):
            report = agent.get_chaos_report()
            print(f"      Chaos Level: {report.get('chaos_level', 0):.0%}")
            tactics = report.get('tactics_used', {})
            if any(v > 0 for v in tactics.values()):
                print(f"      Tactics Used: {sum(tactics.values())}")

        if hasattr(agent, 'get_combo_report'):
            report = agent.get_combo_report()
            print(f"      Combos Executed: {report.get('combos_executed', 0)}")

        if hasattr(agent, 'hammers_used'):
            print(f"      Hammers Used: {agent.hammers_used}/{agent.hammers_available}")
            print(f"      Fogs Used: {agent.fogs_used}/{agent.fogs_available}")

    print_header("SHOWCASE COMPLETE", "=")

    return engine


def run_multi_battle_test():
    """Run multiple battles to show learning."""

    print("\n" + "=" * 70)
    print("   MULTI-BATTLE LEARNING TEST")
    print("   Watch the new agents improve over 3 battles!")
    print("=" * 70)

    results = []

    for battle_num in range(1, 4):
        print(f"\n{'~' * 70}")
        print(f"   BATTLE {battle_num} of 3")
        print(f"{'~' * 70}")

        # Create fresh phase manager
        phase_manager = AdvancedPhaseManager(battle_duration=120)
        phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
        phase_manager.add_power_up(PowerUpType.FOG, "creator")

        # Create team
        defense = DefenseMaster(phase_manager=phase_manager)
        budget = BudgetOptimizer(phase_manager=phase_manager)
        trickster = ChaoticTrickster(phase_manager=phase_manager)
        synergy = SynergyCoordinator(phase_manager=phase_manager)

        team = [defense, budget, trickster, synergy]

        # Configure for demo visibility
        for agent in team:
            agent.budget_manager = None

        # Boost spend rates
        budget.spend_rate_normal = 0.4
        budget.spend_rate_boost = 0.7
        budget.spend_rate_final = 0.6
        trickster.chaos_level = 0.5

        # Register synergy team
        synergy.register_team(team)

        # Create and run battle
        engine = BattleEngine(
            battle_duration=120,
            tick_speed=0.02,  # Very fast
            enable_multipliers=True,
            enable_analytics=True
        )

        for agent in team:
            engine.add_agent(agent)

        # Wrap tick for phase updates
        original_tick = engine._tick
        def make_wrapped(pm):
            def wrapped(silent):
                original_tick(silent)
                pm.update(engine.time_manager.current_time)
            return wrapped
        engine._tick = make_wrapped(phase_manager)

        # Run silently
        engine.run(silent=True)

        # Record result
        creator_score = engine.score_tracker.creator_score
        opponent_score = engine.score_tracker.opponent_score
        won = creator_score > opponent_score

        results.append({
            'battle': battle_num,
            'creator': creator_score,
            'opponent': opponent_score,
            'won': won,
            'margin': creator_score - opponent_score
        })

        # Learn from battle
        battle_stats = {
            'gifts_sent': sum(a.action_count for a in team),
            'boost2_triggered': phase_manager.boost2_triggered
        }

        for agent in team:
            if hasattr(agent, 'learn_from_battle'):
                agent.learn_from_battle(won, battle_stats)

        # Print result
        status = "WIN" if won else "LOSS"
        print(f"   Result: {status} | Creator: {creator_score:,} vs Opponent: {opponent_score:,}")
        print(f"   Margin: {'+' if won else ''}{creator_score - opponent_score:,}")

    # Summary
    print("\n" + "=" * 70)
    print("   MULTI-BATTLE SUMMARY")
    print("=" * 70)

    wins = sum(1 for r in results if r['won'])
    print(f"\n   Total: {wins}/{len(results)} wins ({wins/len(results)*100:.0f}%)")
    print(f"   Average Margin: {sum(r['margin'] for r in results) / len(results):,.0f}")

    print("\n   Battle Results:")
    for r in results:
        status = "WIN" if r['won'] else "LOSS"
        print(f"      Battle {r['battle']}: {status} ({r['creator']:,} vs {r['opponent']:,})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="New Agent Types Demo")
    parser.add_argument("--quick", action="store_true", help="Run quick multi-battle test")
    args = parser.parse_args()

    if args.quick:
        run_multi_battle_test()
    else:
        run_showcase_battle()

    print("\n   Demo complete!")
