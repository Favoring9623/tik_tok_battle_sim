"""
Enhanced Tournament Demo - Variable Budgets & Performance Rewards

New Features:
1. Performance-Based Rewards: 80k+ contribution = 3x rewards
2. Random Budget Scenarios: Creates diversity and closer matches
3. Dynamic Gameplay: Each battle has different strategic constraints

Scenarios:
- 🔥 Aggressive: 80-120k spending (all-out attack)
- ⚖️ Balanced: 50-80k spending (standard play)
- 🛡️ Conservative: 30-50k spending (resource management)
- ⚡ Clutch: 100-150k spending (must-win situation)
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
    """
    Run a single battle with random budget scenario.

    Args:
        battle_num: Battle number
        tournament: TournamentManager instance

    Returns:
        Tuple of (winner, creator_score, opponent_score, budget_spent, performance)
    """
    # Get random budget scenario
    scenario_name, budget_limit = tournament.get_random_budget_limit()

    print(f"\n{'='*70}")
    print(f"⚔️  BATTLE {battle_num} - START")
    print(f"{'='*70}")
    print(f"📊 Budget Scenario: {scenario_name}")
    if budget_limit:
        print(f"   Budget Limit: {budget_limit:,} points")
    print(f"💰 Tournament Budget Remaining: {tournament.shared_budget.remaining:,}")
    print(f"🏆 Series: Creator {tournament.creator_wins} - {tournament.opponent_wins} Opponent")
    print(f"{'='*70}\n")

    # Get time extensions
    time_ext = tournament.get_available_time_extensions("creator")

    # Create and run battle
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0.05,  # Fast
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

    # Get agent performance
    performance = engine.analytics.get_agent_performance()

    # Calculate budget spent
    budget_spent = sum(
        stats['total_donated']
        for stats in performance.values()
    )

    # Update shared budget
    tournament.shared_budget.spend(budget_spent, "Tournament")

    return winner, c_score, o_score, budget_spent, performance


def main():
    print("\n" + "="*70)
    print("🎉 ENHANCED TOURNAMENT - VARIABLE BUDGETS & PERFORMANCE REWARDS")
    print("="*70 + "\n")

    print("🆕 New Features:")
    print("  • 🏅 Performance Rewards: 80k+ contribution = 3x rewards!")
    print("  • 🎲 Random Budget Scenarios: Different spending limits per battle")
    print("  • 🎯 Diverse Gameplay: Strategic variety in every match\n")

    # Create tournament
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=180
    )

    # Enable random budgets
    tournament.enable_random_budgets()

    # Start
    tournament.start_tournament()

    # Run battles
    battle_num = 0
    while tournament.can_continue():
        battle_num += 1

        # Run battle
        winner, c_score, o_score, budget, performance = run_battle(
            battle_num, tournament
        )

        # Record with performance data
        tournament.record_battle_result(
            winner=winner,
            creator_score=c_score,
            opponent_score=o_score,
            budget_spent_this_battle=budget,
            agent_performance=performance  # ← Performance-based rewards
        )

        # Pause between battles
        if tournament.can_continue():
            print("\n" + "="*70)
            input("Press Enter to continue to next battle...")

    # Final summary
    stats = tournament.get_tournament_stats()
    print("\n" + "="*70)
    print("🏆 ENHANCED TOURNAMENT SUMMARY")
    print("="*70)
    print(f"\n👑 Champion: {stats['tournament_winner'].upper()}")
    print(f"📊 Final Score: Creator {stats['creator_wins']} - {stats['opponent_wins']} Opponent")
    print(f"💰 Budget: {stats['budget']['spent']:,} / {stats['budget']['total']:,} "
          f"({stats['budget']['spent_percent']:.1f}%)")

    # Performance highlights
    print(f"\n⭐ Performance Highlights:")
    for battle in stats['battles']:
        bonus_text = " 🎉 BONUS!" if battle.get('bonus_rewards_earned', False) else ""
        top_contrib = battle.get('top_contributor', 'N/A')
        top_points = battle.get('top_contribution', 0)
        print(f"   Battle {battle['number']}: {top_contrib} ({top_points:,} pts){bonus_text}")

    print("\n" + "="*70)
    print("✅ Enhanced Tournament Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
