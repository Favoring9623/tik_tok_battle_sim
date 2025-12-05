"""
Quick Tournament Demo (Non-Interactive)

Runs a complete Best of 3 tournament without pauses for testing.
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
    agents = [AgentKinetik(), AgentSentinel(), AgentActivator(), AgentStrikeMaster()]
    for agent in agents:
        agent.coordinator = coordinator
    return agents


def run_battle(battle_num: int, tournament: TournamentManager):
    """Run a single battle."""
    print(f"\n⚔️  BATTLE {battle_num}")
    print(f"Budget remaining: {tournament.shared_budget.remaining:,}\n")

    # Get time extensions
    time_ext = tournament.get_available_time_extensions("creator")

    # Create and run battle
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.05,  # Very fast
        enable_multipliers=True,
        time_extensions=time_ext,
        enable_analytics=True
    )

    for agent in create_team():
        engine.add_agent(agent)

    engine.run(silent=True)

    # Get results
    winner = engine.analytics.winner
    c_score = engine.analytics.final_scores.get("creator", 0)
    o_score = engine.analytics.final_scores.get("opponent", 0)

    # Calculate budget spent
    budget_spent = sum(
        stats['total_donated']
        for stats in engine.analytics.get_agent_performance().values()
    )

    tournament.shared_budget.spend(budget_spent, "Tournament")

    return winner, c_score, o_score, budget_spent


def main():
    print("\n" + "="*70)
    print("🏆 QUICK TOURNAMENT TEST - BEST OF 3")
    print("="*70 + "\n")

    # Create tournament
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=180
    )

    tournament.start_tournament()

    # Run battles
    battle_num = 0
    while tournament.can_continue():
        battle_num += 1
        winner, c_score, o_score, budget = run_battle(battle_num, tournament)
        tournament.record_battle_result(winner, c_score, o_score, budget)

    # Final stats
    stats = tournament.get_tournament_stats()
    print(f"\n✅ TOURNAMENT COMPLETE!")
    print(f"Champion: {stats['tournament_winner'].upper()}")
    print(f"Budget used: {stats['budget']['spent']:,} / {stats['budget']['total']:,}")
    print(f"Battles played: {stats['total_battles']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
