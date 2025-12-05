"""
Best of 5 Tournament Demo

Demonstrates:
- 5-battle tournament series
- Shared budget (250,000 points)
- Reward accumulation over multiple wins
- Strategic budget management
- Complete tournament analytics
"""

from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat, BattleReward
from core.team_coordinator import TeamCoordinator
from core.battle_visualizer import BattleVisualizer
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


def run_single_battle(battle_num: int, tournament: TournamentManager,
                     show_analytics: bool = False) -> tuple:
    """
    Run a single battle in the tournament.

    Args:
        battle_num: Battle number (1-5)
        tournament: TournamentManager instance
        show_analytics: If True, show detailed analytics after battle

    Returns:
        Tuple of (winner, creator_score, opponent_score, budget_spent, analytics)
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
    print(f"🎯 Team: Kinetik 🔫 | Sentinel 🛡️ | Activator 📊 | StrikeMaster 🥊")
    print(f"⏱️  Time extensions: {time_extensions}")
    print(f"💰 Budget remaining: {tournament.shared_budget.remaining:,} points")
    print(f"📊 Series score: Creator {tournament.creator_wins} - {tournament.opponent_wins} Opponent\n")

    engine.run(silent=True)

    # Get results
    winner = engine.analytics.winner if engine.analytics else "tie"
    creator_score = engine.analytics.final_scores.get("creator", 0) if engine.analytics else 0
    opponent_score = engine.analytics.final_scores.get("opponent", 0) if engine.analytics else 0

    # Calculate budget spent
    budget_spent = 0
    if engine.analytics:
        performance = engine.analytics.get_agent_performance()
        for agent, stats in performance.items():
            budget_spent += stats['total_donated']

    # Update shared budget
    tournament.shared_budget.spend(budget_spent, "Tournament")

    # Show analytics if requested
    if show_analytics and engine.analytics:
        visualizer = BattleVisualizer()
        print("\n" + visualizer.create_score_chart(engine.analytics, width=60, height=10))
        print(visualizer.create_agent_comparison(engine.analytics))

    return winner, creator_score, opponent_score, budget_spent, engine.analytics


def main():
    print("\n" + "="*70)
    print("🏆 BEST OF 5 TOURNAMENT DEMONSTRATION")
    print("="*70 + "\n")

    print("This demo showcases:")
    print("  • Extended 5-battle series")
    print("  • Shared budget management (250,000 points)")
    print("  • Reward accumulation and strategy")
    print("  • Complete tournament analytics\n")

    # Create tournament
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_5,
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

    # Track all battle analytics
    all_analytics = []

    # Run battles until tournament complete
    battle_num = 0
    while tournament.can_continue():
        battle_num += 1

        # Print series status between battles
        if battle_num > 1:
            tournament.print_series_status()
            input("\nPress Enter to start next battle...")

        # Run battle (show analytics for final battle)
        show_analytics = (battle_num == tournament.format.value or
                         not tournament.can_continue())

        winner, creator_score, opponent_score, budget_spent, analytics = run_single_battle(
            battle_num, tournament, show_analytics=show_analytics
        )

        all_analytics.append(analytics)

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

    # Tournament complete
    print("\n" + "="*70)
    print("🎉 TOURNAMENT ANALYSIS")
    print("="*70)

    # Overall statistics
    stats = tournament.get_tournament_stats()
    print(f"\n📊 Overall Statistics:")
    print(f"   Format: {stats['format']}")
    print(f"   Total Battles Played: {stats['total_battles']}")
    print(f"   Champion: 👑 {stats['tournament_winner'].upper()}")
    print(f"   Final Score: Creator {stats['creator_wins']} - {stats['opponent_wins']} Opponent")

    # Budget analysis
    budget = stats['budget']
    print(f"\n💰 Budget Analysis:")
    print(f"   Total Budget: {budget['total']:,} points")
    print(f"   Total Spent: {budget['spent']:,} points ({budget['spent_percent']:.1f}%)")
    print(f"   Remaining: {budget['remaining']:,} points")
    print(f"   Avg per Battle: {budget['spent'] // stats['total_battles']:,} points")

    # Rewards earned
    print(f"\n🎁 Final Inventories:")
    print(f"   Creator: {stats['creator_inventory']}")
    print(f"   Opponent: {stats['opponent_inventory']}")

    # Battle-by-battle breakdown
    print(f"\n📋 Battle-by-Battle Results:")
    for i, battle in enumerate(stats['battles'], 1):
        winner_symbol = "✅" if battle['winner'] == stats['tournament_winner'] else "❌"
        print(f"   Battle {i}: {winner_symbol} {battle['winner'].title()} wins "
              f"({battle['creator_score']:,} vs {battle['opponent_score']:,}) "
              f"[Budget: {battle['budget_spent']:,}]")

    # Performance trends
    print(f"\n📈 Performance Trends:")
    creator_scores = [b['creator_score'] for b in stats['battles']]
    opponent_scores = [b['opponent_score'] for b in stats['battles']]
    print(f"   Creator Avg Score: {sum(creator_scores) // len(creator_scores):,}")
    print(f"   Opponent Avg Score: {sum(opponent_scores) // len(opponent_scores):,}")
    print(f"   Avg Margin: {sum(b['score_diff'] for b in stats['battles']) // len(stats['battles']):,}")

    print("\n" + "="*70)
    print("✅ Tournament Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
