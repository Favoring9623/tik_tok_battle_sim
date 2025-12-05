"""
Enhanced Tournament Demo - Full Features

Showcases all tournament enhancements:
- Bracket visualization
- Momentum tracking
- Leaderboard with ELO ratings
- Best of 3 with persona agents

Run multiple tournaments to see leaderboard rankings!
"""

from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat
from core.tournament_bracket import TournamentBracket, BracketVisualizer
from core.tournament_momentum import MomentumTracker
from core.tournament_leaderboard import TournamentLeaderboard
from agents.personas import NovaWhale, PixelPixie, GlitchMancer


def run_enhanced_tournament(leaderboard: TournamentLeaderboard):
    """
    Run a single Best of 3 tournament with all enhancements.

    Args:
        leaderboard: Tournament leaderboard tracker
    """
    print("\n" + "🎯" * 35)
    print("ENHANCED TOURNAMENT - BEST OF 3")
    print("🎯" * 35 + "\n")

    # Initialize systems
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=60  # Faster for demo
    )

    bracket = TournamentBracket(
        format_name="BEST_OF_3",
        battles_to_win=2
    )

    momentum = MomentumTracker(battles_to_win=2)

    # Start tournament
    tournament.start_tournament()

    battle_num = 0

    # Run battles until tournament complete
    while tournament.can_continue():
        battle_num += 1

        # Print pre-battle status
        tournament.print_series_status()
        bracket.print_compact_bracket()
        if battle_num > 1:
            momentum.print_momentum_report()

        print(f"\n{'=' * 70}")
        print(f"⚔️  BATTLE {battle_num} STARTING")
        print(f"{'=' * 70}\n")

        # Create battle engine
        engine = BattleEngine(
            battle_duration=tournament.battle_duration,
            enable_multipliers=True,
            enable_analytics=True
        )

        # Add creator team agents
        engine.add_agent(NovaWhale())
        engine.add_agent(PixelPixie())

        # Add opponent team agents
        engine.add_agent(GlitchMancer())

        # Run battle
        engine.run()

        # Get results
        winner = engine.analytics.winner
        creator_score = engine.analytics.final_scores['creator']
        opponent_score = engine.analytics.final_scores['opponent']
        agent_performance = engine.analytics.get_agent_performance()

        # Track budget spent (simplified - actual tracking would integrate with budget system)
        budget_spent = tournament.shared_budget.spent

        # Record in all systems
        tournament.record_battle_result(
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score,
            budget_spent_this_battle=0,  # Simplified for demo
            agent_performance=agent_performance
        )

        bracket.add_battle_result(
            battle_num=battle_num,
            creator_score=creator_score,
            opponent_score=opponent_score,
            winner=winner
        )

        momentum.record_battle(
            battle_num=battle_num,
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score
        )

        # Show updated bracket
        print("\n")
        bracket.print_bracket()

    # Tournament complete - show final visualizations
    print("\n" + "🏆" * 35)
    print("TOURNAMENT COMPLETE - FINAL STATISTICS")
    print("🏆" * 35 + "\n")

    # Final bracket
    bracket.print_bracket()

    # Bracket visualizations
    BracketVisualizer.print_series_progress_bar(
        creator_wins=tournament.creator_wins,
        opponent_wins=tournament.opponent_wins,
        battles_to_win=tournament.battles_to_win
    )

    BracketVisualizer.print_battle_timeline(bracket.battles)
    BracketVisualizer.print_score_comparison(bracket.battles)

    # Final momentum report
    momentum.print_momentum_report()

    # Record in leaderboard
    tournament_stats = tournament.get_tournament_stats()
    leaderboard.record_tournament(tournament_stats)

    return tournament.tournament_winner


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("🏆 ENHANCED TOURNAMENT SYSTEM DEMO")
    print("=" * 70)
    print("\nFeatures:")
    print("  ✅ ASCII Bracket Visualization")
    print("  ✅ Series Momentum Tracking")
    print("  ✅ ELO Rating System")
    print("  ✅ Tournament Leaderboard")
    print("  ✅ Performance Analytics")
    print("\n" + "=" * 70 + "\n")

    # Initialize leaderboard
    leaderboard = TournamentLeaderboard(save_file="tournament_leaderboard.json")

    # Show current standings if any
    if leaderboard.tournament_count > 0:
        print("📊 Current Standings:")
        leaderboard.print_leaderboard()

    # Ask how many tournaments to run
    print("How many tournaments would you like to run? (1-5): ", end="")
    try:
        count = int(input())
        count = max(1, min(5, count))
    except:
        count = 1
        print(f"Invalid input, running {count} tournament(s)")

    print(f"\n🎮 Running {count} tournament(s)...\n")

    # Run tournaments
    results = []
    for i in range(count):
        if count > 1:
            print(f"\n{'#' * 70}")
            print(f"# TOURNAMENT {i + 1} of {count}")
            print(f"{'#' * 70}\n")

        winner = run_enhanced_tournament(leaderboard)
        results.append(winner)

        if i < count - 1:
            input("\nPress Enter to start next tournament...")

    # Final leaderboard
    print("\n" + "=" * 70)
    print("🏆 FINAL LEADERBOARD")
    print("=" * 70)
    leaderboard.print_leaderboard()

    # Summary
    print("\n📊 Session Summary:")
    print(f"   Tournaments Played: {count}")
    creator_wins = results.count("creator")
    opponent_wins = results.count("opponent")
    print(f"   Creator Wins: {creator_wins}")
    print(f"   Opponent Wins: {opponent_wins}")

    if creator_wins > opponent_wins:
        print(f"\n🏆 SESSION CHAMPION: CREATOR ({creator_wins}-{opponent_wins})")
    elif opponent_wins > creator_wins:
        print(f"\n🏆 SESSION CHAMPION: OPPONENT ({opponent_wins}-{creator_wins})")
    else:
        print(f"\n🤝 SESSION TIED: {creator_wins}-{opponent_wins}")

    print("\n✅ Leaderboard data saved to tournament_leaderboard.json")
    print("\nRun this demo again to continue building your tournament history!\n")


if __name__ == '__main__':
    main()
