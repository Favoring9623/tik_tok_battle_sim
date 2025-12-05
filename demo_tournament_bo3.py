"""
Best of 3 Tournament Demo

Demonstrates:
- 3-battle tournament series
- Shared budget (250,000 points)
- Reward distribution to winners
- Inventory persistence between battles
- Tournament statistics and analytics
"""

from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat, BattleReward
from core.team_coordinator import TeamCoordinator
from agents.specialists.kinetik_sniper import AgentKinetik
from agents.specialists.sentinel import AgentSentinel
from agents.specialists.activator import AgentActivator
from agents.specialists.strike_master import AgentStrikeMaster


def create_team():
    """Create a standard team of 4 specialists."""
    coordinator = TeamCoordinator()

    # Create agents
    kinetik = AgentKinetik()
    sentinel = AgentSentinel()
    activator = AgentActivator()
    strike_master = AgentStrikeMaster()

    # Register with coordinator
    agents = [kinetik, sentinel, activator, strike_master]
    for agent in agents:
        agent.coordinator = coordinator

    return agents, coordinator


def run_single_battle(battle_num: int, tournament: TournamentManager) -> tuple:
    """
    Run a single battle in the tournament.

    Args:
        battle_num: Battle number (1, 2, or 3)
        tournament: TournamentManager instance

    Returns:
        Tuple of (winner, creator_score, opponent_score, budget_spent)
    """
    print(f"\n{'='*70}")
    print(f"⚔️  BATTLE {battle_num} - START")
    print(f"{'='*70}\n")

    # Get time extensions from tournament inventory
    time_extensions = tournament.get_available_time_extensions("creator")

    # Create battle engine
    engine = BattleEngine(
        battle_duration=tournament.battle_duration,
        tick_speed=0.1,  # Fast for demo
        enable_multipliers=True,
        time_extensions=time_extensions,
        enable_analytics=True
    )

    # Create team
    agents, coordinator = create_team()
    for agent in agents:
        engine.add_agent(agent)

    # Run battle
    print(f"Team assembled: Kinetik, Sentinel, Activator, StrikeMaster")
    print(f"Time extensions available: {time_extensions}")
    print(f"Budget remaining: {tournament.shared_budget.remaining:,} points\n")

    engine.run(silent=True)

    # Get results
    winner = engine.analytics.winner if engine.analytics else "tie"
    creator_score = engine.analytics.final_scores.get("creator", 0) if engine.analytics else 0
    opponent_score = engine.analytics.final_scores.get("opponent", 0) if engine.analytics else 0

    # Calculate budget spent (sum of all agent donations)
    budget_spent = 0
    if engine.analytics:
        performance = engine.analytics.get_agent_performance()
        for agent, stats in performance.items():
            budget_spent += stats['total_donated']

    # Update shared budget
    tournament.shared_budget.spend(budget_spent, "Tournament")

    return winner, creator_score, opponent_score, budget_spent


def main():
    print("\n" + "="*70)
    print("🏆 BEST OF 3 TOURNAMENT DEMONSTRATION")
    print("="*70 + "\n")

    # Create tournament
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=180,
        reward_config=BattleReward(
            x5_gloves=1,
            fogs=1,
            hammers=1,
            time_extensions=1
        )
    )

    # Start tournament
    tournament.start_tournament()

    # Run battles until tournament complete
    battle_num = 0
    while tournament.can_continue():
        battle_num += 1

        # Print series status
        if battle_num > 1:
            tournament.print_series_status()

        # Run battle
        winner, creator_score, opponent_score, budget_spent = run_single_battle(
            battle_num, tournament
        )

        # Record result
        tournament.record_battle_result(
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score,
            budget_spent_this_battle=budget_spent
        )

        # Check if tournament is over
        if not tournament.can_continue():
            break

        # Pause between battles
        input("\nPress Enter to continue to next battle...")

    # Tournament complete - stats already printed by tournament.record_battle_result()
    print("\n" + "="*70)
    print("✅ Tournament Complete!")
    print("="*70)

    # Export tournament stats
    stats = tournament.get_tournament_stats()
    print(f"\n📊 Tournament Statistics:")
    print(f"   Format: {stats['format']}")
    print(f"   Total Battles: {stats['total_battles']}")
    print(f"   Champion: {stats['tournament_winner'].upper()}")
    print(f"   Budget Used: {stats['budget']['spent']:,} / {stats['budget']['total']:,} "
          f"({stats['budget']['spent_percent']:.1f}%)")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
