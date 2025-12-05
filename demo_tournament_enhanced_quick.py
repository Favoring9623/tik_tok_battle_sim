"""
Enhanced Tournament Quick Demo (Non-Interactive)

Features:
- Performance-Based Rewards (80k+ = 3x)
- Random Budget Scenarios
- Complete BO3 Tournament
"""

from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat
from core.team_coordinator import TeamCoordinator
from agents.specialists.kinetik_sniper import AgentKinetik
from agents.specialists.sentinel import AgentSentinel
from agents.specialists.activator import AgentActivator
from agents.specialists.strike_master import AgentStrikeMaster


def create_team():
    """Create team."""
    coordinator = TeamCoordinator()
    agents = [AgentKinetik(), AgentSentinel(), AgentActivator(), AgentStrikeMaster()]
    for agent in agents:
        agent.coordinator = coordinator
    return agents


def run_battle(battle_num: int, tournament: TournamentManager):
    """Run battle with scenario."""
    scenario_name, budget_limit = tournament.get_random_budget_limit()

    print(f"\n⚔️  BATTLE {battle_num}")
    print(f"   Scenario: {scenario_name}")
    if budget_limit:
        print(f"   Budget Limit: {budget_limit:,}")
    print(f"   Remaining: {tournament.shared_budget.remaining:,}\n")

    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.05,
        enable_multipliers=True,
        time_extensions=tournament.get_available_time_extensions("creator"),
        enable_analytics=True
    )

    for agent in create_team():
        engine.add_agent(agent)

    engine.run(silent=True)

    # Results
    winner = engine.analytics.winner
    c_score = engine.analytics.final_scores.get("creator", 0)
    o_score = engine.analytics.final_scores.get("opponent", 0)
    performance = engine.analytics.get_agent_performance()
    budget = sum(stats['total_donated'] for stats in performance.values())

    tournament.shared_budget.spend(budget, "Tournament")

    return winner, c_score, o_score, budget, performance


def main():
    print("\n" + "="*70)
    print("🎉 ENHANCED TOURNAMENT QUICK TEST")
    print("="*70 + "\n")

    # Create tournament
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=180
    )

    # Enable random budgets
    tournament.enable_random_budgets()
    tournament.start_tournament()

    # Run battles
    battle_num = 0
    while tournament.can_continue():
        battle_num += 1
        winner, c_score, o_score, budget, perf = run_battle(battle_num, tournament)

        # Record with performance
        tournament.record_battle_result(
            winner=winner,
            creator_score=c_score,
            opponent_score=o_score,
            budget_spent_this_battle=budget,
            agent_performance=perf
        )

    # Summary
    stats = tournament.get_tournament_stats()
    print("\n" + "="*70)
    print("🏆 ENHANCED TOURNAMENT RESULTS")
    print("="*70)
    print(f"\n👑 Champion: {stats['tournament_winner'].upper()}")
    print(f"📊 Score: {stats['creator_wins']}-{stats['opponent_wins']}")
    print(f"💰 Budget: {stats['budget']['spent']:,} / {stats['budget']['total']:,}")

    print(f"\n⭐ Performance Highlights:")
    for b in stats['battles']:
        bonus = " 🎉 BONUS!" if b['bonus_rewards_earned'] else ""
        print(f"   Battle {b['number']}: {b['top_contributor']} ({b['top_contribution']:,}){bonus}")

    print(f"\n🎁 Final Inventory:")
    inv = stats['creator_inventory']
    print(f"   Gloves: {inv['x5_gloves']} | Fogs: {inv['fogs']} | "
          f"Hammers: {inv['hammers']} | Time: {inv['time_extensions']}")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
